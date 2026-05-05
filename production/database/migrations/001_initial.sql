-- ============================================================================
-- Migration 001: Initial Schema
-- ============================================================================
-- Description : Creates the complete CRM/ticket management schema for the
--               Customer Success FTE system, including all 9 tables,
--               indexes, seed data, helper functions, triggers, and views.
-- Applied to  : Fresh PostgreSQL 16 database (fte_db)
-- Depends on  : None (first migration)
-- Reversible  : Yes — see rollback section at the bottom
-- ============================================================================

BEGIN;

-- ─── Extensions ─────────────────────────────────────────────────────────────

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
-- Uncomment when pgvector is installed:
-- CREATE EXTENSION IF NOT EXISTS "vector";

-- ─── 1. Customers ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS customers (
    id                 UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    email              VARCHAR(255) UNIQUE,
    phone              VARCHAR(50),
    name               VARCHAR(255),
    created_at         TIMESTAMPTZ  DEFAULT NOW(),
    updated_at         TIMESTAMPTZ  DEFAULT NOW(),
    total_interactions INTEGER      DEFAULT 0,
    avg_sentiment      DECIMAL(3,2) DEFAULT 0.50,
    preferred_channel  VARCHAR(50)  DEFAULT 'email',
    metadata           JSONB        DEFAULT '{}'
);

-- ─── 2. Customer Identifiers (cross-channel matching) ───────────────────────

CREATE TABLE IF NOT EXISTS customer_identifiers (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id      UUID        REFERENCES customers(id) ON DELETE CASCADE,
    identifier_type  VARCHAR(50) NOT NULL,   -- 'email', 'phone', 'whatsapp'
    identifier_value VARCHAR(255) NOT NULL,
    verified         BOOLEAN     DEFAULT FALSE,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(identifier_type, identifier_value)
);

-- ─── 3. Conversations ────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS conversations (
    id               UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id      UUID          REFERENCES customers(id) ON DELETE CASCADE,
    initial_channel  VARCHAR(50)   NOT NULL,   -- 'email', 'whatsapp', 'web_form'
    started_at       TIMESTAMPTZ   DEFAULT NOW(),
    ended_at         TIMESTAMPTZ,
    status           VARCHAR(50)   DEFAULT 'active',
    sentiment_score  DECIMAL(3,2)  DEFAULT 0.50,
    resolution_type  VARCHAR(50),
    escalated_to     VARCHAR(255),
    channel_history  VARCHAR(50)[] DEFAULT '{}',
    topics           VARCHAR(100)[] DEFAULT '{}',
    metadata         JSONB         DEFAULT '{}'
);

-- ─── 4. Messages ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS messages (
    id                 UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id    UUID        REFERENCES conversations(id) ON DELETE CASCADE,
    channel            VARCHAR(50) NOT NULL,
    direction          VARCHAR(20) NOT NULL,   -- 'inbound', 'outbound'
    role               VARCHAR(20) NOT NULL,   -- 'customer', 'agent', 'system'
    content            TEXT        NOT NULL,
    created_at         TIMESTAMPTZ DEFAULT NOW(),
    sentiment_score    DECIMAL(3,2) DEFAULT 0.50,
    tokens_used        INTEGER,
    latency_ms         INTEGER,
    tool_calls         JSONB       DEFAULT '[]',
    channel_message_id VARCHAR(255),
    delivery_status    VARCHAR(50) DEFAULT 'pending',
    metadata           JSONB       DEFAULT '{}'
);

-- ─── 5. Tickets ──────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS tickets (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id     UUID        REFERENCES conversations(id) ON DELETE CASCADE,
    customer_id         UUID        REFERENCES customers(id) ON DELETE CASCADE,
    source_channel      VARCHAR(50) NOT NULL,
    category            VARCHAR(100),
    priority            VARCHAR(20) DEFAULT 'medium',
    status              VARCHAR(50) DEFAULT 'open',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    resolved_at         TIMESTAMPTZ,
    resolution_notes    TEXT,
    escalation_reason   VARCHAR(100),
    escalation_priority VARCHAR(10),
    escalated_to        VARCHAR(255),
    escalated_at        TIMESTAMPTZ,
    metadata            JSONB       DEFAULT '{}'
);

