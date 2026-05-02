-- ProcureCheck Database Schema for Supabase

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tenders table
CREATE TABLE IF NOT EXISTS tenders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    department TEXT NOT NULL,
    estimated_value TEXT,
    issue_date TEXT,
    closing_date TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    total_pages INTEGER DEFAULT 0,
    extracted_criteria_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Criteria table
CREATE TABLE IF NOT EXISTS criteria (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    field TEXT NOT NULL,
    type TEXT NOT NULL,
    requirement TEXT NOT NULL,
    mandatory BOOLEAN DEFAULT TRUE,
    source TEXT,
    unresolved_ref TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Bidders table
CREATE TABLE IF NOT EXISTS bidders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    location TEXT,
    documents_count INTEGER DEFAULT 0,
    ocr_confidence FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Evaluations table
CREATE TABLE IF NOT EXISTS evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    bidder_id UUID NOT NULL REFERENCES bidders(id) ON DELETE CASCADE,
    criterion_id UUID NOT NULL REFERENCES criteria(id) ON DELETE CASCADE,
    verdict TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    extracted_value TEXT NOT NULL,
    method TEXT NOT NULL,
    source_page TEXT,
    signals JSONB NOT NULL,
    explanation TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(bidder_id, criterion_id)
);

-- Review Queue table
CREATE TABLE IF NOT EXISTS review_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    evaluation_id UUID NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
    urgency TEXT DEFAULT 'medium',
    reason TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    reviewed_by TEXT,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit Logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    officer TEXT NOT NULL,
    detail TEXT NOT NULL,
    doc_hash TEXT,
    version TEXT DEFAULT '1.0',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_criteria_tender ON criteria(tender_id);
CREATE INDEX IF NOT EXISTS idx_bidders_tender ON bidders(tender_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_tender ON evaluations(tender_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_bidder ON evaluations(bidder_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_criterion ON evaluations(criterion_id);
CREATE INDEX IF NOT EXISTS idx_review_queue_tender ON review_queue(tender_id);
CREATE INDEX IF NOT EXISTS idx_review_queue_status ON review_queue(status);
CREATE INDEX IF NOT EXISTS idx_audit_logs_tender ON audit_logs(tender_id);
CREATE INDEX IF NOT EXISTS idx_tenders_status ON tenders(status);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_tenders_updated_at BEFORE UPDATE ON tenders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bidders_updated_at BEFORE UPDATE ON bidders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE tenders ENABLE ROW LEVEL SECURITY;
ALTER TABLE criteria ENABLE ROW LEVEL SECURITY;
ALTER TABLE bidders ENABLE ROW LEVEL SECURITY;
ALTER TABLE evaluations ENABLE ROW LEVEL SECURITY;
ALTER TABLE review_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Create policies (allow all for now, customize based on your auth requirements)
CREATE POLICY "Allow all operations on tenders" ON tenders FOR ALL USING (true);
CREATE POLICY "Allow all operations on criteria" ON criteria FOR ALL USING (true);
CREATE POLICY "Allow all operations on bidders" ON bidders FOR ALL USING (true);
CREATE POLICY "Allow all operations on evaluations" ON evaluations FOR ALL USING (true);
CREATE POLICY "Allow all operations on review_queue" ON review_queue FOR ALL USING (true);
CREATE POLICY "Allow all operations on audit_logs" ON audit_logs FOR ALL USING (true);
