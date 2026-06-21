import { ArrowRight, BrainCircuit, CheckCircle2, Cpu, Database, FolderKanban, Inbox, Layers3, Radio, Sparkles, UploadCloud } from 'lucide-react'
import { DraggableBoard } from '../../components/DraggableBoard'
import { ResizableWorkspace } from '../../components/ResizableWorkspace'
import { EmptyState } from '../../components/ui'
import { displayAgentName, formatTime, statusLabels } from '../../lib/presentation'
import type { AppActions, GuiState } from '../../types'
import { SecretaryPanel } from './SecretaryPanel'

function projectName(state: GuiState | null, projectId: string) {
  return state?.projects.items.find((project) => project.project_id === projectId)?.name || projectId || '未归属项目'
}

const loopStages = ['感知', '推理', '规划', '执行', '反思', '迭代']

function loopStageIndex(stage = '') {
  const value = stage.toLowerCase()
  if (/perceive|intake|context|sense/.test(value)) return 0
  if (/reason|analy|think/.test(value)) return 1
  if (/plan|route|schedule/.test(value)) return 2
  if (/execute|tool|act|run/.test(value)) return 3
  if (/reflect|review|verify|evaluate/.test(value)) return 4
  if (/iterate|complete|deliver|learn/.test(value)) return 5
  return -1
}

