# AgentHub-Lite

AI Agent 个人 / 团队大模型工具平台需求文档

## 1. 项目定位

AgentHub-Lite 是一个基于 LangChain / LangGraph 构建的个人与小团队 AI Agent 平台。

平台目标是让普通用户不需要具备代码开发能力，也可以通过可视化配置的方式创建、使用、调试和管理 Agent。平台支持多模型接入、知识库加载、Skill 扩展、MCP 工具调用、多 Agent 协作、定时任务、告警通知和外部机器人网关集成。

本项目定位为轻量版 Dify / Coze / LangFlow / OpenWebUI，重点服务个人效率工具、小团队内部助手、知识库问答、自动化工作流和 Agent 学习实践场景。

## 2. 项目目标

### 2.1 学习目标

通过该项目系统学习以下 AI 应用开发能力：

1. 大模型 API 接入与统一封装。
2. LangChain / LangGraph Agent 编排。
3. RAG 知识库问答。
4. Function Calling / Tool Calling。
5. MCP 工具生态接入。
6. 多 Agent 协作模式。
7. 长短期记忆管理。
8. 企业级权限、工作区、审计和调度设计。
9. 前后端分离架构开发。
10. 大模型应用的工程化部署。

### 2.2 产品目标

构建一个面向个人和小团队的轻量 Agent 平台，核心目标包括：

1. 用户可以通过页面创建、配置、测试和发布 Agent。
2. Agent 可以绑定模型、提示词、知识库、Skill、MCP 工具和记忆策略。
3. 用户可以在个人或团队工作区内共享 Agent、知识库和工具配置。
4. 平台支持多 Agent 协作，允许多个 Agent 按角色分工完成复杂任务。
5. 平台支持通过 Web 页面、API、外部机器人、定时任务等方式调用 Agent。
6. 平台提供运行日志、调用记录、费用统计、错误追踪和审计能力。

## 3. 技术选型

### 3.1 大模型接入

平台支持多种大模型 Provider：

1. OpenAI / ChatGPT API。
2. DeepSeek API。
3. 通义千问 API。
4. OpenAI Compatible API。
5. 本地模型服务，例如 Ollama、vLLM、LiteLLM。

平台不直接绑定某一个模型厂商，而是通过统一的 Model Provider 层进行封装。

核心要求：

1. 支持统一的 Chat Completion 接口。
2. 支持流式输出。
3. 支持 Function Calling / Tool Calling。
4. 支持模型参数配置，例如 temperature、top_p、max_tokens。
5. 支持不同用户或工作区配置独立 API Key。
6. 支持模型调用日志和 Token 用量统计。

### 3.2 前端

前端技术栈：

1. React。
2. TypeScript。
3. Vite。
4. Ant Design / Shadcn UI。

主要页面包括：

1. 登录 / 注册页面。
2. 工作区管理页面。
3. Agent 创建页面。
4. Agent 调试页面。
5. 知识库管理页面。
6. Skill 管理页面。
7. MCP 管理页面。
8. 多 Agent 协作页面。
9. 定时任务 / 告警页面。
10. 系统管理后台。

### 3.3 后端

后端技术栈：

1. Python。
2. FastAPI。
3. SQLAlchemy / SQLModel。
4. Pydantic。
5. Celery / APScheduler / Redis Queue。
6. WebSocket / SSE 流式输出。

后端负责用户权限、Agent 编排、模型调用、工具调用、知识库检索、任务调度、日志审计等核心逻辑。

### 3.4 中间件与存储

1. PostgreSQL
   用于存储用户、工作区、Agent 配置、权限、任务、日志、API Key 元数据、运行记录等结构化数据。
2. RAGFlow
   用于文档解析、切分、向量化、知识库检索和 RAG 问答。
3. OpenViking
   用于管理 Agent 的上下文资源，包括 Skill、长期记忆、资源文件和可复用上下文。
4. Redis
   用于缓存、任务队列、会话状态、限流和异步任务。
5. MinIO / 本地文件系统
   用于存储用户上传的原始文件、图片、附件和导出文件。

