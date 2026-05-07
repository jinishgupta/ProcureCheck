"""
matching/engine.py  —  Stage 3: Matching & Evaluation

Consumes the per-bidder FAISS index your teammate built in Stage 2
and writes evaluation results directly to the database.

─────────────────────────────────────────────────────────────────
INTERFACE CONTRACT WITH YOUR TEAMMATE (bidder side)
─────────────────────────────────────────────────────────────────
For every bidder, they must produce TWO files in:
    data/bidder_indexes/{bidder_id}/

1. faiss.index      — FAISS IndexFlatIP, vectors L2-normalised,
                      built with model: all-MiniLM-L6-v2

2. pages.json       — JSON array, one object per indexed page:
    [
      {
        "page_number":    12,
        "text":           "raw OCR text of the page...",
        "label":          "[balance_sheet | page 12]",
        "ocr_confidence": 0.94
      },
      ...
    ]

Nothing else is needed from them. Everything below is self-contained.
─────────────────────────────────────────────────────────────────
"""

import os
import re
import json
import math
import uuid
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Optional, Any


from db.database import Database
from db.models import CriterionType, Verdict, ExtractionMethod

# ── Config ───────────────────────────────────────────────────────────────────

# Where your teammate drops the FAISS index + pages.json per bidder
BIDDER_INDEX_DIR = Path("data/bidder_indexes")

# Confidence thresholds (from spec)
REGEX_CONFIDENCE_GATE   = 0.90   # skip LLM if regex hits this
VERDICT_PASS_FAIL_GATE  = 0.70   # below this → always REVIEW (lowered to get more PASS/FAIL)
RETRIEVAL_EVIDENCE_GATE = 0.50   # below this → "evidence not found" → REVIEW

# Groq/Llama model for extraction and evaluation (free tier, better limits than Gemini)
GROQ_MODEL = "llama-3.3-70b-versatile"

# Embedding model — same as KeyBERT already loaded elsewhere in the project
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

# Lazy singletons — deferred to avoid importing PyTorch/faiss at startup
# (Render's port-scan would time out before uvicorn could bind otherwise).

_embedder: Optional[Any] = None

def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer  # noqa: deferred
        _embedder = SentenceTransformer(EMBED_MODEL_NAME)
    return _embedder

def _get_faiss():
    """Return the faiss module, importing it lazily."""
    import faiss  # noqa: deferred
    return faiss


def _get_groq_client():
    """Get Groq client for Llama model (better free tier than Gemini)."""
    from db.config import settings
    from groq import Groq
    return Groq(api_key=settings.groq_api_key)


# ── Criterion type → pipeline type ───────────────────────────────────────────
#
# The DB stores: FINANCIAL, TECHNICAL, CERTIFICATION, EXPERIENCE
# The pipeline works with: numeric, boolean, fuzzy
#
# FINANCIAL    → numeric   (turnover, net worth, EMD — all have ₹ thresholds)
# CERTIFICATION→ boolean   (GST, PAN, BIS, blacklisting — keyword presence)
# EXPERIENCE   → fuzzy     (past orders, years — need LLM to count/assess)
# TECHNICAL    → numeric   if requirement has ≥/≤/> + unit (V50, weight, speed)
#                fuzzy     otherwise (manufacturing facility, ISO cert text)

def _infer_pipeline_type(db_type: str, requirement: str) -> str:
    db_type = db_type.upper()
    if db_type == "FINANCIAL":
        return "numeric"
    if db_type == "CERTIFICATION":
        return "boolean"
    if db_type == "EXPERIENCE":
        return "fuzzy"
    if db_type == "TECHNICAL":
        # has a numeric threshold in the requirement?
        if re.search(r"[≥≤<>]=?\s*[\d]", requirement):
            return "numeric"
        return "fuzzy"
    return "fuzzy"


# ── Retrieval query templates ─────────────────────────────────────────────────

