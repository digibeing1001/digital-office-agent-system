import { useEffect, useMemo, useState, type CSSProperties } from 'react'
import { api } from '../../api'
import type { AppActions, FeishuInstallerCatalog, FeishuInstallerEvent, FeishuInstallerSession } from '../../types'
import { ArrowUpRight, Bot, Check, CheckCircle2, ChevronDown, CircleAlert, Clock3, LoaderCircle, MessageSquareText, PackageCheck, RefreshCw, ShieldCheck, Sparkles, Users } from 'lucide-react'

const checkLabels: Record<string, string> = {
  agent_host: 'Agent 宿主',
  node: 'Node.js',
  npm: 'npm',
  lark_cli: '飞书 CLI',
  feishu_sdk: '飞书 SDK',
}

const eventLabels: Record<FeishuInstallerEvent['event'], string> = {
  session_started: '安装会话已启动',
  authorizing: '正在准备角色应用',
  authorization_required: '等待在线确认',
  ready: '角色导入完成',
  already_ready: '角色已存在，自动复用',
  failed: '导入暂停，需要处理',
  session_complete: '所选团队全部就绪',
}

function shortTime(value: string) {
  if (!value) return ''
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export function FeishuInstaller({ actions }: { actions: AppActions }) {
  const [catalog, setCatalog] = useState<FeishuInstallerCatalog | null>(null)
  const [selected, setSelected] = useState<string[]>([])
  const [expanded, setExpanded] = useState<string[]>([])
  const [notify, setNotify] = useState(false)
  const [notifyProfile, setNotifyProfile] = useState('office-installer')
  const [notifyChatId, setNotifyChatId] = useState('')
  const [confirmed, setConfirmed] = useState(false)
  const [session, setSession] = useState<FeishuInstallerSession | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadCatalog = async () => {
    setLoading(true)
    setError('')
    try {
      const value = await api.getFeishuInstallerCatalog()
      setCatalog(value)
      setSelected((current) => current.length ? current : value.teams.filter((team) => team.recommended).map((team) => team.team_id))
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : '无法读取团队目录。')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { void loadCatalog() }, [])

  useEffect(() => {
    if (!session || ['complete', 'failed'].includes(session.status)) return
    const timer = window.setInterval(async () => {
      try {
        setSession(await api.getFeishuInstallerSession(session.session_id))
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : '无法更新安装进度。')
      }
    }, 2_000)
    return () => window.clearInterval(timer)
  }, [session?.session_id, session?.status])

  const selectedTeams = useMemo(() => catalog?.teams.filter((team) => selected.includes(team.team_id)) || [], [catalog, selected])
  const totalBots = selectedTeams.reduce((sum, team) => sum + team.agent_count, 0)
  const readyBots = selectedTeams.reduce((sum, team) => sum + team.ready_count, 0)
  const missingBots = Math.max(0, totalBots - readyBots)
  const currentReady = session ? Math.max(session.initial_ready_count || 0, session.ready_count || 0) : readyBots
  const progress = session?.bot_count ? Math.min(100, Math.round((currentReady / session.bot_count) * 100)) : 0
  const latestAuthorization = session?.latest_authorization
  const running = session && !['complete', 'failed'].includes(session.status)
  const canStart = Boolean(catalog?.preflight.ready && selected.length && confirmed && (!notify || (notifyProfile.trim() && notifyChatId.trim())) && !running)

  const toggleTeam = (teamId: string) => {
    if (running) return
    setSelected((current) => current.includes(teamId) ? current.filter((id) => id !== teamId) : [...current, teamId])
    setConfirmed(false)
  }

  const start = async () => {
    if (!canStart) return
    setError('')
    try {
      const value = await actions.startFeishuInstaller({
        team_ids: selected,
        confirmed: true,
        notify_profile: notify ? notifyProfile.trim() : undefined,
        notify_chat_id: notify ? notifyChatId.trim() : undefined,
      })
      setSession(value)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : '安装会话未能启动。')
    }
  }

  return <div className="installer-page">
    <section className="installer-hero">
      <div className="installer-hero-copy">
        <span className="installer-kicker"><Sparkles size={15} /> DIGITAL WORKFORCE DEPLOYMENT</span>
        <h1>把一支专家团队，<br /><em>装进飞书。</em></h1>
        <p>选择需要的 Agent 团队。安装器会复用已存在角色，只为缺失的独立 Bot 依次发起一次在线确认。</p>
      </div>
      <div className="installer-scoreboard" aria-label="安装摘要">
        <div><span>可选团队</span><strong>{catalog?.teams.length || '—'}</strong></div>
        <div><span>已选择角色</span><strong>{totalBots || '—'}</strong></div>
        <div><span>首次确认</span><strong>{missingBots || '0'}</strong></div>
        <small><ShieldCheck size={15} /> 密钥不会进入浏览器或安装日志</small>
      </div>
    </section>

    <section className="installer-preflight">
      <div><span className={`preflight-beacon ${catalog?.preflight.ready ? 'ready' : ''}`} /><div><strong>部署环境预检</strong><small>{catalog?.preflight.ready ? '导入所需组件已经就绪' : '请先补齐阻塞组件'}</small></div></div>
      <div className="preflight-checks">
        {catalog && Object.entries(catalog.preflight.checks).map(([id, check]) => <span className={check.ready ? 'ok' : check.required ? 'blocked' : 'optional'} key={id} title={check.value}>
          {check.ready ? <Check size={13} /> : <CircleAlert size={13} />}{checkLabels[id] || id}
        </span>)}
      </div>
      <button aria-label="重新检查环境" className="installer-refresh" disabled={loading || Boolean(running)} onClick={() => void loadCatalog()}><RefreshCw className={loading ? 'spin' : ''} size={16} /></button>
    </section>

    {error && <div className="installer-alert"><CircleAlert size={18} /><div><strong>安装器需要处理</strong><span>{error}</span></div></div>}

    {!session && <>
      <section className="installer-section-heading"><div><span>01</span><div><strong>选择 Agent 团队</strong><small>可以一次选择多个团队；后续项目只复用角色，不重复创建。</small></div></div><em>{selected.length} / {catalog?.teams.length || 0} 已选择</em></section>
      <section className="team-catalog">
        {catalog?.teams.map((team) => {
          const active = selected.includes(team.team_id)
          const open = expanded.includes(team.team_id)
          return <article className={`team-install-card ${active ? 'selected' : ''}`} key={team.team_id} style={{ '--team-accent': team.accent } as CSSProperties}>
            <button className="team-card-select" aria-pressed={active} onClick={() => toggleTeam(team.team_id)}>
              <span className="team-card-index">{active ? <Check size={17} /> : String(catalog.teams.indexOf(team) + 1).padStart(2, '0')}</span>
              <span className="team-card-title"><small>{team.eyebrow}</small><strong>{team.name}</strong></span>
              {team.recommended && <span className="recommended-tag">推荐</span>}
            </button>
            <p>{team.description}</p>
            <div className="team-card-stats"><span><Users size={14} />{team.agent_count} 个角色</span><span><PackageCheck size={14} />{team.ready_count} 个已导入</span></div>
            <div className="team-capabilities">{team.capabilities.map((item) => <span key={item}>{item}</span>)}</div>
            <button className="team-role-toggle" onClick={() => setExpanded((current) => current.includes(team.team_id) ? current.filter((id) => id !== team.team_id) : [...current, team.team_id])}>查看团队成员 <ChevronDown className={open ? 'open' : ''} size={15} /></button>
            {open && <div className="team-role-list">{team.roles.map((role) => <div key={role.bot_key}><span className={role.status === 'ready' ? 'role-status ready' : 'role-status'}><Bot size={13} /></span><span><strong>{role.display_name}</strong><small>{role.agent_id}</small></span>{role.status === 'ready' && <em>已导入</em>}</div>)}</div>}
          </article>
        })}
      </section>

      <section className="installer-config-grid">
        <div className="installer-config-panel">
          <span className="config-number">02</span><div className="config-copy"><strong>飞书对话提醒</strong><p>可选。填写首个引导 Agent 的 Profile 和群 ID，授权链接与进度会同步发送到飞书群。</p></div>
          <label className="switch-line"><input checked={notify} onChange={(event) => setNotify(event.target.checked)} type="checkbox" /><span /><em>{notify ? '已开启' : '暂不开启'}</em></label>
          {notify && <div className="installer-fields"><label><span>引导 Agent Profile</span><input value={notifyProfile} onChange={(event) => setNotifyProfile(event.target.value)} placeholder="office-installer" /></label><label><span>接收提醒的群 ID</span><input value={notifyChatId} onChange={(event) => setNotifyChatId(event.target.value)} placeholder="oc_xxxxxxxxx" /></label></div>}
        </div>
        <div className="installer-confirm-panel">
          <span className="config-number">03</span><div className="config-copy"><strong>确认创建独立 Bot</strong><p>所选团队共有 {totalBots} 个角色，其中 {readyBots} 个可直接复用，预计需要完成 {missingBots} 次首次在线确认。</p></div>
          <label className="installer-confirm-check"><input checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} type="checkbox" /><span>{confirmed && <Check size={15} />}</span><em>我确认导入所选团队，并理解每个缺失角色需要分别在线确认。</em></label>
        </div>
      </section>

      <section className="installer-action-dock">
        <div><span>{selectedTeams.map((team) => team.name).join(' · ') || '尚未选择团队'}</span><strong>{totalBots} 个角色 / {missingBots} 次首次确认</strong></div>
        <button disabled={!canStart} onClick={() => void start()}><PackageCheck size={18} />一键导入所选团队<ArrowUpRight size={17} /></button>
      </section>
    </>}

    {session && <section className={`installer-session ${session.status}`}>
      <header><div><span className="session-icon">{session.status === 'complete' ? <CheckCircle2 size={24} /> : session.status === 'failed' ? <CircleAlert size={24} /> : <LoaderCircle className="spin" size={24} />}</span><div><small>INSTALLATION SESSION · {session.session_id.slice(0, 8)}</small><strong>{session.status === 'complete' ? '团队已经进入飞书' : session.status === 'failed' ? '导入已暂停' : '正在逐个导入 Agent'}</strong></div></div><span className="session-percent">{progress}%</span></header>
      <div className="session-progress"><span style={{ width: `${progress}%` }} /></div>
      <div className="session-metrics"><div><span>已就绪</span><strong>{currentReady}</strong></div><div><span>全部角色</span><strong>{session.bot_count}</strong></div><div><span>仍需处理</span><strong>{Math.max(0, session.bot_count - currentReady)}</strong></div></div>

      {latestAuthorization?.authorization_url && session.status === 'running' && <div className="authorization-callout">
        <span><MessageSquareText size={24} /></span><div><small>当前等待确认</small><strong>{latestAuthorization.display_name}</strong><p>此链接约 {Math.max(1, Math.round((latestAuthorization.expires_in || 600) / 60))} 分钟内有效。确认后安装器会自动继续下一个角色。</p></div><a href={latestAuthorization.authorization_url} rel="noreferrer" target="_blank">打开飞书确认页 <ArrowUpRight size={16} /></a>
      </div>}

      <div className="installer-timeline">
        {(session.events || []).slice().reverse().map((event, index) => <div className={`timeline-event ${event.event}`} key={`${event.time}-${event.event}-${event.bot_key || index}`}><span>{event.event === 'ready' || event.event === 'already_ready' || event.event === 'session_complete' ? <Check size={14} /> : event.event === 'failed' ? <CircleAlert size={14} /> : <Clock3 size={14} />}</span><div><strong>{eventLabels[event.event]}</strong><small>{event.display_name || event.bot_key || '安装器'} · {shortTime(event.time)}</small></div></div>)}
      </div>

      {['complete', 'failed'].includes(session.status) && <div className="session-actions"><button className="secondary-button" onClick={() => { setSession(null); setConfirmed(false); void loadCatalog() }}>{session.status === 'complete' ? '返回团队目录' : '检查后重新导入'}</button>{session.status === 'complete' && <a href="/">进入数字办公室 <ArrowUpRight size={16} /></a>}</div>}
    </section>}
  </div>
}
