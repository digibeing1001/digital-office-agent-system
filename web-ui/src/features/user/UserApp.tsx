import { Archive, CheckSquare2, Database, History, LayoutDashboard, ListTodo, Settings, Users } from 'lucide-react'
import { useState } from 'react'
import { AppShell, type NavItem } from '../../components/AppShell'
import type { AppActions, GuiState } from '../../types'
import { EmployeesPage } from './EmployeesPage'
import { OfficePage } from './OfficePage'
import { ApprovalsPage, DeliverablesPage, KnowledgePage, RecordsPage, SettingsPage, TasksPage } from './UserPages'

const navItems: NavItem[] = [
  { id: 'office', label: '我的办公室', icon: LayoutDashboard },
  { id: 'tasks', label: '任务', icon: ListTodo },
  { id: 'employees', label: '数字员工', icon: Users },
  { id: 'knowledge', label: '资料库', icon: Database },
  { id: 'approvals', label: '审批', icon: CheckSquare2 },
  { id: 'deliverables', label: '交付物', icon: Archive },
  { id: 'records', label: '工作记录', icon: History },
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
  else if (page === 'tasks') content = <TasksPage state={state} />
  else if (page === 'employees') content = <EmployeesPage actions={actions} state={state} />
  else if (page === 'knowledge') content = <KnowledgePage state={state} />
  else if (page === 'approvals') content = <ApprovalsPage actions={actions} state={state} />
  else if (page === 'deliverables') content = <DeliverablesPage state={state} />
  else if (page === 'records') content = <RecordsPage state={state} />
  else content = <SettingsPage state={state} />

  return <AppShell activePage={page} demoMode={demoMode} health={state?.health.status || 'degraded'} navItems={navItems} onNavigate={setPage} onToggleDemo={toggleDemo} surface="user" unread={state?.notifications.unread || 0}>{content}</AppShell>
}
