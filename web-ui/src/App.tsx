import { useCallback, useEffect, useState } from 'react'
import { api } from './api'
import { AdminApp } from './features/admin/AdminApp'
import { UserApp } from './features/user/UserApp'
import type { AgentStatus, CreateAgentInput, CreateProjectInput, CreateWorkflowInput, GuiState, ModelConnectionInput, ModelRuntimeInput, PreferenceInput, ProjectContextInput, SecretaryChatInput, UploadKnowledgeInput } from './types'

export default function App() {
  const [state, setState] = useState<GuiState | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState('')
  const isAdmin = window.location.pathname.startsWith('/admin')

  const refresh = useCallback(async () => {
    try {
      setError('')
      setState(await api.getState())
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : '暂时无法连接数字办公室。')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
    const timer = window.setInterval(() => void refresh(), 20_000)
    return () => window.clearInterval(timer)
  }, [refresh])

  useEffect(() => {
    if ('serviceWorker' in navigator && import.meta.env.PROD) {
      void navigator.serviceWorker.register('/service-worker.js')
    }
  }, [])

  const mutate = async <T,>(label: string, action: () => Promise<T>): Promise<T> => {
    setBusy(label)
    setError('')
    try {
      const result = await action()
      await refresh()
      return result
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : '操作没有完成。')
      throw cause
    } finally {
      setBusy('')
    }
  }

  const actions = {
    secretaryChat: (input: SecretaryChatInput) => mutate('正在理解你的意思...', () => api.secretaryChat(input)),
    createProject: (input: CreateProjectInput) => mutate('正在创建项目…', () => api.createProject(input)),
    createWorkflow: (input: CreateWorkflowInput) =>
      mutate('正在交给秘书…', () => api.createWorkflow(input)),
    createAgent: (input: CreateAgentInput) => mutate('正在创建数字员工…', () => api.createAgent(input)),
    setAgentStatus: (agentId: string, status: AgentStatus, reason?: string) =>
      mutate('正在更新数字员工…', () => api.setAgentStatus(agentId, status, reason)),
    deleteAgent: (agentId: string) => mutate('正在删除数字员工…', () => api.deleteAgent(agentId)),
    decideApproval: (approvalId: string, decision: 'approve' | 'reject') =>
      mutate('正在记录决定…', () => api.decideApproval(approvalId, decision)),
    decideJudgment: (caseId: string, decision: string, workflowRunId?: string, message?: string) =>
      mutate('正在处理审批…', () => api.decideJudgment(caseId, decision, workflowRunId || '', message || '')),
    resumeWorkflow: (runId: string, reason?: string) =>
      mutate('正在恢复工作流…', () => api.resumeWorkflow(runId, reason || '')),
    uploadKnowledge: (input: UploadKnowledgeInput) => mutate('正在上传资料…', () => api.uploadKnowledge(input)),
    updateProjectContext: (projectId: string, context: ProjectContextInput) => mutate('正在整理项目上下文…', () => api.updateProjectContext(projectId, context)),
    confirmProjectIntent: (projectId: string, expectedHash: string) => mutate('正在确认项目意图…', () => api.confirmProjectIntent(projectId, expectedHash)),
    confirmProjectContext: (projectId: string) => mutate('正在确认项目底稿…', () => api.confirmProjectContext(projectId)),
    saveModelConnection: (providerId: string, input: ModelConnectionInput) => mutate('正在保存模型连接…', () => api.saveModelConnection(providerId, input)),
    testModelConnection: (providerId: string) => mutate('正在测试模型连接…', () => api.testModelConnection(providerId)),
    deleteModelConnection: (providerId: string) => mutate('正在断开模型连接…', () => api.deleteModelConnection(providerId)),
    updateModelRuntime: (input: ModelRuntimeInput) => mutate('正在更新自动选路…', () => api.updateModelRuntime(input)),
    archiveProject: (projectId: string, restore = false) => mutate(restore ? '正在恢复项目…' : '正在归档项目…', () => api.archiveProject(projectId, restore)),
    archiveWorkflow: (runId: string, restore = false) => mutate(restore ? '正在恢复对话…' : '正在归档对话…', () => api.archiveWorkflow(runId, restore)),
    updatePreferences: (input: PreferenceInput) => mutate('正在保存使用偏好…', () => api.updatePreferences(input)),
  }

  return <>
    {error && <div className="global-message error"><span>{error}</span><button onClick={() => void refresh()}>重新连接</button></div>}
    {busy && <div className="global-message busy">{busy}</div>}
    {isAdmin ? <AdminApp actions={actions} state={state} /> : <UserApp actions={actions} state={state} />}
  </>
}