## 4. 核心功能

### 4.1 用户与权限

1. 支持用户注册、登录、退出。
2. 支持个人资料和密码管理。
3. 支持角色权限控制，例如 Owner、Admin、Member、Viewer。
4. 支持工作区级别的数据隔离。
5. 支持 API Key 管理和调用权限控制。
6. 支持操作审计日志。

### 4.2 工作区管理

1. 用户可以创建个人工作区或团队工作区。
2. 工作区内可以管理成员、角色和权限。
3. 工作区内共享 Agent、知识库、Skill、MCP 工具配置和模型配置。
4. 支持工作区级别的模型 Key、调用额度和限流策略。

### 4.3 Model Provider 管理

1. 支持配置多个模型供应商。
2. 支持 OpenAI Compatible Base URL。
3. 支持测试模型连通性。
4. 支持为不同 Agent 指定默认模型。
5. 支持保存模型能力标签，例如是否支持工具调用、是否支持视觉、多模态、上下文长度。

### 4.4 Agent 管理

Agent 是平台的核心运行单元。

每个 Agent 包含以下配置：

1. 名称、描述、头像。
2. 系统提示词。
3. 绑定模型。
4. 模型参数。
5. 绑定知识库。
6. 绑定 Skill。
7. 绑定 MCP 工具。
8. 记忆策略。
9. 开场白和示例问题。
10. 可见性和共享权限。

核心能力：

1. 创建、编辑、删除 Agent。
2. 克隆 Agent。
3. 导入 / 导出 Agent 配置。
4. Agent 版本管理。
5. Agent 调试和测试。
6. Agent 发布为 API。
7. Agent 发布到外部机器人渠道。

### 4.5 Agent 调试与会话

1. 支持 Chat UI 与 Agent 对话。
2. 支持 SSE / WebSocket 流式输出。
3. 支持显示工具调用过程。
4. 支持显示知识库召回片段。
5. 支持重新生成回答。
6. 支持会话历史管理。
7. 支持用户反馈，例如点赞、点踩、标记问题。
8. 支持导出对话记录。

### 4.6 知识库管理

知识库基于 RAGFlow 构建。

支持能力：

1. 创建知识库。
2. 上传文档，例如 PDF、Word、Markdown、TXT、HTML。
3. 文档解析、切分、向量化。
4. 文档状态查看。
5. 知识库检索测试。
6. Agent 绑定一个或多个知识库。
7. 支持召回参数配置，例如 top_k、score_threshold。
8. 支持引用来源展示。

### 4.7 Skill 管理

Skill 是可复用的 Agent 能力包，可以包含提示词、工具说明、上下文模板、资源文件或执行逻辑。

支持能力：

1. 创建 Skill。
2. 编辑 Skill 元信息和说明。
3. 上传 Skill 资源文件。
4. 将 Skill 绑定到 Agent。
5. 支持 Skill 分类、标签和搜索。
6. 支持 Skill 导入 / 导出。
7. 支持 Skill 版本管理。

### 4.8 MCP 工具管理

平台支持接入 MCP Server，用于扩展 Agent 的外部工具能力。

支持能力：

1. 创建 MCP Server 配置。
2. 支持 stdio、HTTP、SSE 等连接方式。
3. 展示 MCP Server 暴露的 tools、resources、prompts。
4. 测试 MCP 工具调用。
5. 将 MCP 工具绑定到 Agent。
6. 支持工具级权限控制。
7. 支持工具调用日志。

### 4.9 多 Agent 协作

平台支持基于 LangGraph 构建多 Agent 工作流。

典型协作模式：

1. Supervisor 模式：一个主控 Agent 负责拆解任务并调度其他 Agent。
2. Pipeline 模式：多个 Agent 按固定顺序处理任务。
3. Debate 模式：多个 Agent 给出不同方案，再由评审 Agent 汇总。
4. Tool Specialist 模式：不同 Agent 负责不同工具或领域。

支持能力：