def _build_retrieval_query(field: str, pipeline_type: str) -> str:
    templates = {
        "numeric": f"{field} value amount figure turnover crore lakh net worth",
        "boolean": f"{field} certificate registration number valid issued",
        "fuzzy":   f"{field} completed similar work order experience project",
    }
    return templates.get(pipeline_type, field)


# ── Load bidder index ─────────────────────────────────────────────────────────

def _load_bidder_index(bidder_id: str) -> tuple:
    """
    Load the FAISS index and pages metadata your teammate produced.
    Raises FileNotFoundError with a helpful message if missing.
    """
    index_dir = BIDDER_INDEX_DIR / bidder_id

    index_path = index_dir / "faiss.index"
    pages_path = index_dir / "pages.json"

    if not index_path.exists():
        raise FileNotFoundError(
            f"FAISS index not found for bidder {bidder_id}. "
            f"Expected: {index_path}. "
            "Make sure your teammate has run the bidder ingestion pipeline first."
        )
    if not pages_path.exists():
        raise FileNotFoundError(
            f"pages.json not found for bidder {bidder_id}. "
            f"Expected: {pages_path}."
        )

    index = _get_faiss().read_index(str(index_path))
    with open(pages_path, encoding="utf-8") as f:
        pages = json.load(f)

    return index, pages


# ── FAISS retrieval ───────────────────────────────────────────────────────────

def _retrieve_pages(
    query: str,
    index: Any,
    pages: list[dict],
    top_k: int = 3,
) -> list[dict]:
    """
    Embed the query, search the FAISS index, return top-k page dicts
    each annotated with a 'retrieval_score' key.
    """
    embedder = _get_embedder()
    q_vec = embedder.encode([query], normalize_embeddings=True).astype("float32")

    scores, indices = index.search(q_vec, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(pages):
            continue
        page = dict(pages[idx])           # copy so we don't mutate the list
        page["retrieval_score"] = float(score)
        results.append(page)

    return results


# ── Regex extraction ──────────────────────────────────────────────────────────

# ₹ / Rs. / INR  followed by a number and optional crore/lakh unit
_MONEY_RE = re.compile(
    r"(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d+)?)\s*(crore?|cr\.?|lakh|lac|l\.?)",
    re.IGNORECASE,
)
# dd/mm/yyyy, dd-mm-yyyy, Month YYYY
_DATE_RE = re.compile(
    r"\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4}"
    r"|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?"
    r"|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"\.?\s+\d{4})",
    re.IGNORECASE,
)
# Common boolean keywords found in Indian tender documents
_BOOL_PATTERNS: dict[str, re.Pattern] = {
    "gst":            re.compile(r"\bGST(?:IN)?\s*(?:No\.?|Registration|Number)?\s*[:\-]?\s*[0-9A-Z]{15}", re.I),
    "pan":            re.compile(r"\bPAN\b.*?[A-Z]{5}[0-9]{4}[A-Z]", re.I),
    "bis":            re.compile(r"\bBIS\b|\bBIS/CML/\d+", re.I),
    "iso":            re.compile(r"\bISO\s*9001", re.I),
    "epf":            re.compile(r"\bEPF\b|\bProvident\s+Fund\b", re.I),
    "esic":           re.compile(r"\bESIC\b|\bEmployee\s+State\s+Insurance\b", re.I),
    "msme":           re.compile(r"\bMSME\b|\bUdyam\b", re.I),
    "blacklist":      re.compile(r"not\s+blacklist|non.?blacklist|debarr?ment", re.I),
    "incorporation":  re.compile(r"Certificate\s+of\s+Incorporation", re.I),
    "integrity":      re.compile(r"Integrity\s+Pact", re.I),
}

def _to_inr(value: float, unit: str) -> float:
    u = unit.lower().strip(". ")
    if u in ("crore", "cr"):
        return value * 1e7
    if u in ("lakh", "lac", "l"):
        return value * 1e5
    return value


