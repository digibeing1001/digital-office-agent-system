import { useEffect, useMemo, useState } from 'react'
import { ArrowDown, ArrowUp, Bot, Cable, CheckCircle2, Cpu, ExternalLink, KeyRound, Link2, Server, Settings2, Unplug, Zap } from 'lucide-react'
import { Field, Modal, PageHeading, StatusBadge } from '../../components/ui'
import type { AppActions, GuiState, ModelConnectionInput, ModelRuntimeInput } from '../../types'

type Provider = NonNullable<GuiState>['model_runtime']['providers'][number]
type AgentRuntime = { mode: string; provider: string; model: string; local_runtime?: string }

const familyNames: Record<string, string> = { minimax: 'MiniMax', mimo: '小米 MiMo', kimi: 'Kimi', glm: '智谱 GLM', openai: 'OpenAI', anthropic: 'Anthropic', gemini: 'Gemini', custom: '自定义' }

export function AdminModels({ state, actions }: { state: GuiState | null; actions: AppActions }) {
  const providers = state?.model_runtime.providers || []
  const runtime = state?.model_runtime.runtime
  const localRuntimes = state?.model_runtime.local_runtimes || []
  const employees = state?.digital_employees.items || []
  const [mode, setMode] = useState<'api_key' | 'token_plan'>('api_key')
  const [editing, setEditing] = useState<Provider | null>(null)
  const [message, setMessage] = useState('')
  const [order, setOrder] = useState<string[]>([])
  const [preferredLocalRuntime, setPreferredLocalRuntime] = useState('auto')
  const [agentRuntimeDraft, setAgentRuntimeDraft] = useState<Record<string, AgentRuntime>>({})

  useEffect(() => {
    const configuredOrder = runtime?.provider_order || []
    setOrder([...configuredOrder, ...providers.map((item) => item.provider_id).filter((id) => !configuredOrder.includes(id))])
  }, [providers.length, runtime?.provider_order?.join(',')])

  useEffect(() => {
    setPreferredLocalRuntime(runtime?.preferred_local_runtime || 'auto')
    const next: Record<string, AgentRuntime> = {}
    const configured = runtime?.agents || {}
    employees.forEach((employee) => {
      const agentId = String(employee.agent_id || employee.employee_id || '').trim()
      if (!agentId) return
      const current = configured[agentId] || {}
      next[agentId] = {
        mode: current.mode || 'auto',
        provider: current.provider || '',
        model: current.model || '',
        local_runtime: current.local_runtime || '',
      }
    })
    Object.entries(configured).forEach(([agentId, value]) => {
      if (!next[agentId]) next[agentId] = { mode: value.mode || 'auto', provider: value.provider || '', model: value.model || '', local_runtime: value.local_runtime || '' }
    })
    setAgentRuntimeDraft(next)
  }, [runtime?.preferred_local_runtime, JSON.stringify(runtime?.agents || {}), employees.length])

  const visible = useMemo(() => providers.filter((provider) => provider.credential_mode === mode).sort((a, b) => {
    const rank = { domestic: 0, global: 1, custom: 2 }
    return rank[a.category] - rank[b.category]
  }), [providers, mode])

  const runtimePayload = (patch: Partial<ModelRuntimeInput> = {}): ModelRuntimeInput => ({
    default_mode: runtime?.default_mode || 'auto',
    selection_policy: runtime?.selection_policy || 'local_first',
    provider_order: order,
    preferred_local_runtime: preferredLocalRuntime === 'auto' ? '' : preferredLocalRuntime,
    local_runtime_order: localRuntimes.map((item) => item.id),
    agents: agentRuntimeDraft,
    ...patch,
  })

  const savePolicy = async () => {
    await actions.updateModelRuntime(runtimePayload())
    setMessage('运行策略和本地 Agent 选择已保存。')
  }

  const persistRuntime = async (patch: Partial<ModelRuntimeInput>) => {
    await actions.updateModelRuntime(runtimePayload(patch))
    setMessage('自动选择策略已更新。')
  }

  const move = (id: string, direction: -1 | 1) => {
    const index = order.indexOf(id)
    const target = index + direction
    if (index < 0 || target < 0 || target >= order.length) return
    const next = [...order]
    ;[next[index], next[target]] = [next[target], next[index]]
    setOrder(next)
  }

  const updateAgentRuntime = (agentId: string, patch: Partial<AgentRuntime>) => {
    setAgentRuntimeDraft((current) => ({
      ...current,
      [agentId]: { mode: current[agentId]?.mode || 'auto', provider: current[agentId]?.provider || '', model: current[agentId]?.model || '', local_runtime: current[agentId]?.local_runtime || '', ...patch },
    }))
  }

  const test = async (provider: Provider) => {
    await actions.testModelConnection(provider.provider_id)
    setMessage(`${provider.display_name} 已通过真实调用测试。`)
  }

  return <div className="admin-page model-access-page">
    <PageHeading title="模型接入" description="统一管理大模型 API、Token Plan 和本地 Agent。密钥只保存在服务器本机，页面仅显示脱敏状态。" />
    {message && <div className="inline-success"><CheckCircle2 size={17} />{message}<button onClick={() => setMessage('')}>关闭</button></div>}

    <section className="admin-section model-routing-panel">
      <header><div><h2>运行方式</h2><span>每次执行都会留下选路、用量和失败记录；本地 Agent 和模型 API 都可作为运行入口。</span></div><button className="primary-button" onClick={() => void savePolicy()}><Zap size={16} />保存全部策略</button></header>
      <div className="routing-settings">
        <Field label="默认运行方式"><select value={runtime?.default_mode || 'auto'} onChange={(event) => void persistRuntime({ default_mode: event.target.value as 'host' | 'direct_api' | 'auto' })}><option value="auto">自动选择</option><option value="host">只用本地 Agent</option><option value="direct_api">只用模型 API</option></select></Field>
        <Field label="优先策略"><select value={runtime?.selection_policy || 'local_first'} onChange={(event) => void persistRuntime({ selection_policy: event.target.value as 'local_first' | 'api_first' })}><option value="local_first">本地优先，API 兜底</option><option value="api_first">API 优先，本地兜底</option></select></Field>
        <Field label="默认本地 Agent"><select value={preferredLocalRuntime} onChange={(event) => setPreferredLocalRuntime(event.target.value)}><option value="auto">自动选择可用本地 Agent</option>{localRuntimes.map((item) => <option key={item.id} value={item.id}>{item.display_name}{item.ready ? '' : '（未就绪）'}{item.command && item.command.startsWith('/mnt/') ? ' (Windows)' : ' (WSL)'}</option>)}</select></Field>
      </div>
      <div className="local-runtime-list">{localRuntimes.map((item) => <div key={item.id}><Bot size={18} /><div><strong>{item.display_name}</strong><span>{item.detected ? (item.ready ? `已发现，可选择；支持方式：${item.execution_support}` : '已发现，当前只检测不执行') : '未在本机发现'}</span></div><StatusBadge tone={item.ready ? 'green' : item.detected ? 'amber' : 'gray'}>{item.ready ? '可用' : item.detected ? '待适配' : '未安装'}</StatusBadge></div>)}</div>
      <div className="agent-runtime-matrix">
        <header><div><strong>数字员工运行选择</strong><span>给每个数字员工指定默认本地 Agent。未指定时使用上方默认选择。</span></div></header>
        <div className="agent-runtime-grid">{Object.entries(agentRuntimeDraft).map(([agentId, config]) => {
          const employee = employees.find((item) => (item.agent_id || item.employee_id) === agentId)
          return <article key={agentId}>
            <div><strong>{employee?.display_name_zh || employee?.display_name || agentId}</strong><span>{agentId}</span></div>
            <select value={config.mode || 'auto'} onChange={(event) => updateAgentRuntime(agentId, { mode: event.target.value })}><option value="auto">自动</option><option value="host">本地 Agent</option><option value="direct_api">模型 API</option></select>
            <select value={config.local_runtime || ''} onChange={(event) => updateAgentRuntime(agentId, { local_runtime: event.target.value })}><option value="">跟随默认</option>{localRuntimes.map((item) => <option key={item.id} value={item.id}>{item.display_name}{item.ready ? '' : '（未就绪）'}{item.command && item.command.startsWith('/mnt/') ? ' (Windows)' : ' (WSL)'}</option>)}</select>
          </article>
        })}</div>
      </div>
    </section>

    <div className="model-mode-tabs" role="tablist"><button className={mode === 'api_key' ? 'active' : ''} onClick={() => setMode('api_key')}><KeyRound size={17} />API</button><button className={mode === 'token_plan' ? 'active' : ''} onClick={() => setMode('token_plan')}><Cable size={17} />Token Plan</button></div>

    <section className="model-provider-board">{visible.map((provider) => <article className={`model-provider-card ${provider.configured ? 'connected' : ''}`} key={provider.provider_id}>
      <div className="provider-card-top"><div className="provider-logo"><Cpu size={22} /></div><div><span className="provider-family">{familyNames[provider.provider_family] || provider.provider_family}</span><h3>{provider.display_name}</h3></div><StatusBadge tone={provider.configured ? 'green' : 'gray'}>{provider.configured ? '已连接' : '未连接'}</StatusBadge></div>
      <dl><div><dt>API 地址</dt><dd title={provider.base_url}>{provider.base_url || '等待填写'}</dd></div><div><dt>默认模型</dt><dd>{provider.model || '等待选择'}</dd></div><div><dt>{provider.credential_label || (mode === 'api_key' ? 'API Key' : 'Plan Key')}</dt><dd>{provider.secret_hint || '未配置'}</dd></div></dl>
      <div className="provider-card-actions"><button className="primary-button" onClick={() => setEditing(provider)}><Settings2 size={16} />{provider.configured ? '修改' : '接入'}</button>{provider.configured && <button className="secondary-button" onClick={() => void test(provider)}><Zap size={16} />测试</button>}{provider.help_url && <a href={provider.help_url} rel="noreferrer" target="_blank" title="打开官方说明"><ExternalLink size={16} /></a>}</div>
      <div className="provider-priority"><span>自动选路顺序 {order.indexOf(provider.provider_id) + 1}</span><button title="上移" onClick={() => move(provider.provider_id, -1)}><ArrowUp size={15} /></button><button title="下移" onClick={() => move(provider.provider_id, 1)}><ArrowDown size={15} /></button></div>
    </article>)}</section>
    {!visible.length && <section className="admin-section model-empty"><Server size={28} /><strong>当前没有这一类接入模板</strong></section>}
    {editing && <ConnectionDialog provider={editing} actions={actions} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); setMessage(`${editing.display_name} 已保存。`) }} />}
  </div>
}