1. 创建协作流程。
2. 配置参与的 Agent 和角色。
3. 配置节点、边和执行条件。
4. 调试协作过程。
5. 查看每个 Agent 的输入、输出和工具调用。
6. 将协作流程发布为 API 或定时任务。

### 4.10 记忆管理

支持短期记忆和长期记忆。

短期记忆：

1. 基于会话上下文窗口。
2. 支持历史消息裁剪。
3. 支持摘要压缩。

长期记忆：

1. 基于 OpenViking 或向量存储。
2. 支持用户级记忆。
3. 支持 Agent 级记忆。
4. 支持工作区级共享记忆。
5. 支持记忆检索、编辑和删除。

### 4.11 定时任务

支持将 Agent 或多 Agent 协作流程配置为定时任务。

支持能力：

1. Cron 表达式配置。
2. 固定间隔执行。
3. 手动触发。
4. 启用 / 停用任务。
5. 查看任务执行历史。
6. 失败重试。
7. 超时控制。
8. 任务结果通知。

### 4.12 告警通知

支持多种通知渠道：

1. 邮件。
2. Webhook。
3. 企业微信机器人。
4. 飞书机器人。
5. 钉钉机器人。
6. Telegram Bot。

触发场景：

1. 定时任务完成。
2. 定时任务失败。
3. Agent 调用异常。
4. Token 用量超限。
5. 工具调用失败。
6. 系统服务异常。

### 4.13 外部机器人网关

平台支持将 Agent 接入外部聊天机器人。

支持渠道：

1. 企业微信。
2. 飞书。
3. 钉钉。
4. Telegram。
5. Discord。
6. 自定义 Webhook。

核心能力：

1. 渠道配置。
2. 消息签名校验。
3. 用户身份映射。
4. Agent 路由。
5. 消息上下文保持。
6. 文件、图片等附件处理。

### 4.14 API 调用

平台支持将 Agent 发布为 API。

支持能力：

1. 为 Agent 生成 API Endpoint。
2. 使用 API Key 鉴权。
3. 支持同步调用。
4. 支持流式调用。
5. 支持调用限流。
6. 支持调用日志。
7. 支持 API 文档展示。

### 4.15 日志、审计与统计

平台需要记录关键运行数据：

1. 用户操作日志。
2. Agent 调用日志。
3. 模型请求与响应摘要。
4. Token 用量。
5. 工具调用记录。
6. 知识库召回记录。
7. 任务执行记录。
8. 错误日志和异常堆栈。

统计指标：

1. 调用次数。
2. 成功率。
3. 平均响应时间。
4. Token 消耗。
5. 费用估算。
6. 活跃用户。
7. Agent 使用排行。

## 5. 系统架构

### 5.1 架构分层

推荐采用以下分层：

1. Web Frontend
   负责页面交互、Agent 配置、调试会话和管理后台。
2. API Backend
   负责鉴权、业务接口、配置管理、任务管理和日志查询。
3. Agent Runtime
   负责 LangChain / LangGraph 编排、模型调用、工具调用和记忆处理。
4. Tool Gateway
   负责 MCP 工具、内置工具、外部 API 工具的统一封装。
5. RAG Service
   负责知识库解析、索引、检索和引用返回。
6. Scheduler Worker
   负责任务调度、异步执行、失败重试和通知发送。
7. Storage Layer
   负责 PostgreSQL、Redis、MinIO、向量库等存储能力。

### 5.2 典型调用链路

用户在页面调用 Agent：

1. 前端发起会话请求。
2. 后端校验用户身份、工作区权限和 Agent 权限。
3. 后端加载 Agent 配置。
4. Agent Runtime 初始化模型、提示词、知识库、Skill、MCP 工具和记忆。
5. 如需知识库，调用 RAGFlow 执行检索。
6. 如需工具，调用内置工具或 MCP 工具。
7. 模型生成结果并通过 SSE / WebSocket 返回前端。
8. 后端记录调用日志、Token 用量、工具调用和召回信息。

## 6. 数据模型草案

核心数据表包括：

