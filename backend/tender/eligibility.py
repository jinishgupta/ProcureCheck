import fitz
import json
import os
import re
import time
from google import genai
from keybert import KeyBERT
from dotenv import load_dotenv

load_dotenv()
client1 = genai.Client(api_key=os.getenv("GEMINI_API_KEY_1"))
client2 = genai.Client(api_key=os.getenv("GEMINI_API_KEY_2"))

# load once at startup
kw_model = KeyBERT(model="all-MiniLM-L6-v2")

CHUNK_SIZE = 2500
CHUNK_DELAY = 2

# ─────────────────────────────────────────────
# Step 0: KeyBERT index enrichment
# ─────────────────────────────────────────────

def clean_page_text(text: str) -> str:
    lines = text.splitlines()
    clean = []
    for line in lines:
        line = line.strip()
        if not line or len(line) < 20:
            continue
        # drop lines that are >40% non-ASCII (catches Hindi/symbols/page artifacts)
        non_ascii = sum(1 for c in line if ord(c) > 127)
        if non_ascii / len(line) > 0.4:
            continue
        clean.append(line)
    return " ".join(clean)


def enrich_index_with_summaries(tree: list, pages_cache: dict) -> list:
    for node in tree:
        print(f"  [KeyBERT] {node['title']}")
        node["summary"] = generate_node_summary(node, pages_cache)
        if node.get("nodes"):
            node["nodes"] = enrich_index_with_summaries(
                node["nodes"], pages_cache
            )
    return tree


# ─────────────────────────────────────────────
# Step 1: Load PDF pages
# ─────────────────────────────────────────────

def load_pages(pdf_path: str) -> dict:
    pages = {}
    doc = fitz.open(pdf_path)
    for i in range(len(doc)):
        raw = str(doc[i].get_text("text") or "")
        pages[i + 1] = raw.strip()
    doc.close()
    print(f"[PDF] Loaded {len(pages)} pages")
    return pages


def get_tagged_pages(pages: dict) -> str:
    """Tag all pages with physical index markers."""
    parts = []
    for page_num, text in pages.items():
        tagged = f"<physical_index_{page_num}>\n{text}\n</physical_index_{page_num}>"
        parts.append(tagged)
    return "\n\n".join(parts)


def get_tagged_page_range(pages: dict, start: int, end: int) -> str:
    """Get tagged text for a specific page range."""
    parts = []
    for page_num in range(start, end + 1):
        text = pages.get(page_num, "")
        if not text:
            continue
        tagged = f"<physical_index_{page_num}>\n{text}\n</physical_index_{page_num}>"
        parts.append(tagged)
    return "\n\n".join(parts)


def extract_physical_index(tag: str) -> int | None:
    """Parse '<physical_index_3>' -> 3"""
    match = re.search(r'<physical_index_(\d+)>', tag)
    return int(match.group(1)) if match else None

# ─────────────────────────────────────────────
# Step 2: Agentic tree traversal
# ─────────────────────────────────────────────