def _regex_extract_numeric(text: str) -> tuple[Optional[str], Optional[float], float]:
    """Returns (raw_string, canonical_inr, confidence)."""
    matches = _MONEY_RE.findall(text)
    if not matches:
        return None, None, 0.0

    candidates = []
    for num_str, unit in matches:
        # Skip empty strings
        if not num_str or not num_str.strip():
            continue
        try:
            val = float(num_str.replace(",", ""))
            canonical = _to_inr(val, unit)
            candidates.append((canonical, f"{num_str} {unit}"))
        except ValueError:
            # Skip invalid numbers
            continue

    if not candidates:
        return None, None, 0.0

    best_canonical, best_raw = max(candidates, key=lambda c: c[0])
    conf = 0.95 if len(matches) == 1 else 0.90
    return best_raw, best_canonical, conf


def _regex_extract_boolean(text: str, field_name: str) -> tuple[Optional[str], Optional[bool], float]:
    """Returns (raw_match, True/None, confidence)."""
    field_lower = field_name.lower()

    # Try field-specific pattern first
    for key, pattern in _BOOL_PATTERNS.items():
        if key in field_lower:
            m = pattern.search(text)
            if m:
                return m.group(0), True, 0.97

    # Generic fallback: does any boolean pattern match at all?
    for pattern in _BOOL_PATTERNS.values():
        m = pattern.search(text)
        if m:
            return m.group(0), True, 0.85

    return None, None, 0.0


def _regex_extract(
    pipeline_type: str, field: str, text: str
) -> tuple[Optional[str], Optional[float | bool], float]:
    """Unified entry point. Returns (raw, canonical, confidence)."""
    if pipeline_type == "numeric":
        return _regex_extract_numeric(text)
    if pipeline_type == "boolean":
        raw, val, conf = _regex_extract_boolean(text, field)
        return raw, val, conf
    return None, None, 0.0   # fuzzy → always goes to LLM


# ── LLM extraction ────────────────────────────────────────────────────────────

_EXTRACT_SYSTEM = (
    "You are a document extraction assistant for government tender evaluation. "
    "Extract ONLY the requested field from the document excerpt. "
    "Return JSON with exactly these keys: value (string|number|null), unit (string|null), confidence (0.0-1.0). "
    "If the field is not present, return {\"value\": null, \"unit\": null, \"confidence\": 0.0}. "
    "Do NOT guess or invent values."
)

def _llm_extract(field: str, pipeline_type: str, page_text: str) -> tuple[Optional[str], Optional[float | str], float]:
    """Returns (raw, canonical, confidence)."""
    prompt = (
        f"{_EXTRACT_SYSTEM}\n\n"
        f"Field to extract: {field} (type: {pipeline_type})\n\n"
        f"Document excerpt (first 3000 chars):\n{page_text[:3000]}\n\n"
        "Return JSON only. Example: {{\"value\": \"50 lakh\", \"unit\": \"lakh\", \"confidence\": 0.82}}"
    )
    
    try:
        client = _get_groq_client()
        resp = client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=150,
            messages=[{"role": "system", "content": _EXTRACT_SYSTEM}, {"role": "user", "content": prompt}]
        )
        
        raw_text = resp.choices[0].message.content.strip()
        # Remove markdown code blocks if present
        raw_text = re.sub(r"```(?:json)?|```", "", raw_text).strip()
        
        data = json.loads(raw_text)
        value = data.get("value")
        unit  = data.get("unit") or ""
        conf  = float(data.get("confidence", 0.0))

        if value is None:
            return None, None, 0.0

        # Normalise numeric to INR
        if pipeline_type == "numeric" and isinstance(value, (int, float)):
            return str(value), _to_inr(float(value), unit), conf
        if pipeline_type == "numeric" and isinstance(value, str):
            m = re.search(r"([\d,]+(?:\.\d+)?)\s*(crore?|lakh|lac|cr)?", value, re.I)
            if m:
                num = float(m.group(1).replace(",", ""))
                u   = m.group(2) or unit
                return value, _to_inr(num, u), conf

        return str(value), str(value), conf

    except Exception as e:
        print(f"  [LLM extract error] {field}: {e}")
        return None, None, 0.0