1. users：用户。
2. workspaces：工作区。
3. workspace_members：工作区成员。
4. model_providers：模型供应商。
5. model_credentials：模型凭据元数据。
6. agents：Agent 基础信息。
7. agent_versions：Agent 版本。
8. agent_tools：Agent 绑定工具。
9. agent_skills：Agent 绑定 Skill。
10. knowledge_bases：知识库。
11. knowledge_documents：知识库文档。
12. skills：Skill。
13. mcp_servers：MCP Server 配置。
14. conversations：会话。
15. messages：消息。
16. agent_runs：Agent 运行记录。
17. tool_calls：工具调用记录。
18. scheduled_tasks：定时任务。
19. notifications：通知配置。
20. audit_logs：审计日志。

## 7. 非功能需求

### 7.1 安全性

1. API Key 加密存储。
2. 用户密码安全哈希。
3. 工作区数据隔离。
4. 工具调用权限控制。
5. 外部 Webhook 签名校验。
6. 敏感日志脱敏。

### 7.2 可扩展性

1. 模型 Provider 可扩展。
2. Tool 类型可扩展。
3. MCP Server 可扩展。
4. Agent Runtime 可替换。
5. 知识库后端可替换。
6. 通知渠道可扩展。

### 7.3 可观测性

1. 结构化日志。
2. 请求链路追踪。
3. Agent 运行过程追踪。
4. 错误告警。
5. Token 和费用统计。
6. 系统健康检查。

### 7.4 部署要求

1. 支持本地开发环境一键启动。
2. 支持 Docker Compose 部署。
3. 支持生产环境配置隔离。
4. 支持数据库迁移。
5. 支持日志持久化。
6. 支持服务健康检查。

## 8. 版本规划

### 8.1 MVP 版本

MVP 重点验证个人可用的 Agent 创建与调试闭环。

范围：

1. 用户登录。
2. 单工作区。
3. Model Provider 配置。
4. Agent 创建、编辑、删除。
5. Prompt 配置。
6. Chat 调试页面。
7. SSE 流式输出。
8. 基础调用日志。
9. OpenAI Compatible 模型接入。

### 8.2 V0.2

加入知识库和工具能力。

范围：

1. 知识库管理。
2. RAGFlow 接入。
3. Agent 绑定知识库。
4. 内置工具调用。
5. MCP Server 配置。
6. Agent 绑定 MCP 工具。
7. 工具调用过程展示。

### 8.3 V0.3

加入团队协作和任务能力。

范围：

1. 多工作区。
2. 成员和角色权限。
3. Agent 共享。
4. 定时任务。
5. 通知渠道。
6. API 调用。

### 8.4 V0.4

加入多 Agent 协作和记忆能力。

范围：

1. LangGraph 多 Agent 编排。
2. 多 Agent 协作页面。
3. 长短期记忆管理。
4. OpenViking 接入。
5. 协作流程发布。

### 8.5 V1.0

形成稳定可部署版本。

范围：

1. 完整权限体系。
2. 完整审计日志。
3. API Key 管理。
4. 外部机器人网关。
5. 费用统计。
6. Docker Compose 部署。
7. 系统管理后台。
8. 基础文档和示例模板。

## 9. 开发原则

1. 先完成最小闭环，再逐步扩展复杂能力。
2. 后端优先保证清晰的领域模型和可测试性。
3. 前端优先保证配置流程简单、调试过程透明。
4. 模型、工具、知识库、记忆都通过统一抽象接入。
5. 关键运行过程必须可追踪、可复现、可审计。
6. 默认服务个人和小团队，不追求一开始就做成大型企业平台。

## 10. 项目目录建议

```text
AgentHub-Lite/
  apps/
    web/                  # React 前端
    api/                  # FastAPI 后端
  packages/
    agent-runtime/         # Agent 编排与运行时
    shared/                # 前后端共享类型或协议
  infra/
    docker-compose.yml
    migrations/
  docs/
    requirements.md
    architecture.md
    api.md
  README.md
```

## 11. 当前优先级

当前 MVP 已经完成基础闭环，下一阶段优先把可用性、稳定性和后续扩展边界补齐：