def should_enter_node(title: str, summary: str) -> bool:
    CRITICAL_TITLES = [
        "general condition",
        "notice inviting",
        "special term",
        "special condition",
        "instruction",
        "important",
        "eligibility",
        "qualification",
        "declaration",
        "basic information",
        "solvency",
        # FIX 1: these sections contain EPF/ESIC, bank remittance,
        # integrity agreement, and document checklist items
        "document",
        "checklist",
        "submission",
        "bidder",
        "guideline",
        "requirement",
        "information of",
    ]
    t = title.lower()
    if any(c in t for c in CRITICAL_TITLES):
        print(f"    [Force enter] critical section: '{title}'")
        return True

    if not summary or summary == "No content":
        return False

    prompt = f"""Tender section: "{title}"
Section keywords: {summary}

Could this section contain bidder eligibility criteria — registration, 
experience, turnover, solvency, qualifications, financial requirements?

Reply YES or NO only."""

    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = client2.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={"max_output_tokens": 5}
            )
            text = response.text if response.text else "NO"
            return text.strip().upper().startswith("YES")
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "rate" in error_str.lower():
                wait_seconds = 30 * (2 ** attempt)
                print(f"    [Rate limit] should_enter_node — waiting {wait_seconds}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait_seconds)
            else:
                print(f"    [LLM error] should_enter_node: {e}")
                return False
                
    print("    [Max retries] should_enter_node — skipping")
    return False


def traverse_tree(nodes: list[dict], pages_cache: dict, 
                  parent_path: str = "") -> list[dict]:
    relevant = []

    for node in nodes:
        path = f"{parent_path} > {node['title']}" if parent_path else node['title']
        children = node.get("nodes", [])

        # use pre-computed summary — no page reads during traversal
        summary = node.get("summary", "")

        print(f"  [?] {path}")
        print(f"      summary: {summary[:80]}...")
        enter = should_enter_node(node["title"], summary)

        if not enter:
            print(f"  [Skip] {path}")
            # FIX B: even if we skip this node's pages, still recurse
            # into its children — a skippable parent can contain
            # relevant children (e.g. SCHEDULE OF TENDER > IMPORTANT INSTRUCTIONS)
            if children:
                relevant.extend(traverse_tree(children, pages_cache, path))
            continue

        print(f"  [Enter] {path}")

        if children:
            first_child_start = children[0]["start_index"]

            # FIX 3: was only harvesting node["start_index"] to first_child_start-1.
            # That drops everything in the parent body that comes AFTER the last child
            # (or before the first child if gap > 1 page but not summarised well).
            # Now we harvest: (a) intro pages before first child, (b) tail pages
            # after last child ends (e.g. a summary/checklist page appended to section).

            if node["start_index"] < first_child_start:
                relevant.append({
                    "title": node["title"] + " (intro)",
                    "node_id": node["node_id"],
                    "start_index": node["start_index"],
                    "end_index": first_child_start - 1,
                    "source_path": path,
                })

            # recurse into children
            relevant.extend(traverse_tree(children, pages_cache, path))

            # FIX 3b: harvest tail pages after last child — this is where
            # document checklists, annexure lists, and sign-off tables live
            last_child_end = children[-1]["end_index"]
            if last_child_end < node["end_index"]:
                relevant.append({
                    "title": node["title"] + " (tail)",
                    "node_id": node["node_id"],
                    "start_index": last_child_end + 1,
                    "end_index": node["end_index"],
                    "source_path": path,
                })
        else:
            relevant.append({
                "title": node["title"],
                "node_id": node["node_id"],
                "start_index": node["start_index"],
                "end_index": node["end_index"],
                "source_path": path,
            })

    return relevant


# ─────────────────────────────────────────────
# Step 3: Chunking + LLM extraction
# ─────────────────────────────────────────────

def chunk_by_pages(tagged_text: str, max_chars: int = CHUNK_SIZE) -> list[str]:
    """Split on page boundaries, never mid-page."""
    page_blocks = re.split(r'</physical_index_\d+>\n*', tagged_text)
    page_blocks = [b.strip() for b in page_blocks if b.strip()]
    
    chunks, current = [], ""
    for block in page_blocks:
        if len(current) + len(block) > max_chars and current:
            chunks.append(current.strip())
            current = block
        else:
            current = f"{current}\n\n{block}" if current else block
    if current:
        chunks.append(current.strip())
    return chunks


def find_page_for_position(chunk: str, pos: int) -> int | None:
    """Find which page a character position falls on within a tagged chunk."""
    preceding = chunk[:pos]
    matches = list(re.finditer(r'<physical_index_(\d+)>', preceding))
    return int(matches[-1].group(1)) if matches else None


def clean_json(text: str) -> str:
    text = re.sub(r'```json|```', '', text).strip()
    start = text.find('[')
    end = text.rfind(']')
    if start != -1 and end != -1:
        return text[start:end + 1]
    return text


def generate_node_summary(node: dict, pages_cache: dict) -> str:
    start = node["start_index"]
    end = node["end_index"]
    children = node.get("nodes", [])

    if children:
        first_child_start = children[0]["start_index"]
        # FIX 2: was capping at start+1, which meant a parent whose
        # first child starts on the next page got zero useful content.
        # Now summarise up to 5 intro pages, or the full gap if smaller.
        end = min(start + 5, first_child_start - 1)
        end = max(end, start)  # ensure end >= start

    text = get_tagged_page_range(pages_cache, start, end)
    clean = clean_page_text(text)

    if not clean or len(clean) < 50:
        child_titles = ", ".join(c["title"] for c in children)
        return child_titles if child_titles else "No content"

    try:
        keywords = kw_model.extract_keywords(
            clean[:1500],
            keyphrase_ngram_range=(1, 3),
            stop_words="english",
            top_n=8
        )
        kw_list = []
        for item in keywords:
            if isinstance(item, (tuple, list)):
                kw_list.append(str(item[0]))
            else:
                kw_list.append(str(item))
        return ", ".join(kw_list)
    except Exception as e:
        print(f"  [KeyBERT error] {node['title']}: {e}")
        return clean[:200]


def llm_call(prompt: str, label: str) -> list[dict]:
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = client2.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={"max_output_tokens": 1000}
            )
            raw = response.text or ""
            parsed = json.loads(clean_json(raw))
            return [item for item in parsed if isinstance(item, dict) and "text" in item]

        except (json.JSONDecodeError, ValueError) as e:
            print(f"  [Parse error] {label}: {e}")
            return []

        except anthropic.RateLimitError:
            wait_seconds = 30 * (2 ** attempt)
            print(f"  [Rate limit] {label} — waiting {wait_seconds}s (attempt {attempt+1}/{max_retries})")
            time.sleep(wait_seconds)

        except anthropic.APIError as e:
            print(f"  [API error] {label}: {e}")
            return []

    print(f"  [Max retries] {label} — skipping")
    return []


