-- AgentHub-Lite PostgreSQL schema
-- Run with:
--   psql "postgresql://agenthub:agenthub@localhost:5432/agenthub" -f infra/postgres_schema.sql

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS users (
  id text PRIMARY KEY DEFAULT ('usr_' || replace(gen_random_uuid()::text, '-', '')),
  email citext NOT NULL UNIQUE,
  username citext NOT NULL UNIQUE,
  password_hash text NOT NULL,
  display_name text NOT NULL,
  avatar_url text,
  status text NOT NULL DEFAULT 'active'
    CHECK (status IN ('active', 'disabled', 'pending')),
  last_login_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workspaces (
  id text PRIMARY KEY DEFAULT ('ws_' || replace(gen_random_uuid()::text, '-', '')),
  name text NOT NULL,
  description text,
  owner_user_id text REFERENCES users(id) ON DELETE SET NULL,
  visibility text NOT NULL DEFAULT 'private'
    CHECK (visibility IN ('private', 'team')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workspace_members (
  workspace_id text NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  user_id text NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role text NOT NULL DEFAULT 'owner'
    CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
  joined_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (workspace_id, user_id)
);

CREATE TABLE IF NOT EXISTS model_providers (
  id text PRIMARY KEY DEFAULT ('provider_' || replace(gen_random_uuid()::text, '-', '')),
  workspace_id text NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  name text NOT NULL,
  provider_type text NOT NULL DEFAULT 'openai-compatible',
  base_url text NOT NULL,
  default_model text NOT NULL,
  available_models text[] NOT NULL DEFAULT ARRAY[]::text[],
  supports_streaming boolean NOT NULL DEFAULT true,
  supports_tool_calling boolean NOT NULL DEFAULT true,
  supports_vision boolean NOT NULL DEFAULT false,
  context_window integer,
  is_default boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (workspace_id, name)
);

CREATE TABLE IF NOT EXISTS model_credentials (
  id text PRIMARY KEY DEFAULT ('cred_' || replace(gen_random_uuid()::text, '-', '')),
  model_provider_id text NOT NULL UNIQUE REFERENCES model_providers(id) ON DELETE CASCADE,
  secret_ref text,
  encrypted_api_key text,
  created_by text REFERENCES users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (secret_ref IS NOT NULL OR encrypted_api_key IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS prompts (
  id text PRIMARY KEY DEFAULT ('prompt_' || replace(gen_random_uuid()::text, '-', '')),
  workspace_id text NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  name text NOT NULL,
  description text,
  prompt_type text NOT NULL DEFAULT 'system'
    CHECK (prompt_type IN ('system', 'user', 'tool', 'workflow')),
  content text NOT NULL,
  variables jsonb NOT NULL DEFAULT '[]'::jsonb,
  tags text[] NOT NULL DEFAULT ARRAY[]::text[],
  created_by text REFERENCES users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (workspace_id, name)
);

CREATE TABLE IF NOT EXISTS prompt_versions (
  id text PRIMARY KEY DEFAULT ('prompt_ver_' || replace(gen_random_uuid()::text, '-', '')),
  prompt_id text NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
  version integer NOT NULL,
  content text NOT NULL,
  change_note text,
  created_by text REFERENCES users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (prompt_id, version)
);

CREATE TABLE IF NOT EXISTS knowledge_bases (
  id text PRIMARY KEY DEFAULT ('kb_' || replace(gen_random_uuid()::text, '-', '')),
  workspace_id text NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  name text NOT NULL,
  description text,
  backend text NOT NULL DEFAULT 'ragflow',
  external_id text,
  retrieval_config jsonb NOT NULL DEFAULT '{"top_k": 5, "score_threshold": 0.3}'::jsonb,
  created_by text REFERENCES users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (workspace_id, name)
);

CREATE TABLE IF NOT EXISTS knowledge_documents (
  id text PRIMARY KEY DEFAULT ('doc_' || replace(gen_random_uuid()::text, '-', '')),
  knowledge_base_id text NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
  file_name text NOT NULL,
  file_type text,
  file_size bigint,
  storage_url text,
  external_id text,
  parse_status text NOT NULL DEFAULT 'pending'
    CHECK (parse_status IN ('pending', 'processing', 'ready', 'failed')),
  error_message text,
  created_by text REFERENCES users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS skills (
  id text PRIMARY KEY DEFAULT ('skill_' || replace(gen_random_uuid()::text, '-', '')),
  workspace_id text NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  name text NOT NULL,
  description text,
  category text,
  manifest jsonb NOT NULL DEFAULT '{}'::jsonb,
  tags text[] NOT NULL DEFAULT ARRAY[]::text[],
  created_by text REFERENCES users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (workspace_id, name)
);

CREATE TABLE IF NOT EXISTS mcp_servers (
  id text PRIMARY KEY DEFAULT ('mcp_' || replace(gen_random_uuid()::text, '-', '')),
  workspace_id text NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  name text NOT NULL,
  description text,
  transport text NOT NULL DEFAULT 'stdio'
    CHECK (transport IN ('stdio', 'http', 'sse')),
  command text,
  url text,
  config jsonb NOT NULL DEFAULT '{}'::jsonb,
  enabled boolean NOT NULL DEFAULT true,
  created_by text REFERENCES users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (workspace_id, name)
);

CREATE TABLE IF NOT EXISTS mcp_tools (
  id text PRIMARY KEY DEFAULT ('tool_' || replace(gen_random_uuid()::text, '-', '')),
  mcp_server_id text NOT NULL REFERENCES mcp_servers(id) ON DELETE CASCADE,
  name text NOT NULL,
  description text,
  input_schema jsonb NOT NULL DEFAULT '{}'::jsonb,
  enabled boolean NOT NULL DEFAULT true,
  discovered_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (mcp_server_id, name)
);

CREATE TABLE IF NOT EXISTS agents (
  id text PRIMARY KEY DEFAULT ('agent_' || replace(gen_random_uuid()::text, '-', '')),
  workspace_id text NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  name text NOT NULL,
  description text,
  avatar_url text,
  prompt_id text REFERENCES prompts(id) ON DELETE SET NULL,
  system_prompt text NOT NULL,
  model_provider_id text NOT NULL REFERENCES model_providers(id) ON DELETE RESTRICT,
  model_name text NOT NULL,
  temperature numeric(3, 2) NOT NULL DEFAULT 0.70 CHECK (temperature >= 0 AND temperature <= 2),
  top_p numeric(4, 3) CHECK (top_p IS NULL OR (top_p >= 0 AND top_p <= 1)),
  max_tokens integer CHECK (max_tokens IS NULL OR (max_tokens >= 1 AND max_tokens <= 128000)),
  memory_config jsonb NOT NULL DEFAULT '{"short_term": true, "long_term": false}'::jsonb,
  opening_message text NOT NULL DEFAULT 'Hi, I am ready to help.',
  example_questions text[] NOT NULL DEFAULT ARRAY[]::text[],
  visibility text NOT NULL DEFAULT 'private'
    CHECK (visibility IN ('private', 'workspace', 'public')),
  status text NOT NULL DEFAULT 'draft'
    CHECK (status IN ('draft', 'published', 'archived')),
  created_by text REFERENCES users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (workspace_id, name)
);

CREATE TABLE IF NOT EXISTS agent_versions (
  id text PRIMARY KEY DEFAULT ('agent_ver_' || replace(gen_random_uuid()::text, '-', '')),
  agent_id text NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  version integer NOT NULL,
  snapshot jsonb NOT NULL,
  change_note text,
  created_by text REFERENCES users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (agent_id, version)
);

CREATE TABLE IF NOT EXISTS agent_knowledge_bases (
  agent_id text NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  knowledge_base_id text NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
  retrieval_config jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (agent_id, knowledge_base_id)
);

CREATE TABLE IF NOT EXISTS agent_skills (
  agent_id text NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  skill_id text NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
  config jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (agent_id, skill_id)
);

CREATE TABLE IF NOT EXISTS agent_mcp_tools (
  agent_id text NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  mcp_tool_id text NOT NULL REFERENCES mcp_tools(id) ON DELETE CASCADE,
  config jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (agent_id, mcp_tool_id)
);

CREATE TABLE IF NOT EXISTS conversations (
  id text PRIMARY KEY DEFAULT ('conv_' || replace(gen_random_uuid()::text, '-', '')),
  workspace_id text NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  agent_id text NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  user_id text REFERENCES users(id) ON DELETE SET NULL,
  title text NOT NULL,
  channel text NOT NULL DEFAULT 'web'
    CHECK (channel IN ('web', 'api', 'wechat', 'feishu', 'dingtalk', 'telegram', 'discord', 'webhook')),
  status text NOT NULL DEFAULT 'active'
    CHECK (status IN ('active', 'archived', 'deleted')),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS messages (
  id text PRIMARY KEY DEFAULT ('msg_' || replace(gen_random_uuid()::text, '-', '')),
  conversation_id text NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  agent_id text REFERENCES agents(id) ON DELETE SET NULL,
  user_id text REFERENCES users(id) ON DELETE SET NULL,
  role text NOT NULL CHECK (role IN ('system', 'user', 'assistant', 'tool')),
  content text NOT NULL,
  content_type text NOT NULL DEFAULT 'text',
  tool_call_id text,
  token_count integer NOT NULL DEFAULT 0 CHECK (token_count >= 0),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_runs (
  id text PRIMARY KEY DEFAULT ('run_' || replace(gen_random_uuid()::text, '-', '')),
  workspace_id text NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  agent_id text NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  conversation_id text REFERENCES conversations(id) ON DELETE SET NULL,
  user_id text REFERENCES users(id) ON DELETE SET NULL,
  status text NOT NULL DEFAULT 'running'
    CHECK (status IN ('running', 'succeeded', 'failed', 'cancelled')),
  input text NOT NULL DEFAULT '',
  output text NOT NULL DEFAULT '',
  model_provider_id text REFERENCES model_providers(id) ON DELETE SET NULL,
  model_name text,
  prompt_tokens integer NOT NULL DEFAULT 0 CHECK (prompt_tokens >= 0),
  completion_tokens integer NOT NULL DEFAULT 0 CHECK (completion_tokens >= 0),
  total_tokens integer GENERATED ALWAYS AS (prompt_tokens + completion_tokens) STORED,
  latency_ms integer CHECK (latency_ms IS NULL OR latency_ms >= 0),
  cost_amount numeric(12, 6) NOT NULL DEFAULT 0,
  error_message text,
  trace jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz
);

CREATE TABLE IF NOT EXISTS tool_calls (
  id text PRIMARY KEY DEFAULT ('tool_call_' || replace(gen_random_uuid()::text, '-', '')),
  agent_run_id text NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
  mcp_tool_id text REFERENCES mcp_tools(id) ON DELETE SET NULL,
  tool_name text NOT NULL,
  input jsonb NOT NULL DEFAULT '{}'::jsonb,
  output jsonb,
  status text NOT NULL DEFAULT 'running'
    CHECK (status IN ('running', 'succeeded', 'failed')),
  latency_ms integer CHECK (latency_ms IS NULL OR latency_ms >= 0),
  error_message text,
  created_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz
);

CREATE TABLE IF NOT EXISTS scheduled_tasks (
  id text PRIMARY KEY DEFAULT ('task_' || replace(gen_random_uuid()::text, '-', '')),
  workspace_id text NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  agent_id text REFERENCES agents(id) ON DELETE CASCADE,
  name text NOT NULL,
  cron_expression text,
  interval_seconds integer CHECK (interval_seconds IS NULL OR interval_seconds > 0),
  input_template text NOT NULL DEFAULT '',
  enabled boolean NOT NULL DEFAULT true,
  retry_limit integer NOT NULL DEFAULT 0 CHECK (retry_limit >= 0),
  timeout_seconds integer NOT NULL DEFAULT 300 CHECK (timeout_seconds > 0),
  created_by text REFERENCES users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (cron_expression IS NOT NULL OR interval_seconds IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS notifications (
  id text PRIMARY KEY DEFAULT ('notice_' || replace(gen_random_uuid()::text, '-', '')),
  workspace_id text NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  name text NOT NULL,
  channel text NOT NULL CHECK (channel IN ('email', 'webhook', 'wechat', 'feishu', 'dingtalk', 'telegram')),
  config jsonb NOT NULL DEFAULT '{}'::jsonb,
  enabled boolean NOT NULL DEFAULT true,
  created_by text REFERENCES users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (workspace_id, name)
);

CREATE TABLE IF NOT EXISTS api_keys (
  id text PRIMARY KEY DEFAULT ('ak_' || replace(gen_random_uuid()::text, '-', '')),
  workspace_id text NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  user_id text REFERENCES users(id) ON DELETE SET NULL,
  name text NOT NULL,
  key_hash text NOT NULL UNIQUE,
  key_prefix text NOT NULL,
  scopes text[] NOT NULL DEFAULT ARRAY[]::text[],
  expires_at timestamptz,
  last_used_at timestamptz,
  revoked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id text PRIMARY KEY DEFAULT ('audit_' || replace(gen_random_uuid()::text, '-', '')),
  workspace_id text REFERENCES workspaces(id) ON DELETE SET NULL,
  user_id text REFERENCES users(id) ON DELETE SET NULL,
  action text NOT NULL,
  resource_type text NOT NULL,
  resource_id text,
  ip_address inet,
  user_agent text,
  detail jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_workspace_members_user_id ON workspace_members(user_id);
CREATE INDEX IF NOT EXISTS idx_model_providers_workspace_id ON model_providers(workspace_id);
CREATE INDEX IF NOT EXISTS idx_prompts_workspace_id ON prompts(workspace_id);
CREATE INDEX IF NOT EXISTS idx_agents_workspace_id ON agents(workspace_id);
CREATE INDEX IF NOT EXISTS idx_agents_model_provider_id ON agents(model_provider_id);
CREATE INDEX IF NOT EXISTS idx_conversations_agent_updated ON conversations(agent_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_user_updated ON conversations(user_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_created ON messages(conversation_id, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_agent_runs_agent_created ON agent_runs(agent_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_runs_conversation_id ON agent_runs(conversation_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_agent_run_id ON tool_calls(agent_run_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_workspace_created ON audit_logs(workspace_id, created_at DESC);

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_workspaces_updated_at ON workspaces;
CREATE TRIGGER trg_workspaces_updated_at
  BEFORE UPDATE ON workspaces
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_model_providers_updated_at ON model_providers;
CREATE TRIGGER trg_model_providers_updated_at
  BEFORE UPDATE ON model_providers
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_model_credentials_updated_at ON model_credentials;
CREATE TRIGGER trg_model_credentials_updated_at
  BEFORE UPDATE ON model_credentials
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_prompts_updated_at ON prompts;
CREATE TRIGGER trg_prompts_updated_at
  BEFORE UPDATE ON prompts
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_knowledge_bases_updated_at ON knowledge_bases;
CREATE TRIGGER trg_knowledge_bases_updated_at
  BEFORE UPDATE ON knowledge_bases
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_knowledge_documents_updated_at ON knowledge_documents;
CREATE TRIGGER trg_knowledge_documents_updated_at
  BEFORE UPDATE ON knowledge_documents
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_skills_updated_at ON skills;
CREATE TRIGGER trg_skills_updated_at
  BEFORE UPDATE ON skills
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_mcp_servers_updated_at ON mcp_servers;
CREATE TRIGGER trg_mcp_servers_updated_at
  BEFORE UPDATE ON mcp_servers
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_agents_updated_at ON agents;
CREATE TRIGGER trg_agents_updated_at
  BEFORE UPDATE ON agents
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_conversations_updated_at ON conversations;
CREATE TRIGGER trg_conversations_updated_at
  BEFORE UPDATE ON conversations
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_scheduled_tasks_updated_at ON scheduled_tasks;
CREATE TRIGGER trg_scheduled_tasks_updated_at
  BEFORE UPDATE ON scheduled_tasks
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_notifications_updated_at ON notifications;
CREATE TRIGGER trg_notifications_updated_at
  BEFORE UPDATE ON notifications
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

INSERT INTO users (id, email, username, password_hash, display_name)
VALUES (
  'user-admin',
  'admin@example.local',
  'admin',
  'pbkdf2_sha256$260000$agenthub-dev-salt$+Rukjpe84S0eH2VMUKZp9ADWdNtGCyXSKg2cVp1ULfY=',
  'Admin'
)
ON CONFLICT (id) DO UPDATE
SET
  email = EXCLUDED.email,
  username = EXCLUDED.username,
  password_hash = EXCLUDED.password_hash,
  display_name = EXCLUDED.display_name;

INSERT INTO workspaces (id, name, description, owner_user_id, visibility)
VALUES ('default', 'Default Workspace', 'AgentHub-Lite default workspace.', 'user-admin', 'private')
ON CONFLICT (id) DO NOTHING;

INSERT INTO workspace_members (workspace_id, user_id, role)
VALUES ('default', 'user-admin', 'owner')
ON CONFLICT (workspace_id, user_id) DO NOTHING;

INSERT INTO model_providers (
  id,
  workspace_id,
  name,
  provider_type,
  base_url,
  default_model,
  available_models,
  supports_streaming,
  supports_tool_calling,
  is_default
)
VALUES (
  'openai-compatible',
  'default',
  'OpenAI Compatible',
  'openai-compatible',
  'https://api.openai.com/v1',
  'gpt-4.1-mini',
  ARRAY['gpt-4.1-mini'],
  true,
  true,
  true
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO prompts (id, workspace_id, name, description, prompt_type, content, created_by)
VALUES (
  'prompt-default-agent-system',
  'default',
  'Default Agent System Prompt',
  'Default system prompt for the MVP assistant.',
  'system',
  'You are a helpful AI agent for AgentHub-Lite.',
  'user-admin'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO agents (
  id,
  workspace_id,
  name,
  description,
  prompt_id,
  system_prompt,
  model_provider_id,
  model_name,
  temperature,
  max_tokens,
  opening_message,
  example_questions,
  visibility,
  status,
  created_by
)
VALUES (
  'default-agent',
  'default',
  'Default Assistant',
  'MVP sample Agent.',
  'prompt-default-agent-system',
  'You are a helpful AI agent for AgentHub-Lite.',
  'openai-compatible',
  'gpt-4.1-mini',
  0.70,
  1024,
  'Hi, I am the default assistant. Ask me anything.',
  ARRAY['Summarize today''s project plan.', 'Draft a simple task checklist.'],
  'workspace',
  'published',
  'user-admin'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO conversations (id, workspace_id, agent_id, user_id, title, channel)
VALUES ('default-conversation', 'default', 'default-agent', 'user-admin', 'Default conversation', 'web')
ON CONFLICT (id) DO NOTHING;

INSERT INTO messages (id, conversation_id, agent_id, role, content)
VALUES (
  'welcome-message',
  'default-conversation',
  'default-agent',
  'assistant',
  'Hi, I am the default assistant. Ask me anything.'
)
ON CONFLICT (id) DO NOTHING;

COMMIT;
