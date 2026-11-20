// Novel Memory — lightweight DSH host plugin.
//
// Scope boundary: this plugin does NOT inject a global system prompt and does NOT
// write a global memory store. It only manages entity-review suggestions and the
// user confirmation queue. Applying confirmed suggestions to Basic Memory is left
// to the main agent through bm_write/bm_edit.

import { randomUUID } from 'node:crypto'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

import {
  decide,
  formatList,
  listPending,
  mergeSuggestion
} from './lib/review-store.js'

export const inject = ['tools']

function expandHome(input, fallback) {
  const raw = String(input ?? '').trim()
  if (!raw) return path.resolve(fallback)
  if (raw === '~') return os.homedir()
  if (raw.startsWith('~/') || raw.startsWith('~\\')) {
    return path.join(os.homedir(), raw.slice(2))
  }
  return path.resolve(raw)
}

function readJsonl(file) {
  if (!fs.existsSync(file)) return []
  const rows = []
  for (const line of fs.readFileSync(file, 'utf8').split('\n')) {
    if (!line.trim()) continue
    try {
      const row = JSON.parse(line)
      if (row && typeof row === 'object') rows.push(row)
    } catch {
      // A damaged line must not make the whole queue unreadable.
    }
  }
  return rows
}

function writeJsonl(file, rows) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  const tmp = `${file}.tmp-${process.pid}`
  fs.writeFileSync(tmp, rows.map((row) => JSON.stringify(row)).join('\n') + (rows.length ? '\n' : ''), 'utf8')
  fs.renameSync(tmp, file)
}

