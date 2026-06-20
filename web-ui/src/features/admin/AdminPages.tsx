import { useState } from 'react'
import { Activity, Archive, Box, CheckCircle2, Cpu, Database, HardDrive, Plus, Power, RotateCcw, ShieldCheck, Trash2, TriangleAlert, Wrench } from 'lucide-react'
import { EmptyState, Field, Modal, PageHeading, StatusBadge } from '../../components/ui'
import { displayAgentName, displayAgentRole, formatTime, statusLabels } from '../../lib/presentation'
import type { AgentSummary, AppActions, CreateAgentInput, GuiState } from '../../types'

function healthTone(value: boolean): 'green' | 'red' { return value ? 'green' : 'red' }

export function AdminOverview({ state }: { state: GuiState | null }) {
  const checks = Object.entries(state?.health.checks || {})
  const healthy = checks.filter(([, value]) => value).length
  return <div className="admin-page"><PageHeading title="系统概览" description="查看数字办公室是否正常运行，以及当前有哪些工作需要处理。" />
    <div className="metric-strip"><div><Activity size={20} /><span>服务状态</span><strong>{state?.health.status === 'ok' ? '正常' : '需要检查'}</strong></div><div><Box size={20} /><span>数字员工</span><strong>{state?.digital_employees.count || 0}</strong></div><div><Database size={20} /><span>资料条目</span><strong>{state?.knowledge.company_entries || 0}</strong></div><div><TriangleAlert size={20} /><span>待审批</span><strong>{state?.approvals.by_status.pending || 0}</strong></div></div>
    <div className="admin-columns"><section className="admin-section"><header><h2>运行状态</h2><span>{healthy}/{checks.length} 项正常</span></header><div className="health-grid">{checks.slice(0, 12).map(([name, value]) => <div key={name}><StatusBadge tone={healthTone(value)}>{value ? '正常' : '缺失'}</StatusBadge><span>{name.replaceAll('_', ' ')}</span></div>)}</div></section><section className="admin-section"><header><h2>最近任务</h2><span>{state?.workflows.active_count || 0} 项进行中</span></header><div className="compact-list">{state?.workflows.recent.slice(0, 6).map((run) => <div key={run.run_id}><span className="status-dot blue" /><div><strong>{run.title || run.run_id}</strong><span>{statusLabels[run.status] || run.status} · {formatTime(run.updated_at)}</span></div></div>)}{!state?.workflows.recent.length && <EmptyState title="没有运行记录" body="用户提交任务后会出现在这里。" />}</div></section></div>
  </div>
}

const emptyAgent: CreateAgentInput = { agent_id: '', display_name: '', role_description: '', template_agent_id: 'writer', skills: [], keywords: [], workflow_packs: [] }

