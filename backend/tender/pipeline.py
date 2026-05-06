"""
Tender Pipeline Orchestrator

Runs the full tender processing pipeline:
  1. Extract headings from PDF (index.py)
  2. Filter noise, assign structure, build tree
  3. Enrich with KeyBERT summaries
  4. Traverse tree to find eligibility sections
  5. Extract criteria from relevant sections (eligibility.py)
  6. Deduplicate and clean criteria
"""

import fitz
import json

from tender.index import (
    extract_headings,
    llm_noise_filter,
    assign_page_ranges,
    llm_assign_structure,
    build_tree,
    assign_node_ids,
    print_tree,
)
from tender.eligibility import (
    load_pages,
    enrich_index_with_summaries,
    traverse_tree,
    get_tagged_page_range,
    extract_criteria_from_section,
    deduplicate_criteria,
    is_false_positive,
    clean_criteria_with_llm,
)


def run_tender_pipeline(pdf_path: str) -> dict:
    """
    Run the complete tender processing pipeline on a PDF file.
    
    Returns:
        dict with keys:
            - doc_name: str
            - total_pages: int
            - structure: list[dict]  (the heading tree)
            - criteria: list[dict]   (extracted eligibility criteria)
    """
    print(f"\n{'='*60}")
    print(f"[Pipeline] Starting tender pipeline for: {pdf_path}")
    print(f"{'='*60}\n")
    
    # ── Step 1: Get total pages ──
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    doc.close()
    print(f"[Pipeline] PDF has {total_pages} pages")
    
    # ── Step 2: Extract headings ──
    print(f"\n--- Extracting headings ---")
    headings = extract_headings(pdf_path)
    
    if not headings:
        print("[Pipeline] No headings found — returning empty result")
        return {
            "doc_name": pdf_path,
            "total_pages": total_pages,
            "structure": [],
            "criteria": [],
        }
    
    # ── Step 3: Filter noise ──
    print(f"\n--- Filtering noise ---")
    headings = llm_noise_filter(headings)
    
    # ── Step 4: Assign page ranges ──
    print(f"\n--- Assigning page ranges ---")
    headings = assign_page_ranges(headings, total_pages, pdf_path)
    
    # ── Step 5: Assign hierarchical structure ──
    print(f"\n--- Assigning structure ---")
    headings = llm_assign_structure(headings)
    
    # ── Step 6: Build tree ──
    print(f"\n--- Building tree ---")
    tree = build_tree(headings)
    assign_node_ids(tree)
    
    print(f"\n--- Tree structure ---")
    print_tree(tree)
    
    # ── Step 7: Load pages for eligibility extraction ──
    print(f"\n--- Loading pages ---")
    pages_cache = load_pages(pdf_path)
    
    # ── Step 8: Enrich index with KeyBERT summaries ──
    print(f"\n--- Generating KeyBERT summaries ---")
    tree = enrich_index_with_summaries(tree, pages_cache)
    
    # ── Step 9: Traverse tree to find relevant sections ──
    print(f"\n--- Traversing index tree ---")
    relevant_sections = traverse_tree(tree, pages_cache)
    
    print(f"\n[Traversal] {len(relevant_sections)} sections selected:")
    for s in relevant_sections:
        print(f"  [{s['node_id']}] {s['source_path']} (p.{s['start_index']}-{s['end_index']})")
    
    # ── Step 10: Extract eligibility criteria ──
    print(f"\n--- Extracting eligibility criteria ---")
    all_criteria = []
    
    for section in relevant_sections:
        print(f"\n[Section] {section['source_path']} (p.{section['start_index']}-{section['end_index']})")
        page_text = get_tagged_page_range(
            pages_cache, section["start_index"], section["end_index"]
        )
        criteria = extract_criteria_from_section(section, page_text)
        all_criteria.extend(criteria)
    
    # ── Step 11: Deduplicate ──
    print(f"\n[Total] {len(all_criteria)} criteria before dedup")
    all_criteria = deduplicate_criteria(all_criteria)
    all_criteria = [c for c in all_criteria if not is_false_positive(c["text"])]
    print(f"[Total] {len(all_criteria)} criteria after false positive filter")
    
    # ── Step 12: LLM cleaning pass ──
    print(f"\n--- Cleaning criteria with Gemini ---")
    all_criteria = clean_criteria_with_llm(all_criteria)
    
    # ── Summary ──
    registered   = [c for c in all_criteria if c["applies_to"] == "registered"]
    unregistered = [c for c in all_criteria if c["applies_to"] == "unregistered"]
    all_bidders  = [c for c in all_criteria if c["applies_to"] == "all"]
    
    print(f"\n[Pipeline Summary]")
    print(f"  Total pages:   {total_pages}")
    print(f"  Total criteria: {len(all_criteria)}")
    print(f"  All bidders:   {len(all_bidders)}")
    print(f"  Registered:    {len(registered)}")
    print(f"  Unregistered:  {len(unregistered)}")
    print(f"{'='*60}\n")
    
    return {
        "doc_name": pdf_path,
        "total_pages": total_pages,
        "structure": tree,
        "criteria": all_criteria,
    }
