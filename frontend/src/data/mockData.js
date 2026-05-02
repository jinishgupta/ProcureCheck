// Mock data for ProcureCheck frontend

export const tenderOverview = {
  id: 'CRPF-2026-IT-0042',
  title: 'Supply of Ballistic Helmets (BIS IS 17051:2018)',
  issueDate: '2026-03-15',
  closingDate: '2026-04-30',
  department: 'Central Reserve Police Force — Procurement Directorate',
  estimatedValue: '₹12.8 Cr',
  totalPages: 287,
  extractedCriteria: 24,
  corrigenda: 2,
}

export const extractedCriteria = [
  { id: 1, field: 'Annual Turnover (Last 3 FY)', type: 'financial', requirement: '≥ ₹15 Crore average annual turnover for FY 2023-24, 2024-25, 2025-26', mandatory: true, source: 'Section 4.2.1(a)', unresolvedRef: null },
  { id: 2, field: 'BIS License for IS 17051:2018', type: 'certification', requirement: 'Valid BIS license for manufacturing ballistic helmets as per IS 17051:2018', mandatory: true, source: 'Section 4.2.3', unresolvedRef: null },
  { id: 3, field: 'Past Supply Experience', type: 'experience', requirement: 'Minimum 3 completed orders of similar items to any Central/State Govt agency in last 5 years', mandatory: true, source: 'Section 4.2.2', unresolvedRef: 'As defined in Annexure-IV (completion certificate format)' },
  { id: 4, field: 'Net Worth (Positive)', type: 'financial', requirement: 'Positive net worth as on 31.03.2026 certified by CA', mandatory: true, source: 'Section 4.2.1(b)', unresolvedRef: null },
  { id: 5, field: 'EMD Submission', type: 'financial', requirement: 'EMD of ₹25,60,000 via BG/FDR/DD', mandatory: true, source: 'Section 3.1', unresolvedRef: null },
  { id: 6, field: 'GST Registration', type: 'certification', requirement: 'Valid GSTIN with active status', mandatory: true, source: 'Section 4.2.4(a)', unresolvedRef: null },
  { id: 7, field: 'PAN Card', type: 'certification', requirement: 'Valid PAN of the bidding entity', mandatory: true, source: 'Section 4.2.4(b)', unresolvedRef: null },
  { id: 8, field: 'V50 Ballistic Test Report', type: 'technical', requirement: 'V50 ≥ 610 m/s for 9mm FMJ at NIJ Level IIIA or equivalent BIS test', mandatory: true, source: 'Section 5.3.1', unresolvedRef: null },
  { id: 9, field: 'Helmet Weight', type: 'technical', requirement: '≤ 1.45 kg (Size Large) including padding and retention system', mandatory: true, source: 'Section 5.3.4', unresolvedRef: null },
  { id: 10, field: 'Manufacturing Facility', type: 'technical', requirement: 'Own manufacturing unit with ISO 9001:2015 certification', mandatory: false, source: 'Section 4.3.1', unresolvedRef: null },
  { id: 11, field: 'Warranty Period', type: 'technical', requirement: 'Minimum 5 years from date of delivery', mandatory: true, source: 'Section 6.2', unresolvedRef: null },
  { id: 12, field: 'Blacklisting Declaration', type: 'certification', requirement: 'Self-declaration of non-blacklisting by any Govt. agency', mandatory: true, source: 'Section 4.2.5', unresolvedRef: null },
]

export const bidders = [
  { id: 'B1', name: 'Armour Systems Pvt Ltd', location: 'Bangalore, KA', documents: 42, ocrConfidence: 0.94 },
  { id: 'B2', name: 'ShieldTech Industries', location: 'Kanpur, UP', documents: 38, ocrConfidence: 0.87 },
  { id: 'B3', name: 'Kavach Defence Corp', location: 'Pune, MH', documents: 45, ocrConfidence: 0.91 },
  { id: 'B4', name: 'Surya Protective Gear', location: 'Hyderabad, TS', documents: 31, ocrConfidence: 0.72 },
]