# ── Threshold evaluation ──────────────────────────────────────────────────────

def _parse_threshold(requirement: str) -> tuple[str, float]:
    """Pull the first numeric threshold from a requirement string."""
    # Handle Unicode comparison operators
    req = requirement.replace("≥", ">=").replace("≤", "<=")
    for op in [">=", "<=", ">", "<", "=="]:
        if op in req:
            rhs = req.split(op, 1)[1].strip()
            m = re.search(r"([\d,]+(?:\.\d+)?)\s*(crore?|lakh|lac|cr)?", rhs, re.I)
            if m:
                val = float(m.group(1).replace(",", ""))
                unit = m.group(2) or ""
                return op, _to_inr(val, unit)
    return ">=", 0.0


def _meets_threshold(canonical, pipeline_type: str, requirement: str) -> bool:
    if canonical is None:
        return False
    if pipeline_type == "boolean":
        return bool(canonical)
    if pipeline_type == "numeric":
        op, threshold = _parse_threshold(requirement)
        try:
            return eval(f"{float(canonical)} {op} {threshold}")  # safe: only numbers+op
        except Exception:
            return False
    # fuzzy → always REVIEW, never auto-PASS or FAIL
    return False


# ── Logprob scoring ───────────────────────────────────────────────────────────

def _logprob_score(field: str, requirement: str, extracted: str, page_text: str) -> float:
    """
    Ask Groq/Llama to assess H1 vs H2 and return P(H1)/(P(H1)+P(H2)).
    Falls back to 0.75 if the API is unavailable.
    """
    client = _get_groq_client()

    def _score_hypothesis(claim: str) -> float:
        prompt = (
            f"Criterion: {field}\n"
            f"Requirement: {requirement}\n"
            f"Extracted value: {extracted}\n"
            f"Claim: {claim}\n\n"
            f"Document excerpt:\n{page_text[:2000]}\n\n"
            "Reply with a single word: TRUE or FALSE"
        )
        try:
            resp = client.chat.completions.create(
                model=GROQ_MODEL,
                max_tokens=5,
                messages=[{"role": "user", "content": prompt}]
            )
            text = resp.choices[0].message.content.strip().upper()
            # TRUE→high confidence, FALSE→low confidence
            return 0.90 if text.startswith("TRUE") else 0.10
        except Exception:
            return 0.75

    try:
        p_h1 = _score_hypothesis(f"The bidder meets the requirement: {requirement}")
        p_h2 = _score_hypothesis(f"The bidder does NOT meet the requirement: {requirement}")
        total = p_h1 + p_h2
        return (p_h1 / total) if total > 0 else 0.75
    except Exception:
        return 0.75


# ── Composite confidence & verdict ────────────────────────────────────────────

def _compute_verdict(
    extraction_conf: float,
    ocr_conf: float,
    retrieval_score: float,
    logprob_score: float,
    passes_threshold: bool,
    pipeline_type: str,
) -> tuple[str, float]:
    """Returns (verdict_string, final_confidence)."""
    # Weighted average (not product) — product of four 0–1 values can never
    # reach the 0.90 gate even when every individual signal is strong.
    # Weights: logprob matters most (does it actually meet the requirement?),
    # extraction next, then retrieval, OCR last (usually high and stable).
    final = (
        0.40 * logprob_score +
        0.30 * extraction_conf +
        0.20 * retrieval_score +
        0.10 * ocr_conf
    )
    final = max(0.0, min(1.0, final))

    # Fuzzy criteria always go to REVIEW — humans must judge "similar work"
    if pipeline_type == "fuzzy":
        return "REVIEW", final

    if final >= VERDICT_PASS_FAIL_GATE and passes_threshold:
        return "PASS", final
    elif final >= VERDICT_PASS_FAIL_GATE and not passes_threshold:
        return "FAIL", final
    else:
        return "REVIEW", final


