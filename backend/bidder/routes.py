from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from typing import Optional
from db.models import Bidder, BidderCreate, BidderListResponse
from db.database import Database
from datetime import datetime
import uuid
import os
import shutil
from bidder.pipeline.pipeline_runner import BidderPipeline

router = APIRouter(prefix="/bidders", tags=["bidders"])


@router.get("/", response_model=BidderListResponse)
async def get_bidders(tender_id: Optional[str] = None):
    """Get all bidders, optionally filtered by tender"""
    try:
        with Database.get_cursor() as cursor:
            if tender_id:
                cursor.execute("""
                    SELECT * FROM bidders
                    WHERE tender_id = %s
                    ORDER BY created_at
                """, (tender_id,))
            else:
                cursor.execute("SELECT * FROM bidders ORDER BY created_at")
            
            rows = cursor.fetchall()
            bidders = [Bidder(**dict(row)) for row in rows]
            
            return BidderListResponse(bidders=bidders, total=len(bidders))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{bidder_id}", response_model=Bidder)
async def get_bidder(bidder_id: str):
    """Get a specific bidder"""
    try:
        with Database.get_cursor() as cursor:
            cursor.execute("SELECT * FROM bidders WHERE id = %s", (bidder_id,))
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Bidder not found")
            
            return Bidder(**dict(row))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Bidder)