export function apply(ctx, config = {}) {
  const reviewDir = expandHome(config.reviewDir, path.join(os.homedir(), '.dsh', 'novel-memory', 'reviews'))
  const listLimit = Math.max(1, Number(config.listLimit) || 20)
  const pendingFile = path.join(reviewDir, 'pending.jsonl')
  const historyFile = path.join(reviewDir, 'history.jsonl')
  const disposers = []

  ctx.effect(() => () => {
    for (const dispose of disposers.reverse()) {
      try { dispose() } catch { /* cleanup must not throw */ }
    }
  })

  function loadPending() {
    return readJsonl(pendingFile).filter((row) => row.status !== undefined ? row.status === 'pending' : true)
  }

  function savePending(rows) {
    writeJsonl(pendingFile, rows)
  }

  function appendHistory(rows) {
    if (rows.length === 0) return
    const current = readJsonl(historyFile)
    writeJsonl(historyFile, [...current, ...rows])
  }

  function register(tool) {
    const dispose = ctx.tools.register(tool)
    if (typeof dispose === 'function') disposers.push(dispose)
  }

  register({
    name: 'novel_entity_review',
    description:
      'Queue entity-level setting suggestions from the current scene. Never writes Basic Memory notes and never changes global settings. Each suggestion needs entity_name, setting, and evidence with source_note, paragraph, quote, and trigger.',
    parameters: {
      suggestions: {
        type: 'array',
        required: true,
        description: 'Suggestions to queue. Each item: kind(new|update|status_progression), entity_name, entity_type?, field?, setting, current_canon_status?, proposed_canon_status?, superseded?, evidence[]'
      }
    },
    isConcurrencySafe: () => false,
    async execute(args) {
      const input = Array.isArray(args?.suggestions)
        ? args.suggestions
        : (args?.suggestion ? [args.suggestion] : [])
      if (input.length === 0) return 'No suggestions provided.'

      const pending = loadPending()
      const now = new Date().toISOString()
      const added = []
      const merged = []
      for (const suggestion of input) {
        const withId = {
          ...suggestion,
          id: suggestion.id || randomUUID(),
          created_by: suggestion.created_by || 'main_llm'
        }
        const result = mergeSuggestion(pending, withId, now)
        if (result.created) added.push(result.entry.id)
        else merged.push(result.entry.id)
      }
      savePending(pending)
      return `Queued ${added.length} new suggestion(s), merged ${merged.length} duplicate(s). Pending total: ${loadPending().length}.`
    }
  })

  register({
    name: 'novel_review_list',
    description: 'List pending entity-review suggestions with evidence location.',
    parameters: {
      limit: { type: 'integer', description: `Maximum entries to show (default ${listLimit}).` }
    },
    isConcurrencySafe: () => true,
    async execute(args) {
      const limit = Math.min(100, Math.max(1, Number(args?.limit) || listLimit))
      return formatList(listPending(loadPending(), limit))
    }
  })

  register({
    name: 'novel_review_decide',
    description:
      'Approve, reject, or archive pending suggestions by 1-based index. Approval does not write Basic Memory directly; it returns the confirmed entries so the main agent can apply them with bm_write/bm_edit.',
    parameters: {
      decision: {
        type: 'string',
        required: true,
        enum: ['approve', 'reject', 'archive'],
        description: 'approve=confirmed, reject=dropped, archive=kept without applying'
      },
      indices: {
        type: 'array',
        required: true,
        description: '1-based indices from novel_review_list, e.g. [1,3]'
      }
    },
    isConcurrencySafe: () => false,
    async execute(args) {
      const decisionArg = String(args?.decision ?? '').trim()
      const map = { approve: 'approved', reject: 'rejected', archive: 'archived' }
      const decision = map[decisionArg]
      if (!decision) return 'decision must be approve, reject, or archive.'
      const indices = (Array.isArray(args?.indices) ? args.indices : [])
        .map((n) => Number(n))
        .filter((n) => Number.isInteger(n) && n >= 1)
      if (indices.length === 0) return 'indices must contain at least one positive integer.'

      const pending = loadPending()
      const changed = decide(pending, indices, decision)
      if (changed.length === 0) return 'No matching pending suggestions.'

      const remaining = pending.filter((row) => row.status === 'pending')
      savePending(remaining)
      appendHistory(changed)

      if (decision !== 'approved') {
        return `${decisionArg} ${changed.length} suggestion(s). Remaining pending: ${remaining.length}.`
      }
      return [
        `Approved ${changed.length} suggestion(s). Remaining pending: ${remaining.length}.`,
        'Apply them in Basic Memory with bm_write/bm_edit, preserving superseded values and evidence.',
        JSON.stringify(changed, null, 2)
      ].join('\n')
    }
  })

  // Command surface is optional; if the host has no commands service, tools still work.
  ctx.inject(['commands'], (cmdCtx) => {
    const dispose = cmdCtx.commands.register({
      name: 'novel-review',
      description: 'List or decide entity-review suggestions: list | approve <n>... | reject <n>... | archive <n>...',
      input: { hint: 'list | approve <n>... | reject <n>... | archive <n>...' },
      handler(invocation) {
        const tokens = String(invocation.rawInput ?? '').trim().split(/\s+/).filter(Boolean)
        const op = (tokens[0] ?? 'list').toLowerCase()
        const indices = tokens.slice(1).map((n) => Number(n)).filter((n) => Number.isInteger(n) && n >= 1)
        if (op === 'list') {
          return { kind: 'success', text: formatList(listPending(loadPending(), listLimit)) }
        }
        if (['approve', 'reject', 'archive'].includes(op)) {
          if (indices.length === 0) return { kind: 'error', text: `${op} needs at least one index.` }
          const pending = loadPending()
          const status = { approve: 'approved', reject: 'rejected', archive: 'archived' }[op]
          const changed = decide(pending, indices, status)
          if (changed.length === 0) return { kind: 'error', text: 'No matching pending suggestions.' }
          savePending(pending.filter((row) => row.status === 'pending'))
          appendHistory(changed)
          return { kind: 'success', text: `${op} ${changed.length} suggestion(s).` }
        }
        return { kind: 'success', text: 'Usage: /novel-review list | approve <n>... | reject <n>... | archive <n>...' }
      }
    })
    if (typeof dispose === 'function') disposers.push(dispose)
  })
}