# ── Per-criterion evaluation ──────────────────────────────────────────────────

def _evaluate_one(
    criterion: dict,          # row from criteria table
    bidder_id: str,
    index: Any,
    pages: list[dict],
) -> dict:
    """
    Run the full pipeline for one (criterion, bidder) pair.
    Returns a dict ready to insert into the evaluations table.
    """
    field        = criterion["field"]
    requirement  = criterion["requirement"]
    db_type      = criterion["type"]
    pipeline_type = _infer_pipeline_type(db_type, requirement)

    # ── 1. Retrieve top-3 pages ──────────────────────────────────────────────
    query  = _build_retrieval_query(field, pipeline_type)
    retrieved = _retrieve_pages(query, index, pages, top_k=3)

    if not retrieved or retrieved[0]["retrieval_score"] < RETRIEVAL_EVIDENCE_GATE:
        return _no_evidence_result(criterion, bidder_id, retrieved)

    best_page = retrieved[0]
    combined_text = "\n".join(p["text"] for p in retrieved)
    ocr_conf  = float(best_page.get("ocr_confidence", 0.80))
    ret_score = float(best_page["retrieval_score"])

    # ── 2. Regex extraction ──────────────────────────────────────────────────
    raw_val, canonical_val, extraction_conf = _regex_extract(pipeline_type, field, combined_text)

    method = ExtractionMethod.REGEX.value

    # ── 3. LLM fallback if regex confidence is below gate ───────────────────
    if extraction_conf < REGEX_CONFIDENCE_GATE:
        raw_val, canonical_val, extraction_conf = _llm_extract(field, pipeline_type, combined_text)
        method = ExtractionMethod.LLM.value

    # ── 4. Logprob scoring ───────────────────────────────────────────────────
    if raw_val and extraction_conf > 0:
        logprob = _logprob_score(field, requirement, raw_val, best_page["text"])
    else:
        logprob = 0.0   # no value found → 0 logprob drives confidence to 0 → REVIEW

    # ── 5. Threshold check ───────────────────────────────────────────────────
    passes = _meets_threshold(canonical_val, pipeline_type, requirement)

    # ── 6. Composite verdict ─────────────────────────────────────────────────
    verdict, final_conf = _compute_verdict(
        extraction_conf, ocr_conf, ret_score, logprob, passes, pipeline_type
    )

    # ── 7. Build human-readable explanation ─────────────────────────────────
    explanation = _build_explanation(
        field, requirement, raw_val, pipeline_type,
        passes, verdict, final_conf,
        best_page, method,
        extraction_conf, ocr_conf, ret_score, logprob,
    )

    return {
        "tender_id":       criterion["tender_id"],
        "bidder_id":       bidder_id,
        "criterion_id":    criterion["id"],
        "verdict":         verdict,
        "confidence":      round(final_conf, 4),
        "extracted_value": str(raw_val) if raw_val else "Not found",
        "method":          method,
        "source_page":     f"Page {best_page.get('page_number', '?')} — {best_page.get('label', '')}",
        "signals": {
            "extraction": round(extraction_conf, 4),
            "ocr":        round(ocr_conf, 4),
            "retrieval":  round(ret_score, 4),
            "llm":        round(logprob, 4),
        },
        "explanation": explanation,
    }


def _no_evidence_result(criterion: dict, bidder_id: str, retrieved: list) -> dict:
    ret_score = retrieved[0]["retrieval_score"] if retrieved else 0.0
    return {
        "tender_id":       criterion["tender_id"],
        "bidder_id":       bidder_id,
        "criterion_id":    criterion["id"],
        "verdict":         "REVIEW",
        "confidence":      0.0,
        "extracted_value": "Not found",
        "method":          ExtractionMethod.REGEX.value,
        "source_page":     None,
        "signals": {
            "extraction": 0.0,
            "ocr":        0.0,
            "retrieval":  round(ret_score, 4),
            "llm":        0.0,
        },
        "explanation": (
            f"No relevant pages found for '{criterion['field']}' "
            f"(best retrieval score: {ret_score:.2f} < {RETRIEVAL_EVIDENCE_GATE}). "
            "Flagged REVIEW — evidence not found does not mean FAIL."
        ),
    }


