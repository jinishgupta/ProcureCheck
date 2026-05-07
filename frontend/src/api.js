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

// Export request for custom API calls
export { request }

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

export async function createBidder({ tenderId, name, location }) {
  return request('/bidders/', {
    method: 'POST',
    body: JSON.stringify({
      tender_id: tenderId,
      name,
      location,
      documents_count: 0,
      ocr_confidence: 0
    }),
  })
}

export async function uploadBidderDocuments(bidderId, files) {
  const formData = new FormData()
  files.forEach(file => {
    formData.append('files', file)
  })

  const url = `${API_BASE}/bidders/${bidderId}/upload`
  const res = await fetch(url, { method: 'POST', body: formData })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Upload error ${res.status}`)
  }
  return res.json()
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
