/**
 * api.js — All calls to the FastAPI backend live here.
 *
 * Why: Keeping API calls in one place means if the backend URL
 * changes, you only update this one file.
 */

const BASE_URL = '/api'   // Vite proxy forwards this to http://localhost:8000

export async function checkBackendHealth() {
  const res = await fetch(`${BASE_URL}/health`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`Backend health check failed with HTTP ${res.status}.`)

  const data = await res.json()
  if (data.status !== 'ok') throw new Error('Backend health check returned an unexpected status.')
  return data
}

/**
 * Get the next question to ask the user.
 * @param {Object} profile - Answers collected so far
 * @param {string} lang    - "en" or "hi"
 */
export async function fetchNextQuestion(profile, lang = 'en') {
  const res = await fetch(`${BASE_URL}/next-question`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ profile, lang }),
  })
  if (!res.ok) throw new Error('Failed to fetch next question')
  return res.json()
  // Returns: { next_question: {...} | null, contradictions: [...], done: bool }
}

/**
 * Validate and normalize a raw answer using the backend's question contract.
 */
export async function validateAnswer(questionId, answer, lang = 'en') {
  const res = await fetch(`${BASE_URL}/validate-answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question_id: questionId, answer, lang }),
  })
  if (!res.ok) {
    let detail = `Answer validation failed with HTTP ${res.status}.`
    try {
      const data = await res.json()
      if (data.detail) detail = data.detail
    } catch {
      // Keep the HTTP status as the actionable fallback.
    }
    throw new Error(detail)
  }
  return res.json()
}

/**
 * Ask the configured AI provider to clarify a rule-based question.
 * The server supplies the authoritative question text and options.
 */
export async function clarifyQuestion(questionId, message, lang = 'en') {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question_id: questionId, message, lang }),
  })

  let data
  try {
    data = await res.json()
  } catch {
    throw new Error(`AI clarification failed with HTTP ${res.status}.`)
  }
  if (!res.ok) {
    throw new Error(data.detail || `AI clarification failed with HTTP ${res.status}.`)
  }
  return data
}

/**
 * Run the full eligibility check with all collected answers.
 * @param {Object} profile - All collected answers
 * @param {string} lang    - "en" or "hi"
 */
export async function checkEligibility(profile, lang = 'en') {
  const res = await fetch(`${BASE_URL}/check-eligibility`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ profile, lang }),
  })
  if (!res.ok) throw new Error('Failed to check eligibility')
  return res.json()
  // Returns: { results: [...], summary: {...}, contradictions: [...], disclaimer: "..." }
}

/**
 * Get list of all demo schemes (no personal data needed).
 * @param {string} lang - "en" or "hi"
 */
export async function fetchSchemes(lang = 'en') {
  const res = await fetch(`${BASE_URL}/schemes?lang=${lang}`)
  if (!res.ok) throw new Error('Failed to fetch schemes')
  return res.json()
}
