import type { ComponentType, ReactNode } from 'react'
import { Activity, ArrowLeft, Bell, Building2, ChevronDown, ChevronRight, Folder, FolderKanban, Menu, MessageSquare, Plus, Presentation, Settings, Search, ShieldCheck, X } from 'lucide-react'
import { useState } from 'react'

export interface NavItem {
  id: string
  label: string
  icon: ComponentType<{ size?: number; strokeWidth?: number }>
}

export interface SidebarConversation {
  id: string
  title: string
}

export interface SidebarProject {
  id: string
  name: string
  conversations: SidebarConversation[]
}

export interface ProjectNavigation {
  projects: SidebarProject[]
  expandedProjectIds: string[]
  activeProjectId?: string
  activeConversationId?: string
  onOpenProjects: () => void
  onOpenProject: (projectId: string) => void
  onOpenConversation: (projectId: string, conversationId: string) => void
  onToggleProject: (projectId: string) => void
  onCreateProject: () => void
}

interface AppShellProps {
  surface: 'user' | 'admin'
  navItems: NavItem[]
  bottomNavItems?: NavItem[]
  activePage: string
  onNavigate: (id: string) => void
  health: string
  unread: number
  demoMode?: boolean
  onToggleDemo?: () => void
  pageTitle?: string
  breadcrumbs?: string[]
  backLabel?: string
  onBack?: () => void
  projectNavigation?: ProjectNavigation
  children: ReactNode
}