export const matrixData = {
  'B1': {
    1: { verdict: 'PASS', confidence: 0.96, extractedValue: '₹18.4 Cr (avg)', method: 'regex', sourcePage: 'Page 12', signals: { extraction: 0.99, ocr: 0.95, retrieval: 0.98, llm: 1.0 }, explanation: 'Turnover extracted from audited balance sheets. Average of ₹17.2Cr, ₹19.1Cr, ₹18.9Cr = ₹18.4Cr exceeds ₹15Cr threshold.' },
    2: { verdict: 'PASS', confidence: 0.98, extractedValue: 'BIS/CML/4721890', method: 'regex', sourcePage: 'Page 23', signals: { extraction: 0.99, ocr: 0.98, retrieval: 0.99, llm: 1.0 }, explanation: 'Valid BIS license number matched against IS 17051:2018 standard reference.' },
    3: { verdict: 'PASS', confidence: 0.93, extractedValue: '5 orders found', method: 'llm', sourcePage: 'Pages 28-34', signals: { extraction: 0.95, ocr: 0.94, retrieval: 0.97, llm: 0.95 }, explanation: 'Five completed supply orders to BSF, CISF, and Army identified with completion certificates.' },
    8: { verdict: 'PASS', confidence: 0.95, extractedValue: 'V50 = 648 m/s', method: 'regex', sourcePage: 'Page 41', signals: { extraction: 0.98, ocr: 0.95, retrieval: 0.99, llm: 1.0 }, explanation: 'V50 value of 648 m/s exceeds minimum threshold of 610 m/s.' },
    9: { verdict: 'PASS', confidence: 0.97, extractedValue: '1.38 kg', method: 'regex', sourcePage: 'Page 42', signals: { extraction: 0.99, ocr: 0.96, retrieval: 0.99, llm: 1.0 }, explanation: 'Weight of 1.38 kg is within the 1.45 kg limit.' },
  },
  'B2': {
    1: { verdict: 'REVIEW', confidence: 0.73, extractedValue: '₹14.8 Cr (avg)', method: 'llm', sourcePage: 'Page 8', signals: { extraction: 0.88, ocr: 0.87, retrieval: 0.92, llm: 0.82 }, explanation: 'Extracted turnover ₹14.8Cr is close to but below ₹15Cr threshold. OCR confidence on scanned balance sheet is moderate.' },
    2: { verdict: 'PASS', confidence: 0.91, extractedValue: 'BIS/CML/5102344', method: 'regex', sourcePage: 'Page 18', signals: { extraction: 0.98, ocr: 0.89, retrieval: 0.97, llm: 1.0 }, explanation: 'BIS license found and verified.' },
    3: { verdict: 'FAIL', confidence: 0.92, extractedValue: '2 orders found', method: 'llm', sourcePage: 'Pages 22-25', signals: { extraction: 0.95, ocr: 0.88, retrieval: 0.96, llm: 0.94 }, explanation: 'Only 2 completed orders found, below the minimum 3 required.' },
    8: { verdict: 'PASS', confidence: 0.94, extractedValue: 'V50 = 635 m/s', method: 'regex', sourcePage: 'Page 31', signals: { extraction: 0.98, ocr: 0.90, retrieval: 0.98, llm: 1.0 }, explanation: 'V50 of 635 m/s exceeds 610 m/s threshold.' },
    9: { verdict: 'REVIEW', confidence: 0.68, extractedValue: '1.44 kg (unclear)', method: 'llm', sourcePage: 'Page 32', signals: { extraction: 0.82, ocr: 0.72, retrieval: 0.95, llm: 0.85 }, explanation: 'Weight value partially obscured in scanned document. Extracted 1.44 kg is very close to 1.45 kg limit.' },
  },
  'B3': {
    1: { verdict: 'PASS', confidence: 0.97, extractedValue: '₹22.1 Cr (avg)', method: 'regex', sourcePage: 'Page 14', signals: { extraction: 0.99, ocr: 0.92, retrieval: 0.99, llm: 1.0 }, explanation: 'Average turnover ₹22.1Cr substantially exceeds ₹15Cr requirement.' },
    2: { verdict: 'PASS', confidence: 0.96, extractedValue: 'BIS/CML/4890112', method: 'regex', sourcePage: 'Page 20', signals: { extraction: 0.99, ocr: 0.93, retrieval: 0.98, llm: 1.0 }, explanation: 'Valid BIS license confirmed.' },
    3: { verdict: 'PASS', confidence: 0.94, extractedValue: '7 orders found', method: 'llm', sourcePage: 'Pages 26-38', signals: { extraction: 0.96, ocr: 0.91, retrieval: 0.97, llm: 0.96 }, explanation: 'Seven completed orders to various defence agencies identified.' },
    8: { verdict: 'REVIEW', confidence: 0.78, extractedValue: 'V50 = 605 m/s (?)', method: 'llm', sourcePage: 'Page 44', signals: { extraction: 0.85, ocr: 0.91, retrieval: 0.96, llm: 0.82 }, explanation: 'Extracted V50 of 605 m/s is below 610 m/s threshold but extraction confidence is moderate due to table formatting.' },
    9: { verdict: 'PASS', confidence: 0.95, extractedValue: '1.32 kg', method: 'regex', sourcePage: 'Page 45', signals: { extraction: 0.99, ocr: 0.92, retrieval: 0.98, llm: 1.0 }, explanation: 'Weight of 1.32 kg is well within limit.' },
  },
  'B4': {
    1: { verdict: 'FAIL', confidence: 0.94, extractedValue: '₹9.2 Cr (avg)', method: 'regex', sourcePage: 'Page 6', signals: { extraction: 0.97, ocr: 0.72, retrieval: 0.96, llm: 1.0 }, explanation: 'Average turnover ₹9.2Cr is significantly below ₹15Cr requirement.' },
    2: { verdict: 'REVIEW', confidence: 0.55, extractedValue: 'Not found', method: 'llm', sourcePage: 'N/A', signals: { extraction: 0.60, ocr: 0.72, retrieval: 0.65, llm: 0.70 }, explanation: 'BIS license not found in submitted documents. Low retrieval score suggests document may be missing.' },
    3: { verdict: 'REVIEW', confidence: 0.62, extractedValue: '3 orders (unverified)', method: 'llm', sourcePage: 'Pages 15-19', signals: { extraction: 0.78, ocr: 0.72, retrieval: 0.88, llm: 0.75 }, explanation: 'Three work orders found but completion certificates could not be matched. ±2% tolerance check failed.' },
    8: { verdict: 'FAIL', confidence: 0.91, extractedValue: 'V50 = 580 m/s', method: 'regex', sourcePage: 'Page 24', signals: { extraction: 0.97, ocr: 0.75, retrieval: 0.96, llm: 1.0 }, explanation: 'V50 of 580 m/s is below 610 m/s threshold.' },
    9: { verdict: 'PASS', confidence: 0.90, extractedValue: '1.41 kg', method: 'regex', sourcePage: 'Page 25', signals: { extraction: 0.98, ocr: 0.74, retrieval: 0.97, llm: 1.0 }, explanation: 'Weight within limit despite lower OCR confidence.' },
  },
}