export function AdminAgents({ state, actions }: { state: GuiState | null; actions: AppActions }) {
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState<CreateAgentInput>(emptyAgent)
  const [skills, setSkills] = useState('')
  const [keywords, setKeywords] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<AgentSummary | null>(null)
  const agents = state?.agents.items || []
  const templates = agents.filter((agent) => agent.origin !== 'custom' && agent.agent_id !== 'secretary')

  const create = async (event: React.FormEvent) => {
    event.preventDefault()
    await actions.createAgent({ ...form, skills: skills.split(/[,，\s]+/).filter(Boolean), keywords: keywords.split(/[,，]+/).map((item) => item.trim()).filter(Boolean) })
    setShowCreate(false)
    setForm(emptyAgent)
    setSkills('')
    setKeywords('')
  }

  const permanentlyDelete = async () => {
    if (!deleteTarget) return
    await actions.deleteAgent(deleteTarget.agent_id)
    setDeleteTarget(null)
  }

  return <div className="admin-page"><PageHeading title="Agent 管理" description="创建、启用、停用和归档数字员工。内置 Agent 受到保护，不能误删。" action={<button className="primary-button" onClick={() => setShowCreate(true)}><Plus size={17} />创建 Agent</button>} />
    <section className="admin-section table-section"><div className="admin-table agent-table"><div className="admin-table-head"><span>Agent</span><span>来源</span><span>模型</span><span>状态</span><span>操作</span></div>{agents.map((agent) => <div className="admin-table-row" key={agent.agent_id}><div><strong>{displayAgentName(agent)}</strong><small>{agent.agent_id} · {displayAgentRole(agent)}</small></div><span>{agent.origin === 'custom' ? `自建 / ${agent.template_agent_id}` : '系统内置'}</span><span>{agent.provider || '默认'}<small>{agent.model || agent.profile}</small></span><StatusBadge tone={(agent.status || 'active') === 'active' ? 'green' : agent.status === 'archived' ? 'gray' : 'amber'}>{statusLabels[agent.status || 'active']}</StatusBadge><div className="table-actions">{agent.editable ? <>{agent.status === 'active' && <button title="停用" onClick={() => void actions.setAgentStatus(agent.agent_id, 'inactive')}><Power size={16} /></button>}{agent.status !== 'active' && <button title="恢复启用" onClick={() => void actions.setAgentStatus(agent.agent_id, 'active')}><RotateCcw size={16} /></button>}{agent.status !== 'archived' && <button title="归档" onClick={() => void actions.setAgentStatus(agent.agent_id, 'archived')}><Archive size={16} /></button>}{agent.status === 'archived' && <button className="danger" title="永久删除" onClick={() => setDeleteTarget(agent)}><Trash2 size={16} /></button>}</> : <span className="protected-label"><ShieldCheck size={15} />受保护</span>}</div></div>)}</div></section>
    {showCreate && <Modal title="创建 Agent" onClose={() => setShowCreate(false)} footer={<><button className="secondary-button" onClick={() => setShowCreate(false)}>取消</button><button className="primary-button" form="admin-create-agent" type="submit">创建并启用</button></>}><form className="form-grid" id="admin-create-agent" onSubmit={create}><Field label="显示名称"><input required value={form.display_name} onChange={(event) => setForm({ ...form, display_name: event.target.value })} /></Field><Field label="Agent 标识"><input pattern="[a-z0-9][a-z0-9._-]*" required value={form.agent_id} onChange={(event) => setForm({ ...form, agent_id: event.target.value.toLowerCase() })} /></Field><Field label="岗位模板"><select value={form.template_agent_id} onChange={(event) => setForm({ ...form, template_agent_id: event.target.value })}>{templates.map((agent) => <option key={agent.agent_id} value={agent.agent_id}>{displayAgentName(agent)}</option>)}</select></Field><Field label="工作职责"><textarea required rows={3} value={form.role_description} onChange={(event) => setForm({ ...form, role_description: event.target.value })} /></Field><Field label="增加 Skills"><input value={skills} onChange={(event) => setSkills(event.target.value)} placeholder="用逗号分隔" /></Field><Field label="分配关键词"><input value={keywords} onChange={(event) => setKeywords(event.target.value)} placeholder="用逗号分隔" /></Field></form></Modal>}
    {deleteTarget && <Modal title="永久删除 Agent" onClose={() => setDeleteTarget(null)} footer={<><button className="secondary-button" onClick={() => setDeleteTarget(null)}>取消</button><button className="danger-button" onClick={() => void permanentlyDelete()}><Trash2 size={16} />确认永久删除</button></>}><div className="delete-warning"><TriangleAlert size={24} /><div><strong>“{displayAgentName(deleteTarget)}”删除后不能恢复</strong><p>历史任务、交付物和审计记录会继续保留。只有这个 Agent 的配置会被永久删除。</p></div></div></Modal>}
  </div>
}

export function AdminSkills({ state }: { state: GuiState | null }) {
  const skills = state?.skill_installations.items || []
  return <div className="admin-page"><PageHeading title="Skills" description="查看已经安装的能力包、许可证和使用情况。" />
    <section className="admin-section table-section"><div className="admin-table skill-table"><div className="admin-table-head"><span>能力包</span><span>状态</span><span>许可证</span><span>文件</span><span>使用方</span></div>{skills.map((skill) => <div className="admin-table-row" key={skill.name}><div><Wrench size={16} /><strong>{skill.name}</strong></div><StatusBadge tone={skill.status.includes('installed') ? 'green' : 'amber'}>{skill.status}</StatusBadge><span>{skill.license || '未登记'}</span><span>{skill.skill_files}</span><span>{skill.used_by?.join('、') || '尚未绑定'}</span></div>)}</div></section>
  </div>
}

export function AdminRuns({ state }: { state: GuiState | null }) {
  const rows = state?.runtime_replay.recent_runs || []
  return <div className="admin-page"><PageHeading title="运行监控" description="查看任务阶段、交接、检查点、调用预算和停止原因。" />
    <section className="admin-section table-section"><div className="admin-table runs-table"><div className="admin-table-head"><span>运行</span><span>阶段</span><span>循环</span><span>交接</span><span>检查点</span><span>账本</span></div>{rows.map((run) => <div className="admin-table-row" key={run.run_id}><strong>{run.run_id}</strong><StatusBadge tone="blue">{run.current_stage}</StatusBadge><span>{run.cycle_index}</span><span>{run.handoffs}{run.pending_handoffs ? ` / ${run.pending_handoffs} 待确认` : ''}</span><span>{run.checkpoints}</span><span>{run.ledger_events}</span></div>)}</div>{!rows.length && <EmptyState title="没有运行中的任务" body="任务开始后会显示实时运行信息。" />}</section>
  </div>
}

