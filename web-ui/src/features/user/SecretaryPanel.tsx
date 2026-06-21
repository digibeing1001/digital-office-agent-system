import { useEffect, useMemo, useRef, useState } from 'react'
import { Check, FileUp, FolderPlus, Send, Sparkles } from 'lucide-react'
import type { AppActions, GuiState, ProjectContextInput, ProjectContextQuestion, ProjectSummary } from '../../types'

function slugSuggestion(value: string) {
  const clean = value.trim().toLowerCase().replace(/[^a-z0-9\u4e00-\u9fff]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 48)
  return clean || `project-${Date.now().toString(36)}`
}

function titleFromMessage(value: string) {
  return value.trim().replace(/\s+/g, ' ').slice(0, 22) || '新项目'
}

function splitItems(value: string) {
  return value.split(/[\n；;]/).map((item) => item.trim()).filter(Boolean)
}

function answerPatch(questions: ProjectContextQuestion[], answers: Record<string, string>, base: ProjectContextInput = {}): ProjectContextInput {
  const patch: ProjectContextInput = {}
  questions.forEach((question, index) => {
    const answer = answers[`${question.field}-${index}`]?.trim()
    if (!answer) return
    if (question.field === 'goal') patch.goal = answer
    else if (question.field === 'deadline') patch.deadline = answer
    else if (question.field === 'open_questions') patch.open_questions = [...(base.open_questions || []), ...(patch.open_questions || []), ...splitItems(answer).map((item) => ({ question: item, critical: false }))]
    else if (question.field === 'sources' || question.field === 'source_refs') patch.source_refs = [...(base.source_refs || []), ...(patch.source_refs || []), ...splitItems(answer)]
    else if (question.field === 'deliverables') patch.deliverables = [...(base.deliverables || []), ...(patch.deliverables || []), ...splitItems(answer)]
    else if (question.field === 'acceptance_criteria') patch.acceptance_criteria = [...(base.acceptance_criteria || []), ...(patch.acceptance_criteria || []), ...splitItems(answer)]
    else if (question.field === 'constraints') patch.constraints = [...(base.constraints || []), ...(patch.constraints || []), ...splitItems(answer)]
  })
  return patch
}