export const reviewItems = [
  { id: 'R1', criterion: 'Annual Turnover (Last 3 FY)', bidder: 'ShieldTech Industries', confidence: 0.73, extractedValue: '₹14.8 Cr', requiredValue: '≥ ₹15 Crore', urgency: 'high', reason: 'Extracted value ₹14.8Cr is within 1.3% of threshold. Scanned balance sheet has moderate OCR confidence (87%). Manual verification recommended.', signals: { extraction: 0.88, ocr: 0.87, retrieval: 0.92, llm: 0.82 }, sourcePage: 'Page 8' },
  { id: 'R2', criterion: 'V50 Ballistic Test Report', bidder: 'Kavach Defence Corp', confidence: 0.78, extractedValue: 'V50 = 605 m/s', requiredValue: '≥ 610 m/s', urgency: 'high', reason: 'V50 value extracted as 605 m/s from a complex table layout. LLM confidence moderate. Value is 0.8% below threshold.', signals: { extraction: 0.85, ocr: 0.91, retrieval: 0.96, llm: 0.82 }, sourcePage: 'Page 44' },
  { id: 'R3', criterion: 'BIS License for IS 17051:2018', bidder: 'Surya Protective Gear', confidence: 0.55, extractedValue: 'Not found', requiredValue: 'Valid BIS license', urgency: 'medium', reason: 'No BIS license document detected in submission. Retrieval score is low — document may have been uploaded to wrong section or omitted entirely.', signals: { extraction: 0.60, ocr: 0.72, retrieval: 0.65, llm: 0.70 }, sourcePage: 'N/A' },
  { id: 'R4', criterion: 'Helmet Weight', bidder: 'ShieldTech Industries', confidence: 0.68, extractedValue: '1.44 kg', requiredValue: '≤ 1.45 kg', urgency: 'medium', reason: 'Weight value partially obscured in scanned test report. Value 1.44kg is 0.7% from limit. OCR confidence 72% on this page.', signals: { extraction: 0.82, ocr: 0.72, retrieval: 0.95, llm: 0.85 }, sourcePage: 'Page 32' },
  { id: 'R5', criterion: 'Past Supply Experience', bidder: 'Surya Protective Gear', confidence: 0.62, extractedValue: '3 orders (unverified)', requiredValue: '≥ 3 completed orders', urgency: 'low', reason: 'Work orders found but completion certificates do not match within ±2% tolerance on values. Company name slightly differs between documents.', signals: { extraction: 0.78, ocr: 0.72, retrieval: 0.88, llm: 0.75 }, sourcePage: 'Pages 15-19' },
]

