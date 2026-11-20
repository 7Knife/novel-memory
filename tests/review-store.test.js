import test from 'node:test'
import assert from 'node:assert/strict'

import {
  dedupKey,
  decide,
  formatList,
  listPending,
  mergeSuggestion,
  validateSuggestion
} from '../dsh-plugin/lib/review-store.js'

const sample = (overrides = {}) => ({
  kind: 'new',
  entity_name: '白塔监察院',
  setting: '以白塔为中心的新兴监察机构',
  evidence: [{
    source_note: 'vault/notes/scenes/ch03-s05.md',
    paragraph: 7,
    quote: '白塔的旗号从城门上降下。',
    trigger: 'canon_change'
  }],
  ...overrides
})

test('validateSuggestion requires evidence', () => {
  assert.equal(validateSuggestion(sample()), null)
  assert.match(validateSuggestion({ kind: 'new', entity_name: 'X', setting: 'Y', evidence: [] }), /evidence/)
})

test('dedupKey ignores whitespace differences', () => {
  assert.equal(
    dedupKey(sample({ entity_name: '  白塔 监察院 ', setting: ' 以白塔 为中心的新兴监察机构 ' })),
    dedupKey(sample())
  )
})

test('mergeSuggestion merges duplicates and increments hits', () => {
  const pending = []
  const first = mergeSuggestion(pending, sample(), '2026-01-01T00:00:00Z')
  const second = mergeSuggestion(pending, sample({ hits: 99 }), '2026-01-02T00:00:00Z')
  assert.equal(first.created, true)
  assert.equal(second.created, false)
  assert.equal(pending.length, 1)
  assert.equal(pending[0].hits, 2)
  assert.equal(pending[0].last_seen, '2026-01-02T00:00:00Z')
})

test('decide marks selected pending entries and listPending hides them', () => {
  const pending = []
  mergeSuggestion(pending, sample())
  mergeSuggestion(pending, sample({ entity_name: '黑鸦会', setting: '地下组织' }))
  const changed = decide(pending, [1], 'approved')
  assert.equal(changed.length, 1)
  assert.equal(listPending(pending).length, 1)
  assert.match(formatList(listPending(pending)), /黑鸦会/)
})
