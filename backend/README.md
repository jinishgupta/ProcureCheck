# ProcureCheck Backend API

FastAPI backend with Supabase database for the AI-Based Tender Evaluation Platform.

## Tech Stack

- **FastAPI** - Modern Python web framework
- **Supabase** - PostgreSQL database with real-time capabilities
- **Pydantic** - Data validation and settings management
- **Uvicorn** - ASGI server

## Setup

### 1. Install Dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Supabase

1. Create a Supabase project at https://supabase.com
2. Go to Project Settings > API
3. Copy your project URL and anon key
4. Run the SQL schema in the Supabase SQL Editor:
   ```bash
   # Copy contents of supabase_schema.sql and run in Supabase SQL Editor
   ```

### 3. Environment Variables

Create a `.env` file in the backend directory:

```bash
cp .env.example .env
```

Edit `.env` and add your Supabase credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
ENVIRONMENT=development
```

### 4. Run the Server

```bash
# Development mode with auto-reload
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## API Endpoints

### Tenders
- `GET /api/tenders/` - List all tenders
- `GET /api/tenders/{tender_id}` - Get specific tender
- `POST /api/tenders/` - Create new tender
- `PATCH /api/tenders/{tender_id}` - Update tender
- `DELETE /api/tenders/{tender_id}` - Delete tender
- `POST /api/tenders/{tender_id}/upload` - Upload tender document

### Criteria
- `GET /api/criteria/?tender_id={id}` - List criteria for tender
- `GET /api/criteria/{criterion_id}` - Get specific criterion
- `POST /api/criteria/` - Create new criterion
- `DELETE /api/criteria/{criterion_id}` - Delete criterion

### Bidders
- `GET /api/bidders/?tender_id={id}` - List bidders for tender
- `GET /api/bidders/{bidder_id}` - Get specific bidder
- `POST /api/bidders/` - Create new bidder
- `POST /api/bidders/{bidder_id}/upload` - Upload bidder documents
- `DELETE /api/bidders/{bidder_id}` - Delete bidder

### Evaluations
- `GET /api/evaluations/matrix/{tender_id}` - Get evaluation matrix
- `POST /api/evaluations/` - Create evaluation
- `GET /api/review-queue/{tender_id}` - Get review queue
- `PATCH /api/review-queue/{review_id}` - Update review item
- `GET /api/audit-trail/{tender_id}` - Get audit trail
- `GET /api/dashboard/stats` - Get dashboard statistics

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py          # Configuration settings
│   ├── database.py        # Supabase client
│   ├── models.py          # Pydantic models
│   └── routes/
│       ├── __init__.py
│       ├── tenders.py     # Tender endpoints
│       ├── criteria.py    # Criteria endpoints
│       ├── bidders.py     # Bidder endpoints
│       └── evaluations.py # Evaluation endpoints
├── main.py                # FastAPI application
├── requirements.txt       # Python dependencies
├── supabase_schema.sql    # Database schema
├── .env.example          # Environment variables template
└── README.md             # This file
```

## Database Schema

### Tables

1. **tenders** - Tender documents
2. **criteria** - Eligibility criteria extracted from tenders
3. **bidders** - Bidder information and documents
4. **evaluations** - Evaluation results (bidder × criterion)
5. **review_queue** - Items requiring human review
6. **audit_logs** - Complete audit trail

### Relationships

- Tender → Criteria (one-to-many)
- Tender → Bidders (one-to-many)
- Tender → Evaluations (one-to-many)
- Bidder × Criterion → Evaluation (many-to-many through evaluations)
- Evaluation → Review Queue (one-to-one, optional)

## Development

### Testing the API

Use the interactive docs at http://localhost:8000/docs to test endpoints.

Or use curl:

```bash
# Create a tender
curl -X POST http://localhost:8000/api/tenders/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Supply of Ballistic Helmets",
    "department": "Central Reserve Police Force",
    "estimated_value": "₹12.8 Cr"
  }'

# Get all tenders
curl http://localhost:8000/api/tenders/

# Get dashboard stats
curl http://localhost:8000/api/dashboard/stats
```

### Adding New Endpoints

1. Create route function in appropriate file under `app/routes/`
2. Add Pydantic models in `app/models.py` if needed
3. Import and include router in `main.py`

## Next Steps

The current implementation provides:
- ✅ Complete CRUD operations for all entities
- ✅ Supabase integration
- ✅ Audit trail logging
- ✅ Review queue management
- ✅ Dashboard statistics

To implement the AI processing logic:
1. Add OCR processing (PyMuPDF, Google Cloud Vision)
2. Add LLM integration (Gemini API)
3. Add vector search (FAISS)
4. Add document processing pipeline
5. Add confidence scoring logic
6. Add cross-document validation

## License

Proprietary - AI for Bharat Project
