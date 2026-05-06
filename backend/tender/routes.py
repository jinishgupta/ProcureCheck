import os
import uuid
import tempfile
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from db.database import Database
from db.models import (
    Tender, TenderCreate, TenderUpdate, TenderListResponse, TenderStatus,
    Criterion, CriterionCreate, CriteriaListResponse, CriterionType,
)
from tender.pipeline import run_tender_pipeline


# ─── Tender Router ─────────────────────────────────────────

tender_router = APIRouter(prefix="/tenders", tags=["tenders"])


@tender_router.get("/", response_model=TenderListResponse)
async def get_tenders():
    """Get all tenders"""
    try:
        with Database.get_cursor() as cursor:
            # Get all tenders with counts
            cursor.execute("""
                SELECT 
                    t.*,
                    COALESCE(b.bidders_count, 0) as bidders_count,
                    COALESCE(r.pending_reviews, 0) as pending_reviews
                FROM tenders t
                LEFT JOIN (
                    SELECT tender_id, COUNT(*) as bidders_count
                    FROM bidders
                    GROUP BY tender_id
                ) b ON t.id = b.tender_id
                LEFT JOIN (
                    SELECT tender_id, COUNT(*) as pending_reviews
                    FROM review_queue
                    WHERE status = 'pending'
                    GROUP BY tender_id
                ) r ON t.id = r.tender_id
                ORDER BY t.created_at DESC
            """)
            
            rows = cursor.fetchall()
            tenders = [Tender(**dict(row)) for row in rows]
            
            return TenderListResponse(tenders=tenders, total=len(tenders))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@tender_router.get("/{tender_id}", response_model=Tender)
