"""
index_extractor.py
------------------
Uses Claude (via Anthropic API) to detect and parse the index/table-of-contents
from the first few pages of a bidder document.

WHY LLM and not regex:
  GCP Vision flattens index tables into a single line of text with no newlines:
    "1 Tender Acceptance Letter 3 Enclosed 2 Integrity Pact 4-5 Enclosed ..."
  Any line-by-line heuristic is blind to this. Claude reads the raw blob and
  returns a clean JSON mapping in one call.

RETURN FORMAT (with page ranges):
  {
    "section name lowercase": { "start": <0-based int>, "end": <0-based int> },
    ...
  }
  "end" is inclusive. For single-page sections end == start.
"""

import json
import os
import re
import anthropic

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


def extract_index(page_texts: dict) -> dict:
    """
    Detect and parse the table of contents from OCR text of first N pages.

    Args:
        page_texts: { page_num (int): ocr_text (str) }

    Returns:
        { "section name lowercase": {"start": int, "end": int} }
        "start" and "end" are 0-based page indices (inclusive).
        Empty dict if no index found.
    """
    if not ANTHROPIC_API_KEY:
        print("⚠️  ANTHROPIC_API_KEY not set in .env — index extraction skipped.")
        print("    Falling back to full OCR + FAISS.")
        return {}

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    pages_block = "\n".join(
        f"--- PAGE {p} (0-indexed) ---\n{t}" for p, t in sorted(page_texts.items())
    )

    prompt = f"""You are parsing a scanned government tender submission document.

The OCR text below is from the FIRST FEW PAGES of the document.
IMPORTANT: GCP Vision may have collapsed an entire index table into ONE long line 
with no newlines, like: "1 Section Name 3 Enclosed 2 Other Section 5-6 Enclosed ..."

The index entries contain PAGE RANGES for some sections (e.g. "4-5" means pages 4 to 5).

Your task:
1. Find the TABLE OF CONTENTS / INDEX OF DOCUMENTS page.
2. Extract EVERY SINGLE row — including large sections like "Tender Pages Signed" or
   "Signed Tender Pages" that span many pages (e.g. 5-34). These set the page boundaries
   for ALL subsequent sections. Missing one row corrupts all downstream page assignments.
3. Page numbers are 1-based (printed on the document). Convert to 0-based: subtract 1.
   Example: printed "4-5"  →  start=3, end=4
   Example: printed "7"    →  start=6, end=6
   Example: printed "5-34" →  start=4, end=33
4. Return ONLY a valid JSON object:
   {{
     "section name in lowercase": {{"start": <int>, "end": <int>}},
     ...
   }}
5. Include ALL rows even if they look like raw tender documents, not submission docs.
6. If no table of contents is found, return an empty object: {{}}

OCR TEXT:
{pages_block}

Return only the JSON object. No explanation. No markdown fences."""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=2000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()

        # Strip markdown fences if Claude adds them
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)

        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not match:
            print("⚠️  Claude returned no JSON object for index extraction.")
            return {}

        mapping = json.loads(match.group(0))

        # Sanitize: keys to lowercase, values to {start, end} 0-based ints
        # Claude returns 0-based (prompt instructs subtract 1), just validate here
        clean = {}
        for k, v in mapping.items():
            key = str(k).lower().strip()
            try:
                if isinstance(v, dict):
                    start = int(v.get("start", v.get("page", 0)))
                    end   = int(v.get("end", start))
                else:
                    start = int(v)
                    end   = start
                if start < 0: start = 0
                if end < start: end = start
                clean[key] = {"start": start, "end": end}
            except (ValueError, TypeError):
                continue

        return clean

    except json.JSONDecodeError as e:
        print(f"⚠️  Index JSON parse error: {e}")
        return {}
    except Exception as e:
        print(f"⚠️  Index extraction failed: {e}")
        return {}
