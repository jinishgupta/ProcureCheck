from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import tenders, criteria, bidders, evaluations

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
app.include_router(tenders.router, prefix="/api")
app.include_router(criteria.router, prefix="/api")
app.include_router(bidders.router, prefix="/api")
app.include_router(evaluations.router, prefix="/api")


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