export function SecretaryPanel({ actions, state, fixedProject, compact = false }: { actions: AppActions; state: GuiState | null; fixedProject?: ProjectSummary; compact?: boolean }) {
  const projects = state?.projects.items || []
  const [mode, setMode] = useState<'existing' | 'new'>(fixedProject ? 'existing' : projects.length ? 'existing' : 'new')
  const [projectId, setProjectId] = useState(fixedProject?.project_id || projects[0]?.project_id || '')
  const [projectName, setProjectName] = useState('')
  const [message, setMessage] = useState('')
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [localMessages, setLocalMessages] = useState<Array<{ from: 'user' | 'secretary'; text: string }>>([])
  const [submitting, setSubmitting] = useState(false)
  const [contextError, setContextError] = useState('')
  const endRef = useRef<HTMLDivElement>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const selectedProject = useMemo(() => fixedProject || (mode === 'existing' ? projects.find((project) => project.project_id === projectId) : undefined), [fixedProject, mode, projectId, projects])
  const readiness = selectedProject?.context_readiness
  const setupRequired = Boolean(selectedProject && readiness?.required && !readiness.confirmed)
  const questions = readiness?.suggestions || []

  useEffect(() => {
    setLocalMessages([{ from: 'secretary', text: selectedProject ? `这里是「${selectedProject.name}」。我会先和你把意图与关键资料对齐，确认后再正式安排数字员工。` : '把你想做的事告诉我。我会先复述你的意图，再用几个关键问题帮你建立项目。' }])
  }, [selectedProject?.project_id])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }, [localMessages, submitting, readiness?.confirmed, questions.length])

  const createOrDispatch = async (event: React.FormEvent) => {
    event.preventDefault()
    const clean = message.trim()
    if (!clean) return
    setSubmitting(true)
    try {
      if (!fixedProject && mode === 'new') {
        const targetName = projectName.trim() || titleFromMessage(clean)
        const response = await actions.createProject({ name: targetName, project_id: slugSuggestion(targetName), brief: clean })
        const project = response.project as { project_id?: string; name?: string } | undefined
        const targetId = project?.project_id || slugSuggestion(targetName)
        setProjectId(targetId)
        setMode('existing')
        setLocalMessages((items) => [...items, { from: 'user', text: clean }, { from: 'secretary', text: `我理解你希望围绕“${clean.slice(0, 80)}”建立「${project?.name || targetName}」。先请确认我的理解，再回答下面至少三个问题；我会据此整理项目底稿。` }])
      } else if (setupRequired) {
        setLocalMessages((items) => [...items, { from: 'user', text: clean }, { from: 'secretary', text: '我已经把这条补充记在当前对话里。为了让它真正进入项目底稿，请继续填写下方最关键的三个问题。' }])
      } else {
        await actions.createWorkflow({ task: clean, priority: 'normal', project_id: selectedProject?.project_id })
        setLocalMessages((items) => [...items, { from: 'user', text: clean }, { from: 'secretary', text: `已确认意图和项目底稿。我会把这项工作放进「${selectedProject?.name || '当前项目'}」，并按 Loop 记录过程、用量和交付物。` }])
      }
      setMessage('')
      setProjectName('')
    } finally {
      setSubmitting(false)
    }
  }

  const confirmIntent = async () => {
    if (!selectedProject || !readiness?.intent) return
    await actions.confirmProjectIntent(selectedProject.project_id, readiness.intent.hash)
  }

  const saveAnswers = async () => {
    if (!selectedProject) return
    const answered = Object.values(answers).filter((value) => value.trim()).length
    if (answered < 3) {
      setContextError('请至少回答三个问题。它们决定项目的目标、验收方式和事实依据。')
      return
    }
    setContextError('')
    await actions.updateProjectContext(selectedProject.project_id, answerPatch(questions, answers, readiness?.context || {}))
    setAnswers({})
  }

  const uploadFile = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file || !selectedProject) return
    const base64 = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(String(reader.result).split(',')[1] || '')
      reader.onerror = () => reject(reader.error)
      reader.readAsDataURL(file)
    })
    await actions.uploadKnowledge({ scope: 'project', project_id: selectedProject.project_id, title: file.name, filename: file.name, mime_type: file.type, content_base64: base64, notes: '由用户在秘书对话中补充的项目依据。' })
    setLocalMessages((items) => [...items, { from: 'secretary', text: `已把「${file.name}」放进项目资料库。它会作为后续判断的来源，而不是被反复复制进上下文。` }])
    event.target.value = ''
  }

  return <section className={`secretary-panel ${compact ? 'compact' : ''}`}>
    <header><span className="secretary-orb">秘</span><div><strong>秘书</strong><small>{selectedProject ? `${selectedProject.name} · 项目对话` : '我的办公室 · 新建项目'}</small></div>{readiness && <span className={`context-score ${readiness.confirmed ? 'ready' : ''}`}>{readiness.confirmed ? '底稿已确认' : `准备度 ${readiness.readiness_score}%`}</span>}</header>
    <div className="secretary-context"><Sparkles size={16} /><span>{selectedProject ? '当前项目的目标、资料和确认记录会随 Loop 一直保留' : '秘书会先理解，再追问，确认后才执行'}</span>{!fixedProject && selectedProject && <button className="text-button" type="button" onClick={() => setMode('new')}><FolderPlus size={14} />新建项目</button>}</div>
    {!fixedProject && !selectedProject && <div className="project-choice"><button className={mode === 'existing' ? 'active' : ''} disabled={!projects.length} onClick={() => setMode('existing')} type="button">已有项目</button><button className={mode === 'new' ? 'active' : ''} onClick={() => setMode('new')} type="button"><FolderPlus size={14} />新建项目</button>{mode === 'existing' && <select value={projectId} onChange={(event) => setProjectId(event.target.value)}>{projects.map((project) => <option key={project.project_id} value={project.project_id}>{project.name}</option>)}</select>}{mode === 'new' && <input value={projectName} onChange={(event) => setProjectName(event.target.value)} placeholder="项目名称可留空，由秘书建议" />}</div>}
    <div className="secretary-messages">{localMessages.map((item, index) => <div className={`secretary-message ${item.from}`} key={`${item.from}-${index}`}>{item.text}</div>)}
      {setupRequired && readiness?.intent && <div className="intent-confirmation"><span>秘书对你的意图理解</span><strong>{readiness.intent.summary || '尚未形成意图摘要'}</strong><p>请检查目标和对象是否准确。确认后，核心目标发生变化会要求重新确认。</p>{!readiness.intent.confirmed ? <button className="primary-button" onClick={() => void confirmIntent()}><Check size={16} />这就是我的意思</button> : <span className="confirmed-mark"><Check size={15} />意图已确认</span>}</div>}
      {setupRequired && <div className="socratic-questions"><div className="question-heading"><div><span>建立项目底稿</span><strong>请至少回答三个关键问题</strong></div><button className="secondary-button" disabled={!selectedProject} onClick={() => fileRef.current?.click()}><FileUp size={16} />上传依据</button></div>{questions.map((question, index) => <label key={`${question.field}-${index}`}><span>{index + 1}</span><div><strong>{question.prompt}</strong><small>{question.why}</small><textarea rows={2} value={answers[`${question.field}-${index}`] || ''} onChange={(event) => setAnswers({ ...answers, [`${question.field}-${index}`]: event.target.value })} placeholder="把你的判断、事实或不确定之处写在这里" /></div></label>)}{contextError && <p className="form-error">{contextError}</p>}<div className="question-actions"><button className="primary-button" onClick={() => void saveAnswers()}>交给秘书整理</button>{readiness?.ready && readiness.intent?.confirmed && <button className="secondary-button" onClick={() => selectedProject && void actions.confirmProjectContext(selectedProject.project_id)}><Check size={16} />确认项目底稿并开始工作</button>}</div></div>}
      <div ref={endRef} />
    </div>
    <form className="secretary-compose" onSubmit={createOrDispatch}><textarea value={message} onChange={(event) => setMessage(event.target.value)} placeholder={!selectedProject ? '告诉秘书你想完成什么…' : setupRequired ? '补充你的想法；正式信息请填写上方问题…' : '在这个项目里继续安排工作…'} rows={compact ? 3 : 4} /><div className="compose-actions"><button className="icon-button" disabled={!selectedProject} onClick={() => fileRef.current?.click()} title="上传项目资料" type="button"><FileUp size={18} /></button><button className="primary-button" disabled={!message.trim() || submitting} type="submit"><Send size={16} />{submitting ? '处理中' : setupRequired ? '补充说明' : selectedProject ? '发送并执行' : '告诉秘书'}</button></div></form>
    <input ref={fileRef} className="visually-hidden" type="file" onChange={(event) => void uploadFile(event)} />
  </section>
}
