import { useEffect, useMemo, useRef, useState } from 'react'
import { Check, FileUp, FolderPlus, Send, ShieldAlert, Sparkles } from 'lucide-react'
import type { AppActions, GuiState, ProjectContextInput, ProjectContextQuestion, ProjectSummary } from '../../types'

type SecretaryMode = 'chat' | 'existing' | 'new'

function slugSuggestion(value: string) {
  const clean = value.trim().toLowerCase().replace(/[^a-z0-9一-鿿]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 48)
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
  const [mode, setMode] = useState<SecretaryMode>(fixedProject ? 'existing' : 'chat')
  const [projectId, setProjectId] = useState(fixedProject?.project_id || '')
  const [projectName, setProjectName] = useState('')
  const [message, setMessage] = useState('')
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [localMessages, setLocalMessages] = useState<Array<{ from: 'user' | 'secretary'; text: string }>>([])
  const [suggestedProject, setSuggestedProject] = useState<{ name: string; id: string } | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [thinking, setThinking] = useState(false)
  const [contextError, setContextError] = useState('')
  const endRef = useRef<HTMLDivElement>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const selectedProject = useMemo(() => fixedProject || (mode === 'existing' ? projects.find((project) => project.project_id === projectId) : undefined), [fixedProject, mode, projectId, projects])
  const readiness = selectedProject?.context_readiness
  const setupRequired = Boolean(selectedProject && readiness?.required && !readiness.confirmed)
  const questions = readiness?.suggestions || []

  useEffect(() => {
    if (fixedProject) {
      setMode('existing')
      setProjectId(fixedProject.project_id)
    }
  }, [fixedProject?.project_id])

  useEffect(() => {
    if (mode === 'existing' && !projectId && projects[0]?.project_id) {
      setProjectId(projects[0].project_id)
    }
  }, [mode, projectId, projects])

  useEffect(() => {
    setSuggestedProject(null)
    setLocalMessages([{
      from: 'secretary',
      text: selectedProject
        ? `这里是「${selectedProject.name}」。我会先和你把意图与关键资料对齐，确认后再正式安排数字员工。`
        : '你好，我在。这里默认是普通对话；如果要开始一项正式工作，请点击输入框上方的「新建项目」。',
    }])
  }, [selectedProject?.project_id])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }, [localMessages, suggestedProject, submitting, thinking, readiness?.confirmed, questions.length])

  const startNewProject = (name = '', id = '') => {
    setMode('new')
    setSuggestedProject(null)
    setProjectName(name)
    if (id) setProjectId(id)
    setLocalMessages((items) => [...items, { from: 'secretary', text: '好的，我们先进入新建项目流程。请简单说明这件事的目标，我会先复述意图，再用至少三个关键问题帮你补齐项目底稿。' }])
  }

  const switchToExistingProject = () => {
    setMode('existing')
    setSuggestedProject(null)
    if (!projectId && projects[0]?.project_id) setProjectId(projects[0].project_id)
  }

  const createOrDispatch = async (event: React.FormEvent) => {
    event.preventDefault()
    const clean = message.trim()
    if (!clean) return
    setSubmitting(true)
    setThinking(true)
    setLocalMessages((items) => [...items, { from: 'user', text: clean }])
    try {
      if (!fixedProject && mode === 'new') {
        const targetName = projectName.trim() || titleFromMessage(clean)
        const response = await actions.createProject({ name: targetName, project_id: slugSuggestion(targetName), brief: clean })
        const project = response.project as { project_id?: string; name?: string } | undefined
        const targetId = project?.project_id || slugSuggestion(targetName)
        setProjectId(targetId)
        setMode('existing')
        setLocalMessages((items) => [...items, { from: 'secretary', text: `我理解你希望围绕「${project?.name || targetName}」推进：${clean.slice(0, 80)}。请先确认我的理解，再回答下方至少三个关键问题；我会据此整理项目底稿。` }])
      } else if (!selectedProject) {
        const preview = await actions.secretaryChat({ message: clean, execute: true, runtime: 'auto', execution_timeout: 120 })
        setLocalMessages((items) => [...items, { from: 'secretary', text: preview.reply }])
        if (preview.should_create_project) {
          setSuggestedProject({ name: preview.suggested_project_name || titleFromMessage(clean), id: preview.suggested_project_id || slugSuggestion(clean) })
        } else {
          setSuggestedProject(null)
        }
      } else if (setupRequired) {
        setLocalMessages((items) => [...items, { from: 'secretary', text: '我已经把这条补充记在当前对话里。为了让它真正进入项目底稿，请继续填写下方最关键的三个问题。' }])
      } else {
        const activeProject = selectedProject!
        const workflow = await actions.createWorkflow({ task: clean, priority: 'normal', project_id: activeProject.project_id, execute: true, runtime: 'auto', execution_timeout: 300 })
        const execution = workflow.execution as { status?: string; output_excerpt?: string; diagnostics_excerpt?: string } | null | undefined
        const reply = execution?.status === 'completed'
          ? `已确认意图和项目底稿，并完成第一轮 Agent 执行。${execution.output_excerpt ? `\n\n${execution.output_excerpt.slice(0, 600)}` : ''}`
          : `已把这项工作放进「${activeProject.name}」的 Loop 记录。${execution?.diagnostics_excerpt ? `\n\n执行诊断：${execution.diagnostics_excerpt.slice(0, 400)}` : '如果本地 Agent 或 API 还未就绪，请在管理中心选择可用运行方式。'}`
        setLocalMessages((items) => [...items, { from: 'secretary', text: reply }])
        setMessage('')
        if (mode !== 'new') setProjectName('')
        return
      }
      setMessage('')
      if (mode !== 'new') setProjectName('')
    } finally {
      setSubmitting(false)
      setThinking(false)
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

  const pendingJudgments = (state?.judgments?.recent || []).filter((jc) => {
    if (jc.status !== "pending") return false
    if (!selectedProject) return false
    return (state?.workflows.recent || []).some((w) => w.run_id === jc.workflow_run_id && w.project_id === selectedProject.project_id)
  })
  const [judging, setJudging] = useState(false)
  const handleJudgment = async (caseId: string, decision: string, workflowRunId: string) => {
    setJudging(true)
    try {
      const result = await actions.decideJudgment(caseId, decision, workflowRunId, decision === "approve" ? "批准并继续执行" : "")
      const resume = result?.resume as { status?: string } | undefined
      if (resume) {
        setLocalMessages((items) => [...items, { from: "secretary", text: decision === "approve" ? `已批准这项判断，工作流正在恢复（${resume.status || "resuming"}）。` : `已记录决定：${decision}。` }])
      }
    } finally {
      setJudging(false)
    }
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
    <header><span className="secretary-orb">秘</span><div><strong>秘书</strong><small>{selectedProject ? `${selectedProject.name} · 项目对话` : '我的办公室 · 普通对话'}</small></div>{readiness && <span className={`context-score ${readiness.confirmed ? 'ready' : ''}`}>{readiness.confirmed ? '底稿已确认' : `准备度 ${readiness.readiness_score}%`}</span>}</header>
    <div className="secretary-context"><Sparkles size={16} /><span>{selectedProject ? '当前项目的目标、资料和确认记录会随 Loop 一直保留' : '普通聊天不会自动创建项目；正式工作请先进入新建项目流程'}</span></div>
    <div className="secretary-messages" role="log" aria-live="polite" aria-label="与秘书的对话">{localMessages.map((item, index) => <div className={`secretary-message secretary-message--${item.from}`} key={`${item.from}-${index}`}>{item.text}</div>)}
      {thinking && <div className="secretary-message secretary-message--secretary thinking-bubble"><span className="thinking-dots"><i></i><i></i><i></i></span></div>}
      {suggestedProject && <div className="secretary-suggestion-card"><span>秘书建议</span><strong>这句话可能适合新建项目</strong><p>如果这项工作需要沉淀资料、交付物和过程记录，请进入项目流程；如果只是聊天，可以继续直接问我。</p><div className="secretary-suggestion-card__actions"><button className="suggestion-pill suggestion-pill--primary" type="button" onClick={() => startNewProject(suggestedProject.name, suggestedProject.id)}><FolderPlus size={16} />新建项目</button><button className="suggestion-pill" type="button" onClick={() => setSuggestedProject(null)}>
继续聊天</button></div></div>}
      {setupRequired && readiness?.intent && <div className="intent-confirmation"><span>秘书对你的意图理解</span><strong>{readiness.intent.summary || '尚未形成意图摘要'}</strong><p>请检查目标和对象是否准确。确认后，核心目标发生变化会要求重新确认。</p>{!readiness.intent.confirmed ? <button className="suggestion-pill suggestion-pill--primary" onClick={() => void confirmIntent()}><Check size={16} />这就是我的意思</button> : <span className="confirmed-mark"><Check size={15} />意图已确认</span>}</div>}
      {setupRequired && <div className="socratic-questions"><div className="question-heading"><div><span>建立项目底稿</span><strong>请至少回答三个关键问题</strong></div><button className="tool-chip" disabled={!selectedProject} onClick={() => fileRef.current?.click()}><FileUp size={16} />
上传依据</button></div>{questions.map((question, index) => <label key={`${question.field}-${index}`}><span>{index + 1}</span><div><strong>{question.prompt}</strong><small>{question.why}</small><textarea rows={2} value={answers[`${question.field}-${index}`] || ''} onChange={(event) => setAnswers({ ...answers, [`${question.field}-${index}`]: event.target.value })} placeholder="把你的判断、事实或不确定之处写在这里" /></div></label>)}{contextError && <p className="form-error">{contextError}</p>}<div className="question-actions"><button className="suggestion-pill suggestion-pill--primary" onClick={() => void saveAnswers()}>
交给秘书整理</button>{readiness?.ready && readiness.intent?.confirmed && <button className="suggestion-pill" onClick={() => selectedProject && void actions.confirmProjectContext(selectedProject.project_id)}><Check size={16} />
确认项目底稿并开始工作</button>}</div></div>}
      {pendingJudgments.length > 0 && <div className="judgment-cards">{pendingJudgments.map((jc) => <div className="judgment-card" key={jc.case_id}><div className="judgment-card__header"><ShieldAlert size={18} /><div><strong>需要你的判断</strong><small>{jc.required_human_role} · 风险：{jc.risk_label}</small></div></div>{jc.reason && <p className="judgment-card__reason">{jc.reason}</p>}{jc.triggers && jc.triggers.length > 0 && <div className="judgment-card__triggers">{jc.triggers.map((tr, i) => <span key={i} className="judgment-trigger">{String(tr.type || "unknown")} · {String(tr.confidence || "")}</span>)}</div>}<div className="judgment-card__actions"><button className="suggestion-pill suggestion-pill--primary" disabled={judging} onClick={() => void handleJudgment(jc.case_id, "approve", jc.workflow_run_id)}><Check size={16} />批准并继续</button><button className="suggestion-pill" disabled={judging} onClick={() => void handleJudgment(jc.case_id, "request_evidence", jc.workflow_run_id)}>要求补充证据</button><button className="suggestion-pill" disabled={judging} onClick={() => void handleJudgment(jc.case_id, "reject", jc.workflow_run_id)}>拒绝</button></div></div>)}</div>}
      <div ref={endRef} />
    </div>
    {!fixedProject && <div className="secretary-intake-toolbar">
      <button className={`tool-chip ${mode === 'new' ? 'tool-chip--active' : ''}`} type="button" onClick={() => startNewProject(projectName)}><FolderPlus size={14} />
新建项目</button>
      <button className={`tool-chip ${mode === 'existing' ? 'tool-chip--active' : ''}`} disabled={!projects.length} type="button" onClick={switchToExistingProject}>
放入已有项目</button>
      <button className={`tool-chip ${mode === 'chat' ? 'tool-chip--active' : ''}`} type="button" onClick={() => { setMode('chat'); setSuggestedProject(null) }}>
普通对话</button>
      {mode === 'existing' && <select value={projectId} onChange={(event) => setProjectId(event.target.value)}>{projects.map((project) => <option key={project.project_id} value={project.project_id}>{project.name}</option>)}</select>}
      {mode === 'new' && <input value={projectName} onChange={(event) => setProjectName(event.target.value)} placeholder="项目名称可留空，秘书会根据你的说明命名" />}
    </div>}
    <form className="secretary-compose" onSubmit={createOrDispatch}><textarea value={message} onChange={(event) => setMessage(event.target.value)} placeholder={!selectedProject ? (mode === 'new' ? '说明这个新项目要完成什么...' : '直接问秘书问题；正式工作请先点上方「新建项目」...') : setupRequired ? '补充你的想法；正式信息请填写上方问题...' : '在这个项目里继续安排工作...'} rows={compact ? 3 : 4} /><div className="compose-actions"><button className="compose-file-btn" disabled={!selectedProject} onClick={() => fileRef.current?.click()} title="上传项目资料" type="button"><FileUp size={18} /></button><button className={`compose-send-btn ${message.trim() && !submitting ? 'compose-send-btn--active' : ''}`} disabled={!message.trim() || submitting} type="submit">{submitting ? '...' : <Send size={16} />}</button></div></form>
    <input ref={fileRef} className="visually-hidden" type="file" onChange={(event) => void uploadFile(event)} />
  </section>
}
