-- ============================================================================
-- CUSTOMER SUCCESS FTE — CRM/TICKET MANAGEMENT SYSTEM
-- ============================================================================
-- Phase 2: Specialization
-- 
-- This PostgreSQL schema serves as the complete CRM system for tracking:
-- - Customers (unified across all channels)
-- - Conversations and message history
-- - Support tickets and their lifecycle
-- - Knowledge base for AI responses (with vector search)
-- - Performance metrics and reporting
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
-- For vector similarity search (requires pgvector extension)
-- CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================================================
-- 1. CUSTOMERS TABLE (Unified customer database)
-- ============================================================================
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_interactions INTEGER DEFAULT 0,
    avg_sentiment DECIMAL(3,2) DEFAULT 0.50,
    preferred_channel VARCHAR(50) DEFAULT 'email',
    metadata JSONB DEFAULT '{}'
);

-- ============================================================================
-- 2. CUSTOMER IDENTIFIERS (Cross-channel identity matching)
-- ============================================================================
CREATE TABLE customer_identifiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    identifier_type VARCHAR(50) NOT NULL,  -- 'email', 'phone', 'whatsapp'
    identifier_value VARCHAR(255) NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(identifier_type, identifier_value)
);

-- ============================================================================
-- 3. CONVERSATIONS TABLE (Conversation threads)
-- ============================================================================
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    initial_channel VARCHAR(50) NOT NULL,  -- 'email', 'whatsapp', 'web_form'
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'active',  -- 'active', 'resolved', 'escalated', 'pending'
    sentiment_score DECIMAL(3,2) DEFAULT 0.50,
    resolution_type VARCHAR(50),  -- 'ai_resolved', 'escalated_to_human', 'customer_abandoned', 'merged'
    escalated_to VARCHAR(255),
    channel_history VARCHAR(50)[] DEFAULT '{}',  -- Array of channels used in this conversation
    topics VARCHAR(100)[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

-- ============================================================================
-- 4. MESSAGES TABLE (Individual messages with full tracking)
-- ============================================================================
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL,  -- 'email', 'whatsapp', 'web_form'
    direction VARCHAR(20) NOT NULL,  -- 'inbound', 'outbound'
    role VARCHAR(20) NOT NULL,  -- 'customer', 'agent', 'system'
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sentiment_score DECIMAL(3,2) DEFAULT 0.50,
    tokens_used INTEGER,
    latency_ms INTEGER,
    tool_calls JSONB DEFAULT '[]',
    channel_message_id VARCHAR(255),  -- External ID (Gmail message ID, Twilio SID)
    delivery_status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'sent', 'delivered', 'failed'
    metadata JSONB DEFAULT '{}'
);

-- ============================================================================
-- 5. TICKETS TABLE (Support ticket lifecycle tracking)
-- ============================================================================
CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    source_channel VARCHAR(50) NOT NULL,  -- 'email', 'whatsapp', 'web_form'
    category VARCHAR(100),  -- 'general', 'technical', 'billing', 'feedback', 'bug_report'
    priority VARCHAR(20) DEFAULT 'medium',  -- 'low', 'medium', 'high', 'urgent'
    status VARCHAR(50) DEFAULT 'open',  -- 'open', 'processing', 'resolved', 'escalated', 'closed'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    escalation_reason VARCHAR(100),
    escalation_priority VARCHAR(10),  -- 'P0', 'P1', 'P2', 'P3'
    escalated_to VARCHAR(255),
    escalated_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

-- ============================================================================
-- 6. KNOWLEDGE BASE TABLE (Product documentation with vector embeddings)
-- ============================================================================
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    keywords TEXT[] DEFAULT '{}',
    -- embedding VECTOR(1536),  -- Uncomment when pgvector is installed
    -- For prototype: we use keyword-based search
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- 7. CHANNEL CONFIGS TABLE (Per-channel configuration)
-- ============================================================================
CREATE TABLE channel_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel VARCHAR(50) UNIQUE NOT NULL,  -- 'email', 'whatsapp', 'web_form'
    enabled BOOLEAN DEFAULT TRUE,
    config JSONB NOT NULL,  -- API keys, webhook URLs, etc.
    response_template TEXT,
    max_response_length INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- 8. AGENT METRICS TABLE (Performance tracking)
