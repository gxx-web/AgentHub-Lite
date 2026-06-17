import { Bot, Boxes, Database, PlayCircle, Settings, Users } from "lucide-react";
import { agents, knowledgeBases, modelProviders, workspaces } from "./mock";

const navItems = [
  { label: "Agents", icon: Bot },
  { label: "知识库", icon: Database },
  { label: "MCP", icon: Boxes },
  { label: "工作区", icon: Users },
  { label: "系统", icon: Settings }
];

export function App() {
  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">A</div>
          <div>
            <strong>AgentHub-Lite</strong>
            <span>个人 / 团队 Agent 平台</span>
          </div>
        </div>
        <nav className="nav-list">
          {navItems.map((item) => (
            <button className="nav-item" key={item.label} type="button">
              <item.icon size={18} />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <h1>Agent 工作台</h1>
            <p>创建、调试并发布可复用的大模型 Agent。</p>
          </div>
          <button className="primary-button" type="button">
            <PlayCircle size={18} />
            新建 Agent
          </button>
        </header>

        <section className="metrics-grid">
          <Metric label="工作区" value={workspaces.length} />
          <Metric label="Agents" value={agents.length} />
          <Metric label="知识库" value={knowledgeBases.length} />
          <Metric label="模型供应商" value={modelProviders.length} />
        </section>

        <section className="content-grid">
          <div className="panel">
            <div className="panel-header">
              <h2>Agent 列表</h2>
              <span>MVP</span>
            </div>
            <div className="agent-list">
              {agents.map((agent) => (
                <article className="agent-card" key={agent.id}>
                  <div>
                    <h3>{agent.name}</h3>
                    <p>{agent.description}</p>
                  </div>
                  <span>{agent.model}</span>
                </article>
              ))}
            </div>
          </div>

          <div className="panel">
            <div className="panel-header">
              <h2>调试会话</h2>
              <span>SSE Ready</span>
            </div>
            <div className="chat-preview">
              <div className="message assistant">
                AgentHub-Lite runtime is ready.
              </div>
              <div className="message user">帮我总结今天的项目计划。</div>
              <div className="composer">
                <input aria-label="chat input" placeholder="输入消息调试 Agent" />
                <button type="button">发送</button>
              </div>
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

