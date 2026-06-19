import { useState } from 'react'
import { Archive, Check, Clock3, Database, FileCheck2, History, LockKeyhole, Search, Settings, X } from 'lucide-react'
import { EmptyState, PageHeading, StatusBadge } from '../../components/ui'
import { displayAgentName, formatTime, stageLabels, statusLabels } from '../../lib/presentation'
import type { AppActions, GuiState } from '../../types'

function toneForStatus(status: string): 'green' | 'blue' | 'red' | 'amber' | 'gray' {
  if (['completed', 'approved', 'active'].includes(status)) return 'green'
  if (['failed', 'rejected', 'cancelled'].includes(status)) return 'red'
  if (status.includes('waiting') || status === 'pending' || status === 'blocked') return 'amber'
  if (['archived', 'stopped'].includes(status)) return 'gray'
  return 'blue'
}

export function TasksPage({ state }: { state: GuiState | null }) {
  const workflows = state?.workflows.recent || []
  const runtime = state?.runtime_replay.recent_runs || []
  return <div className="standard-page"><PageHeading title="任务" description="查看每项工作由谁负责、现在进行到哪一步，以及是否需要你处理。" />
    <div className="table-list">
      {workflows.map((workflow) => {
        const run = runtime.find((item) => item.run_id === workflow.run_id)
        const agent = state?.digital_employees.items.find((item) => item.agent_id === workflow.agent_id)
        return <article className="table-row task-list-row" key={workflow.run_id}>
          <div className="row-icon"><Clock3 size={18} /></div><div className="row-main"><div><strong>{workflow.title || '未命名任务'}</strong><StatusBadge tone={toneForStatus(workflow.status)}>{statusLabels[workflow.status] || workflow.status}</StatusBadge></div><p>{displayAgentName(agent)} · {run ? stageLabels[run.current_stage] || run.current_stage : '等待开始'} · {formatTime(workflow.updated_at)}</p></div>
          <div className="row-stats"><span>{run?.handoffs || 0}<small>交接</small></span><span>{run?.checkpoints || 0}<small>检查点</small></span></div>
        </article>
      })}
      {!workflows.length && <EmptyState title="还没有任务" body="回到我的办公室，把第一件事告诉秘书。" />}
    </div>
  </div>
}

export function KnowledgePage({ state }: { state: GuiState | null }) {
  const spaces = state?.knowledge.spaces.items || []
  return <div className="standard-page"><PageHeading title="资料库" description="统一管理公司资料、项目资料和外部资料，数字员工只会读取自己有权限使用的内容。" />
    <div className="knowledge-summary"><div><Database size={22} /><strong>{state?.knowledge.company_entries || 0}</strong><span>公司资料</span></div><div><Archive size={22} /><strong>{spaces.length}</strong><span>资料空间</span></div><div><LockKeyhole size={22} /><strong>{state?.knowledge.external_mounts || 0}</strong><span>外部来源</span></div></div>
    <label className="large-search"><Search size={18} /><input placeholder="搜索资料、项目和交付物" /></label>
    <section className="plain-section"><h2>资料空间</h2>{spaces.length ? <div className="document-list">{spaces.map((space, index) => <div className="document-row" key={String(space.space_id || index)}><span className="file-symbol"><Database size={17} /></span><div><strong>{String(space.name || space.space_id || '资料空间')}</strong><span>{String(space.description || '受权限保护的资料空间')}</span></div></div>)}</div> : <EmptyState title="还没有资料空间" body="添加公司资料或创建项目后，这里会出现对应的资料空间。" />}</section>
  </div>
}

export function ApprovalsPage({ state, actions }: { state: GuiState | null; actions: AppActions }) {
  const approvals = state?.approvals.recent || []
  return <div className="standard-page"><PageHeading title="审批" description="需要你确认的高风险、外部发送和重要变更都会停在这里。" />
    <div className="approval-list">{approvals.map((approval) => <article className="approval-row" key={approval.approval_id}><div className="approval-mark">批</div><div className="row-main"><div><strong>{approval.title}</strong><StatusBadge tone={toneForStatus(approval.status)}>{statusLabels[approval.status] || approval.status}</StatusBadge></div><p>{approval.project_id || '全局事项'} · {formatTime(approval.updated_at)}</p></div>{approval.status === 'pending' && <div className="decision-buttons"><button className="reject-button" onClick={() => void actions.decideApproval(approval.approval_id, 'reject')}><X size={16} />拒绝</button><button className="approve-button" onClick={() => void actions.decideApproval(approval.approval_id, 'approve')}><Check size={16} />批准</button></div>}</article>)}{!approvals.length && <EmptyState title="没有待审批事项" body="需要你确认的工作会清楚地出现在这里。" />}</div>
  </div>
}

