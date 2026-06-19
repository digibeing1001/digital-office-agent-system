import { ArrowRight, CheckCircle2, FolderKanban, Inbox, Sparkles, UploadCloud } from 'lucide-react'
import { displayAgentName, formatTime, statusLabels } from '../../lib/presentation'
import type { AppActions, GuiState } from '../../types'
import { EmptyState, StatusBadge } from '../../components/ui'
import { SecretaryPanel } from './SecretaryPanel'

function activeProjectCount(state: GuiState | null) {
  return (state?.projects.items || []).filter((project) => project.status === 'active').length
}

function projectName(state: GuiState | null, projectId: string) {
  return state?.projects.items.find((project) => project.project_id === projectId)?.name || projectId || '未归属项目'
}

export function OfficePage({
  state,
  actions,
  demoMode,
  onOpenPage,
}: {
  state: GuiState | null
  actions: AppActions
  demoMode: boolean
  onOpenPage: (page: string) => void
}) {
  const activeRuns = (state?.workflows.recent || []).filter((run) => !['completed', 'cancelled', 'stopped'].includes(run.status))
  const pendingApprovals = (state?.approvals.recent || []).filter((approval) => approval.status === 'pending')
  const recentProjects = (state?.projects.items || []).slice(0, 5)
  const recentDeliverables = (state?.tasks.recent || []).filter((task) => ['completed', 'delivered'].includes(task.status)).slice(0, 4)

  return <div className="office-dashboard">
    {demoMode && <div className="demo-banner"><Sparkles size={16} /><span>演示模式：适合给客户或投资人展示完整工作方式，不会影响真实数据。</span></div>}
    <section className="dashboard-main">
      <div className="dashboard-left">
        <header className="dashboard-hero">
          <div>
            <span className="eyebrow">我的办公室</span>
            <h1>今天先看项目，再让秘书安排工作。</h1>
            <p>每个项目都有自己的对话、资料、任务过程和交付物。上下文留在项目里，后面继续做就不会散。</p>
          </div>
          <button className="primary-button" onClick={() => onOpenPage('projects')}><FolderKanban size={17} />查看项目</button>
        </header>
        <div className="dashboard-metrics">
          <div><strong>{activeProjectCount(state)}</strong><span>进行中项目</span></div>
          <div><strong>{activeRuns.length}</strong><span>进行中对话</span></div>
          <div><strong>{pendingApprovals.length}</strong><span>待确认事项</span></div>
          <div><strong>{state?.knowledge.company_entries || 0}</strong><span>公司资料</span></div>
        </div>
        <div className="dashboard-grid">
          <section className="plain-card">
            <header><h2>最近项目</h2><button className="text-button" onClick={() => onOpenPage('projects')}>全部项目 <ArrowRight size={15} /></button></header>
            <div className="project-card-list">
              {recentProjects.map((project) => {
                const knowledge = state?.knowledge.project_entries?.[project.project_id]?.count || 0
                const active = activeRuns.filter((run) => run.project_id === project.project_id).length
                return <button key={project.project_id} onClick={() => onOpenPage('projects')}>
                  <span className="project-icon"><FolderKanban size={17} /></span>
                  <span><strong>{project.name}</strong><small>{active} 个进行中对话 · {knowledge} 份项目资料</small></span>
                </button>
              })}
              {!recentProjects.length && <EmptyState title="还没有项目" body="把第一件事告诉右侧秘书，秘书会帮你新建项目。" />}
            </div>
          </section>
          <section className="plain-card">
            <header><h2>需要你确认</h2><button className="text-button" onClick={() => onOpenPage('projects')}>去项目里处理 <ArrowRight size={15} /></button></header>
            <div className="mini-list">
              {pendingApprovals.slice(0, 4).map((approval) => <article key={approval.approval_id}><Inbox size={16} /><div><strong>{approval.title}</strong><small>{projectName(state, approval.project_id)} · {formatTime(approval.updated_at)}</small></div></article>)}
              {!pendingApprovals.length && <EmptyState title="暂无待确认事项" body="需要你拍板的动作会按项目出现在这里。" />}
            </div>
          </section>
          <section className="plain-card">
            <header><h2>正在进行</h2><button className="text-button" onClick={() => onOpenPage('projects')}>查看项目对话 <ArrowRight size={15} /></button></header>
            <div className="conversation-list">
              {activeRuns.slice(0, 5).map((run) => {
                const agent = state?.digital_employees.items.find((item) => item.agent_id === run.agent_id)
                return <article key={run.run_id}>
                  <span className="conversation-mark"><CheckCircle2 size={16} /></span>
                  <div><strong>{run.title || '未命名对话'}</strong><small>{projectName(state, run.project_id)} · {displayAgentName(agent)} · {statusLabels[run.status] || run.status}</small></div>
                </article>
              })}
              {!activeRuns.length && <EmptyState title="暂无进行中的工作" body="右侧告诉秘书要做什么，秘书会把它放进项目并安排员工。" />}
            </div>
          </section>
          <section className="plain-card">
            <header><h2>最近交付</h2><button className="text-button" onClick={() => onOpenPage('projects')}>按项目查看 <ArrowRight size={15} /></button></header>
            <div className="mini-list">
              {recentDeliverables.map((item) => <article key={item.task_id}><UploadCloud size={16} /><div><strong>{item.title}</strong><small>{projectName(state, item.project_id)} · {formatTime(item.updated_at)}</small></div></article>)}
              {!recentDeliverables.length && <EmptyState title="暂无交付物" body="工作完成后，结果会自动归到对应项目。" />}
            </div>
          </section>
        </div>
      </div>
      <SecretaryPanel actions={actions} state={state} />
    </section>
  </div>
}
