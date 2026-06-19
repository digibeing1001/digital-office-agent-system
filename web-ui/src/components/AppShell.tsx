import type { ComponentType, ReactNode } from 'react'
import { Bell, Building2, ChevronRight, Menu, Settings, ShieldCheck, X } from 'lucide-react'
import { useState } from 'react'

export interface NavItem {
  id: string
  label: string
  icon: ComponentType<{ size?: number; strokeWidth?: number }>
}

interface AppShellProps {
  surface: 'user' | 'admin'
  navItems: NavItem[]
  activePage: string
  onNavigate: (id: string) => void
  health: string
  unread: number
  demoMode?: boolean
  onToggleDemo?: () => void
  children: ReactNode
}

export function AppShell({ surface, navItems, activePage, onNavigate, health, unread, demoMode, onToggleDemo, children }: AppShellProps) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const target = surface === 'user' ? '/admin' : '/'
  const targetLabel = surface === 'user' ? '管理中心' : '返回用户端'

  const navigate = (id: string) => {
    onNavigate(id)
    setMobileOpen(false)
  }

  return <div className={`app-shell ${surface}`}>
    <aside className={`sidebar ${mobileOpen ? 'open' : ''}`}>
      <div className="brand-row">
        <span className="brand-mark"><Building2 size={20} /></span>
        <div><strong>Digital Office</strong><span>{surface === 'user' ? '数字办公室' : '管理中心'}</span></div>
        <button aria-label="关闭菜单" className="mobile-close icon-button" onClick={() => setMobileOpen(false)}><X size={19} /></button>
      </div>
      <nav aria-label={surface === 'user' ? '用户端导航' : '管理端导航'}>
        {navItems.map(({ id, label, icon: Icon }) => <button className={activePage === id ? 'nav-button active' : 'nav-button'} key={id} onClick={() => navigate(id)}>
          <Icon size={18} strokeWidth={1.8} /><span>{label}</span>
        </button>)}
      </nav>
      <div className="sidebar-bottom">
        <div className="service-state"><span className={`status-dot ${health === 'ok' ? 'green' : 'amber'}`} /><span>{health === 'ok' ? '服务正常' : '需要检查'}</span></div>
        <a className="surface-link" href={target}><ShieldCheck size={17} /><span>{targetLabel}</span><ChevronRight size={15} /></a>
      </div>
    </aside>

    <div className="app-frame">
      <header className="app-topbar">
        <button aria-label="打开菜单" className="menu-button icon-button" onClick={() => setMobileOpen(true)}><Menu size={20} /></button>
        <div className="topbar-title">{navItems.find((item) => item.id === activePage)?.label}</div>
        <div className="topbar-actions">
          {surface === 'user' && <button className={demoMode ? 'demo-toggle active' : 'demo-toggle'} onClick={onToggleDemo}>{demoMode ? '退出演示' : '演示模式'}</button>}
          <button aria-label="通知" className="icon-button notification-button" onClick={() => navigate(surface === 'user' ? 'approvals' : 'audit')}><Bell size={18} />{unread > 0 && <span>{unread}</span>}</button>
          <button aria-label="设置" className="icon-button" onClick={() => navigate(surface === 'user' ? 'settings' : 'system')}><Settings size={18} /></button>
          <span className="user-avatar">主</span>
        </div>
      </header>
      <main className="app-content">{children}</main>
    </div>
  </div>
}