export function OfficePage({ state, actions, demoMode, onOpenPage }: { state: GuiState | null; actions: AppActions; demoMode: boolean; onOpenPage: (page: string) => void }) {
  const activeRuns = (state?.workflows.recent || []).filter((run) => !['completed', 'cancelled', 'stopped'].includes(run.status))
  const pendingApprovals = (state?.approvals.recent || []).filter((approval) => approval.status === 'pending')
  const recentProjects = (state?.projects.items || []).slice(0, 6)
  const recentDeliverables = (state?.tasks.recent || []).filter((task) => ['completed', 'delivered'].includes(task.status)).slice(0, 5)
  const activeProjects = recentProjects.filter((project) => project.status === 'active').length
  const latestRuntime = state?.runtime_replay.recent_runs?.[0]
  const currentLoopStage = loopStageIndex(latestRuntime?.current_stage)
  const configuredModels = (state?.model_runtime.providers || []).filter((provider) => provider.configured && provider.enabled).length
  const readyLocalRuntimes = (state?.model_runtime.local_runtimes || []).filter((runtime) => runtime.ready).length
  const installedSkills = state?.skill_installations.count || 0

  const boardItems = [
    {
      id: 'projects',
      content: <section className="plain-card office-side-card">
        <header><h2>最近项目</h2><button className="text-button" onClick={() => onOpenPage('projects')}>全部 <ArrowRight size={15} /></button></header>
        <div className="project-card-list">{recentProjects.map((project) => {
          const knowledge = state?.knowledge.project_entries?.[project.project_id]?.count || 0
          const active = activeRuns.filter((run) => run.project_id === project.project_id).length
          return <button key={project.project_id} onClick={() => onOpenPage('projects')}>
            <span className="project-icon"><FolderKanban size={17} /></span>
            <span><strong>{project.name}</strong><small>{active} 个对话 · {knowledge} 份资料</small></span>
            <em>{project.context_readiness?.confirmed ? '已确认' : `${project.context_readiness?.readiness_score || 0}%`}</em>
          </button>
        })}{!recentProjects.length && <EmptyState title="还没有项目" body="在左侧和秘书说出第一件要做的事。" />}</div>
      </section>,
    },
    {
      id: 'approvals',
      content: <section className="plain-card office-side-card">
        <header><h2>需要你确认</h2><span className="side-count">{pendingApprovals.length}</span></header>
        <div className="mini-list">{pendingApprovals.slice(0, 5).map((approval) => <article key={approval.approval_id}><Inbox size={16} /><div><strong>{approval.title}</strong><small>{projectName(state, approval.project_id)} · {formatTime(approval.updated_at)}</small></div></article>)}{!pendingApprovals.length && <EmptyState title="没有待确认事项" body="需要你拍板时，秘书会放到这里。" />}</div>
      </section>,
    },
    {
      id: 'running',
      content: <section className="plain-card office-side-card">
        <header><h2>正在进行</h2><span className="side-count">{activeRuns.length}</span></header>
        <div className="conversation-list">{activeRuns.slice(0, 6).map((run) => {
          const agent = state?.digital_employees.items.find((item) => item.agent_id === run.agent_id)
          return <article key={run.run_id}><span className="conversation-mark"><CheckCircle2 size={16} /></span><div><strong>{run.title || '未命名对话'}</strong><small>{projectName(state, run.project_id)} · {displayAgentName(agent)} · {statusLabels[run.status] || run.status}</small></div></article>
        })}{!activeRuns.length && <EmptyState title="暂无进行中的工作" body="项目底稿确认后，执行进度会出现在这里。" />}</div>
      </section>,
    },
    {
      id: 'deliverables',
      content: <section className="plain-card office-side-card">
        <header><h2>最近交付</h2><button className="text-button" onClick={() => onOpenPage('projects')}>查看 <ArrowRight size={15} /></button></header>
        <div className="mini-list">{recentDeliverables.map((item) => <article key={item.task_id}><UploadCloud size={16} /><div><strong>{item.title}</strong><small>{projectName(state, item.project_id)} · {formatTime(item.updated_at)}</small></div></article>)}{!recentDeliverables.length && <EmptyState title="暂无交付物" body="完成的结果会自动归入对应项目。" />}</div>
      </section>,
    },
  ]

  const sidePanel = <div className="office-side-content">
    <header className="office-side-heading">
      <div><strong>项目动态</strong><span>拖动卡片调整顺序</span></div>
      <button className="text-button" onClick={() => onOpenPage('projects')}>项目中心 <ArrowRight size={15} /></button>
    </header>
    <section className="office-system-card" aria-label="智能底座状态">
      <header><div><span className="system-live-dot" /><strong>智能底座</strong></div><span>{latestRuntime ? `第 ${latestRuntime.cycle_index + 1} 轮` : '待命'}</span></header>
      <div className="system-capabilities">
        <div><Layers3 size={15} /><strong>{installedSkills}</strong><span>可用技能</span></div>
        <div><BrainCircuit size={15} /><strong>{configuredModels}</strong><span>在线模型</span></div>
        <div><Cpu size={15} /><strong>{readyLocalRuntimes}</strong><span>本地环境</span></div>
        <div><Database size={15} /><strong>{state?.knowledge.rag_index_configured ? '已启用' : '待配置'}</strong><span>知识检索</span></div>
      </div>
      <div className="loop-track" aria-label="Loop 工作阶段">
        {loopStages.map((stage, index) => <div className={`${index === currentLoopStage ? 'active' : ''} ${index < currentLoopStage ? 'passed' : ''}`} key={stage}><span>{index + 1}</span><small>{stage}</small></div>)}
      </div>
      <footer><Radio size={13} /><span>{latestRuntime ? `当前阶段：${latestRuntime.current_stage} · ${latestRuntime.ledger_events} 条可追溯记录` : '收到任务后，系统会按六阶段受控推进'}</span></footer>
    </section>
    <DraggableBoard items={boardItems} storageKey="digital-office-home" variant="rail" />
  </div>

  return <div className="office-dashboard office-workspace-page">
    {demoMode && <div className="demo-banner"><Sparkles size={16} /><span>演示模式：展示完整工作方式，不会影响真实数据。</span></div>}
    <header className="office-commandbar">
      <div className="office-commandbar-title"><span className="eyebrow">我的办公室</span><h1>今天，从一件讲清楚的事开始</h1><p>秘书负责理解与确认，数字员工负责执行，所有判断与交付都沉淀在项目上下文中。</p></div>
      <div className="office-status-strip" aria-label="办公室状态">
        <div><strong>{activeProjects}</strong><span>进行中项目</span></div>
        <div><strong>{activeRuns.length}</strong><span>工作中</span></div>
        <div><strong>{pendingApprovals.length}</strong><span>待确认</span></div>
      </div>
    </header>
    <ResizableWorkspace storageKey="digital-office-office" side={sidePanel}>
      <SecretaryPanel actions={actions} state={state} compact />
    </ResizableWorkspace>
  </div>
}