-- ─── 6. Knowledge Base ───────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS knowledge_base (
    id         UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    title      VARCHAR(500)  NOT NULL,
    content    TEXT          NOT NULL,
    category   VARCHAR(100),
    keywords   TEXT[]        DEFAULT '{}',
    -- embedding VECTOR(1536),  -- Enable after pgvector install
    created_at TIMESTAMPTZ   DEFAULT NOW(),
    updated_at TIMESTAMPTZ   DEFAULT NOW()
);

-- ─── 7. Channel Configs ──────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS channel_configs (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    channel             VARCHAR(50) UNIQUE NOT NULL,
    enabled             BOOLEAN     DEFAULT TRUE,
    config              JSONB       NOT NULL,
    response_template   TEXT,
    max_response_length INTEGER,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ─── 8. Agent Metrics ────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agent_metrics (
    id           UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name  VARCHAR(100)   NOT NULL,
    metric_value DECIMAL(10,4)  NOT NULL,
    channel      VARCHAR(50),
    dimensions   JSONB          DEFAULT '{}',
    recorded_at  TIMESTAMPTZ    DEFAULT NOW()
);

-- ─── 9. Escalations ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS escalations (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id        UUID        REFERENCES tickets(id) ON DELETE CASCADE,
    conversation_id  UUID        REFERENCES conversations(id) ON DELETE CASCADE,
    reason           VARCHAR(100) NOT NULL,
    priority         VARCHAR(10)  NOT NULL,   -- 'P0', 'P1', 'P2', 'P3'
    route_to         VARCHAR(100) NOT NULL,
    status           VARCHAR(50)  DEFAULT 'pending',
    context_summary  TEXT,
    created_at       TIMESTAMPTZ  DEFAULT NOW(),
    resolved_at      TIMESTAMPTZ,
    metadata         JSONB        DEFAULT '{}'
);

-- ─── Indexes ─────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_customers_email             ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_phone             ON customers(phone);
CREATE INDEX IF NOT EXISTS idx_customer_identifiers_value  ON customer_identifiers(identifier_value);
CREATE INDEX IF NOT EXISTS idx_customer_identifiers_cust   ON customer_identifiers(customer_id);
CREATE INDEX IF NOT EXISTS idx_conversations_customer      ON conversations(customer_id);
CREATE INDEX IF NOT EXISTS idx_conversations_status        ON conversations(status);
CREATE INDEX IF NOT EXISTS idx_conversations_channel       ON conversations(initial_channel);
CREATE INDEX IF NOT EXISTS idx_conversations_started       ON conversations(started_at);
CREATE INDEX IF NOT EXISTS idx_conversations_sentiment     ON conversations(sentiment_score);
CREATE INDEX IF NOT EXISTS idx_messages_conversation       ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_channel            ON messages(channel);
CREATE INDEX IF NOT EXISTS idx_messages_created            ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_delivery           ON messages(delivery_status);
CREATE INDEX IF NOT EXISTS idx_tickets_status              ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_channel             ON tickets(source_channel);
CREATE INDEX IF NOT EXISTS idx_tickets_customer            ON tickets(customer_id);
CREATE INDEX IF NOT EXISTS idx_tickets_created             ON tickets(created_at);
CREATE INDEX IF NOT EXISTS idx_tickets_escalated           ON tickets(status) WHERE status = 'escalated';
CREATE INDEX IF NOT EXISTS idx_knowledge_category          ON knowledge_base(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_keywords          ON knowledge_base USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_metrics_name                ON agent_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_metrics_recorded            ON agent_metrics(recorded_at);
CREATE INDEX IF NOT EXISTS idx_metrics_channel             ON agent_metrics(channel);
CREATE INDEX IF NOT EXISTS idx_escalations_status          ON escalations(status);
CREATE INDEX IF NOT EXISTS idx_escalations_reason          ON escalations(reason);
CREATE INDEX IF NOT EXISTS idx_escalations_created         ON escalations(created_at);

-- ─── Helper Functions & Triggers ─────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_customer_sentiment()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE customers
    SET avg_sentiment = (
        SELECT COALESCE(AVG(sentiment_score), 0.50)
        FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        WHERE c.customer_id = NEW.customer_id
    ),
    total_interactions = (
        SELECT COUNT(DISTINCT c.id)
        FROM conversations c
        WHERE c.customer_id = NEW.customer_id
    ),
    updated_at = NOW()
    WHERE id = NEW.customer_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_customer_sentiment ON conversations;
CREATE TRIGGER trg_update_customer_sentiment
AFTER INSERT OR UPDATE ON conversations
FOR EACH ROW EXECUTE FUNCTION update_customer_sentiment();

CREATE OR REPLACE FUNCTION set_ticket_resolved_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'resolved' AND OLD.status != 'resolved' THEN
        NEW.resolved_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_ticket_resolved_at ON tickets;
CREATE TRIGGER trg_ticket_resolved_at
BEFORE UPDATE ON tickets
FOR EACH ROW EXECUTE FUNCTION set_ticket_resolved_at();

-- ─── Views ───────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW daily_ticket_summary AS
SELECT
    DATE(created_at)                                          AS date,
    source_channel,
    status,
    COUNT(*)                                                   AS ticket_count,
    COUNT(*) FILTER (WHERE status = 'escalated')               AS escalated_count,
    COUNT(*) FILTER (WHERE status = 'resolved')                AS resolved_count,
    AVG(EXTRACT(EPOCH FROM (resolved_at - created_at)) / 60)
        FILTER (WHERE resolved_at IS NOT NULL)                 AS avg_resolution_minutes
FROM tickets
GROUP BY DATE(created_at), source_channel, status;

CREATE OR REPLACE VIEW customer_satisfaction AS
SELECT
    c.id                  AS customer_id,
    c.name,
    c.email,
    c.avg_sentiment,
    c.total_interactions,
    COUNT(DISTINCT t.id)                                        AS total_tickets,
    COUNT(DISTINCT t.id) FILTER (WHERE t.status = 'escalated') AS escalated_tickets,
    COUNT(DISTINCT t.id) FILTER (WHERE t.status = 'resolved')  AS resolved_tickets,
    ARRAY_AGG(DISTINCT t.source_channel)                        AS channels_used
FROM customers c
LEFT JOIN tickets t ON t.customer_id = c.id
GROUP BY c.id, c.name, c.email, c.avg_sentiment, c.total_interactions;

CREATE OR REPLACE VIEW channel_performance AS
SELECT
    t.source_channel,
    COUNT(*)                                                       AS total_tickets,
    COUNT(*) FILTER (WHERE t.status = 'escalated')                 AS escalated,
    COUNT(*) FILTER (WHERE t.status = 'resolved')                  AS resolved,
    ROUND(AVG(c.sentiment_score)::numeric, 2)                      AS avg_sentiment,
    ROUND(AVG(EXTRACT(EPOCH FROM (t.resolved_at - t.created_at))
              / 60)::numeric, 1)                                   AS avg_resolution_min
FROM tickets t
JOIN conversations c ON c.id = t.conversation_id
GROUP BY t.source_channel;

-- ─── Seed Data: Channel Configurations ───────────────────────────────────────

INSERT INTO channel_configs (channel, enabled, config, max_response_length)
VALUES
(
    'email', TRUE,
    '{
        "api_type": "gmail",
        "max_length": 2000,
        "preferred_length": 500,
        "requires_greeting": true,
        "requires_signature": true,
        "emoji_allowed": false,
        "style": "formal"
    }',
    2000
),
(
    'whatsapp', TRUE,
    '{
        "api_type": "twilio",
        "max_length": 1600,
        "preferred_length": 300,
        "requires_greeting": true,
        "requires_signature": false,
        "emoji_allowed": true,
        "style": "casual"
    }',
    1600
),
(
    'web_form', TRUE,
    '{
        "api_type": "fastapi",
        "max_length": 1000,
        "preferred_length": 300,
        "requires_greeting": false,
        "requires_signature": true,
        "emoji_allowed": false,
        "style": "semi_formal"
    }',
    1000
)
ON CONFLICT (channel) DO NOTHING;