def _build_explanation(
    field, requirement, raw_val, pipeline_type,
    passes, verdict, final_conf,
    best_page, method,
    ext_conf, ocr_conf, ret_score, logprob,
) -> str:
    parts = []
    if raw_val:
        parts.append(
            f"Extracted '{raw_val}' from page {best_page.get('page_number', '?')} "
            f"via {method} ({best_page.get('label', '')})."
        )
    else:
        parts.append(f"Could not extract a value for '{field}'.")

    if pipeline_type != "fuzzy":
        status = "meets" if passes else "does NOT meet"
        parts.append(f"Value {status} requirement: {requirement}.")

    parts.append(
        f"Composite confidence {final_conf:.0%} "
        f"(extraction {ext_conf:.0%} × OCR {ocr_conf:.0%} "
        f"× retrieval {ret_score:.0%} × logprob {logprob:.0%})."
    )

    if verdict == "REVIEW" and pipeline_type == "fuzzy":
        parts.append("Fuzzy criterion — sent to officer review by default.")
    elif verdict == "REVIEW":
        parts.append("Confidence below threshold — flagged for human review.")

    return " ".join(parts)


# ── Save to database ──────────────────────────────────────────────────────────

def _save_evaluation(result: dict, cursor) -> str:
    """Insert one evaluation row; auto-insert review_queue row if REVIEW."""
    eval_id = str(uuid.uuid4())
    now = datetime.utcnow()

    cursor.execute("""
        INSERT INTO evaluations (
            id, tender_id, bidder_id, criterion_id,
            verdict, confidence, extracted_value, method,
            source_page, signals, explanation, created_at
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (bidder_id, criterion_id) DO UPDATE SET
            verdict         = EXCLUDED.verdict,
            confidence      = EXCLUDED.confidence,
            extracted_value = EXCLUDED.extracted_value,
            method          = EXCLUDED.method,
            source_page     = EXCLUDED.source_page,
            signals         = EXCLUDED.signals,
            explanation     = EXCLUDED.explanation
        RETURNING id
    """, (
        eval_id,
        result["tender_id"],
        result["bidder_id"],
        result["criterion_id"],
        result["verdict"],
        result["confidence"],
        result["extracted_value"],
        result["method"],
        result["source_page"],
        json.dumps(result["signals"]),
        result["explanation"],
        now,
    ))

    row = cursor.fetchone()
    saved_id = row["id"] if row else eval_id

    # Auto-add to review queue if REVIEW verdict
    if result["verdict"] == "REVIEW":
        urgency = "high" if result["confidence"] < 0.70 else "medium"
        cursor.execute("""
            INSERT INTO review_queue (
                id, tender_id, evaluation_id, urgency, reason, status, created_at
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT DO NOTHING
        """, (
            str(uuid.uuid4()),
            result["tender_id"],
            saved_id,
            urgency,
            f"Confidence {result['confidence']:.0%} — {result['explanation'][:120]}",
            "pending",
            now,
        ))

    return saved_id


