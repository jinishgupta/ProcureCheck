from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Optional
from db.models import Bidder, BidderCreate, BidderListResponse
from db.database import Database
from datetime import datetime
import uuid

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


@router.post("/{bidder_id}/upload")
async def upload_bidder_documents(bidder_id: str, files: list[UploadFile] = File(...)):
    """Upload bidder documents (placeholder for future processing)"""
    try:
        with Database.get_cursor() as cursor:
            # Check if bidder exists
            cursor.execute("SELECT * FROM bidders WHERE id = %s", (bidder_id,))
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Bidder not found")
            
            bidder_data = dict(row)
            
            # TODO: Implement actual file processing
            # For now, just update document count
            new_count = bidder_data.get("documents_count", 0) + len(files)
            cursor.execute("""
                UPDATE bidders
                SET documents_count = %s, updated_at = %s
                WHERE id = %s
            """, (new_count, datetime.utcnow(), bidder_id))
            
            return {
                "message": "Files uploaded successfully",
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