export function AppShell({ surface, navItems, bottomNavItems = [], activePage, onNavigate, health, unread, demoMode, onToggleDemo, pageTitle, breadcrumbs = [], backLabel = '返回上一级', onBack, projectNavigation, children }: AppShellProps) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const target = surface === 'user' ? '/admin' : '/'
  const targetLabel = surface === 'user' ? '管理中心' : '返回用户端'

  const navigate = (id: string) => {
    onNavigate(id)
    setMobileOpen(false)
  }

  const projectNavigate = (action: () => void) => {
    action()
    setMobileOpen(false)
  }

  const resolvedTitle = pageTitle || [...navItems, ...bottomNavItems].find((item) => item.id === activePage)?.label

  return <div className={`app-shell ${surface}`}>
    <aside className={`sidebar ${projectNavigation ? 'has-project-tree' : ''} ${mobileOpen ? 'open' : ''}`}>
      <div className="brand-row">
        <img className="brand-mark" src="/icons/brand-mark.svg" alt="" width="28" height="28" />
        <div><strong>Digital Office</strong><span>{surface === 'user' ? '数字办公室 · 智能工作系统' : '系统管理中心'}</span></div>
        <span className="brand-edition">v0.3</span>
        <button aria-label="关闭菜单" className="mobile-close icon-button" onClick={() => setMobileOpen(false)}><X size={19} /></button>
      </div>
      <nav className="primary-nav" aria-label={surface === 'user' ? '用户端导航' : '管理端导航'}>
        {navItems.map(({ id, label, icon: Icon }) => <button className={activePage === id ? 'nav-button active' : 'nav-button'} key={id} onClick={() => navigate(id)}>
          <Icon size={18} strokeWidth={1.8} /><span>{label}</span>
        </button>)}
      </nav>
      {projectNavigation && <section className="sidebar-projects" aria-label="项目与对话">
        <div className="sidebar-projects-heading">
          <button className={activePage === 'projects' && !projectNavigation.activeProjectId ? 'sidebar-projects-home active' : 'sidebar-projects-home'} onClick={() => projectNavigate(projectNavigation.onOpenProjects)}>
            <FolderKanban size={17} strokeWidth={1.8} /><span>项目</span>
          </button>
          <button aria-label="新建项目" className="sidebar-add-button" title="新建项目" onClick={() => projectNavigate(projectNavigation.onCreateProject)}><Plus size={16} /></button>
        </div>
        <div className="project-tree" role="tree">
          {projectNavigation.projects.map((project) => {
            const expanded = projectNavigation.expandedProjectIds.includes(project.id)
            const active = projectNavigation.activeProjectId === project.id
            return <div className="project-tree-node" key={project.id} role="treeitem" aria-expanded={expanded}>
              <div className={active ? 'project-tree-row active' : 'project-tree-row'}>
                <button className="project-expand-button" aria-label={`${expanded ? '收起' : '展开'}${project.name}`} onClick={() => projectNavigation.onToggleProject(project.id)}>
                  {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                </button>
                <button className="project-tree-link" title={project.name} aria-current={active && !projectNavigation.activeConversationId ? 'page' : undefined} onClick={() => projectNavigate(() => projectNavigation.onOpenProject(project.id))}>
                  <Folder size={15} /><span>{project.name}</span><small>{project.conversations.length}</small>
                </button>
              </div>
              {expanded && <div className="conversation-tree" role="group">
                {project.conversations.slice(0, 5).map((conversation) => {
                  const conversationActive = active && projectNavigation.activeConversationId === conversation.id
                  return <button className={conversationActive ? 'conversation-tree-link active' : 'conversation-tree-link'} title={conversation.title} aria-current={conversationActive ? 'page' : undefined} key={conversation.id} onClick={() => projectNavigate(() => projectNavigation.onOpenConversation(project.id, conversation.id))}>
                    <MessageSquare size={14} /><span>{conversation.title}</span>
                  </button>
                })}
                {!project.conversations.length && <span className="conversation-tree-empty">暂无对话</span>}
                {project.conversations.length > 5 && <button className="conversation-tree-more" onClick={() => projectNavigate(() => projectNavigation.onOpenProject(project.id))}>查看其余 {project.conversations.length - 5} 条</button>}
              </div>}
            </div>
          })}
          {!projectNavigation.projects.length && <button className="project-tree-empty" onClick={() => projectNavigate(projectNavigation.onCreateProject)}><Folder size={16} /><span>还没有项目</span><small>点击新建</small></button>}
        </div>
      </section>}
      <div className="sidebar-bottom">
        {!!bottomNavItems.length && <nav className="bottom-nav" aria-label="项目文件夹">
          {bottomNavItems.map(({ id, label, icon: Icon }) => <button className={activePage === id ? 'nav-button active bottom-nav-button' : 'nav-button bottom-nav-button'} key={id} onClick={() => navigate(id)}>
            <Icon size={18} strokeWidth={1.8} /><span>{label}</span>
          </button>)}
        </nav>}
        <div className="service-state"><span className={`status-dot ${health === 'ok' ? 'green' : 'amber'}`} /><span>{health === 'ok' ? '服务正常' : '需要检查'}</span></div>
        <a className="surface-link" href={target}><ShieldCheck size={17} /><span>{targetLabel}</span><ChevronRight size={15} /></a>
      </div>
    </aside>
    {mobileOpen && <button aria-label="关闭侧边栏" className="sidebar-scrim" onClick={() => setMobileOpen(false)} />}

    <div className="app-frame">
      <header className="app-topbar">
        <div className="topbar-context">
          <button aria-label="打开菜单" className="menu-button icon-button" onClick={() => setMobileOpen(true)}><Menu size={20} /></button>
          {onBack && <button className="back-button" onClick={onBack} aria-label={backLabel}><ArrowLeft size={17} /><span>{backLabel}</span></button>}
          <div className="topbar-heading">
            {!!breadcrumbs.length && <div className="topbar-breadcrumb" aria-label="当前位置">{breadcrumbs.map((item, index) => <span key={`${item}-${index}`}>{index > 0 && <ChevronRight size={12} />}{item}</span>)}</div>}
            <strong className="topbar-title">{resolvedTitle}</strong>
          </div>
        </div>
        <div className="topbar-actions">
          <span className={`topbar-runtime ${health === 'ok' ? 'online' : ''}`}><Activity size={14} /><span>{health === 'ok' ? '智能底座运行中' : '系统需要检查'}</span></span>
          {surface === 'user' && <button className={demoMode ? 'demo-toggle active' : 'demo-toggle'} onClick={onToggleDemo}><Presentation size={15} />{demoMode ? '退出演示' : '演示模式'}</button>}
          <button aria-label="通知" className="icon-button notification-button" onClick={() => navigate(surface === 'user' ? 'projects' : 'audit')}><Bell size={18} />{unread > 0 && <span>{unread}</span>}</button>
          <button aria-label="设置" className="icon-button" onClick={() => navigate(surface === 'user' ? 'settings' : 'system')}><Settings size={18} /></button>
          <img className="user-avatar" src="/avatar.svg" alt="" width="32" height="32" />
        </div>
      </header>
      <main className="app-content" id="main-content" tabIndex={-1}>{children}</main>
    </div>
  </div>
}