def _save_audit_log(tender_id: str, bidder_name: str, summary: dict, cursor):
    cursor.execute("""
        INSERT INTO audit_logs (id, tender_id, action, officer, detail, version, timestamp)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (
        str(uuid.uuid4()),
        tender_id,
        "EVALUATION_COMPLETE",
        "System",
        (
            f"Bidder '{bidder_name}': "
            f"PASS={summary['PASS']}, FAIL={summary['FAIL']}, REVIEW={summary['REVIEW']}"
        ),
        "1.0",
        datetime.utcnow(),
    ))


# ── Public API ────────────────────────────────────────────────────────────────

def run_evaluation_for_bidder(
    tender_id: str,
    bidder_id: str,
    bidder_name: str,
    criteria: list[dict],
) -> dict:
    """
    Run full Stage 3 matching for one bidder against all criteria.
    Saves results to DB and returns a summary dict.

    Called by the /api/matching/run/{tender_id} endpoint.
    """
    print(f"\n[Engine] Evaluating bidder: {bidder_name} ({bidder_id})")

    # Load FAISS index and pages that your teammate produced
    try:
        index, pages = _load_bidder_index(bidder_id)
    except FileNotFoundError as e:
        print(f"  [Skip] {e}")
        return {
            "bidder_id":   bidder_id,
            "bidder_name": bidder_name,
            "error":       str(e),
            "PASS":  0, "FAIL": 0, "REVIEW": 0,
        }

    summary = {"PASS": 0, "FAIL": 0, "REVIEW": 0}
    results = []

    for criterion in criteria:
        print(f"  [Criterion] {criterion['field']}")
        result = _evaluate_one(criterion, bidder_id, index, pages)
        results.append(result)
        summary[result["verdict"]] += 1
        print(f"    → {result['verdict']} (conf={result['confidence']:.2%})")

    # Write everything to DB in one transaction
    with Database.get_cursor() as cursor:
        for result in results:
            _save_evaluation(result, cursor)
        _save_audit_log(tender_id, bidder_name, summary, cursor)

        # Update tender status to evaluation_in_progress
        cursor.execute("""
            UPDATE tenders SET status = 'evaluation_in_progress', updated_at = %s
            WHERE id = %s AND status NOT IN ('evaluation_complete', 'completed')
        """, (datetime.utcnow(), tender_id))

    print(f"  [Done] PASS={summary['PASS']} FAIL={summary['FAIL']} REVIEW={summary['REVIEW']}")
    return {"bidder_id": bidder_id, "bidder_name": bidder_name, **summary}


def run_evaluation_for_tender(tender_id: str) -> dict:
    """
    Run evaluation for ALL bidders in a tender.
    Called once by the /api/matching/run/{tender_id} endpoint.
    Returns a full summary across all bidders.
    """
    print(f"\n{'='*60}")
    print(f"[Engine] Starting evaluation for tender {tender_id}")
    print(f"{'='*60}")

    with Database.get_cursor() as cursor:
        # Load criteria
        cursor.execute("SELECT * FROM criteria WHERE tender_id = %s", (tender_id,))
        criteria = [dict(row) for row in cursor.fetchall()]

        # Load bidders
        cursor.execute("SELECT * FROM bidders WHERE tender_id = %s ORDER BY created_at", (tender_id,))
        bidders = [dict(row) for row in cursor.fetchall()]

    if not criteria:
        return {"error": "No criteria found for this tender. Run the tender pipeline first."}
    if not bidders:
        return {"error": "No bidders found for this tender."}

    print(f"[Engine] {len(criteria)} criteria, {len(bidders)} bidders")

    all_summaries = []
    total = {"PASS": 0, "FAIL": 0, "REVIEW": 0}

    for bidder in bidders:
        result = run_evaluation_for_bidder(
            tender_id=tender_id,
            bidder_id=bidder["id"],
            bidder_name=bidder["name"],
            criteria=criteria,
        )
        all_summaries.append(result)
        for k in total:
            total[k] += result.get(k, 0)

    # Mark tender as evaluation complete
    with Database.get_cursor() as cursor:
        cursor.execute("""
            UPDATE tenders SET status = 'evaluation_complete', updated_at = %s
            WHERE id = %s
        """, (datetime.utcnow(), tender_id))

    print(f"\n[Engine] Done. Total across all bidders: {total}")
    return {
        "tender_id":  tender_id,
        "criteria_count": len(criteria),
        "bidder_count":   len(bidders),
        "per_bidder":     all_summaries,
        "totals":         total,
    }
