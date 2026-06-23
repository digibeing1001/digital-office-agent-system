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

export interface ProjectSummary {
  project_id: string
  name: string
  status: string
  agent_roster: string[]
  updated_at: string
  context_readiness?: ProjectContextReadiness
}

export interface ProjectContextQuestion {
  field: string
  prompt: string
  why: string
  priority: 'required' | 'recommended' | 'socratic'
}

export interface ProjectContextReadiness {
  required: boolean
  readiness_score: number
  readiness_threshold: number
  ready: boolean
  confirmed: boolean
  context_version: number
  blockers: string[]
  suggestions: ProjectContextQuestion[]
  intent?: { summary: string; hash: string; confirmed: boolean; confirmed_at: string; confirmed_by: string }
  context?: ProjectContextInput & { version?: number }
}

export interface ProjectContextInput {
  intent_summary?: string
  goal?: string
  deliverables?: string[]
  acceptance_criteria?: string[]
  constraints?: string[]
  source_refs?: string[]
  deadline?: string
  stakeholders?: string[]
  risk_level?: 'low' | 'normal' | 'high' | 'regulated'
  open_questions?: Array<{ question: string; critical: boolean }>
  assumptions?: string[]
}

export interface KnowledgeEntrySummary {
  entry_id: string
  title: string
  kind: string
  status: string
  created_at: string
  source_file: string
}

export interface EmployeePerformance {
  agent_id: string
  run_count: number
  task_count: number
  success_count: number
  issue_count: number
  active_count: number
  token_estimate: number
  model_calls: number
  tool_calls: number
  last_active_at: string
  success_rate: number
}

export interface EmployeeSuggestion {
  suggested_agent_id: string
  display_name: string
  template_agent_id: string
  reason: string
  skills: string[]
  keywords: string[]
  priority: 'high' | 'medium' | 'low'
}

