import {
  ArrowLeft,
  Bot,
  Check,
  Edit3,
  KeyRound,
  LogIn,
  LogOut,
  MessageSquare,
  Plus,
  RotateCcw,
  Save,
  Send,
  Settings,
  TestTube2,
  Trash2,
  UserPlus,
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

type ViewKey = "agents" | "chat" | "providers";
type EditorMode = "list" | "create" | "edit";

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

type AgentRun = {
  id: string;
  agent_id: string;
  conversation_id?: string | null;
  status: string;
  input: string;
  output: string;
  model_name?: string | null;
  error_message?: string | null;
  created_at: string;
  completed_at?: string | null;
};

type LoginResponse = {
  access_token: string;
  token_type: string;
  user_id: string;
  username: string;
  display_name: string;
  workspace_id: string;
};

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
let authToken: string | null = null;
const demoAccount = {
  username: "admin",
  password: "123456",
};

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
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState<LoginResponse | null>(null);
  const [activeView, setActiveView] = useState<ViewKey>("agents");
  const [agentEditorMode, setAgentEditorMode] = useState<EditorMode>("list");
  const [providerEditorMode, setProviderEditorMode] = useState<EditorMode>("list");
  const [agents, setAgents] = useState<Agent[]>([]);
  const [providers, setProviders] = useState<ModelProvider[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState("default-agent");
  const [selectedProviderId, setSelectedProviderId] = useState("openai-compatible");
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [agentDraft, setAgentDraft] = useState(emptyAgentDraft);
  const [providerDraft, setProviderDraft] = useState(emptyProviderDraft);
  const [messageDraft, setMessageDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [loginDraft, setLoginDraft] = useState(demoAccount);
  const [loginError, setLoginError] = useState<string | null>(null);
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
    if (isAuthenticated) {
      void bootstrap();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (selectedAgent) {
      setAgentDraft(toAgentDraft(selectedAgent));
      void loadConversations(selectedAgent.id);
    }
  }, [selectedAgent?.id]);

  useEffect(() => {
    if (selectedProvider && providerEditorMode !== "create") {
      setProviderDraft(toProviderDraft(selectedProvider));
    }
  }, [selectedProvider?.id, providerEditorMode]);

  async function bootstrap() {
    await Promise.all([loadProviders(), loadAgents(), loadRuns()]);
    setStatus("工作台已就绪");
  }

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoggingIn(true);
    try {
      const user = await request<LoginResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({
          username: loginDraft.username.trim(),
          password: loginDraft.password,
        }),
      });
      setLoginError(null);
      setError(null);
      authToken = user.access_token;
      setCurrentUser(user);
      setIsAuthenticated(true);
    } catch (err) {
      setLoginError(formatError(err) || "账号或密码错误。");
    } finally {
      setIsLoggingIn(false);
    }
  }

  function logout() {
    setIsAuthenticated(false);
    setCurrentUser(null);
    authToken = null;
    setActiveView("agents");
    setStatus("正在加载工作台...");
  }

  function openRegisterPlaceholder() {
    setLoginError("注册功能已预留，后续接入后端用户体系。");
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

  function startCreateAgent() {
    const provider = providers[0];
    setAgentDraft({
      ...emptyAgentDraft,
      model_provider_id: provider?.id ?? emptyAgentDraft.model_provider_id,
      model_name: provider?.default_model ?? emptyAgentDraft.model_name,
    });
    setAgentEditorMode("create");
  }

  function startEditAgent(agent: Agent) {
    setSelectedAgentId(agent.id);
    setAgentDraft(toAgentDraft(agent));
    setAgentEditorMode("edit");
  }

  function backToAgentList() {
    setAgentEditorMode("list");
  }

  function startCreateProvider() {
    setProviderDraft(emptyProviderDraft);
    setSelectedProviderId("");
    setProviderEditorMode("create");
  }

  function startEditProvider(provider: ModelProvider) {
    setSelectedProviderId(provider.id);
    setProviderDraft(toProviderDraft(provider));
    setProviderEditorMode("edit");
  }

  function backToProviderList() {
    setProviderEditorMode("list");
    if (providers[0]) {
      setSelectedProviderId(providers[0].id);
    }
  }

  async function loadConversations(agentId: string) {
    const data = await request<Conversation[]>(`/chat/conversations?agent_id=${agentId}`);
    setConversations(data);
    setSelectedConversationId((current) => data.find((item) => item.id === current)?.id ?? data[0]?.id ?? null);
  }

  async function loadRuns() {
    const data = await request<AgentRun[]>("/chat/runs");
    setRuns(data);
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
      setAgentEditorMode("edit");
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
      setAgentEditorMode("list");
      setStatus(`已保存 Agent：${updated.name}`);
    });
  }

  async function deleteAgent(agent: Agent) {
    if (!window.confirm(`确认删除 Agent「${agent.name}」？`)) return;
    await runAction(async () => {
      await request<void>(`/agents/${agent.id}`, { method: "DELETE" });
      setAgents((current) => current.filter((item) => item.id !== agent.id));
      setSelectedAgentId((current) => (current === agent.id ? agents.find((item) => item.id !== agent.id)?.id ?? "" : current));
      setAgentEditorMode("list");
      setStatus(`已删除 Agent：${agent.name}`);
    });
  }

  async function createProvider(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction(async () => {
      const provider = await request<ModelProvider>("/model-providers", {
        method: "POST",
        body: JSON.stringify(fromProviderDraft(providerDraft)),
      });
      setProviders((current) => [provider, ...current]);
      setSelectedProviderId(provider.id);
      setProviderDraft(toProviderDraft(provider));
      setProviderEditorMode("edit");
      setStatus(`已创建模型配置：${provider.name}`);
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
      setProviderEditorMode("list");
      setStatus(`已保存模型配置：${updated.name}`);
    });
  }

  async function deleteProvider(provider: ModelProvider) {
    if (!window.confirm(`确认删除模型配置「${provider.name}」？已被 Agent 使用的配置不能删除。`)) return;
    await runAction(async () => {
      await request<void>(`/model-providers/${provider.id}`, { method: "DELETE" });
      setProviders((current) => current.filter((item) => item.id !== provider.id));
      setSelectedProviderId((current) => (current === provider.id ? providers.find((item) => item.id !== provider.id)?.id ?? "" : current));
      setProviderEditorMode("list");
      await loadAgents();
      setStatus(`已删除模型配置：${provider.name}`);
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
    const assistantMessageId = `stream-${Date.now()}`;
    appendAssistantPlaceholder(optimisticConversation.id, assistantMessageId);

    await runAction(async () => {
      let conversationId = optimisticConversation.id;
      let assistantContent = "";
      await streamRequest(
        "/chat/stream",
        {
          agent_id: selectedAgent.id,
          conversation_id: optimisticConversation.id.startsWith("pending-")
            ? undefined
            : optimisticConversation.id,
          input,
        },
        {
          onConversation(id) {
            conversationId = id;
            if (optimisticConversation.id !== id) {
              replaceConversationId(optimisticConversation.id, id);
            }
          },
          onMessage(chunk) {
            assistantContent += chunk;
            updateAssistantMessage(conversationId, assistantMessageId, assistantContent);
          },
          onError(message) {
            updateAssistantMessage(conversationId, assistantMessageId, `调用失败：${message}`);
          },
        },
      );
      const updatedConversation: Conversation = {
        ...optimisticConversation,
        id: conversationId,
        messages: [
          ...optimisticConversation.messages,
          {
            id: assistantMessageId,
            role: "assistant",
            content: assistantContent || "调用失败，请查看运行日志。",
            created_at: new Date().toISOString(),
          },
        ],
        updated_at: new Date().toISOString(),
      };
      setConversations((current) => {
        const withoutPending = current.filter((conversation) => (
          conversation.id !== optimisticConversation.id && conversation.id !== conversationId
        ));
        return [updatedConversation, ...withoutPending];
      });
      setSelectedConversationId(conversationId);
      await loadRuns();
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

  function replaceConversationId(fromId: string, toId: string) {
    setConversations((current) =>
      current.map((conversation) =>
        conversation.id === fromId ? { ...conversation, id: toId } : conversation,
      ),
    );
    setSelectedConversationId((current) => (current === fromId ? toId : current));
  }

  function appendAssistantPlaceholder(conversationId: string, messageId: string) {
    const now = new Date().toISOString();
    setConversations((current) =>
      current.map((conversation) =>
        conversation.id === conversationId
          ? {
              ...conversation,
              messages: [
                ...conversation.messages,
                { id: messageId, role: "assistant" as const, content: "", created_at: now },
              ],
              updated_at: now,
            }
          : conversation,
      ),
    );
  }

  function updateAssistantMessage(conversationId: string, messageId: string, content: string) {
    setConversations((current) =>
      current.map((conversation) =>
        conversation.id === conversationId
          ? {
              ...conversation,
              messages: conversation.messages.map((message) =>
                message.id === messageId ? { ...message, content } : message,
              ),
              updated_at: new Date().toISOString(),
            }
          : conversation,
      ),
    );
  }

  if (!isAuthenticated) {
    return (
      <main className="login-shell">
        <section className="login-panel" aria-labelledby="login-title">
          <div className="brand login-brand">
            <div className="brand-mark">A</div>
            <div>
              <strong>AgentHub-Lite</strong>
              <span>MVP Agent 控制台</span>
            </div>
          </div>
          <div className="login-copy">
            <h1 id="login-title">登录工作台</h1>
            <p>使用临时账号进入系统，后续可替换为后端鉴权。</p>
          </div>
          <form className="login-form" onSubmit={login}>
            <label>
              账号
              <input
                autoComplete="username"
                autoFocus
                value={loginDraft.username}
                onChange={(event) =>
                  setLoginDraft({ ...loginDraft, username: event.target.value })
                }
              />
            </label>
            <label>
              密码
              <input
                autoComplete="current-password"
                type="password"
                value={loginDraft.password}
                onChange={(event) =>
                  setLoginDraft({ ...loginDraft, password: event.target.value })
                }
              />
            </label>
            {loginError && <div className="login-error">{loginError}</div>}
            <div className="login-actions">
              <button className="primary-button" disabled={isLoggingIn} type="submit">
                <LogIn size={17} />
                {isLoggingIn ? "登录中" : "登录"}
              </button>
              <button className="secondary-button" onClick={openRegisterPlaceholder} type="button">
                <UserPlus size={17} />
                注册
              </button>
            </div>
          </form>
        </section>
      </main>
    );
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
            <h1>
              {activeView === "providers"
                ? "模型配置"
                : activeView === "chat"
                  ? "调试会话"
                  : "Agent 列表"}
            </h1>
            <p>
              {activeView === "providers"
                ? "配置 OpenAI Compatible 接口、API Key 和可选模型列表。"
                : activeView === "chat"
                  ? "选择 Agent 后发起会话，检查模型回复和调试效果。"
                  : "查看、创建和维护 Agent，模型从已创建的模型配置中选择。"}
            </p>
          </div>
          <div className="topbar-actions">
            <span className="status-pill">
              <Check size={15} />
              {currentUser ? `${currentUser.display_name} · ${status}` : status}
            </span>
            <button className="secondary-button" onClick={() => void bootstrap()} type="button">
              <RotateCcw size={17} />
              刷新
            </button>
            <button className="secondary-button" onClick={logout} type="button">
              <LogOut size={17} />
              退出
            </button>
          </div>
        </header>

        {error && <div className="error-banner">{error}</div>}

        {activeView === "providers" ? (
          <section className="content-grid provider-layout">
            <section className="panel">
              <div className="panel-header">
                <h2>供应商</h2>
                <button className="primary-button" onClick={startCreateProvider} type="button">
                  <Plus size={17} />
                  新增
                </button>
              </div>
              <div className="record-list">
                {providers.map((provider) => (
                  <div className="record-row" key={provider.id}>
                    <button
                      className={provider.id === selectedProviderId ? "record-main active" : "record-main"}
                      onClick={() => startEditProvider(provider)}
                      type="button"
                    >
                      <strong>{provider.name}</strong>
                      <span>{provider.provider_type} · {provider.default_model}</span>
                    </button>
                    <div className="row-actions">
                      <button className="icon-button" onClick={() => startEditProvider(provider)} title="编辑" type="button">
                        <Edit3 size={16} />
                      </button>
                      <button className="icon-button danger" onClick={() => void deleteProvider(provider)} title="删除" type="button">
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                ))}
                {providers.length === 0 && <div className="empty-state">还没有模型配置。</div>}
              </div>
            </section>

            <section className="panel">
              <div className="panel-header">
                <h2>{providerEditorMode === "create" ? "新增模型配置" : "模型供应商配置"}</h2>
                <span>{providerEditorMode === "create" ? "新配置" : selectedProvider?.has_api_key ? "已配置 Key" : "未配置 Key"}</span>
              </div>
              <form className="config-form" onSubmit={providerEditorMode === "create" ? createProvider : (event) => event.preventDefault()}>
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
                  <button className="secondary-button" onClick={backToProviderList} type="button">
                    <ArrowLeft size={17} />
                    返回列表
                  </button>
                  <button className="secondary-button" onClick={testProvider} type="button">
                    <TestTube2 size={17} />
                    测试连接
                  </button>
                  {providerEditorMode === "create" ? (
                    <button className="primary-button" type="submit">
                      <Plus size={17} />
                      创建模型配置
                    </button>
                  ) : (
                    <button className="primary-button" onClick={saveProvider} type="button">
                      <KeyRound size={17} />
                      保存模型配置
                    </button>
                  )}
                </div>
              </form>
            </section>
          </section>
        ) : activeView === "agents" ? (
          <section className={agentEditorMode === "list" ? "single-panel-layout" : "content-grid agent-editor-layout"}>
            <section className="panel agent-panel">
              <div className="panel-header">
                <h2>Agent 列表</h2>
                <button className="primary-button" onClick={startCreateAgent} type="button">
                  <Plus size={17} />
                  新增 Agent
                </button>
              </div>

              <div className="record-list">
                {agents.map((agent) => {
                  const provider = providers.find((item) => item.id === agent.model_provider_id);
                  return (
                    <div className="record-row" key={agent.id}>
                      <button
                        className={agent.id === selectedAgentId ? "record-main active" : "record-main"}
                        onClick={() => startEditAgent(agent)}
                        type="button"
                      >
                        <strong>{agent.name}</strong>
                        <span>{provider?.name ?? agent.model_provider_id} · {agent.model_name}</span>
                      </button>
                      <div className="row-actions">
                        <button className="icon-button" onClick={() => startEditAgent(agent)} title="编辑" type="button">
                          <Edit3 size={16} />
                        </button>
                        <button className="icon-button danger" onClick={() => void deleteAgent(agent)} title="删除" type="button">
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  );
                })}
                {agents.length === 0 && <div className="empty-state">还没有 Agent。</div>}
              </div>
            </section>

            {agentEditorMode !== "list" && (
              <section className="panel agent-panel">
                <div className="panel-header">
                  <h2>{agentEditorMode === "create" ? "创建 Agent" : "修改 Agent"}</h2>
                  <button className="secondary-button" onClick={backToAgentList} type="button">
                    <ArrowLeft size={17} />
                    返回列表
                  </button>
                </div>

                <form
                  className="config-form compact-form"
                  onSubmit={agentEditorMode === "create" ? createAgent : (event) => event.preventDefault()}
                >
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
                  <label>
                    模型供应商
                    <select
                      value={agentDraft.model_provider_id}
                      onChange={(event) => {
                        const provider = providers.find((item) => item.id === event.target.value);
                        setAgentDraft({
                          ...agentDraft,
                          model_provider_id: event.target.value,
                          model_name: provider?.default_model ?? "",
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
                    <select
                      value={agentDraft.model_name}
                      onChange={(event) => setAgentDraft({ ...agentDraft, model_name: event.target.value })}
                    >
                      {(agentProvider?.available_models ?? [agentDraft.model_name]).map((model) => (
                        <option key={model} value={model}>
                          {model}
                        </option>
                      ))}
                    </select>
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
                    系统提示词
                    <textarea
                      value={agentDraft.system_prompt}
                      onChange={(event) =>
                        setAgentDraft({ ...agentDraft, system_prompt: event.target.value })
                      }
                      rows={5}
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
                    <button className="secondary-button" onClick={backToAgentList} type="button">
                      取消
                    </button>
                    {agentEditorMode === "create" ? (
                      <button className="primary-button" type="submit">
                        <Plus size={17} />
                        创建 Agent
                      </button>
                    ) : (
                      <button className="primary-button" onClick={saveAgent} type="button">
                        <Save size={17} />
                        保存修改
                      </button>
                    )}
                  </div>
                </form>
              </section>
            )}
          </section>
        ) : (
          <section className="content-grid">
            <section className="panel agent-panel">
              <div className="panel-header">
                <h2>选择 Agent</h2>
                <span>{agents.length} 个 Agent</span>
              </div>
              <div className="record-list">
                {agents.map((agent) => (
                  <button
                    className={agent.id === selectedAgentId ? "record-main active" : "record-main"}
                    key={agent.id}
                    onClick={() => setSelectedAgentId(agent.id)}
                    type="button"
                  >
                    <strong>{agent.name}</strong>
                    <span>{agent.model_name}</span>
                  </button>
                ))}
              </div>
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
                    {message.content || "正在生成..."}
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
                  {isSending ? "生成中" : "发送"}
                </button>
              </form>

              <div className="run-log">
                <div className="run-log-header">
                  <strong>运行日志</strong>
                  <button className="secondary-button compact-button" onClick={() => void loadRuns()} type="button">
                    <RotateCcw size={15} />
                    刷新
                  </button>
                </div>
                <div className="run-list">
                  {runs.slice(0, 8).map((run) => (
                    <div className={`run-item ${run.status}`} key={run.id}>
                      <div>
                        <strong>{run.status === "succeeded" ? "成功" : run.status === "failed" ? "失败" : run.status}</strong>
                        <span>{run.model_name ?? run.agent_id}</span>
                      </div>
                      <p>{run.error_message || run.input || "无输入"}</p>
                    </div>
                  ))}
                  {runs.length === 0 && <div className="empty-state">暂无运行记录。</div>}
                </div>
              </div>
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
      ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
      ...init.headers,
    },
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

async function streamRequest(
  path: string,
  body: unknown,
  handlers: {
    onConversation: (id: string) => void;
    onMessage: (chunk: string) => void;
    onError: (message: string) => void;
  },
) {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
    },
    body: JSON.stringify(body),
  });
  if (!response.ok || !response.body) {
    throw new Error(await response.text());
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      handleSseEvent(part, handlers);
    }
  }
  if (buffer.trim()) {
    handleSseEvent(buffer, handlers);
  }
}

function handleSseEvent(
  raw: string,
  handlers: {
    onConversation: (id: string) => void;
    onMessage: (chunk: string) => void;
    onError: (message: string) => void;
  },
) {
  const lines = raw.split("\n");
  const event = lines.find((line) => line.startsWith("event:"))?.slice(6).trim();
  const data = lines
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trimStart())
    .join("\n");
  if (event === "conversation") handlers.onConversation(data);
  if (event === "message") handlers.onMessage(data);
  if (event === "error") handlers.onError(data);
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
