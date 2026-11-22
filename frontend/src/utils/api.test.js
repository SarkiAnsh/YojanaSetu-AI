import assert from 'node:assert/strict'
import test from 'node:test'
import { validateAnswer } from './api.js'

test('sends raw answers to the backend validation contract', async () => {
  const originalFetch = globalThis.fetch
  let request
  globalThis.fetch = async (url, options) => {
    request = { url, options }
    return {
      ok: true,
      json: async () => ({ valid: true, value: 'kutcha_house', error: null }),
    }
  }

  try {
    const result = await validateAnswer('housing_condition', 'kutcha house', 'en')
    assert.equal(request.url, '/api/validate-answer')
    assert.deepEqual(JSON.parse(request.options.body), {
      question_id: 'housing_condition',
      answer: 'kutcha house',
      lang: 'en',
    })
    assert.deepEqual(result, { valid: true, value: 'kutcha_house', error: null })
  } finally {
    globalThis.fetch = originalFetch
  }
})

test('preserves backend validation errors for invalid answers', async () => {
  const originalFetch = globalThis.fetch
  globalThis.fetch = async () => ({
    ok: true,
    json: async () => ({
      valid: false,
      value: null,
      error: 'Please choose one of the listed options.',
    }),
  })

  try {
    const result = await validateAnswer('housing_condition', 'maybe', 'en')
    assert.equal(result.valid, false)
    assert.equal(result.value, null)
    assert.match(result.error, /listed options/)
  } finally {
    globalThis.fetch = originalFetch
  }
})
