import { Activity, Bot, Boxes, FileClock, Gauge, Settings, ShieldCheck } from 'lucide-react'
import { useState } from 'react'
import { AppShell, type NavItem } from '../../components/AppShell'
import type { AppActions, GuiState } from '../../types'
import { AdminAgents, AdminAudit, AdminOverview, AdminPolicy, AdminRuns, AdminSkills, AdminSystem } from './AdminPages'

const navItems: NavItem[] = [
  { id: 'overview', label: '系统概览', icon: Gauge },
  { id: 'agents', label: 'Agent 管理', icon: Bot },
  { id: 'skills', label: 'Skills', icon: Boxes },
  { id: 'runs', label: '运行监控', icon: Activity },
  { id: 'policy', label: '权限与预算', icon: ShieldCheck },
  { id: 'audit', label: '审计', icon: FileClock },
  { id: 'system', label: '系统维护', icon: Settings },
]

export function AdminApp({ state, actions }: { state: GuiState | null; actions: AppActions }) {
  const [page, setPage] = useState('overview')
  let content
  if (page === 'overview') content = <AdminOverview state={state} />
  else if (page === 'agents') content = <AdminAgents actions={actions} state={state} />
  else if (page === 'skills') content = <AdminSkills state={state} />
  else if (page === 'runs') content = <AdminRuns state={state} />
  else if (page === 'policy') content = <AdminPolicy state={state} />
  else if (page === 'audit') content = <AdminAudit state={state} />
  else content = <AdminSystem state={state} />
  return <AppShell activePage={page} health={state?.health.status || 'degraded'} navItems={navItems} onNavigate={setPage} surface="admin" unread={state?.notifications.unread || 0}>{content}</AppShell>
}