export function AdminPolicy({ state }: { state: GuiState | null }) {
  const budgets = state?.loop_runtime.default_budgets || {}
  return <div className="admin-page"><PageHeading title="权限与预算" description="控制 Agent 能访问什么，以及每项任务最多能使用多少资源。" />
    <div className="admin-columns"><section className="admin-section"><header><h2>默认任务预算</h2><span>LOOP 控制器</span></header><div className="key-value-list">{Object.entries(budgets).map(([key, value]) => <div key={key}><span>{key.replaceAll('_', ' ')}</span><strong>{value}</strong></div>)}</div></section><section className="admin-section"><header><h2>权限边界</h2><span>系统策略</span></header><div className="policy-list"><div><CheckCircle2 size={17} /><span>高风险工作必须经过审批</span></div><div><CheckCircle2 size={17} /><span>数字员工只能读取授权资料</span></div><div><CheckCircle2 size={17} /><span>Skills 不能自行创建下级 Agent</span></div><div><CheckCircle2 size={17} /><span>系统变更必须经过确认和回归检查</span></div></div></section></div>
  </div>
}

export function AdminAudit({ state }: { state: GuiState | null }) {
  return <div className="admin-page"><PageHeading title="审计" description="查询任务、审批、Agent 变更和资料访问留下的记录。" />
    <section className="admin-section table-section"><div className="admin-table audit-table"><div className="admin-table-head"><span>时间</span><span>事件</span><span>操作者</span><span>对象</span><span>结果</span></div>{[...(state?.audit.recent || [])].reverse().map((row, index) => <div className="admin-table-row" key={String(row.event_id || index)}><span>{formatTime(String(row.time || ''))}</span><strong>{String(row.event || '')}</strong><span>{String((row.actor as Record<string, unknown> | undefined)?.user_id || '')}</span><span>{String((row.resource as Record<string, unknown> | undefined)?.id || row.agent_id || '')}</span><StatusBadge tone="gray">{String(row.outcome || 'recorded')}</StatusBadge></div>)}</div></section>
  </div>
}

export function AdminSystem({ state }: { state: GuiState | null }) {
  const providers = state?.model_runtime.providers || []
  const configuredProviders = providers.filter((provider) => provider.configured).length
  return <div className="admin-page"><PageHeading title="系统维护" description="查看安装版本、备份、更新和运行环境。" />
    <div className="admin-columns"><section className="admin-section"><header><h2>安装与更新</h2><StatusBadge tone="green">内部版本</StatusBadge></header><div className="maintenance-block"><HardDrive size={28} /><div><strong>Digital Office 0.3</strong><span>使用受管理的 update 命令更新，个人数据和运行记录不会被覆盖。</span><code>~/.hermes/update</code></div></div></section><section className="admin-section"><header><h2>数据保护</h2><span>本地运行</span></header><div className="maintenance-block"><Archive size={28} /><div><strong>备份与恢复</strong><span>备份包含项目、任务、审批、运行记录和设置。恢复需要管理员确认。</span><code>office-system backup</code></div></div></section></div>
    <section className="admin-section"><header><h2>模型接入</h2><span>{configuredProviders}/{providers.length} 个 API 已就绪</span></header><div className="provider-grid">{providers.map((provider) => <div className="provider-row" key={provider.provider_id}><Cpu size={18} /><div><strong>{provider.display_name}</strong><span>{provider.configured ? `${provider.protocol} · 可由数字员工直接调用` : `需要配置 ${provider.missing.join('、')}`}</span></div><StatusBadge tone={provider.configured ? 'green' : 'gray'}>{provider.configured ? '已连接' : '未配置'}</StatusBadge></div>)}</div></section>
    <section className="admin-section"><header><h2>后端能力</h2><span>{state?.capabilities.length || 0} 项</span></header><div className="capability-grid">{state?.capabilities.map((capability) => <div key={capability.id}><StatusBadge tone="green">可用</StatusBadge><strong>{capability.id.replaceAll('_', ' ')}</strong></div>)}</div></section>
  </div>
}
