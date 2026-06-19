import { useMemo, useState } from 'react'
import { Archive, ArrowRight, CheckCircle2, FileCheck2, FolderKanban, History, MessageSquarePlus, Plus, ShieldCheck, UploadCloud } from 'lucide-react'
import { EmptyState, Field, Modal, PageHeading, StatusBadge } from '../../components/ui'
import { displayAgentName, formatTime, statusLabels } from '../../lib/presentation'
import type { AppActions, GuiState, ProjectSummary } from '../../types'
import { KnowledgeUploadDialog } from './KnowledgeUploadDialog'
import { SecretaryPanel } from './SecretaryPanel'

function slugSuggestion(value: string) {
  const cleaned = value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fff]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 48)
  return cleaned || 'new-project'
}

function projectTasks(state: GuiState | null, projectId: string) {
  return (state?.workflows.recent || []).filter((run) => run.project_id === projectId)
}

function projectDeliverables(state: GuiState | null, projectId: string) {
  return (state?.tasks.recent || []).filter((task) => task.project_id === projectId && ['completed', 'delivered'].includes(task.status))
}

export function ProjectsPage({ state, actions }: { state: GuiState | null; actions: AppActions }) {
  const projects = state?.projects.items || []
  const [selectedId, setSelectedId] = useState(projects[0]?.project_id || '')
  const [selectedConversationId, setSelectedConversationId] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [showUpload, setShowUpload] = useState(false)
  const selected = projects.find((project) => project.project_id === selectedId) || projects[0]

  return <div className="standard-page projects-page">
    <PageHeading title="项目" description="每一件正式工作都放进一个项目里。项目会保存对话、资料、任务过程和交付物，后面继续做时不会丢上下文。" action={<button className="primary-button" onClick={() => setShowCreate(true)}><Plus size={17} />新建项目</button>} />
    <div className="projects-layout">
      <section className="project-list-panel">
        <header><span>{projects.length} 个项目</span><button className="text-button" onClick={() => setShowCreate(true)}>新建</button></header>
        {projects.map((project) => {
          const knowledge = state?.knowledge.project_entries?.[project.project_id]?.count || 0
          const active = projectTasks(state, project.project_id).filter((run) => !['completed', 'cancelled', 'stopped'].includes(run.status)).length
          return <button className={project.project_id === selected?.project_id ? 'project-list-item active' : 'project-list-item'} key={project.project_id} onClick={() => setSelectedId(project.project_id)}>
            <span className="project-icon"><FolderKanban size={17} /></span>
            <span><strong>{project.name}</strong><small>{active} 个进行中对话 · {knowledge} 份资料</small></span>
          </button>
        })}
        {!projects.length && <EmptyState title="还没有项目" body="先把想做的事告诉秘书，秘书会帮你建一个项目。" />}
      </section>
      {selected ? <ProjectDetail actions={actions} onOpenConversation={setSelectedConversationId} onUpload={() => setShowUpload(true)} project={selected} selectedConversationId={selectedConversationId} state={state} /> : <section className="project-empty-panel"><EmptyState title="请选择一个项目" body="项目会把相关对话、资料和交付物放在一起。" /></section>}
    </div>
    {showCreate && <CreateProjectDialog actions={actions} onClose={() => setShowCreate(false)} onCreated={(projectId) => { setSelectedId(projectId); setShowCreate(false) }} />}
    {showUpload && selected && <KnowledgeUploadDialog actions={actions} defaultProjectId={selected.project_id} defaultScope="project" onClose={() => setShowUpload(false)} state={state} />}
  </div>
}

