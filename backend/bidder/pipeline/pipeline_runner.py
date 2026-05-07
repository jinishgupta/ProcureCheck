"""
pipeline_runner.py
------------------
Orchestrates the full OCR pipeline for one bidder document.

Output: two files per bidder
  - bidder_manifest.json  : index metadata + section/criteria mapping (no text)
  - bidder_sections.jsonl : one JSON line per chunk (text + metadata)
"""

from pipeline.pdf_processor import DocumentProcessor
from pipeline.image_preprocessor import preprocess
from pipeline.ocr_engine import extract_text_with_confidence
from pipeline.index_extractor import extract_index
from pipeline.section_chunker import assign_section
from pipeline.embedding_engine import embed
from pipeline.faiss_indexer import BidderIndex
from pipeline.criteria_mapper import map_criteria_to_sections, load_criteria_with_ids
from config import *

from collections import defaultdict
import json
import os


class BidderPipeline:

    def __init__(self, file_path, eligibility_json_path="data/input/eligibility.json",
                 output_dir="data/outputs"):
        self.file_path        = file_path
        self.eligibility_path = eligibility_json_path
        self.output_dir       = output_dir
        self.index            = BidderIndex(FAISS_DIM)
        self.section_map      = {}       # { "section name": 0-based page }
        self.criteria_by_id   = {}       # { "C01": { text, applies_to, ... } }
        self.doc_processor    = DocumentProcessor(file_path, "data/processed")

        # Populated during run()
        self._manifest   = {}
        self._all_chunks = []            # flat list, also written to .jsonl

    # ------------------------------------------------------------------
    def _extract_text_for_page(self, page_num):
        content_type, content = self.doc_processor.get_page_content(page_num)
        if content_type == "text":
            return content, 1.0
        img = preprocess(content)
        return extract_text_with_confidence(img, GCP_KEY_PATH)

    # ------------------------------------------------------------------
    def _chunk_words(self, words, section, criterion_ids,
                     chunk_size=300, overlap=50):
        """
        Splits a flat word list into overlapping chunks.
        chunk_size=300 words  ≈ 1 page of dense OCR text.
        overlap=50 words      preserves context at chunk boundaries.
        chunk_id format: <section_slug>_<chunk_index>
        """
        import re
        section_slug = re.sub(r"[^a-z0-9]+", "_", section.lower()).strip("_")[:30]
        chunks = []

        for chunk_idx, i in enumerate(range(0, len(words), chunk_size - overlap)):
            batch = words[i:i + chunk_size]
            if not batch:
                continue
            text_str   = " ".join(w["word"] for w in batch)
            start_page = batch[0]["page"]
            end_page   = batch[-1]["page"]
            avg_conf   = round(sum(w["conf"] for w in batch) / len(batch), 4)
            chunk_id   = f"{section_slug}_{chunk_idx}"

            enriched = f"[{section} | pages {start_page}–{end_page}]\n{text_str}"
            emb      = embed(enriched)
            self.index.add(emb, {"chunk_id": chunk_id, "section": section})

            chunks.append({
                "chunk_id":       chunk_id,
                "pages":          list(range(start_page, end_page + 1)) if end_page > start_page else [start_page],
                "text":           text_str,
                "ocr_confidence": avg_conf,
                "criterion_ids":  criterion_ids,
            })
        return chunks


    # ------------------------------------------------------------------
    def run(self):
        total = self.doc_processor.total_pages
        print(f"\n📄 Document: {self.file_path}  ({total} pages)")

        # ================================================================
        # STEP 1 — FIND INDEX  (scan first 5 pages, send text to Claude)
        # ================================================================
        print("\n── STEP 1: Index detection ──────────────────────────────")
        extraction_cache = {}
        max_scan = min(5, total)

        for i in range(max_scan):
            text, conf = self._extract_text_for_page(i)
            extraction_cache[i] = {"text": text, "conf": conf}
            print(f"  [page {i} OCR text ({len(text)} chars, conf={conf:.2f})]")
            print(f"  {text[:300]}{'...' if len(text) > 300 else ''}")
            print()

        page_texts = {i: extraction_cache[i]["text"] for i in range(max_scan)}
        self.section_map = extract_index(page_texts)

        if self.section_map:
            # section_map values are now {"start": int, "end": int}
            first_content_page = min(v["start"] for v in self.section_map.values())
            index_page_set = set(range(1, first_content_page))  # pages between cover and first content
            index_start    = 1
            print(f"  ✅ Index found  |  {len(self.section_map)} sections parsed")
            print(f"\n  Section → Page map:")
            for sec, bounds in sorted(self.section_map.items(), key=lambda x: x[1]["start"]):
                s, e = bounds["start"], bounds["end"]
                page_label = f"{s}" if s == e else f"{s}–{e}"
                print(f"    page {page_label:>6}  →  {sec}")

            index_detection_meta = {
                "found":           True,
                "index_page_set":  list(index_page_set),
                "sections_parsed": len(self.section_map),
            }
        else:
            print("  ⚠️  No index found → fallback: OCR ALL pages + FAISS")
            index_detection_meta = {"found": False}
            index_page_set = set()
            index_start    = -1

        # ================================================================
        # STEP 2 — MAP CRITERIA → SECTIONS  (one Claude call)
        # ================================================================
        print("\n── STEP 2: Criteria → Section mapping ───────────────────")
        section_to_ids   = None
        criteria_section_map = {}   # { "C01": ["section name", ...] }

        if self.section_map:
            section_to_ids, self.criteria_by_id = map_criteria_to_sections(
                self.eligibility_path, self.section_map
            )
            # Invert for manifest: criteria_id → [sections]
            for sec, ids in section_to_ids.items():
                for cid in ids:
                    criteria_section_map.setdefault(cid, []).append(sec)

            print(f"  Criteria → Section map:")
            for cid, secs in criteria_section_map.items():
                ctext = self.criteria_by_id.get(cid, {}).get("text", "")[:60]
                print(f"    {cid}: {secs}  ← \"{ctext}...\"")
        else:
            try:
                self.criteria_by_id, _ = load_criteria_with_ids(self.eligibility_path)
            except Exception:
                pass

        # ================================================================
        # STEP 3 — LAZY OCR: only relevant pages
        # ================================================================
        print("\n── STEP 3: Lazy OCR ─────────────────────────────────────")
        pre_index_words = []
        page_data       = []

        for i in range(total):
            # Pre-index pages (cover, forwarding letter)
            if index_start > 0 and i < index_start:
                cached = extraction_cache.get(i)
                text   = cached["text"] if cached else self._extract_text_for_page(i)[0]
                conf   = cached["conf"] if cached else 1.0
                for word in text.split():
                    pre_index_words.append({"word": word, "page": i, "conf": conf})
                continue

            # Index pages themselves — skip
            if i in index_page_set:
                continue

            section = assign_section(i, self.section_map)

            if section_to_ids is not None:
                if section not in section_to_ids:
                    continue                        # ← cost saving: skip irrelevant
                crit_ids = section_to_ids[section]
            else:
                crit_ids = list(self.criteria_by_id.keys())
            if i in extraction_cache:
                text, conf = extraction_cache[i]["text"], extraction_cache[i]["conf"]
            else:
                print(f"  🔍 OCR page {i:>3}  (section: '{section}')")
                text, conf = self._extract_text_for_page(i)

            page_data.append({
                "page": i, "text": text, "conf": conf,
                "section": section, "criterion_ids": crit_ids,
            })

        # ================================================================
        # STEP 4 — CHUNKING
        # ================================================================
        print("\n── STEP 4: Chunking ─────────────────────────────────────")

        # Pre-index → one combined chunk per section "pre-index"
        processed_sections = {}

        if pre_index_words:
            chunks = self._chunk_words(pre_index_words, "pre-index", [])
            processed_sections["pre-index"] = {
                "pages":        list({w["page"] for w in pre_index_words}),
                "criterion_ids": [],
                "chunks":       chunks,
            }
            self._all_chunks.extend(chunks)

        # Group page_data by section (preserves cross-page text coherence)
        section_groups   = defaultdict(list)
        section_criteria = {}

        for p in page_data:
            sec = p["section"]
            section_criteria[sec] = p["criterion_ids"]
            for word in p["text"].split():
                section_groups[sec].append({
                    "word": word, "page": p["page"], "conf": p["conf"],
                })

        for sec, words in section_groups.items():
            crit_ids = section_criteria[sec]
            chunks   = self._chunk_words(words, sec, crit_ids)
            pages    = sorted({w["page"] for w in words})
            processed_sections[sec] = {
                "pages":        pages,
                "criterion_ids": crit_ids,
                "chunks":       chunks,
            }
            self._all_chunks.extend(chunks)
            print(f"  ✅ '{sec}'  pages={pages}  chunks={len(chunks)}")

        # ================================================================
        # BUILD MANIFEST
        # ================================================================
        self._manifest = {
            "bidder_id":           os.path.splitext(os.path.basename(self.file_path))[0],
            "source_file":         self.file_path,
            "index_detection":     index_detection_meta,
            "section_page_map":    {
                sec: {"pages": f"{v['start']}–{v['end']}" if v['start'] != v['end'] else str(v['start'])}
                for sec, v in self.section_map.items()
            } if self.section_map else {},
            "criteria_lookup":     self.criteria_by_id,
            "criteria_section_map": criteria_section_map,
            "section_summary": {
                sec: {
                    "pages":         info["pages"],
                    "criterion_ids": info["criterion_ids"],
                    "chunk_ids":     [c["chunk_id"] for c in info["chunks"]],
                }
                for sec, info in processed_sections.items()
            },
        }

        print(f"\n✅ Pipeline complete — {len(self._all_chunks)} total chunks across "
              f"{len(processed_sections)} sections")
        return processed_sections

    # ------------------------------------------------------------------
    def save_output(self, bidder_id=None):
        os.makedirs(self.output_dir, exist_ok=True)
        bid = bidder_id or self._manifest.get("bidder_id", "bidder")

        # File 1: manifest (no text, lightweight)
        manifest_path = os.path.join(self.output_dir, f"{bid}_manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(self._manifest, f, indent=2)
        print(f"💾 Manifest  → {manifest_path}")

        # File 2: chunks as JSONL (one line per chunk, lazy-readable)
        chunks_path = os.path.join(self.output_dir, f"{bid}_sections.jsonl")
        with open(chunks_path, "w") as f:
            for chunk in self._all_chunks:
                f.write(json.dumps(chunk) + "\n")
        print(f"💾 Sections  → {chunks_path}  ({len(self._all_chunks)} chunks)")