async def create_bidder(bidder: BidderCreate):
    """Create a new bidder"""
    try:
        with Database.get_cursor() as cursor:
            bidder_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            cursor.execute("""
                INSERT INTO bidders (
                    id, tender_id, name, location, documents_count, ocr_confidence, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """, (
                bidder_id, bidder.tender_id, bidder.name, bidder.location,
                bidder.documents_count, bidder.ocr_confidence, now, now
            ))
            
            row = cursor.fetchone()
            
            # Create audit log
            cursor.execute("""
                INSERT INTO audit_logs (id, tender_id, action, officer, detail, version, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                str(uuid.uuid4()), bidder.tender_id, "BIDDER_UPLOADED", "System",
                f"Bidder '{bidder.name}' documents uploaded ({bidder.documents_count} files)",
                "1.0", now
            ))
            
            return Bidder(**dict(row))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from concurrent.futures import ThreadPoolExecutor
import numpy as np
import faiss

def process_bidder_documents(file_paths: list[str], tender_id: str, bidder_id: str):
    """Process bidder documents - matching pipeline should be triggered separately after all bidders are uploaded"""
    try:
        print(f"\n{'='*60}")
        print(f"[Bidder Pipeline] Starting processing for bidder: {bidder_id}")
        print(f"[Bidder Pipeline] Number of documents: {len(file_paths)}")
        print(f"{'='*60}\n")
        
        def run_pipeline(fp):
            print(f"[Bidder Pipeline] Processing document: {os.path.basename(fp)}")
            pipeline = BidderPipeline(fp, tender_id, bidder_id)
            pipeline.run()
            print(f"[Bidder Pipeline] ✅ Completed: {os.path.basename(fp)}")
            return pipeline
            
        # Run pipelines in parallel (3-4 at a time)
        with ThreadPoolExecutor(max_workers=4) as executor:
            pipelines = list(executor.map(run_pipeline, file_paths))
            
        print(f"\n[Bidder Pipeline] ✅ Parallel processing of {len(file_paths)} documents completed.")
        
        # Merge outputs
        from bidder.pipeline.config import FAISS_DIM
        merged_index = faiss.IndexFlatIP(FAISS_DIM)
        merged_chunks = []
        
        print(f"[Bidder Pipeline] Merging FAISS indexes...")
        for p in pipelines:
            merged_chunks.extend(p._all_chunks)
            for vec in p.index.embeddings:
                merged_index.add(vec)
                
        # Save merged output
        output_dir = os.path.join("data", "bidder_indexes", bidder_id)
        os.makedirs(output_dir, exist_ok=True)
        
        index_path = os.path.join(output_dir, "faiss.index")
        faiss.write_index(merged_index, index_path)
        
        pages_out = []
        for c in merged_chunks:
            pages_out.append({
                "page_number": c["pages"][0] if c.get("pages") else 1,
                "text": c["text"],
                "label": f"[{c['chunk_id']}]",
                "ocr_confidence": c["ocr_confidence"]
            })
            
        pages_path = os.path.join(output_dir, "pages.json")
        import json
        with open(pages_path, "w") as f:
            json.dump(pages_out, f, indent=2)
            
        print(f"[Bidder Pipeline] 💾 Merged FAISS Index → {index_path}")
        print(f"[Bidder Pipeline] 💾 Merged Pages json  → {pages_path} ({len(pages_out)} items)")
        
        # Update bidder OCR confidence
        with Database.get_cursor() as cursor:
            avg_conf = sum(p["ocr_confidence"] for p in pages_out) / len(pages_out) if pages_out else 0.95
            cursor.execute(
                "UPDATE bidders SET ocr_confidence = %s WHERE id = %s", 
                (avg_conf, bidder_id)
            )
            print(f"[Bidder Pipeline] Updated bidder OCR confidence: {avg_conf:.2%}")
        
        print(f"\n[Bidder Pipeline] ✅ All processing complete for bidder: {bidder_id}")
        print(f"[Bidder Pipeline] ℹ️  Matching pipeline will run automatically after all bidders are uploaded")
        print(f"{'='*60}\n")
        
        # Check if all bidders for this tender have been processed
        with Database.get_cursor() as cursor:
            # Count total bidders for this tender
            cursor.execute("""
                SELECT COUNT(*) as total FROM bidders WHERE tender_id = %s
            """, (tender_id,))
            total_bidders = cursor.fetchone()['total']
            
            # Count bidders with FAISS indexes (processed)
            cursor.execute("""
                SELECT COUNT(*) as processed FROM bidders 
                WHERE tender_id = %s AND ocr_confidence > 0
            """, (tender_id,))
            processed_bidders = cursor.fetchone()['processed']
            
            print(f"[Bidder Pipeline] Progress: {processed_bidders}/{total_bidders} bidders processed")
            
            # Only trigger matching if ALL bidders are processed
            if processed_bidders >= total_bidders and total_bidders > 0:
                print(f"\n[Matching Pipeline] ✅ All {total_bidders} bidders processed!")
                print(f"[Matching Pipeline] Auto-triggering evaluation for tender: {tender_id}")
                
                from matching.engine import run_evaluation_for_tender
                try:
                    result = run_evaluation_for_tender(tender_id)
                    print(f"[Matching Pipeline] ✅ Evaluation complete!")
                    print(f"[Matching Pipeline] Results: {result.get('totals', {})}")
                except Exception as e:
                    print(f"[Matching Pipeline] ❌ Error during evaluation: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"[Bidder Pipeline] ⏳ Waiting for remaining bidders to be processed...")
            
    except Exception as e:
        print(f"❌ Error in parallel background processing for {bidder_id}: {e}")
        import traceback
        traceback.print_exc()

@router.post("/{bidder_id}/upload")
async def upload_bidder_documents(
    bidder_id: str, 
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...)
):
    """Upload bidder documents (placeholder for future processing)"""
    try:
        with Database.get_cursor() as cursor:
            # Check if bidder exists
            cursor.execute("SELECT * FROM bidders WHERE id = %s", (bidder_id,))
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Bidder not found")
            
            bidder_data = dict(row)
            tender_id = bidder_data["tender_id"]
            
            # Update document count
            new_count = bidder_data.get("documents_count", 0) + len(files)
            cursor.execute("""
                UPDATE bidders
                SET documents_count = %s, updated_at = %s
                WHERE id = %s
            """, (new_count, datetime.utcnow(), bidder_id))
            
            # Process all uploaded files for indexing
            if files:
                upload_dir = os.path.join("data", "uploads", "bidders", bidder_id)
                os.makedirs(upload_dir, exist_ok=True)
                
                file_paths = []
                for file in files:
                    file_path = os.path.join(upload_dir, file.filename)
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
                    file_paths.append(file_path)
                
                background_tasks.add_task(process_bidder_documents, file_paths, tender_id, bidder_id)

            return {
                "message": "Files uploaded successfully. Processing started in background.",
                "files_count": len(files),
                "filenames": [f.filename for f in files]
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{bidder_id}")
async def delete_bidder(bidder_id: str):
    """Delete a bidder"""
    try:
        with Database.get_cursor() as cursor:
            # Check if bidder exists
            cursor.execute("SELECT id FROM bidders WHERE id = %s", (bidder_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Bidder not found")
            
            # Delete bidder
            cursor.execute("DELETE FROM bidders WHERE id = %s", (bidder_id,))
            
            return {"message": "Bidder deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
