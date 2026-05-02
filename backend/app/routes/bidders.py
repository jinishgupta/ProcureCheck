from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Optional
from app.models import Bidder, BidderCreate, BidderListResponse
from app.database import get_db
from datetime import datetime
import uuid

router = APIRouter(prefix="/bidders", tags=["bidders"])


@router.get("/", response_model=BidderListResponse)
async def get_bidders(tender_id: Optional[str] = None):
    """Get all bidders, optionally filtered by tender"""
    try:
        db = get_db()
        query = db.table("bidders").select("*")
        
        if tender_id:
            query = query.eq("tender_id", tender_id)
        
        response = query.order("created_at").execute()
        bidders = [Bidder(**item) for item in response.data]
        
        return BidderListResponse(bidders=bidders, total=len(bidders))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{bidder_id}", response_model=Bidder)
async def get_bidder(bidder_id: str):
    """Get a specific bidder"""
    try:
        db = get_db()
        response = db.table("bidders").select("*").eq("id", bidder_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Bidder not found")
        
        return Bidder(**response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Bidder)
async def create_bidder(bidder: BidderCreate):
    """Create a new bidder"""
    try:
        db = get_db()
        
        bidder_data = {
            "id": str(uuid.uuid4()),
            **bidder.model_dump(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        response = db.table("bidders").insert(bidder_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create bidder")
        
        # Create audit log
        audit_data = {
            "id": str(uuid.uuid4()),
            "tender_id": bidder.tender_id,
            "action": "BIDDER_UPLOADED",
            "officer": "System",
            "detail": f"Bidder '{bidder.name}' documents uploaded ({bidder.documents_count} files)",
            "version": "1.0",
            "timestamp": datetime.utcnow().isoformat(),
        }
        db.table("audit_logs").insert(audit_data).execute()
        
        return Bidder(**response.data[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{bidder_id}/upload")
async def upload_bidder_documents(bidder_id: str, files: list[UploadFile] = File(...)):
    """Upload bidder documents (placeholder for future processing)"""
    try:
        db = get_db()
        
        # Check if bidder exists
        existing = db.table("bidders").select("*").eq("id", bidder_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Bidder not found")
        
        bidder_data = existing.data[0]
        
        # TODO: Implement actual file processing
        # For now, just update document count
        update_data = {
            "documents_count": bidder_data.get("documents_count", 0) + len(files),
            "updated_at": datetime.utcnow().isoformat(),
        }
        db.table("bidders").update(update_data).eq("id", bidder_id).execute()
        
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
        db = get_db()
        
        # Check if bidder exists
        existing = db.table("bidders").select("id").eq("id", bidder_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Bidder not found")
        
        # Delete bidder
        db.table("bidders").delete().eq("id", bidder_id).execute()
        
        return {"message": "Bidder deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
