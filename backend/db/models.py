from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class TenderStatus(str, Enum):
    DRAFT = "draft"
    CRITERIA_EXTRACTED = "criteria_extracted"
    AWAITING_BIDS = "awaiting_bids"
    EVALUATION_IN_PROGRESS = "evaluation_in_progress"
    EVALUATION_COMPLETE = "evaluation_complete"
    COMPLETED = "completed"


class CriterionType(str, Enum):
    FINANCIAL = "financial"
    TECHNICAL = "technical"
    CERTIFICATION = "certification"
    EXPERIENCE = "experience"


class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW = "REVIEW"


class ExtractionMethod(str, Enum):
    REGEX = "regex"
    LLM = "llm"


# Tender Models
class TenderBase(BaseModel):
    title: str
    department: str
    estimated_value: Optional[str] = None
    issue_date: Optional[str] = None
    closing_date: Optional[str] = None


class TenderCreate(TenderBase):
    pass


class TenderUpdate(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    estimated_value: Optional[str] = None
    issue_date: Optional[str] = None
    closing_date: Optional[str] = None
    status: Optional[TenderStatus] = None
    total_pages: Optional[int] = None
    extracted_criteria_count: Optional[int] = None


class Tender(TenderBase):
    id: str
    status: TenderStatus
    total_pages: Optional[int] = None
    extracted_criteria_count: Optional[int] = None
    bidders_count: int = 0
    pending_reviews: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Criterion Models
class CriterionBase(BaseModel):
    tender_id: str
    field: str
    type: CriterionType
    requirement: str
    mandatory: bool = True
    source: Optional[str] = None
    unresolved_ref: Optional[str] = None


class CriterionCreate(CriterionBase):
    pass


class Criterion(CriterionBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Bidder Models
class BidderBase(BaseModel):
    tender_id: str
    name: str
    location: Optional[str] = None
    documents_count: int = 0
    ocr_confidence: float = 0.0


class BidderCreate(BidderBase):
    pass


class Bidder(BidderBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Evaluation Models
class EvaluationSignals(BaseModel):
    extraction: float
    ocr: float
    retrieval: float
    llm: float


class EvaluationBase(BaseModel):
    tender_id: str
    bidder_id: str
    criterion_id: str
    verdict: Verdict
    confidence: float
    extracted_value: str
    method: ExtractionMethod
    source_page: Optional[str] = None
    signals: EvaluationSignals
    explanation: str


class EvaluationCreate(EvaluationBase):
    pass


class Evaluation(EvaluationBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Review Queue Models
class ReviewItemBase(BaseModel):
    tender_id: str
    evaluation_id: str
    urgency: str = "medium"  # high, medium, low
    reason: str


class ReviewItemCreate(ReviewItemBase):
    pass


class ReviewItem(ReviewItemBase):
    id: str
    status: str = "pending"  # pending, confirmed, overridden
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Audit Trail Models
class AuditLogBase(BaseModel):
    tender_id: str
    action: str
    officer: str
    detail: str
    doc_hash: Optional[str] = None
    version: str = "1.0"


class AuditLogCreate(AuditLogBase):
    pass


class AuditLog(AuditLogBase):
    id: str
    timestamp: datetime
    
    class Config:
        from_attributes = True


# Response Models
class TenderListResponse(BaseModel):
    tenders: List[Tender]
    total: int


class CriteriaListResponse(BaseModel):
    criteria: List[Criterion]
    total: int


class BidderListResponse(BaseModel):
    bidders: List[Bidder]
    total: int


class EvaluationMatrixResponse(BaseModel):
    evaluations: List[Evaluation]
    bidders: List[Bidder]
    criteria: List[Criterion]


class ReviewQueueResponse(BaseModel):
    items: List[ReviewItem]
    total: int


class AuditTrailResponse(BaseModel):
    logs: List[AuditLog]
    total: int


class DashboardStats(BaseModel):
    active_tenders: int
    pending_reviews: int
    bidders_evaluated: int
    compliance_rate: int
