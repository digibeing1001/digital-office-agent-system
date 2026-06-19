import { useMemo, useState } from 'react'
import { Archive, Briefcase, Database, FolderKanban, Search, Settings, UploadCloud, UserRound } from 'lucide-react'
import { EmptyState, PageHeading, StatusBadge } from '../../components/ui'
import { formatTime } from '../../lib/presentation'
import type { AppActions, GuiState } from '../../types'
import { KnowledgeUploadDialog } from './KnowledgeUploadDialog'

export function KnowledgePage({ state, actions }: { state: GuiState | null; actions: AppActions }) {
  const [showUpload, setShowUpload] = useState(false)
  const [activeTab, setActiveTab] = useState<'company' | 'projects' | 'personal'>('company')
  const projectEntryTotal = useMemo(() => Object.values(state?.knowledge.project_entries || {}).reduce((total, item) => total + item.count, 0), [state])
  const personalSpaces = (state?.knowledge.spaces.items || []).filter((space) => String(space.space_type || '').includes('personal'))

  return <div className="standard-page knowledge-page">
    <PageHeading title="知识库" description="公司资料、项目资料和个人资料都在这里。日常项目资料建议直接进项目文件夹管理。" action={<button className="primary-button" onClick={() => setShowUpload(true)}><UploadCloud size={17} />上传资料</button>} />
    <div className="knowledge-tabs" role="tablist">
      <button className={activeTab === 'company' ? 'active' : ''} onClick={() => setActiveTab('company')}><Database size={17} />公司知识库</button>
      <button className={activeTab === 'projects' ? 'active' : ''} onClick={() => setActiveTab('projects')}><FolderKanban size={17} />项目知识库</button>
      <button className={activeTab === 'personal' ? 'active' : ''} onClick={() => setActiveTab('personal')}><UserRound size={17} />个人知识库</button>
    </div>
    <div className="knowledge-summary"><div><Database size={22} /><strong>{state?.knowledge.company_entries || 0}</strong><span>公司资料</span></div><div><FolderKanban size={22} /><strong>{projectEntryTotal}</strong><span>项目资料</span></div><div><Archive size={22} /><strong>{personalSpaces.length}</strong><span>个人空间</span></div></div>
    <label className="large-search"><Search size={18} /><input placeholder="搜索资料、项目和交付物" /></label>
    {activeTab === 'company' && <section className="plain-card knowledge-panel">
      <header><h2>公司知识库</h2><span>适合放公司介绍、产品资料、制度、通用模板</span></header>
      {(state?.knowledge.company_entries || 0) ? <div className="document-list"><div className="document-row"><span className="file-symbol"><Database size={17} /></span><div><strong>公司资料</strong><span>{state?.knowledge.company_entries || 0} 份资料可供授权数字员工使用</span></div></div></div> : <EmptyState title="公司知识库还没有资料" body="上传公司介绍、业务说明、制度模板等通用资料。" />}
    </section>}
    {activeTab === 'projects' && <section className="plain-card knowledge-panel">
      <header><h2>项目知识库</h2><span>每个项目都有自己的资料夹</span></header>
      <div className="document-list">
        {(state?.projects.items || []).map((project) => {
          const entries = state?.knowledge.project_entries?.[project.project_id]
          return <div className="document-row" key={project.project_id}><span className="file-symbol"><FolderKanban size={17} /></span><div><strong>{project.name}</strong><span>{entries?.count || 0} 份资料 · 进入项目文件夹可继续管理</span></div></div>
        })}
        {!state?.projects.items.length && <EmptyState title="还没有项目知识库" body="创建项目后，这里会自动出现对应项目资料。" />}
      </div>
    </section>}
    {activeTab === 'personal' && <section className="plain-card knowledge-panel">
      <header><h2>个人知识库</h2><span>适合放只和你有关的偏好、草稿和私有资料</span></header>
      <div className="document-list">
        {personalSpaces.map((space, index) => <div className="document-row" key={String(space.space_id || index)}><span className="file-symbol"><UserRound size={17} /></span><div><strong>{String(space.name || space.space_id || '个人资料')}</strong><span>{String(space.description || '只有授权后才会被数字员工使用')}</span></div></div>)}
        {!personalSpaces.length && <EmptyState title="还没有个人知识库" body="后续可以在这里放个人常用资料和偏好。" />}
      </div>
    </section>}
    {showUpload && <KnowledgeUploadDialog actions={actions} defaultScope="company" onClose={() => setShowUpload(false)} state={state} />}
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