function ProjectDetail({ project, state, actions, onUpload, selectedConversationId, onOpenConversation }: { project: ProjectSummary; state: GuiState | null; actions: AppActions; onUpload: () => void; selectedConversationId: string; onOpenConversation: (runId: string) => void }) {
  const conversations = projectTasks(state, project.project_id)
  const entries = state?.knowledge.project_entries?.[project.project_id]?.items || []
  const deliverables = projectDeliverables(state, project.project_id)
  const approvals = (state?.approvals.recent || []).filter((item) => item.project_id === project.project_id)
  const records = (state?.audit.recent || []).filter((item) => item.project_id === project.project_id).slice(-8).reverse()
  const roster = project.agent_roster
    .map((agentId) => state?.digital_employees.items.find((agent) => agent.agent_id === agentId))
    .filter(Boolean)

  const openedConversation = conversations.find((run) => run.run_id === selectedConversationId)

  return <section className="project-detail-panel">
    <div className="project-detail-grid">
      <div className="project-main">
        <div className="project-hero">
          <div>
            <StatusBadge tone={project.status === 'active' ? 'green' : 'gray'}>{project.status === 'active' ? '进行中' : project.status}</StatusBadge>
            <h2>{project.name}</h2>
            <p>项目编号：{project.project_id} · 最近更新 {formatTime(project.updated_at)}</p>
          </div>
          <div className="project-actions">
            <button className="secondary-button" onClick={onUpload}><UploadCloud size={17} />上传资料</button>
          </div>
        </div>
        <div className="project-stats">
          <div><strong>{conversations.length}</strong><span>项目对话</span></div>
          <div><strong>{entries.length}</strong><span>项目资料</span></div>
          <div><strong>{approvals.length}</strong><span>审批</span></div>
          <div><strong>{deliverables.length}</strong><span>交付物</span></div>
        </div>
        {openedConversation ? <ConversationView run={openedConversation} state={state} onBack={() => onOpenConversation('')} /> : <div className="project-sections">
          <section className="plain-card">
            <header><h3>项目对话</h3><span>每条对话都是一条独立任务线</span></header>
            <div className="conversation-list">
              {conversations.map((run) => {
                const agent = state?.digital_employees.items.find((item) => item.agent_id === run.agent_id)
                return <button className="conversation-button" key={run.run_id} onClick={() => onOpenConversation(run.run_id)}>
                  <span className="conversation-mark"><MessageSquarePlus size={16} /></span>
                  <div><strong>{run.title || '未命名对话'}</strong><small>{displayAgentName(agent)} · {statusLabels[run.status] || run.status} · {formatTime(run.updated_at)}</small></div>
                </button>
              })}
              {!conversations.length && <EmptyState title="还没有项目对话" body="在右侧告诉秘书下一步要做什么，秘书会开启新的项目对话。" />}
            </div>
          </section>
          <section className="plain-card">
            <header><h3>项目资料</h3><button className="text-button" onClick={onUpload}>上传资料 <UploadCloud size={15} /></button></header>
            <div className="knowledge-mini-list">
              {entries.map((entry) => <article key={entry.entry_id}><span className="file-symbol"><Archive size={16} /></span><div><strong>{entry.title}</strong><small>{entry.kind || '资料'} · {entry.status === 'approved_for_agent_use' ? '可直接使用' : '待确认'}</small></div></article>)}
              {!entries.length && <EmptyState title="还没有项目资料" body="把需求、合同、会议记录、截图等放进来，秘书和数字员工会更懂这个项目。" />}
            </div>
          </section>
          <section className="plain-card compact-card">
            <header><h3>审批</h3><span>需要你确认的事项</span></header>
            <div className="mini-list">
              {approvals.map((item) => <article key={item.approval_id}><ShieldCheck size={16} /><div><strong>{item.title}</strong><small>{statusLabels[item.status] || item.status} · {formatTime(item.updated_at)}</small></div></article>)}
              {!approvals.length && <EmptyState title="暂无审批" body="高风险动作会在这里等待你确认。" />}
            </div>
          </section>
          <section className="plain-card compact-card">
            <header><h3>交付物</h3><span>完成后自动归档</span></header>
            <div className="mini-list">
              {deliverables.map((item) => <article key={item.task_id}><FileCheck2 size={16} /><div><strong>{item.title}</strong><small>{formatTime(item.updated_at)}</small></div></article>)}
              {!deliverables.length && <EmptyState title="暂无交付物" body="任务完成后会在这里沉淀结果。" />}
            </div>
          </section>
          <section className="plain-card full-card">
            <header><h3>工作记录</h3><span>项目过程留痕</span></header>
            <div className="mini-list">
              {records.map((item, index) => <article key={String(item.event_id || index)}><History size={16} /><div><strong>{String(item.event || '工作记录')}</strong><small>{String(item.outcome || 'recorded')} · {formatTime(String(item.time || ''))}</small></div></article>)}
              {!records.length && <EmptyState title="暂无工作记录" body="开始项目对话后，关键过程会自动留下记录。" />}
            </div>
          </section>
        </div>}
      </div>
      <div className="project-chat">
        <SecretaryPanel actions={actions} compact fixedProject={project} state={state} />
      </div>
    </div>
  </section>
}

