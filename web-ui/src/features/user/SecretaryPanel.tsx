import { useMemo, useState } from 'react'
import { FolderPlus, Send, Sparkles } from 'lucide-react'
import type { AppActions, GuiState, ProjectSummary } from '../../types'

function slugSuggestion(value: string) {
  const clean = value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fff]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 48)
  return clean || `project-${Date.now().toString(36)}`
}

function titleFromMessage(value: string) {
  const clean = value.trim().replace(/\s+/g, ' ')
  return clean.slice(0, 22) || '新项目'
}

export function SecretaryPanel({
  actions,
  state,
  fixedProject,
  compact = false,
}: {
  actions: AppActions
  state: GuiState | null
  fixedProject?: ProjectSummary
  compact?: boolean
}) {
  const projects = state?.projects.items || []
  const [mode, setMode] = useState<'existing' | 'new'>(fixedProject ? 'existing' : projects.length ? 'existing' : 'new')
  const [projectId, setProjectId] = useState(fixedProject?.project_id || projects[0]?.project_id || '')
  const [projectName, setProjectName] = useState('')
  const [message, setMessage] = useState('')
  const [localMessages, setLocalMessages] = useState<Array<{ from: 'user' | 'secretary'; text: string }>>([
    {
      from: 'secretary',
      text: fixedProject
        ? `你现在在「${fixedProject.name}」项目里。把新想法、补充资料或下一步工作告诉我，我会放进这个项目。`
        : '把你想做的事告诉我。我会先判断应该放进哪个项目，必要时帮你新建项目。',
    },
  ])
  const [submitting, setSubmitting] = useState(false)

  const selectedProject = useMemo(() => {
    if (fixedProject) return fixedProject
    return projects.find((project) => project.project_id === projectId)
  }, [fixedProject, projectId, projects])

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    const clean = message.trim()
    if (!clean) return
    setSubmitting(true)
    try {
      let targetProjectId = fixedProject?.project_id || projectId
      let targetProjectName = fixedProject?.name || selectedProject?.name || ''
      if (!fixedProject && mode === 'new') {
        targetProjectName = projectName.trim() || titleFromMessage(clean)
        const response = await actions.createProject({ name: targetProjectName, project_id: slugSuggestion(targetProjectName) })
        const project = response.project as { project_id?: string; name?: string } | undefined
        targetProjectId = project?.project_id || slugSuggestion(targetProjectName)
        targetProjectName = project?.name || targetProjectName
        setProjectId(targetProjectId)
        setMode('existing')
      }
      await actions.createWorkflow({ task: clean, priority: 'normal', project_id: targetProjectId || undefined })
      setLocalMessages((items) => [
        ...items,
        { from: 'user', text: clean },
        { from: 'secretary', text: targetProjectId ? `我已经把这件事放进「${targetProjectName || targetProjectId}」，并开始安排数字员工处理。` : '我已经记录下来，并开始安排数字员工处理。' },
      ])
      setMessage('')
      setProjectName('')
    } finally {
      setSubmitting(false)
    }
  }

  return <aside className={`secretary-panel ${compact ? 'compact' : ''}`}>
    <header>
      <span className="secretary-orb">秘</span>
      <div><strong>秘书</strong><small>{fixedProject ? '项目内对话' : '办公室对话'}</small></div>
    </header>
    <div className="secretary-context">
      <Sparkles size={16} />
      <span>{fixedProject ? `当前项目：${fixedProject.name}` : selectedProject ? `将放入：${selectedProject.name}` : '可以先新建项目'}</span>
    </div>
    {!fixedProject && <div className="project-choice">
      <button className={mode === 'existing' ? 'active' : ''} disabled={!projects.length} onClick={() => setMode('existing')} type="button">放进已有项目</button>
      <button className={mode === 'new' ? 'active' : ''} onClick={() => setMode('new')} type="button"><FolderPlus size={14} />新建项目</button>
      {mode === 'existing' && <select value={projectId} onChange={(event) => setProjectId(event.target.value)}>
        {projects.map((project) => <option key={project.project_id} value={project.project_id}>{project.name}</option>)}
      </select>}
      {mode === 'new' && <input value={projectName} onChange={(event) => setProjectName(event.target.value)} placeholder="项目名称，秘书会帮你整理" />}
    </div>}
    <div className="secretary-messages">
      {localMessages.map((item, index) => <div className={`secretary-message ${item.from}`} key={index}>{item.text}</div>)}
    </div>
    <form className="secretary-compose" onSubmit={submit}>
      <textarea value={message} onChange={(event) => setMessage(event.target.value)} placeholder={fixedProject ? '在这个项目里继续告诉秘书...' : '告诉秘书你想做什么...'} rows={compact ? 3 : 4} />
      <button className="primary-button" disabled={!message.trim() || submitting} type="submit"><Send size={16} />{submitting ? '安排中' : '发送给秘书'}</button>
    </form>
  </aside>
}