def extract_criteria_from_section(section: dict, page_text: str) -> list[dict]:
    source_path = section["source_path"]
    page_range = f"{section['start_index']}-{section['end_index']}"

    if len(page_text.strip()) < 100:
        print(f"  [Skip] {section['title'][:60]} — too short")
        return []

    chunks = chunk_by_pages(page_text)
    print(f"  [Chunks] {section['title'][:50]} -> {len(chunks)} chunk(s)")

    all_raw = []
    for i, chunk in enumerate(chunks):
        label = f"{section['title'][:40]} chunk {i+1}/{len(chunks)}"

        prompt = f"""You are extracting ELIGIBILITY criteria from a government tender — rules that determine WHETHER a contractor qualifies to bid at all.

SECTION: {section['title']}
CHUNK: {i+1} of {len(chunks)}

TEXT:
{chunk}

INCLUDE only criteria about:
- Contractor registration/enlistment (with CPWD, PWD, MES, BRO, state depts etc.)
- Contractor class/grade/category required
- Minimum financial turnover or net worth
- Solvency certificate requirements (minimum solvency % of ECT, banker's certificate)
- Minimum years of experience
- Similar work completion requirements
- Technical capacity (equipment, manpower)
- Joint venture / consortium conditions
- Blacklisting / debarment conditions

EXCLUDE everything else, especially:
- EMD amount, format, validity, payable details
  (Note: solvency certificates are NOT EMD — include them with their % threshold)
- EMD forfeiture conditions
- Document upload/submission procedures
- Bid validity period, site visit, payment terms
- Work specifications, materials, timelines
- Annexure/format instructions (bank seal requirements, certificate formats)
- Any instruction about HOW to bid (vs WHO can bid)
- Payment logistics (bank account details, NEFT/RTGS)
- Post-award labour law compliance obligations (Contract Labour Act license,
  BOCW registration, labour licenses before bills) — these are conditions
  AFTER award, not eligibility to bid
  EXCEPTION: EPF/ESIC registration certificate is eligibility — include it
- Integrity Pact procedural clauses (agent disclosure obligations,
  sub-contractor pact compliance) — EXCEPT the single criterion that
  the signed Integrity Pact must be submitted with bid
- Procurement policy statements ("purchaser reserves right to...")

For "applies_to":
- "registered": enlisted with CPWD/MES/PWD/BRO — registration validity/class/grade
- "unregistered": turnover %, solvency %, past work thresholds (80%/60%/40% of ECT)
- "all": PAN, GST, blacklisting, EPFO/ESIC registration

For financial thresholds, ALWAYS extract the specific percentage or amount:
- WRONG: "Solvency certificate required from bank"
- RIGHT: "Solvency certificate >= 25% of Estimated Cost put to tender (ECT),
          certified by banker, not older than 6 months"

If you see a solvency/turnover/experience criterion WITHOUT a number,
look harder — the number is almost certainly nearby in the same paragraph.

If this chunk has no true eligibility criteria, return [].

Return ONLY raw JSON array, no markdown, no explanation:
[{{"text": "<criterion>", "applies_to": "all|registered|unregistered"}}]"""

        items = llm_call(prompt, label)
        all_raw.extend(items)

        if i < len(chunks) - 1:
            time.sleep(CHUNK_DELAY)

    criteria = []
    for item in all_raw:
        criteria.append({
            "text": item.get("text", "").strip(),
            "applies_to": item.get("applies_to", "all"),
            "source_path": source_path,
            "page_range": page_range,
        })

    print(f"  [Done] {section['title'][:60]} -> {len(criteria)} criteria")
    return criteria