function ConversationView({ run, state, onBack }: { run: ReturnType<typeof projectTasks>[number]; state: GuiState | null; onBack: () => void }) {
  const agent = state?.digital_employees.items.find((item) => item.agent_id === run.agent_id)
  const runtime = state?.runtime_replay.recent_runs.find((item) => item.run_id === run.run_id)
  const relatedTasks = (state?.tasks.recent || []).filter((task) => task.workflow_run_id === run.run_id)

  return <section className="plain-card conversation-view">
    <header><div><h3>{run.title || '项目对话'}</h3><span>{displayAgentName(agent)} · {statusLabels[run.status] || run.status}</span></div><button className="text-button" onClick={onBack}>返回项目看板</button></header>
    <div className="conversation-body">
      <div className="chat-bubble user">我把这项工作交给秘书，并要求放进当前项目。</div>
      <div className="chat-bubble secretary">秘书已经理解目标，并把工作安排给 {displayAgentName(agent)}。资料、过程和交付物都会保存在这个项目里。</div>
      {runtime && <div className="conversation-progress">
        <span>当前进展</span>
        <strong>{runtime.current_stage || '处理中'}</strong>
        <small>{runtime.checkpoints} 个检查点 · {runtime.handoffs} 次工作接力</small>
      </div>}
      {relatedTasks.map((task) => <div className="chat-bubble system" key={task.task_id}>{task.title} · {statusLabels[task.status] || task.status}</div>)}
    </div>
  </section>
}

function CreateProjectDialog({ actions, onClose, onCreated }: { actions: AppActions; onClose: () => void; onCreated: (projectId: string) => void }) {
  const [brief, setBrief] = useState('')
  const [name, setName] = useState('')
  const [projectId, setProjectId] = useState('')
  const [error, setError] = useState('')
  const suggestedName = name.trim() || brief.trim().slice(0, 24) || '新项目'
  const suggestedId = projectId.trim() || slugSuggestion(suggestedName)

  const create = async (event: React.FormEvent) => {
    event.preventDefault()
    setError('')
    if (!brief.trim() && !name.trim()) {
      setError('先简单说一下这个项目要做什么。')
      return
    }
    const result = await actions.createProject({ name: suggestedName, project_id: suggestedId })
    const createdProject = result.project as { project_id?: string } | undefined
    onCreated(createdProject?.project_id || suggestedId)
  }

  return <Modal title="和秘书一起新建项目" onClose={onClose} footer={<><button className="secondary-button" onClick={onClose}>取消</button><button className="primary-button" form="create-project-form" type="submit"><CheckCircle2 size={17} />创建项目</button></>}>
    <form className="form-grid project-create-form" id="create-project-form" onSubmit={create}>
      <Field label="先告诉秘书，这个项目要做什么">
        <textarea rows={4} value={brief} onChange={(event) => { setBrief(event.target.value); if (!name) setName(event.target.value.slice(0, 24)) }} placeholder="例如：帮我准备 A 客户的投标方案，需要整理需求、上传资料、安排写作和法务检查。" />
      </Field>
      <Field label="项目名称">
        <input value={name} onChange={(event) => setName(event.target.value)} placeholder={suggestedName} />
      </Field>
      <Field label="项目编号" hint="用于保存项目文件夹，后续资料、对话和交付物都会归到这里。">
        <input value={projectId} onChange={(event) => setProjectId(event.target.value.toLowerCase())} placeholder={suggestedId} />
      </Field>
      <div className="secretary-tip"><strong>秘书会先做什么？</strong><span>创建项目文件夹，等待你上传关键资料，然后在项目里开启第一条对话。</span></div>
      {error && <p className="form-error">{error}</p>}
    </form>
  </Modal>
}