export interface GuiState {
  kind: string
  version: string
  generated_at: string
  health: { status: string; checks: Record<string, boolean> }
  settings: {
    configured: boolean
    preferences: { company_name?: string; secretary_name?: string; tone_note?: string; choices?: Record<string, string> }
    presets: { default_choices: Record<string, string>; fields: Record<string, { label: string; choices: Record<string, { label: string; description: string }> }> }
  }
  capabilities: Array<{ id: string; status: string; commands: string[] }>
  agents: { count: number; items: AgentSummary[] }
  digital_employees: { count: number; items: AgentSummary[] }
  employee_performance: { items: Record<string, EmployeePerformance>; suggestions: EmployeeSuggestion[] }
  workflow_packs: { count: number; items: Array<Record<string, unknown>> }
  skill_installations: {
    count: number
    by_status: Record<string, number>
    items: Array<{ name: string; status: string; license: string; used_by: string[]; skill_files: number }>
  }
  projects: { count: number; items: ProjectSummary[] }
  workflows: { count: number; active_count: number; by_status: Record<string, number>; recent: WorkflowSummary[] }
  tasks: { count: number; by_status: Record<string, number>; recent: TaskSummary[] }
  approvals: { count: number; by_status: Record<string, number>; recent: ApprovalSummary[] }
  notifications: { count: number; unread: number; recent: Array<Record<string, string>> }
  knowledge: {
    company_entries: number
    project_entries: Record<string, { count: number; items: KnowledgeEntrySummary[] }>
    external_mounts: number
    spaces: { count: number; items: Array<Record<string, unknown>> }
    rag_index_configured: boolean
  }
  runtime_replay: { recent_runs: RuntimeSummary[]; eval_suites: string[] }
  audit: { recent: Array<Record<string, unknown>> }
  loop_runtime: { work_nodes: string[]; controller_decisions: string[]; default_budgets: Record<string, number> }
  model_runtime: {
    status: string
    secret_storage: string
    providers: Array<{
      provider_id: string
      display_name: string
      provider_family: string
      category: 'domestic' | 'global' | 'custom'
      credential_mode: 'api_key' | 'token_plan'
      credential_label: string
      protocol: string
      base_url: string
      configured: boolean
      enabled: boolean
      missing: string[]
      api_key_env: string
      model_env: string
      model: string
      secret_hint: string
      secret_source: string
      suggested_models: string[]
      help_url: string
      model_locked: boolean
    }>
    runtime: {
      default_mode: 'host' | 'direct_api' | 'auto'
      selection_policy: 'local_first' | 'api_first'
      provider_order: string[]
      preferred_local_runtime?: string
      local_runtime_order?: string[]
      agents: Record<string, { mode: string; provider: string; model: string; local_runtime?: string }>
    }
    local_runtimes: Array<{ id: string; display_name: string; detected: boolean; ready: boolean; config_detected: boolean; execution_support: string }>
  }
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

export interface UploadKnowledgeInput {
  scope: 'company' | 'project'
  project_id?: string
  title: string
  body?: string
  filename?: string
  content_base64?: string
  mime_type?: string
  kind?: 'text' | 'word' | 'pdf' | 'image' | 'binary'
  approve?: boolean
  notes?: string
}

export interface CreateProjectInput {
  project_id?: string
  name: string
  brief?: string
  agent_roster?: string[]
  methodology_schedule?: 'manual' | 'weekly' | 'monthly' | 'on_project_close'
}

export interface ModelConnectionInput {
  base_url: string
  model: string
  protocol: string
  secret?: string
  enabled?: boolean
}

export interface ModelRuntimeInput {
  default_mode: 'host' | 'direct_api' | 'auto'
  selection_policy: 'local_first' | 'api_first'
  provider_order: string[]
  preferred_local_runtime?: string
  local_runtime_order?: string[]
  agents?: Record<string, { mode: string; provider: string; model: string; local_runtime?: string }>
}

export interface SecretaryChatInput {
  message: string
}

export interface SecretaryChatResponse {
  status: 'chat' | 'suggest_project'
  intent: string
  should_create_project: boolean
  confidence: number
  reply: string
  suggested_project_name?: string
  suggested_project_id?: string
  next_actions?: string[]
}

export interface PreferenceInput {
  company_name?: string
  secretary_name?: string
  tone_note?: string
  choices: Record<string, string>
}

export interface AppActions {
  secretaryChat: (input: SecretaryChatInput) => Promise<SecretaryChatResponse>
  createProject: (input: CreateProjectInput) => Promise<Record<string, unknown>>
  createWorkflow: (input: { task: string; priority: string; agent_id?: string; project_id?: string }) => Promise<Record<string, unknown>>
  createAgent: (input: CreateAgentInput) => Promise<Record<string, unknown>>
  setAgentStatus: (agentId: string, status: AgentStatus, reason?: string) => Promise<Record<string, unknown>>
  deleteAgent: (agentId: string) => Promise<Record<string, unknown>>
  decideApproval: (approvalId: string, decision: 'approve' | 'reject') => Promise<Record<string, unknown>>
  uploadKnowledge: (input: UploadKnowledgeInput) => Promise<Record<string, unknown>>
  updateProjectContext: (projectId: string, context: ProjectContextInput) => Promise<Record<string, unknown>>
  confirmProjectIntent: (projectId: string, expectedHash: string) => Promise<Record<string, unknown>>
  confirmProjectContext: (projectId: string) => Promise<Record<string, unknown>>
  saveModelConnection: (providerId: string, input: ModelConnectionInput) => Promise<Record<string, unknown>>
  testModelConnection: (providerId: string) => Promise<Record<string, unknown>>
  deleteModelConnection: (providerId: string) => Promise<Record<string, unknown>>
  updateModelRuntime: (input: ModelRuntimeInput) => Promise<Record<string, unknown>>
  updatePreferences: (input: PreferenceInput) => Promise<Record<string, unknown>>
}
