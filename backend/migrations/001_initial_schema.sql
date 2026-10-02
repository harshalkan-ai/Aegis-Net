-- AEGIS-NET Initial Database Schema Migration
-- Migration 001: Initial Schema

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Agents Table
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    role TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Agent Sessions Table
CREATE TABLE IF NOT EXISTS agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Agent Permissions Table
CREATE TABLE IF NOT EXISTS agent_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    is_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    requires_review BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_role_tool UNIQUE (role, tool_name)
);

-- 4. Tool Calls Table
CREATE TABLE IF NOT EXISTS tool_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES agent_sessions(id) ON DELETE SET NULL,
    agent_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. Risk Assessments Table
CREATE TABLE IF NOT EXISTS risk_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_call_id UUID REFERENCES tool_calls(id) ON DELETE CASCADE,
    threat_score DOUBLE PRECISION NOT NULL,
    total_risk DOUBLE PRECISION NOT NULL,
    decision TEXT NOT NULL,
    factors JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. Security Events Table
CREATE TABLE IF NOT EXISTS security_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7. Incidents Table
CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id TEXT NOT NULL,
    session_id UUID,
    tool_call_id UUID REFERENCES tool_calls(id) ON DELETE SET NULL,
    risk_score DOUBLE PRECISION NOT NULL,
    decision TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- 8. Quarantine Records Table
CREATE TABLE IF NOT EXISTS quarantine_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id TEXT NOT NULL,
    session_id UUID,
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 9. Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_name TEXT NOT NULL,
    actor TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 10. Forensics Reports Table
CREATE TABLE IF NOT EXISTS forensics_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID REFERENCES incidents(id) ON DELETE CASCADE,
    cwe_id TEXT,
    attack_vector TEXT,
    mitigation_rule TEXT,
    summary TEXT,
    raw_report JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for Query Performance
CREATE INDEX IF NOT EXISTS idx_agent_sessions_agent ON agent_sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_session ON tool_calls(session_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_agent ON tool_calls(agent_id);
CREATE INDEX IF NOT EXISTS idx_risk_assessments_tool_call ON risk_assessments(tool_call_id);
CREATE INDEX IF NOT EXISTS idx_security_events_session ON security_events(session_id);
CREATE INDEX IF NOT EXISTS idx_incidents_agent ON incidents(agent_id);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_quarantine_records_agent ON quarantine_records(agent_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event ON audit_logs(event_name);
CREATE INDEX IF NOT EXISTS idx_forensics_reports_incident ON forensics_reports(incident_id);

-- Enable Row Level Security (RLS) on all tables
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE tool_calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE security_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE incidents ENABLE ROW LEVEL SECURITY;
ALTER TABLE quarantine_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE forensics_reports ENABLE ROW LEVEL SECURITY;

-- Baseline Service-Role Policies (Full Access for Backend Service Role)
DO $$
BEGIN
    DROP POLICY IF EXISTS "service_role_all_agents" ON agents;
    CREATE POLICY "service_role_all_agents" ON agents FOR ALL TO service_role USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "service_role_all_agent_sessions" ON agent_sessions;
    CREATE POLICY "service_role_all_agent_sessions" ON agent_sessions FOR ALL TO service_role USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "service_role_all_agent_permissions" ON agent_permissions;
    CREATE POLICY "service_role_all_agent_permissions" ON agent_permissions FOR ALL TO service_role USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "service_role_all_tool_calls" ON tool_calls;
    CREATE POLICY "service_role_all_tool_calls" ON tool_calls FOR ALL TO service_role USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "service_role_all_risk_assessments" ON risk_assessments;
    CREATE POLICY "service_role_all_risk_assessments" ON risk_assessments FOR ALL TO service_role USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "service_role_all_security_events" ON security_events;
    CREATE POLICY "service_role_all_security_events" ON security_events FOR ALL TO service_role USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "service_role_all_incidents" ON incidents;
    CREATE POLICY "service_role_all_incidents" ON incidents FOR ALL TO service_role USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "service_role_all_quarantine_records" ON quarantine_records;
    CREATE POLICY "service_role_all_quarantine_records" ON quarantine_records FOR ALL TO service_role USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "service_role_all_audit_logs" ON audit_logs;
    CREATE POLICY "service_role_all_audit_logs" ON audit_logs FOR ALL TO service_role USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "service_role_all_forensics_reports" ON forensics_reports;
    CREATE POLICY "service_role_all_forensics_reports" ON forensics_reports FOR ALL TO service_role USING (true) WITH CHECK (true);
END $$;