# ─────────────────────────────────────────────
# Step 4: Dedup + false positive filter
# ─────────────────────────────────────────────

def deduplicate_criteria(criteria: list[dict]) -> list[dict]:
    def normalize(text: str) -> str:
        return re.sub(r'\s+', ' ', text.lower().strip())

    seen = []
    deduped = []
    for c in criteria:
        norm = normalize(c["text"])
        is_dup = False
        for s in seen:
            words_c = set(norm.split())
            words_s = set(s.split())
            if not words_c or not words_s:
                continue
            overlap = len(words_c & words_s) / min(len(words_c), len(words_s))
            if overlap > 0.65:
                is_dup = True
                break
        if not is_dup:
            seen.append(norm)
            deduped.append(c)

    print(f"[Dedup] {len(criteria)} -> {len(deduped)} after deduplication")
    return deduped


def is_false_positive(text: str) -> bool:
    # regex list removed — LLM prompt handles exclusions
    return False

def clean_criteria_with_llm(criteria: list[dict], batch_size: int = 20) -> list[dict]:
    """Use Groq to remove noise criteria in batches."""
    
    all_kept = []
    batches = [criteria[i:i+batch_size] for i in range(0, len(criteria), batch_size)]
    
    for batch_num, batch in enumerate(batches):
        numbered = "\n".join([
            f"{i:03d}: [{c['applies_to']}] {c['text']}"
            for i, c in enumerate(batch)
        ])
        
        try:
            prompt = f"""You are reviewing extracted eligibility criteria from an Indian government tender.
Your job is to remove ONLY the most obvious noise. When in doubt — KEEP IT.

ALWAYS KEEP — never remove these:
- Registration/enlistment with any govt department (CPWD, MES, PWD, BRO, NBCC etc.)
- Contractor class/grade/category requirement
- Financial turnover threshold (any % of ECT or fixed amount)
- Solvency certificate with % threshold
- Past work experience thresholds (80%/60%/40% of ECT or years)
- PAN card requirement
- GST registration requirement
- EPF/ESIC registration certificate submitted with bid
- Audited balance sheets / ITR / CA certified financials
- Blacklisting/debarment/litigation affidavit
- Integrity Pact submission with bid

ONLY REMOVE if 100% certain it fits one of these:

1. PURE PROCUREMENT POLICY
   Signals: "reserves the right", "may place order", "at discretion of"
   Example: "Purchaser reserves the right to place order on next higher firm"

2. PURE CONFLICT OF INTEREST
   Signals: "near relative", "intimate names", "relative of officer"
   Example: "Contractor shall not tender where near relative of dept is involved"

3. PURE STATUTORY COMPLIANCE — law applies to all contractors regardless, no threshold
   Signals: Act name with no registration/certificate/threshold attached
   Example REMOVE: "Contractor shall comply with Minimum Wages Act 1948"
   Example REMOVE: "Contractor shall comply with Inter-State Migrant Workmen Act"
   Example KEEP: "Valid EPF/ESIC registration certificate required with bid"

4. PAYMENT GATE — must produce something before getting paid, not before bidding
   Signals: "before payment", "before RA bills", "no payment till", "condition for payment"
   Example REMOVE: "No payment will be made till producing EPFO registration"

5. PURE DOCUMENT FORMAT — how to format, not what credential to hold
   Signals: "bank seal", "on letterhead", "stamp paper", "notarized template"

BATCH {batch_num + 1}/{len(batches)} — IDs run from 000 to {len(batch)-1:03d}:
{numbered}

Return ONLY a JSON array of 3-digit IDs to KEEP from THIS batch.
Example: ["000", "003", "007"]
No explanation, no markdown, no extra text."""

            response = client1.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={"max_output_tokens": 200}
            )

            raw = (response.text or "").strip()
            raw = re.sub(r'```json|```', '', raw).strip()
            ids_to_keep = json.loads(raw)
            kept = [batch[int(i)] for i in ids_to_keep if int(i) < len(batch)]
            print(f"  [Batch {batch_num+1}/{len(batches)}] {len(batch)} -> {len(kept)} kept")
            all_kept.extend(kept)

        except Exception as e:
            print(f"  [Batch {batch_num+1}/{len(batches)}] Failed: {e} — keeping all")
            all_kept.extend(batch)

        if batch_num < len(batches) - 1:
            time.sleep(CHUNK_DELAY)

    print(f"[Clean] {len(criteria)} -> {len(all_kept)} after Groq cleaning pass")
    return all_kept

