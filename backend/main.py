from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.config import settings
from tender.routes import tender_router, criteria_router
from bidder.routes import router as bidder_router
from matching.routes import router as matching_router

# Create FastAPI app
app = FastAPI(
    title="ProcureCheck API",
    description="AI-Based Tender Evaluation and Eligibility Analysis Platform",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tender_router, prefix="/api")
app.include_router(criteria_router, prefix="/api")
app.include_router(bidder_router, prefix="/api")
app.include_router(matching_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ProcureCheck API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development"
    )
