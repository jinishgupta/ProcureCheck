# 🏛️ ProcureCheck

> **AI-Based Tender Evaluation and Eligibility Analysis Platform**

ProcureCheck is a comprehensive, full-stack application designed to streamline the government and enterprise procurement process. By leveraging state-of-the-art Artificial Intelligence, Document Processing, and Large Language Models, ProcureCheck automates the evaluation of tender documents and bidder eligibility, saving time and ensuring unbiased, objective assessments.

---

## ✨ Features

- **📄 Automated Document Parsing:** Extracts complex requirements and criteria from Tender PDFs using PyMuPDF and OCR (Google Cloud Vision).
- **🤖 AI-Powered Evaluation:** Utilizes LLMs (Anthropic, Groq, Google GenAI) for semantic understanding, criterion extraction, and matching.
- **🔍 Smart Retrieval & Matching:** Employs `sentence-transformers` and `faiss-cpu` for vector-based semantic search to match bidder documents against tender requirements.
- **⚖️ Human-in-the-Loop:** A dedicated review queue for evaluations with low confidence scores, allowing officers to review, confirm, or override AI decisions.
- **📊 Real-time Dashboard:** Track active tenders, pending reviews, bidder compliance rates, and system analytics in a beautiful, noir-themed UI.
- **⚡ High Performance:** Built on FastAPI for high-throughput asynchronous processing and React/Vite for a lightning-fast frontend.

---

## 🛠️ Technology Stack

### **Frontend**
- **Framework:** [React 19](https://react.dev/) + [Vite](https://vitejs.dev/)
- **Styling:** [Tailwind CSS](https://tailwindcss.com/) + Custom Noir Aesthetics
- **Animations:** [Framer Motion](https://www.framer.com/motion/)
- **Data Visualization:** [Recharts](https://recharts.org/)
- **PDF Generation:** jsPDF + jsPDF-AutoTable

### **Backend**
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **Database:** PostgreSQL (with Supabase schema)
- **AI & ML:** 
  - LLMs: Anthropic, Groq, Google GenAI
  - NLP: Sentence-Transformers, KeyBERT
  - Vector Database: FAISS
  - Vision: Google Cloud Vision, OpenCV
- **Document Processing:** PyMuPDF

---

## 🚀 Getting Started

### Prerequisites
- Node.js (v18+)
- Python (v3.9+)
- PostgreSQL (or Supabase account)

### Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Copy `.env.example` to `.env` and fill in your API keys (Supabase/PostgreSQL, Groq, Anthropic, etc.).
   ```bash
   cp .env.example .env
   ```

5. **Run the FastAPI server:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   *The API will be available at `http://localhost:8000/docs`.*

### Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Run the Vite development server:**
   ```bash
   npm run dev
   ```
   *The app will be available at `http://localhost:5173`.*

---

## 📂 Project Structure

```text
procure-check/
├── backend/                  # FastAPI Application
│   ├── bidder/               # Bidder ingestion & processing
│   ├── data/                 # Local storage for indexes & documents
│   ├── db/                   # Database models and configuration
│   ├── matching/             # AI matching engine (FAISS + LLMs)
│   ├── tender/               # Tender parsing & criteria extraction
│   ├── main.py               # Application entry point
│   └── supabase_schema.sql   # Database schema
└── frontend/                 # React + Vite Application
    ├── public/               # Static assets
    ├── src/
    │   ├── api.js            # Centralized API client
    │   ├── components/       # Reusable UI components
    │   ├── data/             # Mock data and constants
    │   └── pages/            # Application routes/pages
    ├── tailwind.config.js    # Tailwind configuration
    └── package.json          # Frontend dependencies
```

---

## 📖 Project Explanation

The **ProcureCheck** system is built to transform the tedious, error-prone manual tender evaluation process into a streamlined, AI-assisted workflow. Here is how the pipeline works:

1. **Tender Ingestion:** A procurement officer uploads a Tender Document (PDF). The system uses Large Language Models to automatically extract the mandatory criteria (e.g., "Minimum 5 years experience", "ISO 9001 Certification required", "Turnover > $1M").
2. **Bidder Registration:** Bidders and their respective proposal documents are uploaded into the system. These documents are parsed, chunked, and converted into dense vector embeddings stored in a local FAISS index for rapid semantic retrieval.
3. **AI Matching Engine:** For every extracted criterion and every bidder, the AI Matching Engine retrieves the most relevant pages from the bidder's document index. An LLM then evaluates the retrieved context against the criterion to determine a verdict: `PASS`, `FAIL`, or `REVIEW`.
4. **Human-in-the-Loop:** If the AI's confidence score for a verdict falls below a certain threshold, the evaluation is flagged and sent to the **Review Queue**. Here, human officers can verify the AI's reasoning, check the source pages, and either confirm or override the decision.
5. **Dashboard & Analytics:** All results are aggregated into a comprehensive **Bidder Matrix**, giving decision-makers a clear, objective overview of which bidders meet all mandatory criteria, ensuring transparency and compliance.

---

## 📄 License

This project is licensed under the MIT License.
