import {
  Bot,
  Check,
  KeyRound,
  MessageSquare,
  Plus,
  RotateCcw,
  Save,
  Send,
  Settings,
  TestTube2,
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

type ViewKey = "agents" | "chat" | "providers";

type Agent = {
  id: string;
  name: string;
  description?: string | null;
  system_prompt: string;
  model_provider_id: string;
  model_name: string;
  temperature: number;
  max_tokens?: number | null;
  knowledge_base_ids: string[];
  skill_ids: string[];
  mcp_tool_ids: string[];
  opening_message: string;
  example_questions: string[];
};

type ModelProvider = {
  id: string;
  name: string;
  provider_type: string;
  base_url: string;
  default_model: string;
  available_models: string[];
  has_api_key: boolean;
  supports_streaming: boolean;
  supports_tool_calling: boolean;
};

type ChatMessage = {
  id?: string | null;
  role: "user" | "assistant" | "system";
  content: string;
  created_at?: string | null;
};

type Conversation = {
  id: string;
  agent_id: string;
  title: string;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
};

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

const emptyAgentDraft = {
  name: "",
  description: "",
  system_prompt: "你是一个专业、清晰、可靠的 AI 助手。",
  model_provider_id: "openai-compatible",
  model_name: "gpt-4.1-mini",
  temperature: 0.7,
  max_tokens: 1024,
  knowledge_base_ids: "",
  skill_ids: "",
  mcp_tool_ids: "",
  opening_message: "你好，我已经准备好了，可以开始帮你处理任务。",
  example_questions: "总结今天的项目计划\n帮我拆解一个任务清单",
};

const emptyProviderDraft = {
  name: "",
  provider_type: "openai-compatible",
  base_url: "",
  api_key: "",
  default_model: "",
  available_models: "",
  supports_streaming: true,
  supports_tool_calling: true,
};

export function App() {
  const [activeView, setActiveView] = useState<ViewKey>("agents");
  const [agents, setAgents] = useState<Agent[]>([]);
  const [providers, setProviders] = useState<ModelProvider[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState("default-agent");
  const [selectedProviderId, setSelectedProviderId] = useState("openai-compatible");
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [agentDraft, setAgentDraft] = useState(emptyAgentDraft);
  const [providerDraft, setProviderDraft] = useState(emptyProviderDraft);
  const [messageDraft, setMessageDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [status, setStatus] = useState("正在加载工作台...");
  const [error, setError] = useState<string | null>(null);

  const selectedAgent = useMemo(
    () => agents.find((agent) => agent.id === selectedAgentId) ?? agents[0],
    [agents, selectedAgentId],
  );

  const selectedProvider = useMemo(
    () => providers.find((provider) => provider.id === selectedProviderId) ?? providers[0],
    [providers, selectedProviderId],
  );

  const agentProvider = useMemo(
    () => providers.find((provider) => provider.id === agentDraft.model_provider_id),
    [providers, agentDraft.model_provider_id],
  );

  const selectedConversation = useMemo(
    () => conversations.find((conversation) => conversation.id === selectedConversationId),
    [conversations, selectedConversationId],
  );

  useEffect(() => {
    void bootstrap();
  }, []);

  useEffect(() => {
    if (selectedAgent) {
      setAgentDraft(toAgentDraft(selectedAgent));
      void loadConversations(selectedAgent.id);
    }
  }, [selectedAgent?.id]);

  useEffect(() => {
    if (selectedProvider) {
      setProviderDraft(toProviderDraft(selectedProvider));
    }
  }, [selectedProvider?.id]);

  async function bootstrap() {
    await Promise.all([loadProviders(), loadAgents()]);
    setStatus("工作台已就绪");
  }

  async function loadAgents() {
    const data = await request<Agent[]>("/agents");
    setAgents(data);
    setSelectedAgentId((current) => data.find((agent) => agent.id === current)?.id ?? data[0]?.id);
  }

  async function loadProviders() {
    const data = await request<ModelProvider[]>("/model-providers");
    setProviders(data);
    setSelectedProviderId((current) => data.find((provider) => provider.id === current)?.id ?? data[0]?.id);
  }

  async function loadConversations(agentId: string) {
    const data = await request<Conversation[]>(`/chat/conversations?agent_id=${agentId}`);
    setConversations(data);
    setSelectedConversationId((current) => data.find((item) => item.id === current)?.id ?? data[0]?.id ?? null);
  }

  async function createAgent(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction(async () => {
      const agent = await request<Agent>("/agents", {
        method: "POST",
        body: JSON.stringify(fromAgentDraft(agentDraft)),
      });
      setAgents((current) => [...current, agent]);
      setSelectedAgentId(agent.id);
      setStatus(`已创建 Agent：${agent.name}`);
    });
  }

  async function saveAgent() {
    if (!selectedAgent) return;
    await runAction(async () => {
      const updated = await request<Agent>(`/agents/${selectedAgent.id}`, {
        method: "PATCH",
        body: JSON.stringify(fromAgentDraft(agentDraft)),
      });
      setAgents((current) => current.map((agent) => (agent.id === updated.id ? updated : agent)));
      setStatus(`已保存 Agent：${updated.name}`);
    });
  }

  async function saveProvider() {
    if (!selectedProvider) return;
    await runAction(async () => {
      const updated = await request<ModelProvider>(`/model-providers/${selectedProvider.id}`, {
        method: "PATCH",
        body: JSON.stringify(fromProviderDraft(providerDraft)),
      });
      setProviders((current) =>
        current.map((provider) => (provider.id === updated.id ? updated : provider)),
      );
      setProviderDraft(toProviderDraft(updated));
      setStatus(`已保存模型配置：${updated.name}`);
    });
  }

  async function testProvider() {
    if (!selectedProvider) return;
    await runAction(async () => {
      const result = await request<{ ok: boolean; message: string }>(
        `/model-providers/${selectedProvider.id}/test`,
        {
          method: "POST",
          body: JSON.stringify({
            model: providerDraft.default_model,
            message: "你好，请用一句话回复模型连接正常。",
          }),
        },
      );
      setStatus(result.ok ? `模型测试成功：${result.message}` : result.message);
    });
  }

  async function startConversation() {
    if (!selectedAgent) return;
    await runAction(async () => {
      const conversation = await request<Conversation>("/chat/conversations", {
        method: "POST",
        body: JSON.stringify({ agent_id: selectedAgent.id }),
      });
      setConversations((current) => [conversation, ...current]);
      setSelectedConversationId(conversation.id);
      setStatus("已新建会话");
    });
  }

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedAgent || !messageDraft.trim()) return;

    const input = messageDraft.trim();
    setMessageDraft("");
    setIsSending(true);
    const optimisticConversation = ensureConversation(input);

    await runAction(async () => {
      const response = await request<{ conversation_id: string; messages: ChatMessage[] }>("/chat", {
        method: "POST",
        body: JSON.stringify({
          agent_id: selectedAgent.id,
          conversation_id: optimisticConversation.id.startsWith("pending-")
            ? undefined
            : optimisticConversation.id,
          input,
        }),
      });
      await loadConversations(selectedAgent.id);
      setSelectedConversationId(response.conversation_id);
      setStatus("消息已发送");
    });
    setIsSending(false);
  }

  async function runAction(action: () => Promise<void>) {
    setError(null);
    try {
      await action();
    } catch (err) {
      setError(formatError(err));
    }
  }

  function ensureConversation(input: string): Conversation {
    const now = new Date().toISOString();
    if (selectedConversation) {
      const updated = {
        ...selectedConversation,
        messages: [
          ...selectedConversation.messages,
          { id: `pending-${Date.now()}`, role: "user" as const, content: input, created_at: now },
        ],
        updated_at: now,
      };
      setConversations((current) =>
        current.map((conversation) => (conversation.id === updated.id ? updated : conversation)),
      );
      return updated;
    }

    const pending = {
      id: `pending-${Date.now()}`,
      agent_id: selectedAgentId,
      title: "新会话",
      messages: [{ id: `pending-msg-${Date.now()}`, role: "user" as const, content: input, created_at: now }],
      created_at: now,
      updated_at: now,
    };
    setConversations((current) => [pending, ...current]);
    setSelectedConversationId(pending.id);
    return pending;
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">A</div>
          <div>
            <strong>AgentHub-Lite</strong>
            <span>MVP Agent 控制台</span>
          </div>
        </div>
        <nav className="nav-list" aria-label="主导航">
          <NavButton active={activeView === "agents"} icon={Bot} label="Agent 配置" onClick={() => setActiveView("agents")} />
          <NavButton active={activeView === "chat"} icon={MessageSquare} label="调试会话" onClick={() => setActiveView("chat")} />
          <NavButton active={activeView === "providers"} icon={Settings} label="模型配置" onClick={() => setActiveView("providers")} />
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <h1>{activeView === "providers" ? "模型配置" : "Agent 工作台"}</h1>
            <p>
              {activeView === "providers"
                ? "配置 OpenAI Compatible 接口、API Key 和可选模型列表。"
                : "创建 Agent 配置，并选择模型后在会话中调试。"}
            </p>
          </div>
          <div className="topbar-actions">
            <span className="status-pill">
              <Check size={15} />
              {status}
            </span>
            <button className="secondary-button" onClick={() => void bootstrap()} type="button">
              <RotateCcw size={17} />
              刷新
            </button>
          </div>
        </header>

        {error && <div className="error-banner">{error}</div>}

        {activeView === "providers" ? (
          <section className="content-grid provider-layout">
            <section className="panel">
              <div className="panel-header">
                <h2>供应商</h2>
                <span>{providers.length} 个配置</span>
              </div>
              <div className="agent-tabs vertical-tabs">
                {providers.map((provider) => (
                  <button
                    className={provider.id === selectedProviderId ? "agent-tab active" : "agent-tab"}
                    key={provider.id}
                    onClick={() => setSelectedProviderId(provider.id)}
                    type="button"
                  >
                    <strong>{provider.name}</strong>
                    <span>{provider.default_model}</span>
                  </button>
                ))}
              </div>
            </section>

            <section className="panel">
              <div className="panel-header">
                <h2>模型供应商配置</h2>
                <span>{selectedProvider?.has_api_key ? "已配置 Key" : "未配置 Key"}</span>
              </div>
              <form className="config-form" onSubmit={(event) => event.preventDefault()}>
                <label>
                  名称
                  <input
                    value={providerDraft.name}
                    onChange={(event) => setProviderDraft({ ...providerDraft, name: event.target.value })}
                  />
                </label>
                <label>
                  类型
                  <input
                    value={providerDraft.provider_type}
                    onChange={(event) =>
                      setProviderDraft({ ...providerDraft, provider_type: event.target.value })
                    }
                  />
                </label>
                <label className="wide-field">
                  Base URL
                  <input
                    value={providerDraft.base_url}
                    onChange={(event) => setProviderDraft({ ...providerDraft, base_url: event.target.value })}
                    placeholder="https://dashscope.aliyuncs.com/compatible-mode/v1"
                  />
                </label>
                <label className="wide-field">
                  API Key
                  <input
                    type="password"
                    value={providerDraft.api_key}
                    onChange={(event) => setProviderDraft({ ...providerDraft, api_key: event.target.value })}
                    placeholder={selectedProvider?.has_api_key ? "留空表示不修改已有 Key" : "请输入 API Key"}
                  />
                </label>
                <label>
                  默认模型
                  <input
                    list="provider-models"
                    value={providerDraft.default_model}
                    onChange={(event) =>
                      setProviderDraft({ ...providerDraft, default_model: event.target.value })
                    }
                    placeholder="qwen-plus"
                  />
                </label>
                <label>
                  常用模型列表
                  <textarea
                    value={providerDraft.available_models}
                    onChange={(event) =>
                      setProviderDraft({ ...providerDraft, available_models: event.target.value })
                    }
                    placeholder="qwen-plus&#10;qwen-max&#10;qwen-turbo"
                    rows={5}
                  />
                </label>
                <datalist id="provider-models">
                  {splitList(providerDraft.available_models, "\n").map((model) => (
                    <option key={model} value={model} />
                  ))}
                </datalist>
                <div className="hint wide-field">
                  千问 DashScope 兼容模式通常使用 Base URL：
                  https://dashscope.aliyuncs.com/compatible-mode/v1，模型名示例：qwen-plus、qwen-max、qwen-turbo。
                </div>
                <div className="form-actions">
                  <button className="secondary-button" onClick={testProvider} type="button">
                    <TestTube2 size={17} />
                    测试连接
                  </button>
                  <button className="primary-button" onClick={saveProvider} type="button">
                    <KeyRound size={17} />
                    保存模型配置
                  </button>
                </div>
              </form>
            </section>
          </section>
        ) : (
          <section className="content-grid">
            <section className="panel agent-panel">
              <div className="panel-header">
                <h2>Agent 配置</h2>
                <span>{agents.length} 个 Agent</span>
              </div>

              <div className="agent-tabs">
                {agents.map((agent) => (
                  <button
                    className={agent.id === selectedAgentId ? "agent-tab active" : "agent-tab"}
                    key={agent.id}
                    onClick={() => setSelectedAgentId(agent.id)}
                    type="button"
                  >
                    <strong>{agent.name}</strong>
                    <span>{agent.model_name}</span>
                  </button>
                ))}
              </div>

              <form className="config-form" onSubmit={createAgent}>
                <label>
                  名称
                  <input
                    value={agentDraft.name}
                    onChange={(event) => setAgentDraft({ ...agentDraft, name: event.target.value })}
                    placeholder="研究助手"
                  />
                </label>
                <label>
                  描述
                  <input
                    value={agentDraft.description}
                    onChange={(event) =>
                      setAgentDraft({ ...agentDraft, description: event.target.value })
                    }
                    placeholder="用于资料研究和总结"
                  />
                </label>
                <label className="wide-field">
                  系统提示词
                  <textarea
                    value={agentDraft.system_prompt}
                    onChange={(event) =>
                      setAgentDraft({ ...agentDraft, system_prompt: event.target.value })
                    }
                    rows={5}
                  />
                </label>
                <label>
                  模型供应商
                  <select
                    value={agentDraft.model_provider_id}
                    onChange={(event) => {
                      const provider = providers.find((item) => item.id === event.target.value);
                      setAgentDraft({
                        ...agentDraft,
                        model_provider_id: event.target.value,
                        model_name: provider?.default_model ?? agentDraft.model_name,
                      });
                    }}
                  >
                    {providers.map((provider) => (
                      <option key={provider.id} value={provider.id}>
                        {provider.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  模型
                  <input
                    list="agent-models"
                    value={agentDraft.model_name}
                    onChange={(event) => setAgentDraft({ ...agentDraft, model_name: event.target.value })}
                    placeholder="qwen-plus"
                  />
                  <datalist id="agent-models">
                    {(agentProvider?.available_models ?? []).map((model) => (
                      <option key={model} value={model} />
                    ))}
                  </datalist>
                </label>
                <label>
                  温度
                  <input
                    max="2"
                    min="0"
                    step="0.1"
                    type="number"
                    value={agentDraft.temperature}
                    onChange={(event) =>
                      setAgentDraft({ ...agentDraft, temperature: Number(event.target.value) })
                    }
                  />
                </label>
                <label>
                  最大 Token 数
                  <input
                    min="1"
                    type="number"
                    value={agentDraft.max_tokens}
                    onChange={(event) =>
                      setAgentDraft({ ...agentDraft, max_tokens: Number(event.target.value) })
                    }
                  />
                </label>
                <label className="wide-field">
                  开场白
                  <input
                    value={agentDraft.opening_message}
                    onChange={(event) =>
                      setAgentDraft({ ...agentDraft, opening_message: event.target.value })
                    }
                  />
                </label>
                <label>
                  知识库
                  <input
                    value={agentDraft.knowledge_base_ids}
                    onChange={(event) =>
                      setAgentDraft({ ...agentDraft, knowledge_base_ids: event.target.value })
                    }
                    placeholder="docs, policies"
                  />
                </label>
                <label>
                  技能
                  <input
                    value={agentDraft.skill_ids}
                    onChange={(event) => setAgentDraft({ ...agentDraft, skill_ids: event.target.value })}
                    placeholder="summary, planning"
                  />
                </label>
                <label className="wide-field">
                  示例问题
                  <textarea
                    value={agentDraft.example_questions}
                    onChange={(event) =>
                      setAgentDraft({ ...agentDraft, example_questions: event.target.value })
                    }
                    rows={3}
                  />
                </label>
                <div className="form-actions">
                  <button className="secondary-button" onClick={saveAgent} type="button">
                    <Save size={17} />
                    保存当前 Agent
                  </button>
                  <button className="primary-button" type="submit">
                    <Plus size={17} />
                    新建 Agent
                  </button>
                </div>
              </form>
            </section>

            <section className="panel chat-panel">
              <div className="panel-header">
                <h2>调试会话</h2>
                <button className="icon-button" onClick={startConversation} title="新建会话" type="button">
                  <Plus size={18} />
                </button>
              </div>

              <div className="conversation-tabs">
                {conversations.map((conversation) => (
                  <button
                    className={
                      conversation.id === selectedConversationId
                        ? "conversation-tab active"
                        : "conversation-tab"
                    }
                    key={conversation.id}
                    onClick={() => setSelectedConversationId(conversation.id)}
                    type="button"
                  >
                    {conversation.title}
                  </button>
                ))}
              </div>

              <div className="message-list">
                {(selectedConversation?.messages ?? []).map((message) => (
                  <div className={`message ${message.role}`} key={message.id ?? message.content}>
                    {message.content}
                  </div>
                ))}
                {!selectedConversation && (
                  <div className="empty-state">新建一个会话来测试当前 Agent。</div>
                )}
              </div>

              <form className="composer" onSubmit={sendMessage}>
                <input
                  aria-label="聊天消息"
                  disabled={isSending}
                  onChange={(event) => setMessageDraft(event.target.value)}
                  placeholder="输入消息调试当前 Agent"
                  value={messageDraft}
                />
                <button className="primary-button" disabled={isSending} type="submit">
                  <Send size={17} />
                  发送
                </button>
              </form>
            </section>
          </section>
        )}
      </section>
    </main>
  );
}

function NavButton({
  active,
  icon: Icon,
  label,
  onClick,
}: {
  active: boolean;
  icon: typeof Bot;
  label: string;
  onClick: () => void;
}) {
  return (
    <button className={active ? "nav-item active" : "nav-item"} onClick={onClick} type="button">
      <Icon size={18} />
      <span>{label}</span>
    </button>
  );
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

function toAgentDraft(agent: Agent) {
  return {
    name: agent.name,
    description: agent.description ?? "",
    system_prompt: agent.system_prompt,
    model_provider_id: agent.model_provider_id,
    model_name: agent.model_name,
    temperature: agent.temperature,
    max_tokens: agent.max_tokens ?? 1024,
    knowledge_base_ids: agent.knowledge_base_ids.join(", "),
    skill_ids: agent.skill_ids.join(", "),
    mcp_tool_ids: agent.mcp_tool_ids.join(", "),
    opening_message: agent.opening_message,
    example_questions: agent.example_questions.join("\n"),
  };
}

function fromAgentDraft(draft: typeof emptyAgentDraft) {
  return {
    ...draft,
    description: draft.description || null,
    knowledge_base_ids: splitList(draft.knowledge_base_ids),
    skill_ids: splitList(draft.skill_ids),
    mcp_tool_ids: splitList(draft.mcp_tool_ids),
    example_questions: splitList(draft.example_questions, "\n"),
  };
}

function toProviderDraft(provider: ModelProvider) {
  return {
    name: provider.name,
    provider_type: provider.provider_type,
    base_url: provider.base_url,
    api_key: "",
    default_model: provider.default_model,
    available_models: provider.available_models.join("\n"),
    supports_streaming: provider.supports_streaming,
    supports_tool_calling: provider.supports_tool_calling,
  };
}

function fromProviderDraft(draft: typeof emptyProviderDraft) {
  return {
    ...draft,
    api_key: draft.api_key || undefined,
    available_models: splitList(draft.available_models, "\n"),
  };
}

function splitList(value: string, separator = ",") {
  return value
    .split(separator)
    .map((item) => item.trim())
    .filter(Boolean);
}

function formatError(error: unknown) {
  if (!(error instanceof Error)) {
    return "操作失败，请检查后端日志。";
  }
  try {
    const parsed = JSON.parse(error.message);
    if (typeof parsed.detail === "string") return parsed.detail;
    if (parsed.detail?.message) {
      return [
        parsed.detail.message,
        parsed.detail.status_code ? `状态码：${parsed.detail.status_code}` : null,
        parsed.detail.model ? `模型：${parsed.detail.model}` : null,
        parsed.detail.endpoint ? `地址：${parsed.detail.endpoint}` : null,
        parsed.detail.response ? `响应：${parsed.detail.response}` : null,
        parsed.detail.error ? `错误：${parsed.detail.error}` : null,
      ]
        .filter(Boolean)
        .join("\n");
    }
  } catch {
    return error.message;
  }
  return error.message;
}
