export type AgentStatus = 'active' | 'inactive' | 'archived'

export interface AgentSummary {
  agent_id: string
  employee_id?: string
  display_name: string
  display_name_zh?: string
  user_visible_role?: string
  profile?: string
  portable_role?: string
  orchestration_roles?: string[]
  skills?: string[]
  skill_staff?: string[]
  workflow_packs?: string[]
  provider?: string
  model?: string
  status?: AgentStatus
  origin?: 'built_in' | 'custom'
  editable?: boolean
  template_agent_id?: string
  dependencies?: { active_runs: string[]; projects: string[] }
}

export interface WorkflowSummary {
  run_id: string
  title: string
  status: string
  project_id: string
  agent_id: string
  workflow: string
  invocation_mode: string
  requested_by: string
  created_at: string
  updated_at: string
}

export interface TaskSummary {
  task_id: string
  title: string
  status: string
  priority: string
  project_id: string
  assigned_agent: string
  workflow_run_id: string
  updated_at: string
}

export interface ApprovalSummary {
  approval_id: string
  title: string
  status: string
  approver_role: string
  project_id: string
  workflow_run_id: string
  task_id: string
  updated_at: string
}

export interface RuntimeSummary {
  run_id: string
  current_stage: string
  cycle_index: number
  pending_handoffs: number
  handoffs: number
  checkpoints: number
  ledger_events: number
  budget_usage: Record<string, number>
  budgets: Record<string, number>
  last_control_decision: Record<string, unknown>
}

export interface GuiState {
  kind: string
  version: string
  generated_at: string
  health: { status: string; checks: Record<string, boolean> }
  settings: { configured: boolean; preferences: Record<string, unknown> }
  capabilities: Array<{ id: string; status: string; commands: string[] }>
  agents: { count: number; items: AgentSummary[] }
  digital_employees: { count: number; items: AgentSummary[] }
  workflow_packs: { count: number; items: Array<Record<string, unknown>> }
  skill_installations: {
    count: number
    by_status: Record<string, number>
    items: Array<{ name: string; status: string; license: string; used_by: string[]; skill_files: number }>
  }
  projects: { count: number; items: Array<{ project_id: string; name: string; status: string; agent_roster: string[]; updated_at: string }> }
  workflows: { count: number; active_count: number; by_status: Record<string, number>; recent: WorkflowSummary[] }
  tasks: { count: number; by_status: Record<string, number>; recent: TaskSummary[] }
  approvals: { count: number; by_status: Record<string, number>; recent: ApprovalSummary[] }
  notifications: { count: number; unread: number; recent: Array<Record<string, string>> }
  knowledge: { company_entries: number; external_mounts: number; spaces: { count: number; items: Array<Record<string, unknown>> }; rag_index_configured: boolean }
  runtime_replay: { recent_runs: RuntimeSummary[]; eval_suites: string[] }
  audit: { recent: Array<Record<string, unknown>> }
  loop_runtime: { work_nodes: string[]; controller_decisions: string[]; default_budgets: Record<string, number> }
}

export interface CreateAgentInput {
  agent_id: string
  display_name: string
  role_description: string
  template_agent_id: string
  skills: string[]
  keywords: string[]
  workflow_packs: string[]
}

export interface AppActions {
  createWorkflow: (input: { task: string; priority: string; agent_id?: string; project_id?: string }) => Promise<void>
  createAgent: (input: CreateAgentInput) => Promise<void>
  setAgentStatus: (agentId: string, status: AgentStatus, reason?: string) => Promise<void>
  deleteAgent: (agentId: string) => Promise<void>
  decideApproval: (approvalId: string, decision: 'approve' | 'reject') => Promise<void>
}
