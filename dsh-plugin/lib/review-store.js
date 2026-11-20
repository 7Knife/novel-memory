// Pure helpers for the Novel Memory review queue.
// No DSH/Node imports here so this module can be tested with plain node:test.

export const SUGGESTION_KINDS = ['new', 'update', 'status_progression']
export const TRIGGERS = ['scene_end', 'chapter_final', 'canon_change', 'manual']
export const STATUSES = ['pending', 'approved', 'rejected', 'archived']

const normalize = (value) => String(value ?? '').replace(/\s+/g, ' ').trim()

// Chinese names often vary only by internal spacing; collapse it for dedup keys.
const normalizeKeyText = (value) => normalize(value).replace(/\s+/g, '').toLowerCase()

/** Stable dedup key: entity + kind + field + normalized setting. */
export function dedupKey(suggestion) {
  return [
    normalizeKeyText(suggestion.entity_key ?? suggestion.entity_name),
    suggestion.kind,
    normalizeKeyText(suggestion.field),
    normalizeKeyText(suggestion.setting)
  ].join('\u0000')
}

/** Validate the minimum fields needed before a suggestion can be queued. */
export function validateSuggestion(suggestion) {
  if (!suggestion || typeof suggestion !== 'object') return 'suggestion must be an object'
  if (!SUGGESTION_KINDS.includes(suggestion.kind)) return `invalid kind: ${suggestion.kind}`
  if (!normalize(suggestion.entity_name)) return 'entity_name is required'
  if (!normalize(suggestion.setting)) return 'setting is required'
  if (!Array.isArray(suggestion.evidence) || suggestion.evidence.length === 0) {
    return 'at least one evidence item is required'
  }
  for (const item of suggestion.evidence) {
    if (!item || !normalize(item.source_note) || !normalize(item.quote)) {
      return 'each evidence item needs source_note and quote'
    }
    if (!TRIGGERS.includes(item.trigger)) return `invalid trigger: ${item.trigger}`
  }
  return null
}

/**
 * Merge an incoming suggestion into pending entries.
 * Same dedup key: increment hits and merge unique evidence (max 8).
 */
export function mergeSuggestion(pending, incoming, now = new Date().toISOString()) {
  const error = validateSuggestion(incoming)
  if (error) throw new Error(error)

  const key = dedupKey(incoming)
  const existing = pending.find((entry) => dedupKey(entry) === key)
  if (existing) {
    existing.hits = (Number(existing.hits) || 1) + 1
    existing.last_seen = now
    const seen = new Set(existing.evidence.map((e) => `${e.source_note}:${e.paragraph}:${e.quote}`))
    for (const item of incoming.evidence) {
      const id = `${item.source_note}:${item.paragraph}:${item.quote}`
      if (!seen.has(id)) {
        existing.evidence.push(item)
        seen.add(id)
      }
    }
    existing.evidence = existing.evidence.slice(0, 8)
    if (incoming.confidence !== undefined) {
      existing.confidence = Math.max(Number(existing.confidence) || 0, Number(incoming.confidence))
    }
    return { entry: existing, created: false }
  }

  const entry = {
    ...incoming,
    entity_key: incoming.entity_key || normalize(incoming.entity_name).toLowerCase(),
    status: 'pending',
    hits: 1,
    first_seen: now,
    last_seen: now,
    created_by: incoming.created_by || 'main_llm'
  }
  pending.push(entry)
  return { entry, created: true }
}

/** Filter pending entries; status is always pending in the pending queue. */
export function listPending(pending, limit = 20) {
  return pending.filter((entry) => entry.status === 'pending').slice(0, Math.max(1, limit))
}

/** Mark suggestions approved/rejected/archived by 1-based index. */
export function decide(pending, indices, decision) {
  if (!STATUSES.includes(decision)) throw new Error(`invalid decision: ${decision}`)
  const changed = []
  for (const index of indices) {
    const entry = pending[index - 1]
    if (!entry || entry.status !== 'pending') continue
    entry.status = decision
    entry.decided_at = new Date().toISOString()
    changed.push(entry)
  }
  return changed
}

/** Render a compact list for CLI/command use. */
export function formatList(entries) {
  if (entries.length === 0) return 'No pending entity-review suggestions.'
  return entries.map((entry, index) => {
    const evidence = entry.evidence?.[0]
    const where = evidence ? `${evidence.source_note}:${evidence.paragraph ?? '?'}` : 'no evidence'
    return `${index + 1}. [${entry.kind}] ${entry.entity_name} — ${entry.setting} (hits=${entry.hits}, ${where})`
  }).join('\n')
}
