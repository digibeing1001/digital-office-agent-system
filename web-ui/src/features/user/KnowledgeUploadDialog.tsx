import { useMemo, useState } from 'react'
import { UploadCloud } from 'lucide-react'
import { Field, Modal } from '../../components/ui'
import type { AppActions, GuiState, UploadKnowledgeInput } from '../../types'

function guessKind(filename: string): UploadKnowledgeInput['kind'] {
  const ext = filename.split('.').pop()?.toLowerCase()
  if (!ext) return 'binary'
  if (['txt', 'md', 'csv', 'json', 'html'].includes(ext)) return 'text'
  if (['docx'].includes(ext)) return 'word'
  if (ext === 'pdf') return 'pdf'
  if (['png', 'jpg', 'jpeg', 'webp'].includes(ext)) return 'image'
  return 'binary'
}

function readFileAsBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(new Error('文件读取失败，请重新选择。'))
    reader.onload = () => {
      const value = String(reader.result || '')
      resolve(value.includes(',') ? value.split(',')[1] : value)
    }
    reader.readAsDataURL(file)
  })
}

export function KnowledgeUploadDialog({
  actions,
  state,
  defaultProjectId,
  defaultScope = 'project',
  onClose,
}: {
  actions: AppActions
  state: GuiState | null
  defaultProjectId?: string
  defaultScope?: 'company' | 'project'
  onClose: () => void
}) {
  const projects = state?.projects.items || []
  const firstProject = defaultProjectId || projects[0]?.project_id || ''
  const [scope, setScope] = useState<'company' | 'project'>(defaultScope)
  const [projectId, setProjectId] = useState(firstProject)
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [approve, setApprove] = useState(false)
  const [error, setError] = useState('')
  const targetName = useMemo(() => {
    if (scope === 'company') return '公司资料库'
    return projects.find((project) => project.project_id === projectId)?.name || '项目资料库'
  }, [projectId, projects, scope])

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError('')
    const cleanTitle = title.trim() || file?.name.replace(/\.[^.]+$/, '') || ''
    if (!cleanTitle) {
      setError('请给这份资料起一个名称。')
      return
    }
    if (scope === 'project' && !projectId) {
      setError('请先选择一个项目。')
      return
    }
    if (!file && !body.trim()) {
      setError('请选择文件，或者粘贴一段文字资料。')
      return
    }
    const payload: UploadKnowledgeInput = {
      scope,
      project_id: scope === 'project' ? projectId : undefined,
      title: cleanTitle,
      approve,
      notes: `由用户在 ${targetName} 上传`,
    }
    if (file) {
      payload.filename = file.name
      payload.mime_type = file.type
      payload.kind = guessKind(file.name)
      payload.content_base64 = await readFileAsBase64(file)
    } else {
      payload.body = body
      payload.kind = 'text'
    }
    await actions.uploadKnowledge(payload)
    onClose()
  }

  return <Modal title="上传资料" onClose={onClose} footer={<><button className="secondary-button" onClick={onClose}>取消</button><button className="primary-button" form="knowledge-upload-form" type="submit"><UploadCloud size={17} />上传</button></>}>
    <form className="form-grid upload-form" id="knowledge-upload-form" onSubmit={submit}>
      <Field label="放到哪里">
        <select value={scope} onChange={(event) => setScope(event.target.value as 'company' | 'project')}>
          <option value="project">项目资料库</option>
          <option value="company">公司资料库</option>
        </select>
      </Field>
      {scope === 'project' && <Field label="选择项目">
        <select value={projectId} onChange={(event) => setProjectId(event.target.value)}>
          {projects.map((project) => <option key={project.project_id} value={project.project_id}>{project.name}</option>)}
        </select>
      </Field>}
      <Field label="资料名称">
        <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="例如：客户需求记录、供应商合同、产品说明" />
      </Field>
      <Field label="选择文件" hint="支持文本、Markdown、Word、PDF、图片等常见资料。较大的文件建议拆分后上传。">
        <input type="file" onChange={(event) => setFile(event.target.files?.[0] || null)} />
      </Field>
      <Field label="或者直接粘贴文字">
        <textarea rows={6} value={body} onChange={(event) => setBody(event.target.value)} placeholder="把会议纪要、项目背景、客户要求等内容粘贴到这里。" />
      </Field>
      <label className="check-row"><input checked={approve} onChange={(event) => setApprove(event.target.checked)} type="checkbox" /><span>上传后允许数字员工直接使用这份资料</span></label>
      {error && <p className="form-error">{error}</p>}
    </form>
  </Modal>
}