-- ============================================================================
CREATE TABLE agent_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    channel VARCHAR(50),  -- Optional: channel-specific metrics
    dimensions JSONB DEFAULT '{}',  -- Additional dimensions
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- 9. ESCALATIONS TABLE (Track all escalations)
-- ============================================================================
CREATE TABLE escalations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID REFERENCES tickets(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    reason VARCHAR(100) NOT NULL,
    priority VARCHAR(10) NOT NULL,  -- 'P0', 'P1', 'P2', 'P3'
    route_to VARCHAR(100) NOT NULL,  -- 'sales_team', 'billing_team', 'legal_team', etc.
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'assigned', 'resolved'
    context_summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Customer lookups
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_phone ON customers(phone);
CREATE INDEX idx_customer_identifiers_value ON customer_identifiers(identifier_value);
CREATE INDEX idx_customer_identifiers_customer ON customer_identifiers(customer_id);

-- Conversation queries
CREATE INDEX idx_conversations_customer ON conversations(customer_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_channel ON conversations(initial_channel);
CREATE INDEX idx_conversations_started ON conversations(started_at);
CREATE INDEX idx_conversations_sentiment ON conversations(sentiment_score);

-- Message retrieval
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_channel ON messages(channel);
CREATE INDEX idx_messages_created ON messages(created_at);
CREATE INDEX idx_messages_delivery ON messages(delivery_status);

-- Ticket management
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_channel ON tickets(source_channel);
CREATE INDEX idx_tickets_customer ON tickets(customer_id);
CREATE INDEX idx_tickets_created ON tickets(created_at);
CREATE INDEX idx_tickets_escalated ON tickets(status) WHERE status = 'escalated';

-- Knowledge base search
-- CREATE INDEX idx_knowledge_embedding ON knowledge_base USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_knowledge_category ON knowledge_base(category);
CREATE INDEX idx_knowledge_keywords ON knowledge_base USING GIN(keywords);

-- Metrics
CREATE INDEX idx_metrics_name ON agent_metrics(metric_name);
CREATE INDEX idx_metrics_recorded ON agent_metrics(recorded_at);
CREATE INDEX idx_metrics_channel ON agent_metrics(channel);

-- Escalations
CREATE INDEX idx_escalations_status ON escalations(status);
CREATE INDEX idx_escalations_reason ON escalations(reason);
CREATE INDEX idx_escalations_created ON escalations(created_at);

-- ============================================================================
-- SEED DATA: Channel Configurations
-- ============================================================================
INSERT INTO channel_configs (channel, enabled, config, max_response_length) VALUES
('email', TRUE, '{
    "api_type": "gmail",
    "max_length": 2000,
    "preferred_length": 500,
    "requires_greeting": true,
    "requires_signature": true,
    "emoji_allowed": false,
    "style": "formal"
}', 2000),
('whatsapp', TRUE, '{
    "api_type": "twilio",
    "max_length": 1600,
    "preferred_length": 300,
    "requires_greeting": true,
    "requires_signature": false,
    "emoji_allowed": true,
    "style": "casual"
}', 1600),
('web_form', TRUE, '{
    "api_type": "fastapi",
    "max_length": 1000,
    "preferred_length": 300,
    "requires_greeting": false,
    "requires_signature": true,
    "emoji_allowed": false,
    "style": "semi_formal"
}', 1000);

-- ============================================================================
-- SEED DATA: Sample Knowledge Base Entries
-- ============================================================================
INSERT INTO knowledge_base (title, content, category, keywords) VALUES
('Reset Password', 
 'To reset your password: 1. Go to techcorp.io/login 2. Click "Forgot Password?" 3. Enter your email address 4. Check your inbox for the reset link (valid for 1 hour) 5. Click the link and set a new password. Password requirements: minimum 8 characters, 1 uppercase, 1 number. If you don''t receive the email within 5 minutes, check your spam folder.',
 'account',
 ARRAY['password', 'reset', 'forgot', 'login', 'sign in', 'locked', 'access']),

('Invite Team Members',
 'To invite team members: 1. Go to Settings → Team Members 2. Click "Invite Members" 3. Enter email addresses (comma-separated for multiple) 4. Select role: Member (full access) or Viewer (read-only) 5. Click "Send Invites". You can also share a join link from Settings → Team Members → Share Link.',
 'collaboration',
 ARRAY['invite', 'add member', 'team', 'join', 'add people', 'add user']),

('API Rate Limits',
 'API rate limits by plan: Starter: 100 requests/hour, burst limit 20. Professional: 1,000 requests/hour, burst limit 200. Enterprise: 10,000 requests/hour, burst limit 2,000. If you receive a 429 error, you''ve exceeded your rate limit. Wait for the rate limit window to reset (1 hour) or implement exponential backoff.',
 'api',
 ARRAY['api', 'rate limit', '429', 'requests', 'throttle', 'quota']),

('Workflow Automation',
 'To create an automation rule: 1. Go to Project Settings → Automation 2. Click "+ New Rule" 3. Choose a trigger: task created, task assigned, due date approaching, task completed, status changed, or comment added 4. Choose an action: assign to team member, set due date, add label, move to column, send notification, or create subtask 5. Click "Save Rule".',
 'automation',
 ARRAY['automation', 'rule', 'trigger', 'workflow', 'auto', 'automate']),

('Pricing Plans',
 'TechCorp Plans: Starter (Free): Up to 5 users, 1GB storage. Professional ($29/user/month): Unlimited users, 50GB storage, automation, API access. Enterprise ($79/user/month): Everything in Professional plus unlimited storage, SSO/SAML, custom integrations, 99.9% SLA. For custom pricing or volume discounts, contact sales@techcorp.io.',
 'billing',
 ARRAY['pricing', 'plan', 'cost', 'price', 'upgrade', 'plans']),

('Mobile Apps',
 'TechCorp mobile apps: iOS: Search "TechCorp Platform" in the App Store. Android: Search "TechCorp Platform" in Google Play. Features: View/edit tasks, comments, push notifications, project boards, photo attachments, offline mode, biometric login.',
 'mobile',
 ARRAY['mobile', 'app', 'ios', 'android', 'phone', 'iphone']),

('Two-Factor Authentication',
 'To enable 2FA: 1. Go to Settings → Security 2. Click "Enable Two-Factor Authentication" 3. Scan the QR code with your authenticator app 4. Enter the 6-digit code to verify 5. Save your backup codes. Enterprise admins can enforce 2FA for all team members.',
 'security',
 ARRAY['2fa', 'two-factor', 'authentication', 'security', 'mfa']),

('System Status',
 'Check real-time system status at status.techcorp.io. Subscribe to updates via email, SMS, Slack webhook, or RSS feed. If experiencing issues, check status page first for known outages.',
 'status',
 ARRAY['status', 'down', 'outage', 'not working', 'error', 'unavailable']);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to update customer sentiment
CREATE OR REPLACE FUNCTION update_customer_sentiment()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE customers 
    SET avg_sentiment = (
        SELECT COALESCE(AVG(m.sentiment_score), 0.50)
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

-- Trigger to update customer sentiment when conversation changes
CREATE TRIGGER trg_update_customer_sentiment
AFTER INSERT OR UPDATE ON conversations
FOR EACH ROW
EXECUTE FUNCTION update_customer_sentiment();

-- Function to automatically set resolved_at when ticket status changes
CREATE OR REPLACE FUNCTION set_ticket_resolved_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'resolved' AND OLD.status != 'resolved' THEN
        NEW.resolved_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_ticket_resolved_at
BEFORE UPDATE ON tickets
FOR EACH ROW
EXECUTE FUNCTION set_ticket_resolved_at();

-- ============================================================================
-- VIEWS FOR REPORTING
-- ============================================================================

-- Daily ticket summary view
CREATE VIEW daily_ticket_summary AS
SELECT 
    DATE(t.created_at) as date,
    t.source_channel,
    t.status,
    COUNT(*) as ticket_count,
    COUNT(*) FILTER (WHERE t.status = 'escalated') as escalated_count,
    COUNT(*) FILTER (WHERE t.status = 'resolved') as resolved_count,
    AVG(EXTRACT(EPOCH FROM (t.resolved_at - t.created_at))/60) FILTER (WHERE t.resolved_at IS NOT NULL) as avg_resolution_minutes
FROM tickets t
GROUP BY DATE(t.created_at), t.source_channel, t.status;

-- Customer satisfaction view
CREATE VIEW customer_satisfaction AS
SELECT 
    c.id as customer_id,
    c.name,
    c.email,
    c.avg_sentiment,
    c.total_interactions,
    COUNT(DISTINCT t.id) as total_tickets,
    COUNT(DISTINCT t.id) FILTER (WHERE t.status = 'escalated') as escalated_tickets,
    COUNT(DISTINCT t.id) FILTER (WHERE t.status = 'resolved') as resolved_tickets,
    ARRAY_AGG(DISTINCT t.source_channel) as channels_used
FROM customers c
LEFT JOIN tickets t ON t.customer_id = c.id
GROUP BY c.id, c.name, c.email, c.avg_sentiment, c.total_interactions;

-- Channel performance view
CREATE VIEW channel_performance AS
SELECT 
    t.source_channel,
    COUNT(*) as total_tickets,
    COUNT(*) FILTER (WHERE t.status = 'escalated') as escalated,
    COUNT(*) FILTER (WHERE t.status = 'resolved') as resolved,
    ROUND(AVG(t.sentiment_score)::numeric, 2) as avg_sentiment,
    ROUND(AVG(EXTRACT(EPOCH FROM (t.resolved_at - t.created_at))/60)::numeric, 1) as avg_resolution_min
FROM tickets t
JOIN conversations c ON c.id = t.conversation_id
GROUP BY t.source_channel;
