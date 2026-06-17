export const workspaces = [
  {
    id: "default",
    name: "Default Workspace"
  }
];

export const modelProviders = [
  {
    id: "openai-compatible",
    name: "OpenAI Compatible"
  }
];

export const knowledgeBases = [
  {
    id: "docs",
    name: "项目文档库"
  }
];

export const agents = [
  {
    id: "default-agent",
    name: "Default Assistant",
    description: "用于验证 MVP 调试链路的默认 Agent。",
    model: "gpt-4.1-mini"
  },
  {
    id: "research-agent",
    name: "Research Agent",
    description: "面向知识库问答和资料整理的 Agent 模板。",
    model: "openai-compatible"
  }
];

