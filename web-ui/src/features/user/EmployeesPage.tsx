import { useMemo, useState } from 'react'
import { AlertTriangle, Archive, BarChart3, Bot, BriefcaseBusiness, CheckCircle2, Coins, Plus, Power, RotateCcw, Search, Sparkles, TrendingUp, Wrench } from 'lucide-react'
import { displayAgentName, displayAgentRole, formatTime, initials, statusLabels } from '../../lib/presentation'
import type { AgentSummary, AppActions, CreateAgentInput, EmployeeSuggestion, GuiState } from '../../types'
import { EmptyState, Field, Modal, PageHeading, StatusBadge } from '../../components/ui'

const emptyForm: CreateAgentInput = {
  agent_id: '', display_name: '', role_description: '', template_agent_id: 'writer', skills: [], keywords: [], workflow_packs: [],
}

function compactNumber(value: number) {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`
  return String(value || 0)
}

function metricTone(rate: number, issues: number): 'green' | 'amber' | 'gray' {
  if (!rate && !issues) return 'gray'
  if (issues > 0 && rate < 80) return 'amber'
  return 'green'
}

export function EmployeesPage({ state, actions }: { state: GuiState | null; actions: AppActions }) {
  const [query, setQuery] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [selected, setSelected] = useState<AgentSummary | null>(null)
  const [form, setForm] = useState<CreateAgentInput>(emptyForm)
  const [skillText, setSkillText] = useState('')
  const [keywordText, setKeywordText] = useState('')
  const employees = state?.digital_employees.items || []
  const metrics = state?.employee_performance.items || {}
  const suggestions = state?.employee_performance.suggestions || []
  const templates = (state?.agents.items || []).filter((agent) => agent.origin !== 'custom' && agent.agent_id !== 'secretary')
  const filtered = useMemo(() => employees.filter((employee) => `${displayAgentName(employee)} ${displayAgentRole(employee)}`.toLowerCase().includes(query.toLowerCase())), [employees, query])
  const totals = employees.reduce((acc, employee) => {
    const item = metrics[employee.agent_id]
    acc.calls += item?.run_count || 0
    acc.tokens += item?.token_estimate || 0
    acc.success += item?.success_count || 0
    acc.issues += item?.issue_count || 0
    return acc
  }, { calls: 0, tokens: 0, success: 0, issues: 0 })
  const closed = totals.success + totals.issues
  const totalSuccessRate = closed ? Math.round((totals.success / closed) * 100) : 0

  const openCreate = (suggestion?: EmployeeSuggestion) => {
    if (suggestion) {
      setForm({
        ...emptyForm,
        agent_id: suggestion.suggested_agent_id,
        display_name: suggestion.display_name,
        template_agent_id: suggestion.template_agent_id,
        role_description: suggestion.reason,
      })
      setSkillText(suggestion.skills.join(', '))
      setKeywordText(suggestion.keywords.join('，'))
    } else {
      setForm(emptyForm)
      setSkillText('')
      setKeywordText('')
    }
    setShowCreate(true)
  }

  const create = async (event: React.FormEvent) => {
    event.preventDefault()
    await actions.createAgent({
      ...form,
      skills: skillText.split(/[,，\s]+/).filter(Boolean),
      keywords: keywordText.split(/[,，]+/).map((item) => item.trim()).filter(Boolean),
    })
    setShowCreate(false)
  }

  return <div className="standard-page employees-board">
    <PageHeading title="数字员工" description="这里是数字办公室的人事板块。既能看每位数字员工会做什么，也能看它们真实被调用后的表现。" action={<button className="primary-button" onClick={() => openCreate()}><Plus size={17} />新建数字员工</button>} />
    <div className="people-metrics">
      <div><Bot size={20} /><strong>{employees.length}</strong><span>数字员工</span></div>
      <div><BarChart3 size={20} /><strong>{totals.calls}</strong><span>累计调用</span></div>
      <div><TrendingUp size={20} /><strong>{totalSuccessRate ? `${totalSuccessRate}%` : '-'}</strong><span>任务成功率</span></div>
      <div><Coins size={20} /><strong>{compactNumber(totals.tokens)}</strong><span>Token 估算</span></div>
    </div>
    <div className="page-toolbar"><label className="search-control"><Search size={17} /><input aria-label="搜索数字员工" placeholder="搜索员工、能力或岗位" value={query} onChange={(event) => setQuery(event.target.value)} /></label><span>{filtered.length} 位数字员工</span></div>
    {filtered.length ? <div className="employee-performance-grid">
      {filtered.map((employee) => {
        const active = (employee.status || 'active') === 'active'
        const item = metrics[employee.agent_id]
        return <article className={`employee-performance-card ${active ? '' : 'muted'}`} key={employee.agent_id}>
          <button className="employee-card-main" onClick={() => setSelected(employee)}>
            <span className="employee-avatar">{initials(displayAgentName(employee))}</span>
            <span className="employee-copy"><strong>{displayAgentName(employee)}</strong><em>{displayAgentRole(employee)}</em></span>
          </button>
          <div className="employee-meta"><StatusBadge tone={active ? 'green' : employee.status === 'archived' ? 'gray' : 'amber'}>{statusLabels[employee.status || 'active']}</StatusBadge><span>{employee.skill_staff?.length || employee.skills?.length || 0} 项能力</span></div>
          <div className="employee-score-row">
            <div><strong>{item?.run_count || 0}</strong><span>调用</span></div>
            <div><strong>{item?.success_rate ? `${item.success_rate}%` : '-'}</strong><span>成功率</span></div>
            <div><strong>{compactNumber(item?.token_estimate || 0)}</strong><span>Token</span></div>
            <div><strong>{item?.issue_count || 0}</strong><span>异常</span></div>
          </div>
          <div className="employee-health-line">
            <StatusBadge tone={metricTone(item?.success_rate || 0, item?.issue_count || 0)}>{item?.run_count ? '已有调用记录' : '等待首次调用'}</StatusBadge>
            <small>{item?.last_active_at ? `最近 ${formatTime(item.last_active_at)}` : '暂无调用记录'}</small>
          </div>
          <div className="employee-skills">{(employee.skill_staff || employee.skills || []).slice(0, 4).map((skill) => <span key={skill}>{skill}</span>)}</div>
          {employee.editable && <div className="employee-actions">
            {employee.status === 'active' && <button onClick={() => void actions.setAgentStatus(employee.agent_id, 'inactive', '由用户停用')}><Power size={15} />停用</button>}
            {employee.status === 'inactive' && <button onClick={() => void actions.setAgentStatus(employee.agent_id, 'active', '由用户重新启用')}><RotateCcw size={15} />启用</button>}
            {employee.status !== 'archived' && <button onClick={() => void actions.setAgentStatus(employee.agent_id, 'archived', '由用户归档')}><Archive size={15} />归档</button>}
          </div>}
        </article>
      })}
    </div> : <EmptyState title="没有找到数字员工" body="换一个名称或工作方向试试。" />}

    <section className="hiring-panel">
      <header><div><h2>建议补齐的数字员工</h2><p>系统会根据常见办公室分工、项目记录和缺席能力，给出可解释的补员建议。</p></div><Sparkles size={20} /></header>
      <div className="hiring-grid">
        {suggestions.map((suggestion) => <article key={suggestion.suggested_agent_id}>
          <StatusBadge tone={suggestion.priority === 'high' ? 'amber' : 'gray'}>{suggestion.priority === 'high' ? '建议优先补齐' : '可选补齐'}</StatusBadge>
          <h3>{suggestion.display_name}</h3>
          <p>{suggestion.reason}</p>
          <div>{suggestion.skills.slice(0, 3).map((skill) => <span key={skill}>{skill}</span>)}</div>
          <button className="secondary-button" onClick={() => openCreate(suggestion)}><Plus size={16} />按建议创建</button>
        </article>)}
        {!suggestions.length && <EmptyState title="暂时没有明显缺口" body="当项目类型变多、出现失败或重复转派时，这里会给出补员建议。" />}
      </div>
    </section>

    {showCreate && <Modal title="创建数字员工" onClose={() => setShowCreate(false)} footer={<><button className="secondary-button" onClick={() => setShowCreate(false)}>取消</button><button className="primary-button" form="create-agent-form" type="submit">创建并启用</button></>}>
      <form className="form-grid" id="create-agent-form" onSubmit={create}>
        <Field label="名称"><input required value={form.display_name} onChange={(event) => setForm({ ...form, display_name: event.target.value })} placeholder="例如：财务助理" /></Field>
        <Field label="标识" hint="使用英文小写字母、数字和短横线"><input pattern="[a-z0-9][a-z0-9._-]*" required value={form.agent_id} onChange={(event) => setForm({ ...form, agent_id: event.target.value.toLowerCase() })} placeholder="finance" /></Field>
        <Field label="岗位模板"><select value={form.template_agent_id} onChange={(event) => setForm({ ...form, template_agent_id: event.target.value })}>{templates.map((agent) => <option key={agent.agent_id} value={agent.agent_id}>{displayAgentName(agent)}</option>)}</select></Field>
        <Field label="主要工作"><textarea required rows={3} value={form.role_description} onChange={(event) => setForm({ ...form, role_description: event.target.value })} placeholder="用一句话说明它负责什么结果" /></Field>
        <Field label="增加能力" hint="多个 Skill 用逗号分隔"><input value={skillText} onChange={(event) => setSkillText(event.target.value)} placeholder="finance-billing-ops, cost-tracking" /></Field>
        <Field label="自动分配关键词"><input value={keywordText} onChange={(event) => setKeywordText(event.target.value)} placeholder="预算，发票，付款" /></Field>
      </form>
    </Modal>}

    {selected && <Modal title={displayAgentName(selected)} onClose={() => setSelected(null)}>
      <div className="agent-detail">
        <span className="employee-avatar large">{initials(displayAgentName(selected))}</span>
        <div><StatusBadge tone={(selected.status || 'active') === 'active' ? 'green' : 'gray'}>{statusLabels[selected.status || 'active']}</StatusBadge><p>{displayAgentRole(selected)}</p></div>
      </div>
      <dl className="detail-list"><div><dt><BriefcaseBusiness size={16} />岗位来源</dt><dd>{selected.origin === 'custom' ? `基于 ${selected.template_agent_id || '岗位模板'} 创建` : '系统内置岗位'}</dd></div><div><dt><Wrench size={16} />工作能力</dt><dd>{(selected.skill_staff || selected.skills || []).join('、') || '使用岗位默认能力'}</dd></div><div><dt><CheckCircle2 size={16} />调用表现</dt><dd>{metrics[selected.agent_id]?.run_count || 0} 次调用，{metrics[selected.agent_id]?.success_count || 0} 次成功，{metrics[selected.agent_id]?.issue_count || 0} 次异常</dd></div><div><dt><AlertTriangle size={16} />成本记录</dt><dd>Token 估算 {compactNumber(metrics[selected.agent_id]?.token_estimate || 0)}，模型调用 {metrics[selected.agent_id]?.model_calls || 0}，工具调用 {metrics[selected.agent_id]?.tool_calls || 0}</dd></div></dl>
    </Modal>}
  </div>
}