function ConnectionDialog({ provider, actions, onClose, onSaved }: { provider: Provider; actions: AppActions; onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState<ModelConnectionInput>({ base_url: provider.base_url || '', model: provider.model || provider.suggested_models?.[0] || '', protocol: provider.protocol || 'openai_chat_completions', secret: '', enabled: true })
  const save = async (event: React.FormEvent) => {
    event.preventDefault()
    await actions.saveModelConnection(provider.provider_id, form)
    onSaved()
  }
  const disconnect = async () => {
    await actions.deleteModelConnection(provider.provider_id)
    onSaved()
  }
  return <Modal title={`接入 ${provider.display_name}`} onClose={onClose} footer={<>{provider.configured && <button className="danger-button model-disconnect" onClick={() => void disconnect()}><Unplug size={16} />断开连接</button>}<button className="secondary-button" onClick={onClose}>取消</button><button className="primary-button" form="model-connection-form" type="submit"><Link2 size={16} />保存连接</button></>}>
    <form className="form-grid model-connection-form" id="model-connection-form" onSubmit={save}>
      <div className="connection-security-note"><KeyRound size={19} /><div><strong>密钥保存在服务器本机</strong><span>不会返回到浏览器，也不会写入运行日志。留空表示保留原密钥。</span></div></div>
      <Field label="API 地址" hint="可填写模型厂商地址、企业网关或本地兼容服务地址。"><input required type="url" value={form.base_url} onChange={(event) => setForm({ ...form, base_url: event.target.value })} placeholder="https://api.example.com/v1" /></Field>
      <Field label="模型"><input required list={`models-${provider.provider_id}`} disabled={provider.model_locked} value={form.model} onChange={(event) => setForm({ ...form, model: event.target.value })} /><datalist id={`models-${provider.provider_id}`}>{provider.suggested_models?.map((model) => <option key={model} value={model} />)}</datalist></Field>
      <Field label={provider.credential_label || (provider.credential_mode === 'token_plan' ? 'Token Plan Key' : 'API Key')}><input autoComplete="new-password" type="password" value={form.secret} onChange={(event) => setForm({ ...form, secret: event.target.value })} placeholder={provider.configured ? `已保存 ${provider.secret_hint}，留空不修改` : '请输入密钥'} /></Field>
      <Field label="接口协议"><select value={form.protocol} onChange={(event) => setForm({ ...form, protocol: event.target.value })}><option value="openai_chat_completions">OpenAI Chat Completions 兼容</option><option value="openai_responses">OpenAI Responses</option><option value="anthropic_messages">Anthropic Messages</option><option value="gemini_generate_content">Gemini Generate Content</option></select></Field>
    </form>
  </Modal>
}
