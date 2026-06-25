import { useEffect, useRef, useState } from 'react'
import { Archive, ArrowLeft, CheckCircle2, FileCheck2, FileText, FolderKanban, History, MessageSquarePlus, Plus, Settings, ShieldCheck, UploadCloud, Users, Clock, FileSpreadsheet, FileImage, File, Package, ChevronRight, Bot, Loader2 } from 'lucide-react'
import { EmptyState, Field, Modal, PageHeading, StatusBadge } from '../../components/ui'
import { displayAgentName, formatTime, statusLabels } from '../../lib/presentation'
import type { AppActions, GuiState, ProjectSummary } from '../../types'
import { KnowledgeUploadDialog } from './KnowledgeUploadDialog'
import { SecretaryPanel } from './SecretaryPanel'

/* ── helpers ── */

function slugSuggestion(value: string) {
  const cleaned = value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9一-鿿]+/g, '-')
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

/** Derive a completion percentage from conversations */
function projectProgress(state: GuiState | null, projectId: string) {
  const tasks = projectTasks(state, projectId)
  if (!tasks.length) return 0
  const done = tasks.filter((t) => ['completed', 'cancelled', 'stopped'].includes(t.status)).length
  return Math.round((done / tasks.length) * 100)
}

/** Map file kind to a coloured icon */
function fileKindIcon(kind: string) {
  const k = (kind || '').toLowerCase()
  if (k.includes('sheet') || k.includes('excel') || k.includes('csv')) return { Icon: FileSpreadsheet, color: '#16a34a' }
  if (k.includes('image') || k.includes('img') || k.includes('pdf') || k.includes('screenshot')) return { Icon: FileImage, color: '#9333ea' }
  if (k.includes('doc') || k.includes('word') || k.includes('text') || k.includes('contract') || k.includes('需求') || k.includes('合同')) return { Icon: FileText, color: '#2563eb' }
  return { Icon: File, color: '#64748b' }
}

/** Map conversation status to a left-border colour */
function statusBorderColor(status: string) {
  if (status === 'completed') return '#16a34a'
  if (status === 'running' || status === 'active') return '#2563eb'
  if (status === 'failed' || status === 'error') return '#dc2626'
  if (status === 'waiting' || status === 'pending') return '#d97706'
  return '#94a3b8'
}

/** Avatar colour palette for team members */
const avatarColors = ['#2563eb', '#16a34a', '#9333ea', '#d97706', '#dc2626', '#0891b2', '#c026d3', '#4f46e5']

function avatarColor(index: number) {
  return avatarColors[index % avatarColors.length]
}

/* ── Main Page ── */

