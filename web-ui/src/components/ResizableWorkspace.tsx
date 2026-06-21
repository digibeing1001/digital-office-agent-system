import { useEffect, useRef, useState } from 'react'
import type { CSSProperties, KeyboardEvent, PointerEvent, ReactNode } from 'react'
import { PanelRightClose, PanelRightOpen } from 'lucide-react'

const MIN_SIDE_WIDTH = 300
const MAX_SIDE_WIDTH = 520
const MIN_MAIN_WIDTH = 520

function readNumber(key: string, fallback: number) {
  const value = Number(localStorage.getItem(key))
  return Number.isFinite(value) && value > 0 ? value : fallback
}

export function ResizableWorkspace({
  children,
  side,
  storageKey,
  initialSideWidth = 360,
}: {
  children: ReactNode
  side: ReactNode
  storageKey: string
  initialSideWidth?: number
}) {
  const hostRef = useRef<HTMLDivElement>(null)
  const dragStart = useRef({ x: 0, width: initialSideWidth })
  const resizingRef = useRef(false)
  const currentWidth = useRef(initialSideWidth)
  const [sideWidth, setSideWidth] = useState(initialSideWidth)
  const [collapsed, setCollapsed] = useState(false)
  const [dragging, setDragging] = useState(false)

  useEffect(() => {
    const storedWidth = readNumber(`${storageKey}:side-width`, initialSideWidth)
    currentWidth.current = storedWidth
    setSideWidth(storedWidth)
    setCollapsed(localStorage.getItem(`${storageKey}:side-collapsed`) === 'true')
  }, [initialSideWidth, storageKey])

  const clampWidth = (width: number) => {
    const available = (hostRef.current?.clientWidth || 1200) - MIN_MAIN_WIDTH - 12
    return Math.max(MIN_SIDE_WIDTH, Math.min(MAX_SIDE_WIDTH, available, width))
  }

  const persistWidth = (width: number) => {
    const next = clampWidth(width)
    currentWidth.current = next
    setSideWidth(next)
    localStorage.setItem(`${storageKey}:side-width`, String(next))
  }

  const toggleCollapsed = () => {
    const next = !collapsed
    setCollapsed(next)
    localStorage.setItem(`${storageKey}:side-collapsed`, String(next))
  }

  const startResize = (event: PointerEvent<HTMLDivElement>) => {
    if (collapsed) return
    dragStart.current = { x: event.clientX, width: sideWidth }
    resizingRef.current = true
    event.currentTarget.setPointerCapture(event.pointerId)
    setDragging(true)
  }

  const resize = (event: PointerEvent<HTMLDivElement>) => {
    if (!resizingRef.current) return
    const next = clampWidth(dragStart.current.width + dragStart.current.x - event.clientX)
    currentWidth.current = next
    setSideWidth(next)
  }

  const finishResize = (event: PointerEvent<HTMLDivElement>) => {
    if (!resizingRef.current) return
    event.currentTarget.releasePointerCapture(event.pointerId)
    resizingRef.current = false
    setDragging(false)
    persistWidth(currentWidth.current)
  }

  const resizeWithKeyboard = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return
    event.preventDefault()
    if (collapsed) toggleCollapsed()
    persistWidth(sideWidth + (event.key === 'ArrowLeft' ? 24 : -24))
  }

  const style = { '--office-side-width': `${sideWidth}px` } as CSSProperties

  return <div ref={hostRef} className={`resizable-workspace ${collapsed ? 'side-collapsed' : ''} ${dragging ? 'is-resizing' : ''}`} style={style}>
    <main className="office-conversation-column">{children}</main>
    <div
      className="workspace-divider"
      role="separator"
      aria-label="调整工作区和项目动态的宽度"
      aria-orientation="vertical"
      aria-valuemin={MIN_SIDE_WIDTH}
      aria-valuemax={MAX_SIDE_WIDTH}
      aria-valuenow={collapsed ? 0 : Math.round(sideWidth)}
      tabIndex={0}
      onKeyDown={resizeWithKeyboard}
      onPointerDown={startResize}
      onPointerMove={resize}
      onPointerUp={finishResize}
      onPointerCancel={() => { resizingRef.current = false; setDragging(false) }}
    >
      <span className="divider-grip" aria-hidden="true" />
      <button
        type="button"
        title={collapsed ? '展开项目动态' : '收起项目动态'}
        aria-label={collapsed ? '展开项目动态' : '收起项目动态'}
        onPointerDown={(event) => event.stopPropagation()}
        onClick={toggleCollapsed}
      >
        {collapsed ? <PanelRightOpen size={16} /> : <PanelRightClose size={16} />}
      </button>
    </div>
    <aside className="office-side-panel" aria-label="项目动态">{side}</aside>
  </div>
}
