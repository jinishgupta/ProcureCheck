import fitz
import re
import json
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY_1"))

HEADING_PATTERN = re.compile(r'^[A-Z0-9][A-Z0-9\s\-/():,\.&]{2,}$')


def clean_text(text: str) -> str:
    text = text.replace('\u2013', '-').replace('\u2014', '-')
    text = text.replace('\u200b', '').replace('\ufeff', '')
    return text


def is_heading(line: str) -> bool:
    line = line.strip()
    if len(line) < 3:
        return False
    if len(re.findall(r'[A-Z]', line)) < 2:
        return False
    return bool(HEADING_PATTERN.match(line))


def is_valid_heading(line: str) -> bool:
    line = line.strip()
    if len(line) < 5:
        return False
    if len(re.findall(r'[A-Z]', line)) < 2:
        return False
    if re.match(r'^\d+[\s\.]', line): return False
    if re.match(r'^SD/-', line): return False
    if re.fullmatch(r'[IVXLCDM\s]+', line): return False
    if line.count(',') >= 3: return False
    if re.search(r'\bIS\s*:\s*\d+', line): return False
    if re.search(r'P\.O:|PIN-\d{6}', line): return False
    if len(line.split()) < 2: return False
    if re.match(r'^(AND|OR|OF|WITH|FOR|THE|IN|TO|AT|BY)\b', line): return False
    if line.count('/') >= 3: return False
    return True


def extract_headings(pdf_path: str) -> list[dict]:
    after_filter = []
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        try:
            text_dict = page.get_text("dict")
            if not isinstance(text_dict, dict):
                print(f"Unexpected text format on page {page_num + 1}")
                continue
            blocks = text_dict.get("blocks", [])
            if not isinstance(blocks, list):
                print(f"Blocks is not a list on page {page_num + 1}")
                continue
        except Exception as e:
            print(f"Error extracting text from page {page_num + 1}: {e}")
            continue
            
        for block in blocks:
            if not isinstance(block, dict):
                continue
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                if not isinstance(line, dict):
                    continue
                bold_spans = [s for s in line.get("spans", []) if isinstance(s, dict) and bool(s.get("flags", 0) & 16) and s.get("text", "").strip()]
                if not bold_spans:
                    continue
                merged_text = " ".join(clean_text(s.get("text", "").strip()) for s in bold_spans).strip()
                if not merged_text:
                    continue
                entry = {
                    "page": page_num + 1,
                    "heading": merged_text,
                    "bbox": bold_spans[0].get("bbox", [0, 0, 0, 0]),
                    "size": round(bold_spans[0].get("size", 0), 1),
                }
                if is_heading(merged_text) and is_valid_heading(merged_text):
                    after_filter.append(entry)
    doc.close()
    print(f"[Headings] Found {len(after_filter)}")
    return after_filter


def clean_json(text):
    text = re.sub(r'```json|```', '', text).strip()
    end = text.rfind(']')
    if end == -1:
        return text
    start = text.rfind('[', 0, end)
    if start != -1:
        return text[start:end+1]
    return text


def llm_noise_filter(headings: list[dict], batch_size: int = 50) -> list[dict]:
    batches = [headings[i:i+batch_size] for i in range(0, len(headings), batch_size)]
    all_kept = []
    for i, batch in enumerate(batches):
        heading_list = "\n".join([f"{j:04d}: [p{h['page']}] {h['heading']}" for j, h in enumerate(batch)])
        prompt = f"""Clean up headings from a government tender PDF.
ONLY reject if 100% certain it is noise: partial line fragment, address, table column header, page header/footer.
When in doubt KEEP IT.

{heading_list}

Return ONLY raw JSON array of 4-digit IDs to KEEP. Example: ["0000", "0002"]"""
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={"max_output_tokens": 600}
            )
            ids = json.loads(clean_json(response.text))
            all_kept.extend([batch[int(i)] for i in ids if int(i) < len(batch)])
        except Exception as e:
            print(f"[Noise filter] Batch {i} error: {e} — keeping all")
            all_kept.extend(batch)
    print(f"[Noise filter] {len(headings)} → {len(all_kept)}")
    return all_kept


