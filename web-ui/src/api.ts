import type { AgentStatus, CreateAgentInput, CreateProjectInput, CreateWorkflowInput, FeishuInstallerCatalog, FeishuInstallerSession, GuiState, ModelConnectionInput, ModelRuntimeInput, PreferenceInput, ProjectContextInput, SecretaryChatInput, SecretaryChatResponse, StartFeishuInstallerInput, UploadKnowledgeInput } from './types'

const TOKEN_KEY = 'digital-office-web-token'

function authHeaders(): HeadersInit {
  const token = localStorage.getItem(TOKEN_KEY)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init.body ? { 'Content-Type': 'application/json' } : {}),
      ...authHeaders(),
      ...init.headers,
    },
  })
  const payload = await response.json().catch(() => ({ error: '服务器返回了无法读取的内容。' })) as T & { error?: string; summary?: string }
  if (!response.ok) {
    throw new Error(payload.error || payload.summary || `请求失败（${response.status}）`)
  }
  return payload
}

export const api = {
  getState: () => request<GuiState>('/api/gui-state?limit=50'),
  secretaryChat: (input: SecretaryChatInput) =>
    request<SecretaryChatResponse>('/api/secretary/chat', { method: 'POST', body: JSON.stringify(input) }),
  createProject: (input: CreateProjectInput) =>
    request<Record<string, unknown>>('/api/projects', { method: 'POST', body: JSON.stringify(input) }),
  createWorkflow: (input: CreateWorkflowInput) =>
    request<Record<string, unknown>>('/api/workflows', { method: 'POST', body: JSON.stringify(input) }),
  createAgent: (input: CreateAgentInput) =>
    request<Record<string, unknown>>('/api/agents', { method: 'POST', body: JSON.stringify(input) }),
  setAgentStatus: (agentId: string, status: AgentStatus, reason = '') =>
    request<Record<string, unknown>>(`/api/agents/${encodeURIComponent(agentId)}/status`, {
      method: 'POST',
      body: JSON.stringify({ status, reason }),
    }),
  deleteAgent: (agentId: string, confirmed = false) =>
    request<Record<string, unknown>>(`/api/agents/${encodeURIComponent(agentId)}${confirmed ? '?confirmed=true' : ''}`, { method: 'DELETE' }),
  decideApproval: (approvalId: string, decision: 'approve' | 'reject', message = '') =>
    request<Record<string, unknown>>(`/api/approvals/${encodeURIComponent(approvalId)}/decision`, {
      method: 'POST',
      body: JSON.stringify({ decision, message }),
    }),
  decideJudgment: (caseId: string, decision: string, workflowRunId = '', message = '') =>
    request<Record<string, unknown>>(`/api/judgments/${encodeURIComponent(caseId)}/decision`, {
      method: 'POST',
      body: JSON.stringify({ decision, workflow_run_id: workflowRunId, message }),
    }),
  resumeWorkflow: (runId: string, reason = '') =>
    request<Record<string, unknown>>(`/api/workflows/${encodeURIComponent(runId)}/resume`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),
  archiveProject: (projectId: string, restore = false) =>
    request<Record<string, unknown>>(`/api/projects/${encodeURIComponent(projectId)}/archive`, { method: 'POST', body: JSON.stringify({ restore }) }),
  archiveWorkflow: (runId: string, restore = false) =>
    request<Record<string, unknown>>(`/api/workflows/${encodeURIComponent(runId)}/archive`, { method: 'POST', body: JSON.stringify({ restore }) }),
  uploadKnowledge: (input: UploadKnowledgeInput) =>
    request<Record<string, unknown>>('/api/knowledge/uploads', { method: 'POST', body: JSON.stringify(input) }),
  updateProjectContext: (projectId: string, context: ProjectContextInput) =>
    request<Record<string, unknown>>(`/api/projects/${encodeURIComponent(projectId)}/context`, { method: 'POST', body: JSON.stringify({ context }) }),
  confirmProjectIntent: (projectId: string, expectedHash: string) =>
    request<Record<string, unknown>>(`/api/projects/${encodeURIComponent(projectId)}/intent/confirm`, { method: 'POST', body: JSON.stringify({ confirmed: true, expected_hash: expectedHash }) }),
  confirmProjectContext: (projectId: string) =>
    request<Record<string, unknown>>(`/api/projects/${encodeURIComponent(projectId)}/context/confirm`, { method: 'POST', body: JSON.stringify({ confirmed: true }) }),
  saveModelConnection: (providerId: string, input: ModelConnectionInput) =>
    request<Record<string, unknown>>(`/api/model-connections/${encodeURIComponent(providerId)}`, { method: 'POST', body: JSON.stringify(input) }),
  testModelConnection: (providerId: string) =>
    request<Record<string, unknown>>(`/api/model-connections/${encodeURIComponent(providerId)}/test`, { method: 'POST', body: JSON.stringify({}) }),
  deleteModelConnection: (providerId: string) =>
    request<Record<string, unknown>>(`/api/model-connections/${encodeURIComponent(providerId)}?confirmed=true`, { method: 'DELETE' }),
  updateModelRuntime: (input: ModelRuntimeInput) =>
    request<Record<string, unknown>>('/api/model-runtime', { method: 'POST', body: JSON.stringify(input) }),
  updatePreferences: (input: PreferenceInput) =>
    request<Record<string, unknown>>('/api/settings', { method: 'POST', body: JSON.stringify(input) }),
  getFeishuInstallerCatalog: () => request<FeishuInstallerCatalog>('/api/installer/catalog'),
  startFeishuInstaller: (input: StartFeishuInstallerInput) =>
    request<FeishuInstallerSession>('/api/installer/sessions', { method: 'POST', body: JSON.stringify(input) }),
  getFeishuInstallerSession: (sessionId: string) =>
    request<FeishuInstallerSession>(`/api/installer/sessions/${encodeURIComponent(sessionId)}`),
  setToken: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clearToken: () => localStorage.removeItem(TOKEN_KEY),
}