export function ProjectsPage({ state, actions, selectedId, selectedConversationId, onSelectProject, onOpenConversation, createProjectKey }: { state: GuiState | null; actions: AppActions; selectedId: string; selectedConversationId: string; onSelectProject: (projectId: string) => void; onOpenConversation: (conversationId: string) => void; createProjectKey: number }) {
  const projects = state?.projects.items || []
  const [showCreate, setShowCreate] = useState(false)
  const [showUpload, setShowUpload] = useState(false)
  const selected = projects.find((project) => project.project_id === selectedId)

  useEffect(() => {
    if (createProjectKey > 0) setShowCreate(true)
  }, [createProjectKey])

  return <div className="standard-page projects-page">
    <PageHeading title="项目" description="每一件正式工作都放进一个项目里。项目会保存对话、资料、任务过程和交付物，后面继续做时不会丢上下文。" action={<button className="primary-button" onClick={() => setShowCreate(true)}><Plus size={17} />新建项目</button>} />
    <div className="projects-layout">
      {/* ── Project List Panel ── */}
      <section className="project-list-panel">
        <header><span>{projects.length} 个项目</span><button className="text-button" onClick={() => setShowCreate(true)}>新建</button></header>
        {projects.map((project) => {
          const knowledge = state?.knowledge.project_entries?.[project.project_id]?.count || 0
          const active = projectTasks(state, project.project_id).filter((run) => !['completed', 'cancelled', 'stopped'].includes(run.status)).length
          const progress = projectProgress(state, project.project_id)
          const isActive = project.project_id === selected?.project_id
          const rosterAgents = project.agent_roster
            .map((agentId) => state?.digital_employees.items.find((agent) => agent.agent_id === agentId))
            .filter(Boolean)
          return (
            <button
              className={isActive ? 'project-list-item active' : 'project-list-item'}
              key={project.project_id}
              onClick={() => onSelectProject(project.project_id)}
              style={{ position: 'relative', overflow: 'hidden' }}
            >
              {/* Coloured status indicator */}
              <span style={{
                position: 'absolute', left: 0, top: 0, bottom: 0, width: 4,
                background: project.status === 'active' ? '#16a34a' : '#94a3b8',
              }} />

              <span className="project-icon" style={{
                background: project.status === 'active' ? 'var(--green-soft)' : '#f1f5f9',
                color: project.status === 'active' ? 'var(--green)' : '#94a3b8',
              }}>
                <FolderKanban size={17} />
              </span>

              <span style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 4 }}>
                <strong style={{ display: 'block', fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{project.name}</strong>
                <small style={{ display: 'block', color: 'var(--muted)', fontSize: 10 }}>{active} 个进行中对话 · {knowledge} 份资料</small>

                {/* Progress bar */}
                <div style={{
                  height: 3, borderRadius: 2, background: '#e2e8f0', overflow: 'hidden', marginTop: 2,
                }}>
                  <div style={{
                    height: '100%', borderRadius: 2,
                    width: `${progress}%`,
                    background: progress === 100 ? '#16a34a' : 'var(--green)',
                    transition: 'width 0.3s ease',
                  }} />
                </div>
              </span>

              {/* Team member avatars row */}
              {rosterAgents.length > 0 && (
                <span style={{ display: 'flex', flexShrink: 0, marginLeft: 4 }}>
                  {rosterAgents.slice(0, 3).map((agent, i) => (
                    <span key={agent?.agent_id || i} style={{
                      width: 22, height: 22, borderRadius: '50%',
                      background: avatarColor(i), color: '#fff',
                      display: 'grid', placeItems: 'center', fontSize: 9, fontWeight: 600,
                      marginLeft: i > 0 ? -6 : 0,
                      border: '2px solid var(--surface)',
                      position: 'relative' as const,
                    }} title={agent ? displayAgentName(agent) : ''}>
                      {(agent ? displayAgentName(agent) : '?')[0]}
                    </span>
                  ))}
                  {rosterAgents.length > 3 && (
                    <span style={{
                      width: 22, height: 22, borderRadius: '50%',
                      background: '#f1f5f9', color: '#64748b',
                      display: 'grid', placeItems: 'center', fontSize: 8, fontWeight: 600,
                      marginLeft: -6,
                      border: '2px solid var(--surface)',
                    }}>+{rosterAgents.length - 3}</span>
                  )}
                </span>
              )}

              {/* Last updated timestamp */}
              <small style={{ flexShrink: 0, color: 'var(--muted)', fontSize: 9, marginLeft: 4 }}>
                {formatTime(project.updated_at)}
              </small>

              {/* Hover slide-in chevron */}
              <span className="project-hover-actions" style={{
                position: 'absolute', right: -60, top: '50%', transform: 'translateY(-50%)',
                display: 'flex', gap: 4, transition: 'right 0.2s ease',
              }}>
                <ChevronRight size={14} style={{ color: 'var(--muted)' }} />
              </span>

              <style>{`
                .project-list-item:hover .project-hover-actions { right: 8px !important; }
              `}</style>
            </button>
          )
        })}
        {!projects.length && <EmptyState title="还没有项目" body="先把想做的事告诉秘书，秘书会帮你建一个项目。" />}
      </section>

      {selected ? <ProjectDetail actions={actions} onOpenConversation={onOpenConversation} onUpload={() => setShowUpload(true)} project={selected} selectedConversationId={selectedConversationId} state={state} /> : <section className="project-empty-panel"><EmptyState title="请选择一个项目" body="从左侧项目列表或侧边栏进入，项目会把相关对话、资料和交付物放在一起。" /></section>}
    </div>
    {showCreate && <CreateProjectDialog actions={actions} onClose={() => setShowCreate(false)} onCreated={(projectId) => { onSelectProject(projectId); setShowCreate(false) }} />}
    {showUpload && selected && <KnowledgeUploadDialog actions={actions} defaultProjectId={selected.project_id} defaultScope="project" onClose={() => setShowUpload(false)} state={state} />}
  </div>
}

