from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.models import Criterion, CriterionCreate, CriteriaListResponse
from app.database import get_db
from datetime import datetime
import uuid

router = APIRouter(prefix="/criteria", tags=["criteria"])


@router.get("/", response_model=CriteriaListResponse)
async def get_criteria(tender_id: Optional[str] = None):
    """Get all criteria, optionally filtered by tender"""
    try:
        db = get_db()
        query = db.table("criteria").select("*")
        
        if tender_id:
            query = query.eq("tender_id", tender_id)
        
        response = query.order("created_at").execute()
        criteria = [Criterion(**item) for item in response.data]
        
        return CriteriaListResponse(criteria=criteria, total=len(criteria))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{criterion_id}", response_model=Criterion)
async def get_criterion(criterion_id: str):
    """Get a specific criterion"""
    try:
        db = get_db()
        response = db.table("criteria").select("*").eq("id", criterion_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Criterion not found")
        
        return Criterion(**response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Criterion)
async def create_criterion(criterion: CriterionCreate):
    """Create a new criterion"""
    try:
        db = get_db()
        
        criterion_data = {
            "id": str(uuid.uuid4()),
            **criterion.model_dump(),
            "created_at": datetime.utcnow().isoformat(),
        }
        
        response = db.table("criteria").insert(criterion_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create criterion")
        
        # Update tender criteria count
        tender_id = criterion.tender_id
        criteria_count = db.table("criteria").select("id", count="exact").eq("tender_id", tender_id).execute()
        db.table("tenders").update({
            "extracted_criteria_count": len(criteria_count.data),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", tender_id).execute()
        
        return Criterion(**response.data[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{criterion_id}")
async def delete_criterion(criterion_id: str):
    """Delete a criterion"""
    try:
        db = get_db()
        
        # Get criterion to find tender_id
        existing = db.table("criteria").select("*").eq("id", criterion_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Criterion not found")
        
        tender_id = existing.data[0]["tender_id"]
        
        # Delete criterion
        db.table("criteria").delete().eq("id", criterion_id).execute()
        
        # Update tender criteria count
        criteria_count = db.table("criteria").select("id", count="exact").eq("tender_id", tender_id).execute()
        db.table("tenders").update({
            "extracted_criteria_count": len(criteria_count.data),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", tender_id).execute()
        
        return {"message": "Criterion deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