export const auditLogs = [
  { id: 'A1', timestamp: '2026-04-30 14:23:01', action: 'TENDER_UPLOADED', officer: 'Col. R.K. Sharma', detail: 'Tender CRPF-2026-IT-0042 uploaded (287 pages)', docHash: 'a3f2c891...d4e7', version: '1.0' },
  { id: 'A2', timestamp: '2026-04-30 14:23:45', action: 'OCR_COMPLETED', officer: 'System', detail: 'OCR processing complete. 143 native + 144 scanned pages. Avg OCR confidence: 91.2%', docHash: 'a3f2c891...d4e7', version: '1.0' },
  { id: 'A3', timestamp: '2026-04-30 14:28:12', action: 'CRITERIA_EXTRACTED', officer: 'System', detail: '24 eligibility criteria extracted. 1 unresolved cross-reference flagged.', docHash: 'a3f2c891...d4e7', version: '1.0' },
  { id: 'A4', timestamp: '2026-04-30 15:10:00', action: 'CORRIGENDUM_APPLIED', officer: 'Col. R.K. Sharma', detail: 'Corrigendum #2 applied. Section 5.3.4 weight limit changed from 1.50 to 1.45 kg.', docHash: 'b7d1e345...f2a9', version: '1.2' },
  { id: 'A5', timestamp: '2026-04-30 16:45:22', action: 'BIDDER_UPLOADED', officer: 'System', detail: 'Bidder "Armour Systems Pvt Ltd" — 42 documents processed. OCR confidence: 94%', docHash: 'c4a8f912...e3b1', version: '1.2' },
  { id: 'A6', timestamp: '2026-04-30 16:52:10', action: 'BIDDER_UPLOADED', officer: 'System', detail: 'Bidder "ShieldTech Industries" — 38 documents processed. OCR confidence: 87%', docHash: 'd9c2b478...a1f6', version: '1.2' },
  { id: 'A7', timestamp: '2026-04-30 17:01:33', action: 'EVALUATION_STARTED', officer: 'System', detail: 'Automated matching evaluation initiated for 4 bidders × 24 criteria.', docHash: null, version: '1.2' },
  { id: 'A8', timestamp: '2026-04-30 17:15:44', action: 'EVALUATION_COMPLETE', officer: 'System', detail: 'Evaluation complete. 68 PASS, 8 FAIL, 20 REVIEW across all bidders.', docHash: null, version: '1.2' },
  { id: 'A9', timestamp: '2026-05-01 09:30:00', action: 'REVIEW_CONFIRMED', officer: 'Maj. P. Singh', detail: 'ShieldTech turnover REVIEW → confirmed as FAIL. Officer note: "Balance sheet figure is ₹14.8Cr, below threshold."', docHash: null, version: '1.2' },
  { id: 'A10', timestamp: '2026-05-01 10:12:18', action: 'REVIEW_OVERRIDE', officer: 'Maj. P. Singh', detail: 'Kavach V50 REVIEW → overridden to PASS. Officer note: "Verified original test report — actual V50 is 612 m/s, table OCR error."', docHash: null, version: '1.2' },
  { id: 'A11', timestamp: '2026-05-01 11:00:00', action: 'REPORT_EXPORTED', officer: 'Col. R.K. Sharma', detail: 'PDF evaluation report exported. SHA-256: e8f9a2c1b3d4...', docHash: null, version: '1.2' },
]

export const dashboardStats = {
  activeTenders: 3,
  pendingReviews: 20,
  biddersEvaluated: 14,
  complianceRate: 71,
}

export const recentActivity = [
  { time: '2 min ago', text: 'Maj. P. Singh confirmed ShieldTech turnover as FAIL', type: 'review' },
  { time: '15 min ago', text: 'Kavach Defence V50 overridden to PASS', type: 'override' },
  { time: '1 hr ago', text: 'Evaluation completed for CRPF-2026-IT-0042', type: 'system' },
  { time: '2 hr ago', text: 'Surya Protective Gear documents uploaded (31 files)', type: 'upload' },
  { time: '3 hr ago', text: 'Corrigendum #2 applied — weight limit updated', type: 'update' },
  { time: '5 hr ago', text: 'Armour Systems Pvt Ltd documents uploaded (42 files)', type: 'upload' },
]
