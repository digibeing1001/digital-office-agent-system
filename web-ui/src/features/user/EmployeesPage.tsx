import { useMemo, useState } from 'react'
import { Archive, BriefcaseBusiness, Plus, Power, RotateCcw, Search, Wrench } from 'lucide-react'
import { displayAgentName, displayAgentRole, initials, statusLabels } from '../../lib/presentation'
import type { AgentSummary, AppActions, CreateAgentInput, GuiState } from '../../types'
import { EmptyState, Field, Modal, PageHeading, StatusBadge } from '../../components/ui'

const emptyForm: CreateAgentInput = {
  agent_id: '', display_name: '', role_description: '', template_agent_id: 'writer', skills: [], keywords: [], workflow_packs: [],
}

export function EmployeesPage({ state, actions }: { state: GuiState | null; actions: AppActions }) {
  const [query, setQuery] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [selected, setSelected] = useState<AgentSummary | null>(null)
  const [form, setForm] = useState<CreateAgentInput>(emptyForm)
  const [skillText, setSkillText] = useState('')
  const [keywordText, setKeywordText] = useState('')
  const employees = state?.digital_employees.items || []
  const templates = (state?.agents.items || []).filter((agent) => agent.origin !== 'custom' && agent.agent_id !== 'secretary')
  const filtered = useMemo(() => employees.filter((employee) => `${displayAgentName(employee)} ${displayAgentRole(employee)}`.toLowerCase().includes(query.toLowerCase())), [employees, query])

  const create = async (event: React.FormEvent) => {
    event.preventDefault()
    await actions.createAgent({
      ...form,
      skills: skillText.split(/[,，\s]+/).filter(Boolean),
      keywords: keywordText.split(/[,，]+/).map((item) => item.trim()).filter(Boolean),
    })
    setShowCreate(false)
    setForm(emptyForm)
    setSkillText('')
    setKeywordText('')
  }

  return <div className="standard-page">
    <PageHeading title="数字员工" description="查看每位数字员工能做什么，也可以按现有岗位创建新的数字员工。" action={<button className="primary-button" onClick={() => setShowCreate(true)}><Plus size={17} />创建数字员工</button>} />
    <div className="page-toolbar"><label className="search-control"><Search size={17} /><input aria-label="搜索数字员工" placeholder="搜索姓名或工作方向" value={query} onChange={(event) => setQuery(event.target.value)} /></label><span>{filtered.length} 位数字员工</span></div>
    {filtered.length ? <div className="employee-grid">
      {filtered.map((employee) => {
        const active = (employee.status || 'active') === 'active'
        return <article className={`employee-card ${active ? '' : 'muted'}`} key={employee.agent_id}>
          <button className="employee-card-main" onClick={() => setSelected(employee)}>
            <span className="employee-avatar">{initials(displayAgentName(employee))}</span>
            <span className="employee-copy"><strong>{displayAgentName(employee)}</strong><em>{displayAgentRole(employee)}</em></span>
          </button>
          <div className="employee-meta"><StatusBadge tone={active ? 'green' : employee.status === 'archived' ? 'gray' : 'amber'}>{statusLabels[employee.status || 'active']}</StatusBadge><span>{employee.skill_staff?.length || employee.skills?.length || 0} 项能力</span></div>
          <div className="employee-skills">{(employee.skill_staff || employee.skills || []).slice(0, 3).map((skill) => <span key={skill}>{skill}</span>)}</div>
          {employee.editable && <div className="employee-actions">
            {employee.status === 'active' && <button onClick={() => void actions.setAgentStatus(employee.agent_id, 'inactive', '由用户停用')}><Power size={15} />停用</button>}
            {employee.status === 'inactive' && <button onClick={() => void actions.setAgentStatus(employee.agent_id, 'active', '由用户重新启用')}><RotateCcw size={15} />启用</button>}
            {employee.status !== 'archived' && <button onClick={() => void actions.setAgentStatus(employee.agent_id, 'archived', '由用户归档')}><Archive size={15} />归档</button>}
          </div>}
        </article>
      })}
    </div> : <EmptyState title="没有找到数字员工" body="换一个名称或工作方向试试。" />}

    {showCreate && <Modal title="创建数字员工" onClose={() => setShowCreate(false)} footer={<><button className="secondary-button" onClick={() => setShowCreate(false)}>取消</button><button className="primary-button" form="create-agent-form" type="submit">创建并启用</button></>}>
      <form className="form-grid" id="create-agent-form" onSubmit={create}>
        <Field label="名称"><input required value={form.display_name} onChange={(event) => setForm({ ...form, display_name: event.target.value })} placeholder="例如：商业合同助手" /></Field>
        <Field label="标识" hint="使用英文小写字母、数字和短横线"><input pattern="[a-z0-9][a-z0-9._-]*" required value={form.agent_id} onChange={(event) => setForm({ ...form, agent_id: event.target.value.toLowerCase() })} placeholder="contract-assistant" /></Field>
        <Field label="岗位模板"><select value={form.template_agent_id} onChange={(event) => setForm({ ...form, template_agent_id: event.target.value })}>{templates.map((agent) => <option key={agent.agent_id} value={agent.agent_id}>{displayAgentName(agent)}</option>)}</select></Field>
        <Field label="主要工作"><textarea required rows={3} value={form.role_description} onChange={(event) => setForm({ ...form, role_description: event.target.value })} placeholder="用一句话说明它负责什么结果" /></Field>
        <Field label="增加能力" hint="多个 Skill 用逗号分隔；模板已有能力会自动保留"><input value={skillText} onChange={(event) => setSkillText(event.target.value)} placeholder="verification-loop, article-writing" /></Field>
        <Field label="自动分配关键词" hint="秘书看到这些词时，会优先考虑这位数字员工"><input value={keywordText} onChange={(event) => setKeywordText(event.target.value)} placeholder="合同，供应商协议，采购条款" /></Field>
      </form>
    </Modal>}

    {selected && <Modal title={displayAgentName(selected)} onClose={() => setSelected(null)}>
      <div className="agent-detail">
        <span className="employee-avatar large">{initials(displayAgentName(selected))}</span>
        <div><StatusBadge tone={(selected.status || 'active') === 'active' ? 'green' : 'gray'}>{statusLabels[selected.status || 'active']}</StatusBadge><p>{displayAgentRole(selected)}</p></div>
      </div>
      <dl className="detail-list"><div><dt><BriefcaseBusiness size={16} />岗位来源</dt><dd>{selected.origin === 'custom' ? `基于 ${selected.template_agent_id || '岗位模板'} 创建` : '系统内置岗位'}</dd></div><div><dt><Wrench size={16} />工作能力</dt><dd>{(selected.skill_staff || selected.skills || []).join('、') || '使用岗位默认能力'}</dd></div></dl>
    </Modal>}
  </div>
}
