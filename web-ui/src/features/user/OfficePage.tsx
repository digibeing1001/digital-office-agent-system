import { ArrowRight, CheckCircle2, FolderKanban, Inbox, Sparkles, UploadCloud } from 'lucide-react'
import { DraggableBoard } from '../../components/DraggableBoard'
import { EmptyState } from '../../components/ui'
import { displayAgentName, formatTime, statusLabels } from '../../lib/presentation'
import type { AppActions, GuiState } from '../../types'
import { SecretaryPanel } from './SecretaryPanel'

function projectName(state: GuiState | null, projectId: string) {
  return state?.projects.items.find((project) => project.project_id === projectId)?.name || projectId || '未归属项目'
}

export function OfficePage({ state, actions, demoMode, onOpenPage }: { state: GuiState | null; actions: AppActions; demoMode: boolean; onOpenPage: (page: string) => void }) {
  const activeRuns = (state?.workflows.recent || []).filter((run) => !['completed', 'cancelled', 'stopped'].includes(run.status))
  const pendingApprovals = (state?.approvals.recent || []).filter((approval) => approval.status === 'pending')
  const recentProjects = (state?.projects.items || []).slice(0, 6)
  const recentDeliverables = (state?.tasks.recent || []).filter((task) => ['completed', 'delivered'].includes(task.status)).slice(0, 5)
  const activeProjects = recentProjects.filter((project) => project.status === 'active').length

  const boardItems = [
    { id: 'projects', content: <section className="plain-card"><header><h2>最近项目</h2><button className="text-button" onClick={() => onOpenPage('projects')}>全部项目 <ArrowRight size={15} /></button></header><div className="project-card-list">{recentProjects.map((project) => { const knowledge = state?.knowledge.project_entries?.[project.project_id]?.count || 0; const active = activeRuns.filter((run) => run.project_id === project.project_id).length; return <button key={project.project_id} onClick={() => onOpenPage('projects')}><span className="project-icon"><FolderKanban size={17} /></span><span><strong>{project.name}</strong><small>{active} 个进行中对话 · {knowledge} 份项目资料</small></span><em>{project.context_readiness?.confirmed ? '底稿已确认' : `准备度 ${project.context_readiness?.readiness_score || 0}%`}</em></button> })}{!recentProjects.length && <EmptyState title="还没有项目" body="把第一件事告诉秘书，秘书会帮你建立项目。" />}</div></section> },
    { id: 'approvals', content: <section className="plain-card"><header><h2>需要你确认</h2><button className="text-button" onClick={() => onOpenPage('projects')}>去项目处理 <ArrowRight size={15} /></button></header><div className="mini-list">{pendingApprovals.slice(0, 5).map((approval) => <article key={approval.approval_id}><Inbox size={16} /><div><strong>{approval.title}</strong><small>{projectName(state, approval.project_id)} · {formatTime(approval.updated_at)}</small></div></article>)}{!pendingApprovals.length && <EmptyState title="暂无待确认事项" body="需要你拍板的动作会按项目出现在这里。" />}</div></section> },
    { id: 'running', content: <section className="plain-card"><header><h2>正在进行</h2><button className="text-button" onClick={() => onOpenPage('projects')}>查看项目对话 <ArrowRight size={15} /></button></header><div className="conversation-list">{activeRuns.slice(0, 6).map((run) => { const agent = state?.digital_employees.items.find((item) => item.agent_id === run.agent_id); return <article key={run.run_id}><span className="conversation-mark"><CheckCircle2 size={16} /></span><div><strong>{run.title || '未命名对话'}</strong><small>{projectName(state, run.project_id)} · {displayAgentName(agent)} · {statusLabels[run.status] || run.status}</small></div></article> })}{!activeRuns.length && <EmptyState title="暂无进行中的工作" body="在上方告诉秘书要做什么，确认项目底稿后开始执行。" />}</div></section> },
    { id: 'deliverables', content: <section className="plain-card"><header><h2>最近交付</h2><button className="text-button" onClick={() => onOpenPage('projects')}>按项目查看 <ArrowRight size={15} /></button></header><div className="mini-list">{recentDeliverables.map((item) => <article key={item.task_id}><UploadCloud size={16} /><div><strong>{item.title}</strong><small>{projectName(state, item.project_id)} · {formatTime(item.updated_at)}</small></div></article>)}{!recentDeliverables.length && <EmptyState title="暂无交付物" body="工作完成后，结果会自动归到对应项目。" />}</div></section> },
  ]

  return <div className="office-dashboard">
    {demoMode && <div className="demo-banner"><Sparkles size={16} /><span>演示模式：展示完整工作方式，不会影响真实数据。</span></div>}
    <header className="dashboard-hero"><div><span className="eyebrow">我的办公室</span><h1>从一个讲清楚的项目开始。</h1><p>秘书先理解并复述你的意图，再用关键问题补齐上下文。确认后，资料、执行过程和交付物会一直留在项目里。</p></div><button className="primary-button" onClick={() => onOpenPage('projects')}><FolderKanban size={17} />查看全部项目</button></header>
    <div className="dashboard-metrics"><div><strong>{activeProjects}</strong><span>进行中项目</span></div><div><strong>{activeRuns.length}</strong><span>进行中对话</span></div><div><strong>{pendingApprovals.length}</strong><span>待确认事项</span></div><div><strong>{state?.knowledge.company_entries || 0}</strong><span>公司资料</span></div></div>
    <div className="dashboard-secretary"><SecretaryPanel actions={actions} state={state} /></div>
    <div className="dashboard-board-heading"><div><span>项目看板</span><strong>拖动分区可以调整你的办公室</strong></div><small>布局会保存在当前浏览器</small></div>
    <DraggableBoard items={boardItems} storageKey="digital-office-home" />
  </div>
}
