import { useMemo, useState } from 'react'
import { ArrowRight, BriefcaseBusiness, CheckCircle2, ChevronRight, FileCheck2, FolderOpen, Send, Sparkles } from 'lucide-react'
import { displayAgentName, displayAgentRole, formatTime, initials, stageLabels, statusLabels } from '../../lib/presentation'
import type { AgentSummary, AppActions, GuiState, RuntimeSummary, WorkflowSummary } from '../../types'
import { EmptyState, StatusBadge } from '../../components/ui'

const stageOrder = ['context', 'decide', 'act', 'evaluate']

function agentTone(agentId: string): string {
  const tones: Record<string, string> = {
    secretary: 'sage', pm: 'blue', researcher: 'teal', planner: 'slate',
    'vibe-designer': 'rose', coder: 'indigo', writer: 'gold', legal: 'red',
  }
  return tones[agentId] || 'sage'
}

function DemoWorkflow(): WorkflowSummary {
  return {
    run_id: 'demo-contract-review', title: '审查供应商合同并给出修改建议', status: 'acting', project_id: 'demo-procurement',
    agent_id: 'legal', workflow: 'legal_contract_review', invocation_mode: 'secretary', requested_by: 'demo', created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
  }
}

function DemoRuntime(): RuntimeSummary {
  return { run_id: 'demo-contract-review', current_stage: 'act', cycle_index: 1, pending_handoffs: 0, handoffs: 1, checkpoints: 2, ledger_events: 8, budget_usage: { model_calls: 3, tool_calls: 4 }, budgets: { max_model_calls: 12, max_tool_calls: 20 }, last_control_decision: { decision: 'continue' } }
}

