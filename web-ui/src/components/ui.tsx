import type { ReactNode } from 'react'
import { X } from 'lucide-react'

export function StatusDot({ tone = 'green' }: { tone?: 'green' | 'blue' | 'red' | 'amber' | 'gray' }) {
  return <span aria-hidden="true" className={`status-dot ${tone}`} />
}

export function StatusBadge({ children, tone = 'gray' }: { children: ReactNode; tone?: 'green' | 'blue' | 'red' | 'amber' | 'gray' }) {
  return <span className={`status-badge ${tone}`}><StatusDot tone={tone} />{children}</span>
}

export function EmptyState({ title, body, action }: { title: string; body: string; action?: ReactNode }) {
  return <div className="empty-state"><strong>{title}</strong><p>{body}</p>{action}</div>
}

export function PageHeading({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return <header className="page-heading"><div><h1>{title}</h1><p>{description}</p></div>{action}</header>
}

export function Modal({ title, children, onClose, footer }: { title: string; children: ReactNode; onClose: () => void; footer?: ReactNode }) {
  return <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
    <section aria-modal="true" className="modal" role="dialog">
      <header><h2>{title}</h2><button aria-label="鍏抽棴" className="icon-button" onClick={onClose}><X size={19} /></button></header>
      <div className="modal-body">{children}</div>
      {footer && <footer>{footer}</footer>}
    </section>
  </div>
}

export function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return <label className="field"><span>{label}</span>{children}{hint && <small>{hint}</small>}</label>
}