# ─────────────────────────────────────────────
# Main pipeline
# ─────────────────────────────────────────────

if __name__ == "__main__":
    INDEX_PATH = "index.json"
    ENRICHED_INDEX_PATH = "index_enriched.json"
    PDF_PATH = "tender41.pdf"
    OUTPUT_PATH = "eligibility.json"

    pages_cache = load_pages(PDF_PATH)

    # check if raw index is newer than enriched index
    if os.path.exists(ENRICHED_INDEX_PATH):
        raw_mtime = os.path.getmtime(INDEX_PATH)
        enriched_mtime = os.path.getmtime(ENRICHED_INDEX_PATH)
        if raw_mtime > enriched_mtime:
            print(f"[Index] Raw index newer than enriched — rebuilding")
            os.remove(ENRICHED_INDEX_PATH)

    # load or build enriched index
    if os.path.exists(ENRICHED_INDEX_PATH):
        print(f"[Index] Loading enriched index from {ENRICHED_INDEX_PATH}")
        with open(ENRICHED_INDEX_PATH, "r", encoding="utf-8") as f:
            index = json.load(f)
    else:
        print(f"[Index] Enriched index not found — building from {INDEX_PATH}")
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            index = json.load(f)

        print(f"\n--- Generating KeyBERT summaries ---")
        index["structure"] = enrich_index_with_summaries(
            index["structure"], pages_cache
        )

        with open(ENRICHED_INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
        print(f"[Index] Saved enriched index to {ENRICHED_INDEX_PATH}")

    doc_name = index.get("doc_name", PDF_PATH)
    total_pages = index.get("total_pages", 0)
    tree = index.get("structure", [])
    print(f"[Index] {doc_name} | {total_pages} pages | {len(tree)} root nodes")

    # DEBUG: print tree structure temporarily
    def print_tree(nodes, depth=0):
        for n in nodes:
            print("  "*depth + f"[{n['node_id']}] p.{n['start_index']}-{n['end_index']} | {n['title']}")
            print("  "*depth + f"  summary: {n.get('summary','')[:100]}")
            for child in n.get("nodes", []):
                print_tree([child], depth+1)

    print("\n--- DEBUG: Index Tree Structure ---")
    print_tree(tree)

    print(f"\n--- Traversing index tree ---")
    relevant_sections = traverse_tree(tree, pages_cache)

    print(f"\n[Traversal] {len(relevant_sections)} sections selected:")
    for s in relevant_sections:
        print(f"  [{s['node_id']}] {s['source_path']} (p.{s['start_index']}-{s['end_index']})")

    print(f"\n--- Extracting eligibility criteria ---")
    all_criteria = []

    for section in relevant_sections:
        print(f"\n[Section] {section['source_path']} (p.{section['start_index']}-{section['end_index']})")
        page_text = get_tagged_page_range(pages_cache, section["start_index"], section["end_index"])
        criteria = extract_criteria_from_section(section, page_text)
        all_criteria.extend(criteria)

    print(f"\n[Total] {len(all_criteria)} criteria before dedup")
    all_criteria = deduplicate_criteria(all_criteria)
    all_criteria = [c for c in all_criteria if not is_false_positive(c["text"])]
    print(f"[Total] {len(all_criteria)} criteria after false positive filter")

    # Step 5: Haiku cleaning pass
    print(f"\n--- Cleaning criteria with Claude Haiku ---")
    all_criteria = clean_criteria_with_llm(all_criteria)

    registered   = [c for c in all_criteria if c["applies_to"] == "registered"]
    unregistered = [c for c in all_criteria if c["applies_to"] == "unregistered"]
    all_bidders  = [c for c in all_criteria if c["applies_to"] == "all"]

    print(f"\n[Summary]")
    print(f"  All bidders:  {len(all_bidders)}")
    print(f"  Registered:   {len(registered)}")
    print(f"  Unregistered: {len(unregistered)}")

    result = {
        "doc_name": doc_name,
        "total_criteria": len(all_criteria),
        "summary": {
            "all_bidders": len(all_bidders),
            "registered_only": len(registered),
            "unregistered_only": len(unregistered),
        },
        "criteria": all_criteria,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to {OUTPUT_PATH}")