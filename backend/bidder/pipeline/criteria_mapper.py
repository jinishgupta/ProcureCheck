import os
import re
import anthropic
from db.database import Database

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


def load_criteria_with_ids(tender_id: str):
    """
    Loads criteria from the database for the given tender.
    Returns:
        criteria_by_id: { "UUID": { text, ... }, ... }
        criteria_list:  [ { id, text, ... }, ... ]
    """
    criteria_by_id = {}
    criteria_list  = []
    
    with Database.get_cursor() as cursor:
        cursor.execute("SELECT id, requirement as text, field, type FROM criteria WHERE tender_id = %s", (tender_id,))
        rows = cursor.fetchall()
        for row in rows:
            entry = dict(row)
            cid = entry["id"]
            criteria_by_id[cid] = entry
            criteria_list.append(entry)

    return criteria_by_id, criteria_list


def map_criteria_to_sections(tender_id: str, section_map: dict):
    """
    Maps criteria → relevant index sections using Claude (or keyword fallback).
    Returns:
        section_to_ids: { "section_name": ["UUID", "UUID", ...] }
        criteria_by_id: full lookup dict
    """
    try:
        criteria_by_id, criteria_list = load_criteria_with_ids(tender_id)
    except Exception as e:
        print(f"⚠️ Could not load criteria from DB: {e}")
        return {s: [] for s in section_map.keys()}, {}

    section_to_ids = {}

    if ANTHROPIC_API_KEY:
        try:
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

            sections_str  = "\n".join(f"- {s}" for s in section_map.keys())
            criteria_str  = "\n".join(
                f"  {c['id']}: {c['text']}" for c in criteria_list
            )

            prompt = f"""
You are an AI assistant helping with tender document analysis.

The bidder's document has these index sections:
{sections_str}

The tender criteria (with IDs) are:
{criteria_str}

Return a JSON object where:
- keys are EXACT section names from the list above
- values are arrays of criterion IDs (like "C01") that are most likely found in that section

Only include sections that are clearly relevant. Do not guess. Return nothing else except the JSON object.
"""
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=1500,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                predicted = json.loads(match.group(0))
                for sec, id_list in predicted.items():
                    if sec in section_map:
                        section_to_ids[sec] = [i for i in id_list if i in criteria_by_id]

            if section_to_ids:
                print(f"  (Claude mapped sections to IDs: {section_to_ids})")
                return section_to_ids, criteria_by_id

        except Exception as e:
            print(f"⚠️ Anthropic API mapping failed: {e}. Falling back to keyword matching.")

    # ---- FALLBACK: keyword overlap ----
    for c in criteria_list:
        words = set(c["text"].lower().split())
        for sec in section_map.keys():
            sec_words = set(sec.lower().split())
            if words & sec_words:
                section_to_ids.setdefault(sec, []).append(c["id"])

    if not section_to_ids:
        print("⚠️ Criteria mapper could not narrow down sections. Using all.")
        for sec in section_map.keys():
            section_to_ids[sec] = [c["id"] for c in criteria_list]

    return section_to_ids, criteria_by_id
