-- ════════════════════════════════════════════════════════════════════
-- Ghost Workspace — Database Initialization
-- Auto-executed on first PostgreSQL container startup
-- ════════════════════════════════════════════════════════════════════

-- Nebula (Workflow Engine)
CREATE DATABASE nebula;
GRANT ALL PRIVILEGES ON DATABASE nebula TO ghost;

-- Alpha-ID (Identity Layer)
CREATE DATABASE alpha_id;
GRANT ALL PRIVILEGES ON DATABASE alpha_id TO ghost;

-- Gateway
CREATE DATABASE gateway;
GRANT ALL PRIVILEGES ON DATABASE gateway TO ghost;