async def get_tender(tender_id: str):
    """Get a specific tender"""
    try:
        with Database.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    t.*,
                    COALESCE(b.bidders_count, 0) as bidders_count,
                    COALESCE(r.pending_reviews, 0) as pending_reviews
                FROM tenders t
                LEFT JOIN (
                    SELECT tender_id, COUNT(*) as bidders_count
                    FROM bidders
                    GROUP BY tender_id
                ) b ON t.id = b.tender_id
                LEFT JOIN (
                    SELECT tender_id, COUNT(*) as pending_reviews
                    FROM review_queue
                    WHERE status = 'pending'
                    GROUP BY tender_id
                ) r ON t.id = r.tender_id
                WHERE t.id = %s
            """, (tender_id,))
            
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Tender not found")
            
            return Tender(**dict(row))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@tender_router.post("/", response_model=Tender)
async def create_tender(tender: TenderCreate):
    """Create a new tender"""
    try:
        with Database.get_cursor() as cursor:
            tender_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            cursor.execute("""
                INSERT INTO tenders (
                    id, title, department, estimated_value, issue_date, closing_date,
                    status, total_pages, extracted_criteria_count, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """, (
                tender_id, tender.title, tender.department, tender.estimated_value,
                tender.issue_date, tender.closing_date, TenderStatus.DRAFT.value,
                0, 0, now, now
            ))
            
            row = cursor.fetchone()
            result = dict(row)
            result["bidders_count"] = 0
            result["pending_reviews"] = 0
            
            # Create audit log
            cursor.execute("""
                INSERT INTO audit_logs (id, tender_id, action, officer, detail, version, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                str(uuid.uuid4()), tender_id, "TENDER_CREATED", "System",
                f"Tender '{tender.title}' created", "1.0", now
            ))
            
            return Tender(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@tender_router.patch("/{tender_id}", response_model=Tender)
async def update_tender(tender_id: str, tender_update: TenderUpdate):
    """Update a tender"""
    try:
        with Database.get_cursor() as cursor:
            # Check if tender exists
            cursor.execute("SELECT id FROM tenders WHERE id = %s", (tender_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Tender not found")
            
            # Build update query dynamically
            update_data = {
                k: v for k, v in tender_update.model_dump(exclude_unset=True).items()
                if v is not None
            }
            
            if not update_data:
                raise HTTPException(status_code=400, detail="No fields to update")
            
            update_data["updated_at"] = datetime.utcnow()
            
            set_clause = ", ".join([f"{k} = %s" for k in update_data.keys()])
            values = list(update_data.values()) + [tender_id]
            
            cursor.execute(f"""
                UPDATE tenders
                SET {set_clause}
                WHERE id = %s
                RETURNING *
            """, values)
            
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=500, detail="Failed to update tender")
            
            # Get counts
            cursor.execute("""
                SELECT COUNT(*) as count FROM bidders WHERE tender_id = %s
            """, (tender_id,))
            bidders_count = cursor.fetchone()['count']
            
            cursor.execute("""
                SELECT COUNT(*) as count FROM review_queue 
                WHERE tender_id = %s AND status = 'pending'
            """, (tender_id,))
            reviews_count = cursor.fetchone()['count']
            
            result = dict(row)
            result["bidders_count"] = bidders_count
            result["pending_reviews"] = reviews_count
            
            return Tender(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@tender_router.delete("/{tender_id}")
async def delete_tender(tender_id: str):
    """Delete a tender"""
    try:
        with Database.get_cursor() as cursor:
            # Check if tender exists
            cursor.execute("SELECT id FROM tenders WHERE id = %s", (tender_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Tender not found")
            
            # Delete tender (cascade will handle related records)
            cursor.execute("DELETE FROM tenders WHERE id = %s", (tender_id,))
            
            return {"message": "Tender deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@tender_router.post("/{tender_id}/upload")
async def upload_tender_document(tender_id: str, file: UploadFile = File(...)):
    """Upload tender PDF and run the extraction pipeline (synchronous)."""
    try:
        with Database.get_cursor() as cursor:
            # Check if tender exists
            cursor.execute("SELECT id FROM tenders WHERE id = %s", (tender_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Tender not found")
        
        # Save uploaded file to a temp location
        suffix = os.path.splitext(file.filename or "upload.pdf")[1] or ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # Run the pipeline (synchronous — may take minutes)
            result = run_tender_pipeline(tmp_path)
            
            total_pages = result.get("total_pages", 0)
            criteria_list = result.get("criteria", [])
            
            # Store criteria in database
            now = datetime.utcnow()
            with Database.get_cursor() as cursor:
                for criterion in criteria_list:
                    criterion_id = str(uuid.uuid4())
                    
                    # Map applies_to to a CriterionType
                    applies_to = criterion.get("applies_to", "all")
                    text = criterion.get("text", "")
                    source = f"{criterion.get('source_path', '')} (p.{criterion.get('page_range', '')})"
                    
                    # Infer type from text heuristics
                    text_lower = text.lower()
                    if any(kw in text_lower for kw in ["turnover", "net worth", "solvency", "financial"]):
                        ctype = CriterionType.FINANCIAL.value
                    elif any(kw in text_lower for kw in ["registration", "certificate", "pan", "gst", "epf", "esic", "license", "bis"]):
                        ctype = CriterionType.CERTIFICATION.value
                    elif any(kw in text_lower for kw in ["experience", "completed", "past work", "similar work"]):
                        ctype = CriterionType.EXPERIENCE.value
                    else:
                        ctype = CriterionType.TECHNICAL.value
                    
                    cursor.execute("""
                        INSERT INTO criteria (
                            id, tender_id, field, type, requirement, mandatory, source, unresolved_ref, created_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        criterion_id, tender_id,
                        text[:120],  # field = short label
                        ctype,
                        text,        # requirement = full text
                        True,
                        source,
                        None,
                        now,
                    ))
                
                # Update tender
                cursor.execute("""
                    UPDATE tenders
                    SET status = %s, total_pages = %s, extracted_criteria_count = %s, updated_at = %s
                    WHERE id = %s
                """, (
                    TenderStatus.CRITERIA_EXTRACTED.value,
                    total_pages,
                    len(criteria_list),
                    now,
                    tender_id,
                ))
                
                # Create audit log
                cursor.execute("""
                    INSERT INTO audit_logs (id, tender_id, action, officer, detail, version, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    str(uuid.uuid4()), tender_id, "TENDER_UPLOADED", "System",
                    f"Tender document '{file.filename}' processed — {len(criteria_list)} criteria extracted from {total_pages} pages",
                    "1.0", now
                ))
            
            return {
                "message": "Pipeline complete",
                "filename": file.filename,
                "total_pages": total_pages,
                "criteria_count": len(criteria_list),
            }
        
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ─── Criteria Router ───────────────────────────────────────

criteria_router = APIRouter(prefix="/criteria", tags=["criteria"])


@criteria_router.get("/", response_model=CriteriaListResponse)
async def get_criteria(tender_id: Optional[str] = None):
    """Get all criteria, optionally filtered by tender"""
    try:
        with Database.get_cursor() as cursor:
            if tender_id:
                cursor.execute("""
                    SELECT * FROM criteria
                    WHERE tender_id = %s
                    ORDER BY created_at
                """, (tender_id,))
            else:
                cursor.execute("SELECT * FROM criteria ORDER BY created_at")
            
            rows = cursor.fetchall()
            criteria = [Criterion(**dict(row)) for row in rows]
            
            return CriteriaListResponse(criteria=criteria, total=len(criteria))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@criteria_router.get("/{criterion_id}", response_model=Criterion)
async def get_criterion(criterion_id: str):
    """Get a specific criterion"""
    try:
        with Database.get_cursor() as cursor:
            cursor.execute("SELECT * FROM criteria WHERE id = %s", (criterion_id,))
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Criterion not found")
            
            return Criterion(**dict(row))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@criteria_router.post("/", response_model=Criterion)
async def create_criterion(criterion: CriterionCreate):
    """Create a new criterion"""
    try:
        with Database.get_cursor() as cursor:
            criterion_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            cursor.execute("""
                INSERT INTO criteria (
                    id, tender_id, field, type, requirement, mandatory, source, unresolved_ref, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """, (
                criterion_id, criterion.tender_id, criterion.field, criterion.type.value,
                criterion.requirement, criterion.mandatory, criterion.source,
                criterion.unresolved_ref, now
            ))
            
            row = cursor.fetchone()
            
            # Update tender criteria count
            cursor.execute("""
                UPDATE tenders
                SET extracted_criteria_count = (
                    SELECT COUNT(*) FROM criteria WHERE tender_id = %s
                ),
                updated_at = %s
                WHERE id = %s
            """, (criterion.tender_id, now, criterion.tender_id))
            
            return Criterion(**dict(row))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@criteria_router.delete("/{criterion_id}")
async def delete_criterion(criterion_id: str):
    """Delete a criterion"""
    try:
        with Database.get_cursor() as cursor:
            # Get criterion to find tender_id
            cursor.execute("SELECT tender_id FROM criteria WHERE id = %s", (criterion_id,))
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Criterion not found")
            
            tender_id = row['tender_id']
            
            # Delete criterion
            cursor.execute("DELETE FROM criteria WHERE id = %s", (criterion_id,))
            
            # Update tender criteria count
            cursor.execute("""
                UPDATE tenders
                SET extracted_criteria_count = (
                    SELECT COUNT(*) FROM criteria WHERE tender_id = %s
                ),
                updated_at = %s
                WHERE id = %s
            """, (tender_id, datetime.utcnow(), tender_id))
            
            return {"message": "Criterion deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
