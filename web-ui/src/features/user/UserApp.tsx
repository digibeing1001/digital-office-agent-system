import { Database, FolderKanban, LayoutDashboard, Settings, Users } from 'lucide-react'
import { useState } from 'react'
import { AppShell, type NavItem } from '../../components/AppShell'
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
  { id: 'projects', label: '项目文件夹', icon: FolderKanban },
  { id: 'settings', label: '设置', icon: Settings },
]

export function UserApp({ state, actions }: { state: GuiState | null; actions: AppActions }) {
  const [page, setPage] = useState('office')
  const [demoMode, setDemoMode] = useState(() => localStorage.getItem('digital-office-demo') === 'true')

  const toggleDemo = () => {
    setDemoMode((current) => {
      localStorage.setItem('digital-office-demo', String(!current))
      return !current
    })
  }

  let content
  if (page === 'office') content = <OfficePage actions={actions} demoMode={demoMode} onOpenPage={setPage} state={state} />
  else if (page === 'employees') content = <EmployeesPage actions={actions} state={state} />
  else if (page === 'knowledge') content = <KnowledgePage actions={actions} state={state} />
  else if (page === 'projects') content = <ProjectsPage actions={actions} state={state} />
  else content = <SettingsPage state={state} />

  return <AppShell activePage={page} bottomNavItems={bottomNavItems} demoMode={demoMode} health={state?.health.status || 'degraded'} navItems={navItems} onNavigate={setPage} onToggleDemo={toggleDemo} surface="user" unread={state?.notifications.unread || 0}>{content}</AppShell>
}