export function DeliverablesPage({ state }: { state: GuiState | null }) {
  const delivered = (state?.tasks.recent || []).filter((task) => ['completed', 'delivered'].includes(task.status))
  return <div className="standard-page"><PageHeading title="交付物" description="报告、文档、代码和审查意见都会在完成后归档到这里。" />
    <div className="document-list">{delivered.map((item) => <article className="document-row" key={item.task_id}><span className="file-symbol delivered"><FileCheck2 size={18} /></span><div><strong>{item.title}</strong><span>{item.project_id || '未归类项目'} · {formatTime(item.updated_at)}</span></div><StatusBadge tone="green">已归档</StatusBadge></article>)}{!delivered.length && <EmptyState title="还没有交付物" body="任务通过检查并完成后，成果会自动归档。" />}</div>
  </div>
}

export function RecordsPage({ state }: { state: GuiState | null }) {
  const rows = [...(state?.audit.recent || [])].reverse()
  return <div className="standard-page"><PageHeading title="工作记录" description="查看任务、审批、交接和系统操作留下的完整记录。" />
    <div className="timeline-list">{rows.map((row, index) => <article key={String(row.event_id || index)}><span className="timeline-icon"><History size={16} /></span><div><strong>{String(row.event || '系统记录')}</strong><p>{String(row.reason || row.outcome || '已记录')}</p><time>{formatTime(String(row.time || ''))}</time></div></article>)}{!rows.length && <EmptyState title="还没有工作记录" body="开始第一个任务后，重要过程会自动记录。" />}</div>
  </div>
}

export function SettingsPage({ state }: { state: GuiState | null }) {
  const [workMode, setWorkMode] = useState(() => localStorage.getItem('digital-office-work-mode') || 'balanced')
  const [notifications, setNotifications] = useState(() => localStorage.getItem('digital-office-notifications') !== 'off')

  const updateWorkMode = (value: string) => {
    setWorkMode(value)
    localStorage.setItem('digital-office-work-mode', value)
  }

  const toggleNotifications = () => {
    const next = !notifications
    setNotifications(next)
    localStorage.setItem('digital-office-notifications', next ? 'on' : 'off')
  }

  return <div className="standard-page narrow-page"><PageHeading title="设置" description="调整你的使用习惯。安全、权限和系统策略由管理中心统一管理。" />
    <section className="settings-section"><h2>本机界面偏好</h2><div className="settings-row"><div><strong>工作偏好</strong><span>平衡质量、速度和成本</span></div><select value={workMode} onChange={(event) => updateWorkMode(event.target.value)}><option value="balanced">平衡</option><option value="quality">质量优先</option><option value="fast">速度优先</option></select></div><div className="settings-row"><div><strong>通知</strong><span>任务完成、审批和异常时提醒</span></div><button className={notifications ? 'toggle active' : 'toggle'} aria-label={notifications ? '关闭通知' : '开启通知'} aria-pressed={notifications} onClick={toggleNotifications}><span /></button></div></section>
    <section className="settings-section"><h2>连接状态</h2><div className="settings-row"><div><strong>数字办公室后端</strong><span>{state?.generated_at ? `上次更新 ${formatTime(state.generated_at)}` : '等待连接'}</span></div><StatusBadge tone={state?.health.status === 'ok' ? 'green' : 'amber'}>{state?.health.status === 'ok' ? '正常' : '需要检查'}</StatusBadge></div><div className="settings-row"><div><strong>个人设置</strong><span>{state?.settings.configured ? '已经配置' : '尚未完成首次设置'}</span></div><Settings size={18} /></div></section>
  </div>
}
