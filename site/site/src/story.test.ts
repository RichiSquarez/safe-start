import assert from 'node:assert/strict'
import { stepForProgress } from './story.ts'

// ponytail: one boundary check protects the scroll-to-screen mapping.
assert.equal(stepForProgress(-1, 4), 0)
assert.equal(stepForProgress(0, 4), 0)
assert.equal(stepForProgress(0.25, 4), 1)
assert.equal(stepForProgress(0.5, 4), 2)
assert.equal(stepForProgress(0.999, 4), 3)
assert.equal(stepForProgress(1, 4), 3)
assert.equal(stepForProgress(2, 4), 3)
assert.equal(stepForProgress(Number.NaN, 4), 0)
assert.equal(stepForProgress(0.5, 0), 0)
console.log('scroll story boundaries passed')