1. 完成 OpenAI Compatible 原生流式调用，而不是后端拿到完整响应后再分片输出。
2. 完善模型调用超时、失败重试、取消生成和错误提示。
3. 将 Prompt 从 Agent 表单中的纯文本字段抽出，接入 prompts / prompt_versions 表，实现提示词模板管理。
4. 完善 Agent 版本管理，支持配置快照、回滚、克隆和导入 / 导出。
5. 完善会话管理，支持会话删除、重命名、历史消息分页、重新生成回答。
6. 补齐运行日志详情页，展示模型供应商、模型名、耗时、错误详情、输入输出摘要。
7. 引入数据库迁移工具，例如 Alembic，替代手动执行初始化 SQL。
8. 加强安全性，包括 JWT 密钥配置、API Key 加密存储、密码哈希策略和敏感日志脱敏。
9. 为核心接口补充自动化测试，覆盖登录、模型配置、Agent CRUD、会话、SSE 和运行日志。
10. 开始 V0.2 能力设计，优先接入知识库管理、Agent 绑定知识库和基础 RAG 检索。

## 12. 已完成功能

当前代码已经完成 MVP 的主要基础能力：

1. 前后端工程初始化
   - 前端使用 React、TypeScript、Vite。
   - 后端使用 FastAPI、Pydantic。
   - 已提供本地启动命令和基础健康检查。

2. PostgreSQL 数据库设计与初始化
   - 已设计用户、工作区、成员、模型供应商、模型凭据、提示词、Agent、会话、消息、运行日志等核心表。
   - 已生成可执行 SQL 文件：`infra/postgres_schema.sql`。
   - 已生成数据模型说明文档：`docs/数据模型设计方案.md`。
   - 已在本地 PostgreSQL 中初始化 `agenthub` 数据库。

3. 用户登录和 JWT 鉴权
   - 已支持 `admin / 123456` 登录。
   - 登录后后端签发 JWT。
   - 前端自动携带 `Authorization: Bearer <token>`。
   - 模型配置、Agent、会话和运行日志接口已按当前用户工作区过滤。

4. 模型 Provider 配置
   - 支持查看、新增、修改、删除模型配置。
   - 支持 OpenAI Compatible Base URL、API Key、默认模型和模型列表配置。
   - 支持模型连通性测试。
   - 已限制删除正在被 Agent 使用的模型配置。

5. Agent 管理
   - 支持 Agent 列表。
   - 支持新增、编辑、删除 Agent。
   - Agent 创建和编辑时可选择已经创建好的模型配置。
   - Agent 可配置系统提示词、模型参数、开场白和示例问题。

6. Agent 调试与会话
   - 支持选择 Agent 进行调试会话。
   - 支持新建会话和发送消息。
   - 支持无 API Key 时的本地 fallback 回复，便于开发调试。
   - 已优化会话请求流程，使用 PostgreSQL 连接池并避免发送后全量刷新会话列表。

7. SSE 流式输出
   - 后端提供 `/api/v1/chat/stream`。
   - 前端使用 `fetch + ReadableStream` 读取 SSE。
   - 回复内容可以在聊天界面逐段显示。
   - 当前外部模型调用仍是先完整响应后再分段输出，后续需要升级为原生 provider streaming。

8. 基础运行日志
   - 已使用 `agent_runs` 记录成功和失败调用。
   - 运行日志包含状态、输入、输出、模型名、错误信息、创建时间和完成时间。
   - 前端调试页已展示最近运行日志，并支持刷新。

9. 性能优化
   - 后端数据库访问已从每次新建连接改为连接池。
   - 会话列表接口改为摘要查询，避免加载每个会话的完整消息历史。
   - 前端发送消息后改为局部更新当前会话。
   - 本地 fallback 场景下 `/chat` 平均耗时从约 187ms 优化到约 11ms。

10. 编码与开发环境
    - 已新增 `.editorconfig`，统一 UTF-8 编码。
    - 已配置 `psql` 环境变量。
    - 已为构建缓存补充 `.gitignore` 规则。