def llm_assign_structure(headings: list[dict], batch_size: int = 50) -> list[dict]:
    batches = [headings[i:i+batch_size] for i in range(0, len(headings), batch_size)]
    all_headings = []
    previous_context = ""

    for i, batch in enumerate(batches):
        heading_list = "\n".join([f"{j:04d}: [p{h['page']}] {h['heading']}" for j, h in enumerate(batch)])
        context_block = f"\nPreviously assigned (continue numbering from here):\n{previous_context}\n" if previous_context else ""

        prompt = f"""Assign structure indices to headings from a government tender.
Use "1", "1.1", "2", "2.1", "2.1.1" etc.
- Level 1: Major sections (NOTICE INVITING TENDER, GENERAL CONDITIONS, SPECIAL CONDITIONS, SCHEDULE OF QUANTITY, INTEGRITY PACT, forms)
- Level 2: Subsections (EPFO & ESIC, GUARANTEE, EARNEST MONEY, FINAL INSPECTION)
- Level 3: Detail specs (COARSE AGGREGATE, VITRIFIED TILES, LED LIGHT FITTING)
{context_block}
{heading_list}

Return ONLY raw JSON array. Example: [{{"id": "0000", "structure": "1"}}, {{"id": "0001", "structure": "1.1"}}]"""

        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={"max_output_tokens": 1000}
            )
            items = json.loads(clean_json(response.text))
            for item in items:
                idx = int(item["id"])
                if idx < len(batch):
                    batch[idx]["structure"] = item.get("structure", "1")
            for h in batch:
                if "structure" not in h:
                    h["structure"] = "1"
        except Exception as e:
            print(f"[Structure] Batch {i} error: {e} — assigning sequential")
            for j, h in enumerate(batch):
                h["structure"] = str(len(all_headings) + j + 1)

        all_headings.extend(batch)
        previous_context = "\n".join([f"{h['structure']}: [p{h['page']}] {h['heading']}" for h in batch[-10:]])

    return all_headings


def check_appear_start(doc, heading, top_threshold=0.15):
    page = doc[heading["page"] - 1]
    instances = page.search_for(heading["heading"]) or page.search_for(" ".join(heading["heading"].split()[:4]))
    heading_y = instances[0].y0 if instances else heading["bbox"][1]
    return (heading_y / page.rect.height) < top_threshold


def assign_page_ranges(headings: list[dict], total_pages: int, pdf_path: str) -> list[dict]:
    doc = fitz.open(pdf_path)
    for h in headings:
        h["appear_start"] = check_appear_start(doc, h)
    doc.close()

    for i, h in enumerate(headings):
        h["start_index"] = h["page"]
        if i < len(headings) - 1:
            next_h = headings[i + 1]
            if next_h["page"] == h["page"]:
                h["end_index"] = h["page"]
            elif next_h["appear_start"]:
                h["end_index"] = next_h["page"] - 1
            else:
                h["end_index"] = next_h["page"]
        else:
            h["end_index"] = total_pages
        h["end_index"] = max(h["end_index"], h["start_index"])
    return headings


def build_tree(headings: list[dict]) -> list[dict]:
    nodes = {}
    roots = []
    for h in headings:
        structure = h.get("structure", "1")
        node = {
            "title": h["heading"],
            "node_id": "",
            "start_index": h["start_index"],
            "end_index": h["end_index"],
            "nodes": [],
        }
        nodes[structure] = node
        parent = ".".join(structure.split(".")[:-1])
        if parent and parent in nodes:
            nodes[parent]["nodes"].append(node)
        else:
            roots.append(node)
    return roots


def assign_node_ids(nodes, counter=None):
    if counter is None:
        counter = [0]
    for node in nodes:
        node["node_id"] = str(counter[0]).zfill(4)
        counter[0] += 1
        if node.get("nodes"):
            assign_node_ids(node["nodes"], counter)
        if not node["nodes"]:
            node.pop("nodes")

def print_tree(nodes, indent=0):
    for n in nodes:
        prefix = "  " * indent + ("└─ " if indent else "")
        print(f"{prefix}[{n['node_id']}] {n['title']}  (p.{n['start_index']}-{n['end_index']})")
        if n.get("nodes"):
            print_tree(n["nodes"], indent + 1)


if __name__ == "__main__":
    pdf_path = "tender41.pdf"

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    doc.close()

    headings = extract_headings(pdf_path)
    headings = llm_noise_filter(headings)
    headings = assign_page_ranges(headings, total_pages, pdf_path)
    headings = llm_assign_structure(headings)

    tree = build_tree(headings)
    assign_node_ids(tree)

    print("\n" + "="*60)
    print_tree(tree)

    with open("index.json", "w", encoding="utf-8") as f:
        json.dump({"doc_name": pdf_path, "total_pages": total_pages, "structure": tree}, f, indent=2, ensure_ascii=False)
    print("\nSaved to index.json")