export function OfficePage({ state, actions, demoMode, onOpenPage }: { state: GuiState | null; actions: AppActions; demoMode: boolean; onOpenPage: (page: string) => void }) {
  const [task, setTask] = useState('')
  const [mode, setMode] = useState<'quality' | 'fast' | 'economy' | 'important'>('quality')
  const [selectedAgent, setSelectedAgent] = useState('auto')
  const [submitting, setSubmitting] = useState(false)
  const employees = (state?.digital_employees.items || []).filter((agent) => (agent.status || 'active') === 'active')
  const officeAgents = employees.filter((agent) => agent.agent_id !== 'secretary').slice(0, 8)
  const workflow = demoMode ? DemoWorkflow() : state?.workflows.recent.find((item) => !['completed', 'cancelled', 'stopped'].includes(item.status))
  const runtime = demoMode ? DemoRuntime() : state?.runtime_replay.recent_runs.find((item) => item.run_id === workflow?.run_id)
  const pendingApprovals = demoMode ? 1 : Number(state?.approvals.by_status.pending || 0)

  const activeStageIndex = Math.max(0, stageOrder.indexOf(runtime?.current_stage || 'context'))
  const selectedEmployee = useMemo(() => employees.find((agent) => agent.agent_id === selectedAgent), [employees, selectedAgent])

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    const clean = task.trim()
    if (!clean) return
    setSubmitting(true)
    try {
      await actions.createWorkflow({
        task: clean,
        priority: mode === 'important' ? 'urgent' : mode === 'fast' ? 'high' : mode === 'economy' ? 'low' : 'normal',
        agent_id: selectedAgent === 'auto' ? undefined : selectedAgent,
      })
      setTask('')
    } finally {
      setSubmitting(false)
    }
  }

  return <div className="office-page">
    {demoMode && <div className="demo-banner"><Sparkles size={16} /><span>演示模式：当前展示的是可重复演示的供应商合同审查案例，不会写入真实工作记录。</span></div>}
    <section className="office-intro">
      <div><h1>我的办公室</h1><p>把事情告诉秘书，办公室会自己找到合适的人开始工作。</p></div>
      <button className="text-button" onClick={() => onOpenPage('tasks')}>查看全部任务 <ArrowRight size={16} /></button>
    </section>

    <div className="office-layout">
      <section className="office-canvas" aria-label="数字办公室工作区">
        <div className="office-wall"><span>Digital Office</span><time>{new Intl.DateTimeFormat('zh-CN', { weekday: 'long', month: 'long', day: 'numeric' }).format(new Date())}</time></div>
        <div className="office-floor">
          {officeAgents.map((agent, index) => <button className={`agent-room room-${index + 1} tone-${agentTone(agent.agent_id)}`} key={agent.agent_id} onClick={() => { setSelectedAgent(agent.agent_id); onOpenPage('employees') }}>
            <span className="room-sign">{displayAgentName(agent)}</span>
            <span className="desk-avatar">{initials(displayAgentName(agent))}</span>
            <span className="desk-status"><span className="status-dot green" />可接任务</span>
          </button>)}
          <div className="secretary-area">
            <span className="secretary-avatar">秘</span>
            <div><strong>秘书</strong><span>正在安排办公室工作</span></div>
          </div>
          <div className="office-table"><span /><span /><span /></div>
          <div className="filing-wall"><FolderOpen size={20} /><span>资料库</span></div>
        </div>
      </section>

      <aside className="today-panel">
        <header><div><span>今天的工作</span><strong>{workflow ? '1 项正在办理' : '办公室已准备好'}</strong></div><BriefcaseBusiness size={20} /></header>
        {workflow ? <div className="active-work-card">
          <div className="work-card-title"><StatusBadge tone={workflow.status.includes('waiting') ? 'amber' : 'blue'}>{statusLabels[workflow.status] || '办理中'}</StatusBadge><span>{formatTime(workflow.updated_at)}</span></div>
          <h2>{workflow.title || '未命名任务'}</h2>
          <p>{displayAgentName(employees.find((agent) => agent.agent_id === workflow.agent_id))}正在负责这项工作。</p>
          <div className="stage-track">
            {stageOrder.map((stage, index) => <div className={index < activeStageIndex ? 'stage done' : index === activeStageIndex ? 'stage active' : 'stage'} key={stage}>
              <span>{index < activeStageIndex ? <CheckCircle2 size={15} /> : index + 1}</span><em>{stageLabels[stage]}</em>
            </div>)}
          </div>
          {runtime && <div className="handoff-note"><FileCheck2 size={17} /><div><strong>{runtime.handoffs} 次工作交接</strong><span>{runtime.pending_handoffs ? '有交接信息需要补充' : '交接内容已经确认'}</span></div></div>}
          <button className="secondary-button wide" onClick={() => onOpenPage('tasks')}>查看办理过程 <ChevronRight size={16} /></button>
        </div> : <EmptyState title="还没有进行中的任务" body="在下方告诉秘书要做什么，办公室会立即开始安排。" />}
        <button className="approval-summary" onClick={() => onOpenPage('approvals')}><span><strong>{pendingApprovals}</strong> 项待审批</span><ChevronRight size={17} /></button>
      </aside>
    </div>

    <form className="task-composer" onSubmit={submit}>
      <div className="composer-heading"><span className="secretary-mini">秘</span><div><strong>告诉秘书要做什么</strong><span>{selectedEmployee ? `直接交给${displayAgentName(selectedEmployee)}` : '秘书会自动选择合适的数字员工'}</span></div></div>
      <textarea value={task} onChange={(event) => setTask(event.target.value)} placeholder="例如：帮我审查这份供应商合同，列出高风险条款和需要确认的问题。" rows={3} />
      <div className="composer-footer">
        <div className="composer-controls">
          <select aria-label="选择数字员工" value={selectedAgent} onChange={(event) => setSelectedAgent(event.target.value)}>
            <option value="auto">由秘书安排</option>
            {employees.filter((agent) => agent.agent_id !== 'secretary').map((agent) => <option key={agent.agent_id} value={agent.agent_id}>{displayAgentName(agent)}</option>)}
          </select>
          <div className="mode-tabs" aria-label="工作方式">
            {([['quality', '认真做'], ['fast', '快点做'], ['economy', '省着做'], ['important', '重要任务']] as const).map(([value, label]) => <button className={mode === value ? 'active' : ''} key={value} onClick={() => setMode(value)} type="button">{label}</button>)}
          </div>
        </div>
        <button className="primary-button send-button" disabled={!task.trim() || submitting} type="submit"><Send size={17} />{submitting ? '正在安排' : '交给秘书'}</button>
      </div>
    </form>
  </div>
}