/* ── Project Detail ── */

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
  const progress = projectProgress(state, project.project_id)

  return <section className="project-detail-panel">
    <div className="project-detail-grid">
      <div className="project-main">
        {/* ── Enhanced Hero Section ── */}
        <div className="project-hero" style={{ position: 'relative', overflow: 'hidden' }}>
          {/* Gradient accent bar */}
          <div style={{
            position: 'absolute', top: 0, left: 0, right: 0, height: 4,
            background: project.status === 'active'
              ? 'linear-gradient(90deg, #16a34a, #0891b2)'
              : 'linear-gradient(90deg, #94a3b8, #cbd5e1)',
          }} />
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <StatusBadge tone={project.status === 'active' ? 'green' : 'gray'}>{project.status === 'active' ? '进行中' : project.status}</StatusBadge>
              {/* Team roster avatars */}
              {roster.length > 0 && (
                <span style={{ display: 'flex', alignItems: 'center' }}>
                  {roster.slice(0, 5).map((agent, i) => (
                    <span key={agent?.agent_id || i} style={{
                      width: 26, height: 26, borderRadius: '50%',
                      background: avatarColor(i), color: '#fff',
                      display: 'grid', placeItems: 'center', fontSize: 10, fontWeight: 600,
                      marginLeft: i > 0 ? -7 : 0,
                      border: '2px solid #fff',
                      position: 'relative' as const,
                    }} title={agent ? displayAgentName(agent) : ''}>
                      {(agent ? displayAgentName(agent) : '?')[0]}
                    </span>
                  ))}
                  {roster.length > 5 && (
                    <span style={{
                      width: 26, height: 26, borderRadius: '50%',
                      background: '#f1f5f9', color: '#64748b',
                      display: 'grid', placeItems: 'center', fontSize: 9, fontWeight: 600,
                      marginLeft: -7, border: '2px solid #fff',
                    }}>+{roster.length - 5}</span>
                  )}
                </span>
              )}
            </div>
            <h2 style={{ marginTop: 4, fontSize: 24, fontWeight: 700 }}>{project.name}</h2>
            <p style={{ marginTop: 2, color: 'var(--muted)', fontSize: 12 }}>
              项目编号：{project.project_id} · 最近更新 {formatTime(project.updated_at)}
            </p>
          </div>

          {/* Progress ring + action buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexShrink: 0 }}>
            {/* SVG Progress ring */}
            <div style={{ position: 'relative', width: 56, height: 56 }}>
              <svg width="56" height="56" viewBox="0 0 56 56" style={{ transform: 'rotate(-90deg)' }}>
                <circle cx="28" cy="28" r="24" fill="none" stroke="#e2e8f0" strokeWidth="4" />
                <circle cx="28" cy="28" r="24" fill="none"
                  stroke={progress === 100 ? '#16a34a' : '#2563eb'}
                  strokeWidth="4" strokeLinecap="round"
                  strokeDasharray={`${(progress / 100) * 150.8} 150.8`}
                  style={{ transition: 'stroke-dasharray 0.6s ease' }}
                />
              </svg>
              <span style={{
                position: 'absolute', inset: 0, display: 'grid', placeItems: 'center',
                fontSize: 13, fontWeight: 700, color: progress === 100 ? '#16a34a' : '#2563eb',
              }}>{progress}%</span>
            </div>

            <div className="project-actions" style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <button className="secondary-button" onClick={onUpload} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, padding: '6px 12px' }}>
                <UploadCloud size={15} />上传资料
              </button>
              <button className="secondary-button" style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, padding: '6px 12px', opacity: 0.7 }}>
                <Settings size={15} />项目设置
              </button>
            </div>
          </div>
        </div>

        {/* ── Stats Section with Icons & Colored Backgrounds ── */}
        <div className="project-stats" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
          <div style={{
            display: 'grid', gap: 8, padding: '16px 14px', borderRadius: 10,
            background: 'linear-gradient(135deg, #eff6ff, #dbeafe)',
            border: '1px solid #bfdbfe', position: 'relative', overflow: 'hidden',
          }}>
            <span style={{
              position: 'absolute', right: 10, top: 10, width: 32, height: 32,
              borderRadius: 8, background: 'rgba(37,99,235,0.12)', color: '#2563eb',
              display: 'grid', placeItems: 'center',
            }}><MessageSquarePlus size={16} /></span>
            <strong style={{ fontSize: 22, fontVariantNumeric: 'tabular-nums', color: '#1e40af' }}>{conversations.length}</strong>
            <span style={{ color: '#3b82f6', fontSize: 11 }}>项目对话</span>
          </div>

          <div style={{
            display: 'grid', gap: 8, padding: '16px 14px', borderRadius: 10,
            background: 'linear-gradient(135deg, #f0fdf4, #dcfce7)',
            border: '1px solid #bbf7d0', position: 'relative', overflow: 'hidden',
          }}>
            <span style={{
              position: 'absolute', right: 10, top: 10, width: 32, height: 32,
              borderRadius: 8, background: 'rgba(22,163,74,0.12)', color: '#16a34a',
              display: 'grid', placeItems: 'center',
            }}><Archive size={16} /></span>
            <strong style={{ fontSize: 22, fontVariantNumeric: 'tabular-nums', color: '#166534' }}>{entries.length}</strong>
            <span style={{ color: '#22c55e', fontSize: 11 }}>项目资料</span>
          </div>

          <div style={{
            display: 'grid', gap: 8, padding: '16px 14px', borderRadius: 10,
            background: 'linear-gradient(135deg, #fffbeb, #fef3c7)',
            border: '1px solid #fde68a', position: 'relative', overflow: 'hidden',
          }}>
            <span style={{
              position: 'absolute', right: 10, top: 10, width: 32, height: 32,
              borderRadius: 8, background: 'rgba(217,119,6,0.12)', color: '#d97706',
              display: 'grid', placeItems: 'center',
            }}><ShieldCheck size={16} /></span>
            <strong style={{ fontSize: 22, fontVariantNumeric: 'tabular-nums', color: '#92400e' }}>{approvals.length}</strong>
            <span style={{ color: '#f59e0b', fontSize: 11 }}>审批</span>
          </div>

          <div style={{
            display: 'grid', gap: 8, padding: '16px 14px', borderRadius: 10,
            background: 'linear-gradient(135deg, #faf5ff, #f3e8ff)',
            border: '1px solid #e9d5ff', position: 'relative', overflow: 'hidden',
          }}>
            <span style={{
              position: 'absolute', right: 10, top: 10, width: 32, height: 32,
              borderRadius: 8, background: 'rgba(147,51,234,0.12)', color: '#9333ea',
              display: 'grid', placeItems: 'center',
            }}><Package size={16} /></span>
            <strong style={{ fontSize: 22, fontVariantNumeric: 'tabular-nums', color: '#6b21a8' }}>{deliverables.length}</strong>
            <span style={{ color: '#a855f7', fontSize: 11 }}>交付物</span>
          </div>
        </div>

        {openedConversation ? <ConversationView run={openedConversation} state={state} onBack={() => onOpenConversation('')} /> : <div className="project-sections">
          {/* ── Conversation List ── */}
          <section className="plain-card">
            <header><h3>项目对话</h3><span>每条对话都是一条独立任务线</span></header>
            <div className="conversation-list">
              {conversations.map((run) => {
                const agent = state?.digital_employees.items.find((item) => item.agent_id === run.agent_id)
                const borderColor = statusBorderColor(run.status)
                const isActive = ['running', 'active'].includes(run.status)
                return <button className="conversation-button" key={run.run_id} onClick={() => onOpenConversation(run.run_id)}
                  style={{
                    borderLeft: `3px solid ${borderColor}`,
                    paddingLeft: 11,
                    display: 'flex', alignItems: 'center', gap: 12, width: '100%',
                    minHeight: 64, padding: '11px 14px 11px 11px',
                    border: 0, borderBottom: '1px solid var(--line)',
                    background: 'transparent', textAlign: 'left', cursor: 'pointer',
                    borderLeftWidth: 3, borderLeftStyle: 'solid', borderLeftColor: borderColor,
                    transition: 'background 0.15s ease',
                  }}>
                  {/* Agent avatar with status indicator */}
                  <span style={{
                    width: 34, height: 34, borderRadius: '50%', flexShrink: 0,
                    background: isActive ? 'linear-gradient(135deg, #2563eb, #0891b2)' : '#f1f5f9',
                    color: isActive ? '#fff' : '#64748b',
                    display: 'grid', placeItems: 'center',
                    position: 'relative' as const,
                  }}>
                    <Bot size={16} />
                    {isActive && (
                      <span style={{
                        position: 'absolute', bottom: -1, right: -1,
                        width: 10, height: 10, borderRadius: '50%',
                        background: '#16a34a', border: '2px solid #fff',
                      }} />
                    )}
                  </span>

                  <div style={{ flex: 1, minWidth: 0 }}>
                    <strong style={{ display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 12 }}>{run.title || '未命名对话'}</strong>
                    <small style={{ display: 'block', marginTop: 4, color: 'var(--muted)', fontSize: 10 }}>
                      {displayAgentName(agent)} · {statusLabels[run.status] || run.status}
                    </small>
                  </div>

                  {/* Progress spinner for active tasks */}
                  {isActive && (
                    <Loader2 size={14} style={{ color: '#2563eb', animation: 'spin 1s linear infinite', flexShrink: 0 }} />
                  )}

                  {/* Timestamp */}
                  <small style={{ flexShrink: 0, color: 'var(--muted)', fontSize: 9 }}>
                    {formatTime(run.updated_at)}
                  </small>
                </button>
              })}
              {!conversations.length && <EmptyState title="还没有项目对话" body="在右侧告诉秘书下一步要做什么，秘书会开启新的项目对话。" />}
            </div>
          </section>

          {/* ── Materials Section ── */}
          <section className="plain-card">
            <header><h3>项目资料</h3><button className="text-button" onClick={onUpload}>上传资料 <UploadCloud size={15} /></button></header>
            <div className="knowledge-mini-list">
              {entries.map((entry) => {
                const { Icon, color } = fileKindIcon(entry.kind || '')
                const isApproved = entry.status === 'approved_for_agent_use'
                return (
                  <article key={entry.entry_id} style={{
                    display: 'flex', alignItems: 'center', gap: 12,
                    minHeight: 64, padding: '11px 14px',
                    borderBottom: '1px solid var(--line)',
                  }}>
                    {/* File type icon with colour */}
                    <span style={{
                      width: 36, height: 36, borderRadius: 8, flexShrink: 0,
                      background: `${color}14`, color: color,
                      display: 'grid', placeItems: 'center',
                    }}>
                      <Icon size={16} />
                    </span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <strong style={{ display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 12 }}>{entry.title}</strong>
                      <small style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4, color: 'var(--muted)', fontSize: 10 }}>
                        <span>{entry.kind || '资料'}</span>
                        {/* Status badge */}
                        <span style={{
                          display: 'inline-flex', alignItems: 'center', gap: 3,
                          padding: '1px 6px', borderRadius: 4, fontSize: 9, fontWeight: 600,
                          background: isApproved ? '#dcfce7' : '#fef3c7',
                          color: isApproved ? '#166534' : '#92400e',
                        }}>
                          {isApproved ? '可直接使用' : '待确认'}
                        </span>
                      </small>
                    </div>
                  </article>
                )
              })}
              {!entries.length && <EmptyState title="还没有项目资料" body="把需求、合同、会议记录、截图等放进来，秘书和数字员工会更懂这个项目。" />}
            </div>
          </section>

          {/* ── Approvals ── */}
          <section className="plain-card compact-card">
            <header><h3>审批</h3><span>需要你确认的事项</span></header>
            <div className="mini-list">
              {approvals.map((item) => <article key={item.approval_id}><ShieldCheck size={16} /><div><strong>{item.title}</strong><small>{statusLabels[item.status] || item.status} · {formatTime(item.updated_at)}</small></div></article>)}
              {!approvals.length && <EmptyState title="暂无审批" body="高风险动作会在这里等待你确认。" />}
            </div>
          </section>

          {/* ── Deliverables ── */}
          <section className="plain-card compact-card">
            <header><h3>交付物</h3><span>完成后自动归档</span></header>
            <div className="mini-list">
              {deliverables.map((item) => <article key={item.task_id}><FileCheck2 size={16} /><div><strong>{item.title}</strong><small>{formatTime(item.updated_at)}</small></div></article>)}
              {!deliverables.length && <EmptyState title="暂无交付物" body="任务完成后会在这里沉淀结果。" />}
            </div>
          </section>

          {/* ── Work Records ── */}
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

