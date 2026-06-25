import { useEffect, useMemo, useState } from 'react'
import { Archive, Briefcase, ChevronRight, Database, FileText, Filter, FolderKanban, MoreHorizontal, Search, Settings, TrendingUp, UploadCloud, UserRound, Wifi, WifiOff, Cpu, UserCog, File, Image, FileType, FileSpreadsheet } from 'lucide-react'
import { EmptyState, PageHeading, StatusBadge } from '../../components/ui'
import { formatTime } from '../../lib/presentation'
import type { AppActions, GuiState } from '../../types'
import { KnowledgeUploadDialog } from './KnowledgeUploadDialog'

const TAB_CONFIG = [
  { key: 'company' as const, icon: Database, label: '公司知识库' },
  { key: 'projects' as const, icon: FolderKanban, label: '项目知识库' },
  { key: 'personal' as const, icon: UserRound, label: '个人知识库' },
]

const FILE_TYPE_CHIPS = [
  { label: '全部', icon: FileText },
  { label: 'Word', icon: FileType },
  { label: 'PDF', icon: File },
  { label: '图片', icon: Image },
  { label: '表格', icon: FileSpreadsheet },
]

export function KnowledgePage({ state, actions, onOpenProject }: { state: GuiState | null; actions: AppActions; onOpenProject: (projectId: string) => void }) {
  const [showUpload, setShowUpload] = useState(false)
  const [activeTab, setActiveTab] = useState<'company' | 'projects' | 'personal'>('company')
  const [activeFilter, setActiveFilter] = useState('全部')
  const projectEntryTotal = useMemo(() => Object.values(state?.knowledge.project_entries || {}).reduce((total, item) => total + item.count, 0), [state])
  const personalSpaces = (state?.knowledge.spaces.items || []).filter((space) => String(space.space_type || '').includes('personal'))

  const tabCounts: Record<string, number> = {
    company: state?.knowledge.company_entries || 0,
    projects: projectEntryTotal,
    personal: personalSpaces.length,
  }

  const summaryCards = [
    { icon: Database, value: state?.knowledge.company_entries || 0, label: '公司资料', color: '#1f6e56', bgColor: '#e3f3ec' },
    { icon: FolderKanban, value: projectEntryTotal, label: '项目资料', color: '#c89639', bgColor: '#fdf6e8' },
    { icon: Archive, value: personalSpaces.length, label: '个人空间', color: '#d9574d', bgColor: '#fdecea' },
  ]
  return <div className="standard-page knowledge-page">
    <PageHeading title="知识库" description="公司资料、项目资料和个人资料都在这里。日常项目资料建议直接进项目文件夹管理。" action={<button className="primary-button" onClick={() => setShowUpload(true)}><UploadCloud size={17} />上传资料</button>} />
    <div className="knowledge-tabs" role="tablist">
      <div className="knowledge-tabs-track">
        {TAB_CONFIG.map((tab) => {
          const Icon = tab.icon
          return <button className={`knowledge-tab-pill${activeTab === tab.key ? ' active' : ''}`} onClick={() => setActiveTab(tab.key)} key={tab.key}>
            <Icon size={15} /><span>{tab.label}</span>{tabCounts[tab.key] > 0 && <span className="knowledge-tab-count">{tabCounts[tab.key]}</span>}
          </button>
        })}
        <div className={`knowledge-tab-indicator${activeTab === 'company' ? ' at-0' : activeTab === 'projects' ? ' at-1' : ' at-2'}`} />
      </div>
    </div>
    <div className="knowledge-summary-cards">
      {summaryCards.map((card) => {
        const Icon = card.icon
        return <div className="summary-card" key={card.label}>
          <div className="summary-card-icon" style={{ background: card.bgColor, color: card.color }}><Icon size={22} /></div>
          <div className="summary-card-body"><strong className="summary-card-number">{card.value}</strong><span className="summary-card-label">{card.label}</span></div>
          <span className="summary-card-trend"><TrendingUp size={13} /></span>
        </div>
      })}
    </div>
    <div className="knowledge-search-area">
      <label className="large-search"><Search size={18} /><input placeholder="搜索资料、项目和交付物" /></label>
      <div className="knowledge-filter-chips">
        <Filter size={14} />
        {FILE_TYPE_CHIPS.map((chip) => {
          const Icon = chip.icon
          return <button key={chip.label} className={`filter-chip${activeFilter === chip.label ? ' active' : ''}`} onClick={() => setActiveFilter(chip.label)}><Icon size={13} />{chip.label}</button>
        })}
      </div>
    </div>
    {activeTab === 'company' && <section className="plain-card knowledge-panel">
      <header className="knowledge-panel-header"><div className="knowledge-panel-header-text"><h2>公司知识库</h2><span>适合放公司介绍、产品资料、制度、通用模板</span></div></header>
      {(state?.knowledge.company_entries || 0) ? <div className="document-list"><div className="document-row"><span className="file-type-icon" style={{ background: '#e3f3ec', color: '#1f6e56' }}><Database size={16} /></span><div className="document-row-content"><strong>公司资料</strong><span>{state?.knowledge.company_entries || 0} 份资料可供授权数字员工使用</span></div><StatusBadge tone="green">已就绪</StatusBadge><button className="icon-button document-action-btn" aria-label="更多操作"><MoreHorizontal size={16} /></button></div></div> : <EmptyState title="公司知识库还没有资料" body="上传公司介绍、业务说明、制度模板等通用资料。" action={<button className="primary-button" onClick={() => setShowUpload(true)}><UploadCloud size={15} />立即上传</button>} />}
    </section>}
    {activeTab === 'projects' && <section className="plain-card knowledge-panel">
      <header className="knowledge-panel-header"><div className="knowledge-panel-header-text"><h2>项目知识库</h2><span>每个项目都有自己的资料夹</span></div></header>
      <div className="document-list">
        {(state?.projects.items || []).map((project) => {
          const entries = state?.knowledge.project_entries?.[project.project_id]
          return <button className="document-row document-row-button" key={project.project_id} onClick={() => onOpenProject(project.project_id)}><span className="file-type-icon" style={{ background: '#fdf6e8', color: '#c89639' }}><FolderKanban size={16} /></span><div className="document-row-content"><strong>{project.name}</strong><span>{entries?.count || 0} 份资料 · 进入项目可继续管理</span></div><StatusBadge tone={entries?.count ? 'green' : 'gray'}>{entries?.count ? `${entries.count} 份` : '空'}</StatusBadge><ChevronRight size={16} className="document-row-chevron" /></button>
        })}
        {!state?.projects.items.length && <EmptyState title="还没有项目知识库" body="创建项目后，这里会自动出现对应项目资料。" />}
      </div>
    </section>}
    {activeTab === 'personal' && <section className="plain-card knowledge-panel">
      <header className="knowledge-panel-header"><div className="knowledge-panel-header-text"><h2>个人知识库</h2><span>适合放只和你有关的偏好、草稿和私有资料</span></div></header>
      <div className="document-list">
        {personalSpaces.map((space, index) => <div className="document-row" key={String(space.space_id || index)}><span className="file-type-icon" style={{ background: '#fdecea', color: '#d9574d' }}><UserRound size={16} /></span><div className="document-row-content"><strong>{String(space.name || space.space_id || '个人资料')}</strong><span>{String(space.description || '只有授权后才会被数字员工使用')}</span></div><StatusBadge tone="blue">私有</StatusBadge><button className="icon-button document-action-btn" aria-label="更多操作"><MoreHorizontal size={16} /></button></div>)}
        {!personalSpaces.length && <EmptyState title="还没有个人知识库" body="后续可以在这里放个人常用资料和偏好。" />}
      </div>
    </section>}
    {showUpload && <KnowledgeUploadDialog actions={actions} defaultScope="company" onClose={() => setShowUpload(false)} state={state} />}
  </div>
}
export function SettingsPage({ state, actions }: { state: GuiState | null; actions: AppActions }) {
  const presets = state?.settings.presets
  const [choices, setChoices] = useState<Record<string, string>>({})
  const [companyName, setCompanyName] = useState('')
  const [secretaryName, setSecretaryName] = useState('秘书')
  const [notifications, setNotifications] = useState(() => localStorage.getItem('digital-office-notifications') !== 'off')
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    setChoices({ ...(presets?.default_choices || {}), ...(state?.settings.preferences.choices || {}) })
    setCompanyName(state?.settings.preferences.company_name || '')
    setSecretaryName(state?.settings.preferences.secretary_name || '秘书')
  }, [state?.generated_at])

  const toggleNotifications = () => {
    const next = !notifications
    setNotifications(next)
    localStorage.setItem('digital-office-notifications', next ? 'on' : 'off')
  }

  const modelProviders = state?.model_runtime.providers || []
  const readyModels = modelProviders.filter((provider) => provider.configured).length
  const labels: Record<string, string> = { assistant_style: '秘书风格', address_style: '称呼方式', language: '回复语言', initiative_level: '主动程度', pushback_style: '提醒与反驳', approval_strictness: '确认严格度', memory_mode: '记忆范围', work_mode: '工作模式' }

  const save = async () => {
    await actions.updatePreferences({ company_name: companyName, secretary_name: secretaryName, choices })
    setSaved(true)
    window.setTimeout(() => setSaved(false), 2400)
  }

  const backendOk = state?.health.status === 'ok'
  return <div className="standard-page narrow-page"><PageHeading title="设置" description="调整你的使用习惯。安全、权限和系统策略由管理中心统一管理。" />
    <section className="settings-card"><div className="settings-card-header"><div className="settings-card-header-icon" style={{ background: '#e3f3ec', color: '#1f6e56' }}><Briefcase size={20} /></div><div className="settings-card-header-text"><h2>秘书与工作偏好</h2><span>这些设置会写入后端，下一次对话和任务会直接使用。</span></div></div><button className={`primary-button settings-save-btn${saved ? ' saved' : ''}`} onClick={() => void save()}>{saved ? '已保存' : '保存设置'}</button><div className="settings-rows">{[
      { label: '公司名称', hint: '用于项目、报告和秘书称呼中的公司身份', control: <input value={companyName} onChange={(event) => setCompanyName(event.target.value)} placeholder="你的公司" /> },
      { label: '秘书名称', hint: '用户界面和任务沟通中显示的名称', control: <input value={secretaryName} onChange={(event) => setSecretaryName(event.target.value)} /> },
      ...Object.entries(presets?.fields || {}).map(([field, config]) => ({
        label: labels[field] || config.label,
        hint: config.choices[choices[field]]?.description || config.label,
        control: <select value={choices[field] || ''} onChange={(event) => setChoices({ ...choices, [field]: event.target.value })}>{Object.entries(config.choices).map(([value, option]) => <option value={value} key={value}>{option.label}</option>)}</select>,
      })),
    ].map((row, i) => <div className="settings-row" key={i}><div className="settings-row-label"><strong>{row.label}</strong><span>{row.hint}</span></div><div className="settings-row-control">{row.control}</div></div>)}</div></section>
    <section className="settings-card"><div className="settings-card-header"><div className="settings-card-header-icon" style={{ background: '#f0f0ff', color: '#5b5fc7' }}><Settings size={20} /></div><div className="settings-card-header-text"><h2>本机界面偏好</h2></div></div><div className="settings-rows"><div className="settings-row"><div className="settings-row-label"><strong>通知</strong><span>任务完成、审批和异常时提醒</span></div><div className="settings-row-control"><button className={`toggle-switch${notifications ? ' active' : ''}`} aria-label={notifications ? '关闭通知' : '开启通知'} aria-pressed={notifications} onClick={toggleNotifications}><span className="toggle-switch-thumb" /></button></div></div></div></section>
    <section className="settings-card"><div className="settings-card-header"><div className="settings-card-header-icon" style={{ background: '#e8f4fd', color: '#2b7bb9' }}><Wifi size={20} /></div><div className="settings-card-header-text"><h2>连接状态</h2></div></div><div className="connection-status-grid">
      <div className="connection-status-card"><div className="connection-status-icon"><Wifi size={18} /><span className={`status-dot ${backendOk ? 'green' : 'amber'} pulse`} /></div><div className="connection-status-info"><strong>数字办公室后端</strong><span>{state?.generated_at ? `上次更新 ${formatTime(state.generated_at)}` : '等待连接'}</span></div><StatusBadge tone={backendOk ? 'green' : 'amber'}>{backendOk ? '正常' : '需要检查'}</StatusBadge></div>
      <div className="connection-status-card"><div className="connection-status-icon"><Cpu size={18} /><span className={`status-dot ${readyModels ? 'green' : 'gray'}${readyModels ? ' pulse' : ''}`} /></div><div className="connection-status-info"><strong>大模型</strong><span>{readyModels ? `${readyModels} 个 API 已连接，也可以继续使用本地 Agent` : '当前使用本地 Agent，可在管理中心接入模型 API'}</span></div><StatusBadge tone={readyModels ? 'green' : 'gray'}>{readyModels ? '已连接' : '本地模式'}</StatusBadge></div>
      <div className="connection-status-card"><div className="connection-status-icon"><UserCog size={18} /><span className={`status-dot ${state?.settings.configured ? 'green' : 'amber'}`} /></div><div className="connection-status-info"><strong>个人设置</strong><span>{state?.settings.configured ? '已经配置' : '尚未完成首次设置'}</span></div><StatusBadge tone={state?.settings.configured ? 'green' : 'amber'}>{state?.settings.configured ? '已配置' : '待配置'}</StatusBadge></div>
    </div></section>
  </div>
}