-- ─── Seed Data: Knowledge Base ───────────────────────────────────────────────

INSERT INTO knowledge_base (title, content, category, keywords) VALUES
('Reset Password',
 'To reset your password: 1. Go to techcorp.io/login 2. Click "Forgot Password?" 3. Enter your email 4. Check your inbox for the reset link (valid 1 hour) 5. Set a new password. Requirements: 8+ chars, 1 uppercase, 1 number. Check spam if no email within 5 minutes.',
 'account', ARRAY['password','reset','forgot','login','locked','access']),

('Invite Team Members',
 'Invite team members: 1. Settings → Team Members 2. Click "Invite Members" 3. Enter emails (comma-separated) 4. Select role: Member or Viewer 5. Send Invites. Alternatively share a join link from Settings → Team Members → Share Link.',
 'collaboration', ARRAY['invite','add member','team','join','add user']),

('API Rate Limits',
 'Rate limits by plan: Starter 100 req/hour; Professional 1,000 req/hour; Enterprise 10,000 req/hour. 429 error = rate limit hit. Wait for 1-hour window reset or use exponential backoff.',
 'api', ARRAY['api','rate limit','429','requests','throttle','quota']),

('Workflow Automation',
 'Create automation: Settings → Automation → "+ New Rule". Triggers: task created/assigned/completed, due date approaching, status changed, comment added. Actions: assign, set due date, add label, move column, send notification, create subtask.',
 'automation', ARRAY['automation','rule','trigger','workflow','automate']),