/* ── Conversation View ── */

function ConversationView({ run, state, onBack }: { run: ReturnType<typeof projectTasks>[number]; state: GuiState | null; onBack: () => void }) {
  const agent = state?.digital_employees.items.find((item) => item.agent_id === run.agent_id)
  const runtime = state?.runtime_replay.recent_runs.find((item) => item.run_id === run.run_id)
  const relatedTasks = (state?.tasks.recent || []).filter((task) => task.workflow_run_id === run.run_id)
  const bodyRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const body = bodyRef.current
    if (body) body.scrollTo({ top: body.scrollHeight, behavior: 'smooth' })
  }, [relatedTasks.length, runtime?.current_stage, run.status])

  const isActive = ['running', 'active'].includes(run.status)

  return <section className="plain-card conversation-view">
    <header style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
      padding: '0 16px', minHeight: 54, borderBottom: '1px solid var(--line)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        {/* Agent avatar */}
        <span style={{
          width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
          background: isActive ? 'linear-gradient(135deg, #2563eb, #0891b2)' : '#f1f5f9',
          color: isActive ? '#fff' : '#64748b',
          display: 'grid', placeItems: 'center',
        }}>
          <Bot size={15} />
        </span>
        <div style={{ display: 'grid', gap: 2 }}>
          <h3 style={{ fontSize: 14, fontWeight: 600 }}>{run.title || '项目对话'}</h3>
          <span style={{ color: 'var(--muted)', fontSize: 11 }}>
            {displayAgentName(agent)} · {statusLabels[run.status] || run.status}
            {isActive && <Loader2 size={11} style={{ display: 'inline-block', marginLeft: 4, verticalAlign: 'middle', animation: 'spin 1s linear infinite' }} />}
          </span>
        </div>
      </div>
      <button className="secondary-button conversation-back" onClick={onBack}><ArrowLeft size={16} />返回项目看板</button>
    </header>

    <div className="conversation-body" ref={bodyRef}>
      {/* User message bubble */}
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <div className="chat-bubble user" style={{
          maxWidth: '75%', padding: '10px 14px', borderRadius: 12,
          background: 'var(--green)', color: '#fff', borderTopRightRadius: 4,
          fontSize: 13, lineHeight: 1.65,
          boxShadow: '0 1px 2px rgba(0,0,0,0.06)',
        }}>
          我把这项工作交给秘书，并要求放进当前项目。
        </div>
      </div>

      {/* Secretary response bubble with avatar */}
      <div style={{ display: 'flex', justifyContent: 'flex-start', alignItems: 'flex-end', gap: 8 }}>
        <span style={{
          width: 24, height: 24, borderRadius: '50%', flexShrink: 0,
          background: 'var(--green-soft)', color: 'var(--green)',
          display: 'grid', placeItems: 'center',
        }}>
          <Bot size={12} />
        </span>
        <div className="chat-bubble secretary" style={{
          maxWidth: '75%', padding: '10px 14px', borderRadius: 12,
          background: 'var(--surface-soft)', color: 'var(--ink)', borderTopLeftRadius: 4,
          fontSize: 13, lineHeight: 1.65,
          boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
        }}>
          秘书已经理解目标，并把工作安排给 {displayAgentName(agent)}。资料、过程和交付物都会保存在这个项目里。
        </div>
      </div>

      {/* Progress tracker card */}
      {runtime && (
        <div style={{
          alignSelf: 'stretch', borderRadius: 12, overflow: 'hidden',
          border: '1px solid var(--line)', background: '#fff',
          boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
        }}>
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '10px 14px', background: 'linear-gradient(135deg, #eff6ff, #f0f9ff)',
            borderBottom: '1px solid var(--line)',
          }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: '#3b82f6', fontWeight: 600 }}>
              <Clock size={13} />当前进展
            </span>
            {isActive && <Loader2 size={13} style={{ color: '#2563eb', animation: 'spin 1s linear infinite' }} />}
          </div>
          <div style={{ padding: '12px 14px', display: 'grid', gap: 8 }}>
            <strong style={{ fontSize: 14, color: '#1e40af' }}>{runtime.current_stage || '处理中'}</strong>
            <div style={{ display: 'flex', gap: 16 }}>
              <span style={{
                display: 'flex', alignItems: 'center', gap: 4,
                fontSize: 11, color: 'var(--muted)',
                padding: '3px 8px', borderRadius: 6, background: '#f8fafc',
              }}>
                <CheckCircle2 size={12} color="#16a34a" />
                {runtime.checkpoints} 个检查点
              </span>
              <span style={{
                display: 'flex', alignItems: 'center', gap: 4,
                fontSize: 11, color: 'var(--muted)',
                padding: '3px 8px', borderRadius: 6, background: '#f8fafc',
              }}>
                <Users size={12} color="#2563eb" />
                {runtime.handoffs} 次工作接力
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Task status cards */}
      {relatedTasks.map((task) => {
        const taskDone = ['completed', 'delivered'].includes(task.status)
        const taskActive = ['running', 'active'].includes(task.status)
        const taskFailed = ['failed', 'error'].includes(task.status)
        return (
          <div key={task.task_id} style={{
            alignSelf: 'stretch', borderRadius: 10, overflow: 'hidden',
            border: `1px solid ${taskDone ? '#bbf7d0' : taskFailed ? '#fecaca' : 'var(--line)'}`,
            background: taskDone ? '#f0fdf4' : taskFailed ? '#fef2f2' : '#fff',
            display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px',
            boxShadow: '0 1px 2px rgba(0,0,0,0.03)',
          }}>
            <span style={{
              width: 28, height: 28, borderRadius: 6, flexShrink: 0,
              background: taskDone ? '#dcfce7' : taskFailed ? '#fee2e2' : taskActive ? '#dbeafe' : '#f1f5f9',
              color: taskDone ? '#16a34a' : taskFailed ? '#dc2626' : taskActive ? '#2563eb' : '#64748b',
              display: 'grid', placeItems: 'center',
            }}>
              {taskDone ? <CheckCircle2 size={14} /> : taskActive ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <FileCheck2 size={14} />}
            </span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <strong style={{ display: 'block', fontSize: 12, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{task.title}</strong>
            </div>
            <span style={{
              flexShrink: 0, fontSize: 10, fontWeight: 600, padding: '2px 8px', borderRadius: 4,
              background: taskDone ? '#dcfce7' : taskFailed ? '#fee2e2' : taskActive ? '#dbeafe' : '#f1f5f9',
              color: taskDone ? '#166534' : taskFailed ? '#991b1b' : taskActive ? '#1e40af' : '#64748b',
            }}>
              {statusLabels[task.status] || task.status}
            </span>
          </div>
        )
      })}
    </div>
  </section>
}

/* ── Create Project Dialog ── */

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
    const result = await actions.createProject({ name: suggestedName, project_id: suggestedId, brief: brief.trim() })
    const createdProject = result.project as { project_id?: string } | undefined
    onCreated(createdProject?.project_id || suggestedId)
  }

  const templates = [
    { label: '投标方案', desc: '整理需求、上传资料、安排写作和法务检查', icon: FileText },
    { label: '合同审核', desc: '上传合同、法务审查、风险标注', icon: ShieldCheck },
    { label: '会议纪要', desc: '上传录音/笔记、自动整理、分发确认', icon: History },
    { label: '数据分析', desc: '上传数据源、生成报告、可视化输出', icon: FileSpreadsheet },
  ]

  return <Modal title="和秘书一起新建项目" onClose={onClose} footer={<><button className="secondary-button" onClick={onClose}>取消</button><button className="primary-button" form="create-project-form" type="submit"><CheckCircle2 size={17} />创建项目</button></>}>
    <form className="form-grid project-create-form" id="create-project-form" onSubmit={create}>
      {/* Project template suggestions */}
      <div style={{ gridColumn: '1 / -1' }}>
        <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 8, color: 'var(--ink)' }}>快速开始 — 选择项目模板</label>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
          {templates.map((tpl) => (
            <button key={tpl.label} type="button" onClick={() => {
              setBrief(tpl.desc)
              if (!name) setName(tpl.label)
            }} style={{
              display: 'flex', alignItems: 'flex-start', gap: 10,
              padding: '10px 12px', borderRadius: 8,
              border: '1px solid var(--line)', background: '#fff',
              cursor: 'pointer', textAlign: 'left',
              transition: 'all 0.15s ease',
            }}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--green)'; e.currentTarget.style.background = 'var(--green-soft)' }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--line)'; e.currentTarget.style.background = '#fff' }}
            >
              <span style={{
                width: 30, height: 30, borderRadius: 7, flexShrink: 0,
                background: 'var(--green-soft)', color: 'var(--green)',
                display: 'grid', placeItems: 'center',
              }}>
                <tpl.icon size={14} />
              </span>
              <div>
                <strong style={{ display: 'block', fontSize: 12 }}>{tpl.label}</strong>
                <small style={{ display: 'block', marginTop: 2, color: 'var(--muted)', fontSize: 10 }}>{tpl.desc}</small>
              </div>
            </button>
          ))}
        </div>
      </div>

      <Field label="先告诉秘书，这个项目要做什么">
        <textarea rows={4} value={brief} onChange={(event) => { setBrief(event.target.value); if (!name) setName(event.target.value.slice(0, 24)) }} placeholder="例如：帮我准备 A 客户的投标方案，需要整理需求、上传资料、安排写作和法务检查。" />
      </Field>
      <Field label="项目名称">
        <input value={name} onChange={(event) => setName(event.target.value)} placeholder={suggestedName} />
      </Field>
      <Field label="项目编号" hint="用于保存项目文件夹，后续资料、对话和交付物都会归到这里。">
        <input value={projectId} onChange={(event) => setProjectId(event.target.value.toLowerCase())} placeholder={suggestedId} />
      </Field>

      {/* Team member selector placeholder */}
      <div style={{ gridColumn: '1 / -1' }}>
        <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 8, color: 'var(--ink)' }}>分配团队成员</label>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8, padding: '10px 12px',
          borderRadius: 8, border: '1px dashed var(--line)', background: '#fafbfc',
          color: 'var(--muted)', fontSize: 12, cursor: 'pointer',
        }}>
          <Users size={16} />
          <span>创建项目后，在项目设置中分配数字员工</span>
        </div>
      </div>

      <div className="secretary-tip"><strong>秘书会先做什么？</strong><span>创建项目文件夹，等待你上传关键资料，然后在项目里开启第一条对话。</span></div>
      {error && <p className="form-error">{error}</p>}
    </form>
  </Modal>
}
