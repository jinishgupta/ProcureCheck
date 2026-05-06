/**
 * ProcureCheck API Client
 * Centralized API functions for communicating with the backend
 */

const API_BASE = 'http://localhost:8000/api'

// ─── Helpers ──────────────────────────────────────────────

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `API error ${res.status}`)
  }
  return res.json()
}

// ─── Tenders ──────────────────────────────────────────────

export async function getTenders() {
  return request('/tenders/')
}

export async function getTender(tenderId) {
  return request(`/tenders/${tenderId}`)
}

export async function createTender({ title, department, estimatedValue, issueDate, closingDate }) {
  return request('/tenders/', {
    method: 'POST',
    body: JSON.stringify({
      title,
      department,
      estimated_value: estimatedValue || null,
      issue_date: issueDate || null,
      closing_date: closingDate || null,
    }),
  })
}

export async function uploadTenderPDF(tenderId, file) {
  const formData = new FormData()
  formData.append('file', file)

  const url = `${API_BASE}/tenders/${tenderId}/upload`
  const res = await fetch(url, { method: 'POST', body: formData })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Upload error ${res.status}`)
  }
  return res.json()
}

export async function deleteTender(tenderId) {
  return request(`/tenders/${tenderId}`, { method: 'DELETE' })
}

// ─── Criteria ─────────────────────────────────────────────

export async function getCriteria(tenderId) {
  const query = tenderId ? `?tender_id=${tenderId}` : ''
  return request(`/criteria/${query}`)
}

// ─── Bidders ──────────────────────────────────────────────

export async function getBidders(tenderId) {
  const query = tenderId ? `?tender_id=${tenderId}` : ''
  return request(`/bidders/${query}`)
}

// ─── Dashboard ────────────────────────────────────────────

export async function getDashboardStats() {
  return request('/dashboard/stats')
}

// ─── Evaluations ──────────────────────────────────────────

export async function getEvaluationMatrix(tenderId) {
  return request(`/evaluations/matrix/${tenderId}`)
}

// ─── Review Queue ─────────────────────────────────────────

export async function getReviewQueue(tenderId) {
  return request(`/review-queue/${tenderId}`)
}

// ─── Audit Trail ──────────────────────────────────────────

export async function getAuditTrail(tenderId) {
  return request(`/audit-trail/${tenderId}`)
}