('Pricing Plans',
 'Plans: Starter (Free) 5 users 1GB. Professional $29/user/mo unlimited users 50GB. Enterprise $79/user/mo SSO custom integrations 99.9% SLA. Volume discounts: contact sales@techcorp.io.',
 'billing', ARRAY['pricing','plan','cost','price','upgrade']),

('Mobile Apps',
 'iOS: App Store → "TechCorp Platform". Android: Google Play → "TechCorp Platform". Features: tasks, comments, push notifications, offline mode, biometric login.',
 'mobile', ARRAY['mobile','app','ios','android','phone']),

('Two-Factor Authentication',
 'Enable 2FA: Settings → Security → Enable 2FA → Scan QR code → Enter 6-digit code → Save backup codes. Admins can enforce 2FA for all team members.',
 'security', ARRAY['2fa','two-factor','authentication','mfa','security']),

('System Status',
 'Real-time status at status.techcorp.io. Subscribe by email, SMS, Slack webhook, or RSS. Always check status page first for known outages.',
 'status', ARRAY['status','down','outage','not working','error','unavailable'])
ON CONFLICT DO NOTHING;

COMMIT;

-- ============================================================================
-- ROLLBACK (run manually if needed — irreversible data loss!)
-- ============================================================================
-- BEGIN;
-- DROP VIEW IF EXISTS channel_performance;
-- DROP VIEW IF EXISTS customer_satisfaction;
-- DROP VIEW IF EXISTS daily_ticket_summary;
-- DROP TRIGGER IF EXISTS trg_ticket_resolved_at ON tickets;
-- DROP TRIGGER IF EXISTS trg_update_customer_sentiment ON conversations;
-- DROP FUNCTION IF EXISTS set_ticket_resolved_at();
-- DROP FUNCTION IF EXISTS update_customer_sentiment();
-- DROP TABLE IF EXISTS escalations CASCADE;
-- DROP TABLE IF EXISTS agent_metrics CASCADE;
-- DROP TABLE IF EXISTS channel_configs CASCADE;
-- DROP TABLE IF EXISTS knowledge_base CASCADE;
-- DROP TABLE IF EXISTS tickets CASCADE;
-- DROP TABLE IF EXISTS messages CASCADE;
-- DROP TABLE IF EXISTS conversations CASCADE;
-- DROP TABLE IF EXISTS customer_identifiers CASCADE;
-- DROP TABLE IF EXISTS customers CASCADE;
-- COMMIT;
