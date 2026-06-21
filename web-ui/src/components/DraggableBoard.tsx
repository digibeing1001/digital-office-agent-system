import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { GripVertical, Maximize2, Minimize2 } from 'lucide-react'

export interface BoardItem {
  id: string
  content: ReactNode
}

export function DraggableBoard({ items, storageKey, variant = 'grid' }: { items: BoardItem[]; storageKey: string; variant?: 'grid' | 'rail' }) {
  const ids = useMemo(() => items.map((item) => item.id), [items])
  const [order, setOrder] = useState<string[]>(ids)
  const [wide, setWide] = useState<string[]>([])
  const [dragging, setDragging] = useState('')

  useEffect(() => {
    try {
      const stored = JSON.parse(localStorage.getItem(`${storageKey}:layout`) || '{}') as { order?: string[]; wide?: string[] }
      setOrder([...(stored.order || []).filter((id) => ids.includes(id)), ...ids.filter((id) => !(stored.order || []).includes(id))])
      setWide((stored.wide || []).filter((id) => ids.includes(id)))
    } catch {
      setOrder(ids)
    }
  }, [ids.join(','), storageKey])

  const persist = (nextOrder: string[], nextWide: string[]) => {
    setOrder(nextOrder)
    setWide(nextWide)
    localStorage.setItem(`${storageKey}:layout`, JSON.stringify({ order: nextOrder, wide: nextWide }))
  }

  const drop = (target: string) => {
    if (!dragging || dragging === target) return setDragging('')
    const next = order.filter((id) => id !== dragging)
    next.splice(next.indexOf(target), 0, dragging)
    persist(next, wide)
    setDragging('')
  }

  const ordered = order.map((id) => items.find((item) => item.id === id)).filter(Boolean) as BoardItem[]
  return <div className={`draggable-board ${variant === 'rail' ? 'rail-board' : ''}`}>{ordered.map((item) => <div className={`board-item ${variant !== 'rail' && wide.includes(item.id) ? 'wide' : ''} ${dragging === item.id ? 'dragging' : ''}`} draggable key={item.id} onDragStart={() => setDragging(item.id)} onDragEnd={() => setDragging('')} onDragOver={(event) => event.preventDefault()} onDrop={() => drop(item.id)}>
    <div className="board-item-tools"><button className="drag-handle" title="拖动调整位置" aria-label="拖动调整位置"><GripVertical size={16} /></button>{variant !== 'rail' && <button title={wide.includes(item.id) ? '恢复标准宽度' : '加宽此分区'} aria-label={wide.includes(item.id) ? '恢复标准宽度' : '加宽此分区'} onClick={() => persist(order, wide.includes(item.id) ? wide.filter((id) => id !== item.id) : [...wide, item.id])}>{wide.includes(item.id) ? <Minimize2 size={15} /> : <Maximize2 size={15} />}</button>}</div>
    {item.content}
  </div>)}</div>
}
