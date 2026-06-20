import { Database, LayoutDashboard, Settings, Users } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { AppShell, type NavItem, type ProjectNavigation } from '../../components/AppShell'
import type { AppActions, GuiState } from '../../types'
import { EmployeesPage } from './EmployeesPage'
import { OfficePage } from './OfficePage'
import { ProjectsPage } from './ProjectsPage'
import { KnowledgePage, SettingsPage } from './UserPages'

const navItems: NavItem[] = [
  { id: 'office', label: '我的办公室', icon: LayoutDashboard },
  { id: 'employees', label: '数字员工', icon: Users },
  { id: 'knowledge', label: '知识库', icon: Database },
]

const bottomNavItems: NavItem[] = [
  { id: 'settings', label: '设置', icon: Settings },
]

type UserPage = 'office' | 'employees' | 'knowledge' | 'projects' | 'settings'

const pageLabels: Record<UserPage, string> = {
  office: '我的办公室',
  employees: '数字员工',
  knowledge: '知识库',
  projects: '项目',
  settings: '设置',
}

interface UserLocation {
  page: UserPage
  projectId?: string
  conversationId?: string
}

const pages = new Set<UserPage>(['office', 'employees', 'knowledge', 'projects', 'settings'])

function safeDecode(value: string | undefined) {
  if (!value) return ''
  try {
    return decodeURIComponent(value)
  } catch {
    return value
  }
}

function readLocation(): UserLocation {
  const parts = window.location.hash.replace(/^#\/?/, '').split('/').filter(Boolean)
  const page = (pages.has(parts[0] as UserPage) ? parts[0] : 'office') as UserPage
  if (page !== 'projects') return { page }
  return {
    page,
    projectId: safeDecode(parts[1]) || undefined,
    conversationId: parts[2] === 'conversations' ? safeDecode(parts[3]) || undefined : undefined,
  }
}

function locationHash(location: UserLocation) {
  if (location.page !== 'projects') return `#/${location.page}`
  if (!location.projectId) return '#/projects'
  const project = encodeURIComponent(location.projectId)
  return location.conversationId ? `#/projects/${project}/conversations/${encodeURIComponent(location.conversationId)}` : `#/projects/${project}`
}

export function UserApp({ state, actions }: { state: GuiState | null; actions: AppActions }) {
  const [location, setLocation] = useState<UserLocation>(readLocation)
  const [demoMode, setDemoMode] = useState(() => localStorage.getItem('digital-office-demo') === 'true')
  const [expandedProjectIds, setExpandedProjectIds] = useState<string[]>([])
  const [createProjectKey, setCreateProjectKey] = useState(0)
  const projectTreeInitialized = useRef(false)

  const focusMain = () => window.requestAnimationFrame(() => document.getElementById('main-content')?.focus({ preventScroll: true }))

  const navigate = (next: UserLocation, replace = false) => {
    const nextHash = locationHash(next)
    if (replace) window.history.replaceState({ digitalOffice: true }, '', nextHash)
    else if (window.location.hash !== nextHash) window.history.pushState({ digitalOffice: true }, '', nextHash)
    setLocation(next)
    focusMain()
  }

  useEffect(() => {
    if (!window.location.hash) window.history.replaceState({ digitalOffice: true }, '', locationHash({ page: 'office' }))
    const onPopState = () => {
      setLocation(readLocation())
      focusMain()
    }
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  useEffect(() => {
    const projects = state?.projects.items || []
    if (!projectTreeInitialized.current && projects.length) {
      setExpandedProjectIds(projects.slice(0, 2).map((project) => project.project_id))
      projectTreeInitialized.current = true
    }
  }, [state?.projects.items])

  useEffect(() => {
    if (!location.projectId) return
    setExpandedProjectIds((current) => current.includes(location.projectId!) ? current : [...current, location.projectId!])
  }, [location.projectId])

  const toggleDemo = () => {
    setDemoMode((current) => {
      localStorage.setItem('digital-office-demo', String(!current))
      return !current
    })
  }

  const openPage = (page: string) => navigate({ page: pages.has(page as UserPage) ? page as UserPage : 'office' })
  const openProjects = () => navigate({ page: 'projects' })
  const openProject = (projectId: string) => navigate({ page: 'projects', projectId })
  const openConversation = (projectId: string, conversationId: string) => navigate({ page: 'projects', projectId, conversationId })
  const openCreateProject = () => {
    navigate({ page: 'projects' })
    setCreateProjectKey((current) => current + 1)
  }
  const toggleProject = (projectId: string) => setExpandedProjectIds((current) => current.includes(projectId) ? current.filter((item) => item !== projectId) : [...current, projectId])

  const selectedProject = state?.projects.items.find((project) => project.project_id === location.projectId)
  const selectedConversation = state?.workflows.recent.find((run) => run.project_id === location.projectId && run.run_id === location.conversationId)
  const projectNavigation = useMemo<ProjectNavigation>(() => ({
    projects: (state?.projects.items || []).map((project) => ({
      id: project.project_id,
      name: project.name,
      conversations: (state?.workflows.recent || [])
        .filter((run) => run.project_id === project.project_id)
        .map((run) => ({ id: run.run_id, title: run.title || '未命名对话' })),
    })),
    expandedProjectIds,
    activeProjectId: location.projectId,
    activeConversationId: location.conversationId,
    onOpenProjects: openProjects,
    onOpenProject: openProject,
    onOpenConversation: openConversation,
    onToggleProject: toggleProject,
    onCreateProject: openCreateProject,
  }), [state?.projects.items, state?.workflows.recent, expandedProjectIds, location.projectId, location.conversationId])

  const goBack = () => {
    if (location.conversationId && location.projectId) navigate({ page: 'projects', projectId: location.projectId })
    else if (location.projectId) navigate({ page: 'projects' })
    else navigate({ page: 'office' })
  }

  const backLabel = location.conversationId ? '返回项目' : location.projectId ? '返回项目列表' : '返回我的办公室'
  const breadcrumbs = location.conversationId
    ? ['项目', selectedProject?.name || location.projectId || '', selectedConversation?.title || '项目对话']
    : location.projectId ? ['项目', selectedProject?.name || location.projectId] : []
  const pageTitle = selectedConversation?.title || selectedProject?.name || pageLabels[location.page]

  let content
  if (location.page === 'office') content = <OfficePage actions={actions} demoMode={demoMode} onOpenPage={openPage} state={state} />
  else if (location.page === 'employees') content = <EmployeesPage actions={actions} state={state} />
  else if (location.page === 'knowledge') content = <KnowledgePage actions={actions} onOpenProject={openProject} state={state} />
  else if (location.page === 'projects') content = <ProjectsPage actions={actions} createProjectKey={createProjectKey} onOpenConversation={(conversationId) => location.projectId && openConversation(location.projectId, conversationId)} onSelectProject={openProject} selectedConversationId={location.conversationId || ''} selectedId={location.projectId || ''} state={state} />
  else content = <SettingsPage state={state} />

  return <AppShell activePage={location.page} backLabel={backLabel} breadcrumbs={breadcrumbs.filter(Boolean)} bottomNavItems={bottomNavItems} demoMode={demoMode} health={state?.health.status || 'degraded'} navItems={navItems} onBack={location.page === 'office' ? undefined : goBack} onNavigate={openPage} onToggleDemo={toggleDemo} pageTitle={pageTitle} projectNavigation={projectNavigation} surface="user" unread={state?.notifications.unread || 0}>{content}</AppShell>
}
