import type { ReactNode } from 'react'
import { API_BASE } from '../api/client'
import { classificationBadgeClass, classificationLabel } from '../lib/format'

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string
  description?: string
  actions?: ReactNode
}) {
  return (
    <div
      className="page-header"
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        flexWrap: 'wrap',
        gap: '1rem',
      }}
    >
      <div>
        <h2>{title}</h2>
        {description && <p>{description}</p>}
      </div>
      {actions}
    </div>
  )
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="error-banner">
      {message}
      <div style={{ marginTop: 6, fontSize: '0.8rem' }}>
        API: <code>{API_BASE}</code>
      </div>
    </div>
  )
}

export function SuccessBanner({ message }: { message: string }) {
  return <div className="success-banner">{message}</div>
}

export function Loading({ text = 'Loading…' }: { text?: string }) {
  return <div className="loading">{text}</div>
}

export function EmptyRow({ colSpan, text }: { colSpan: number; text: string }) {
  return (
    <tr>
      <td colSpan={colSpan} className="empty-state">
        {text}
      </td>
    </tr>
  )
}

export function ClassificationBadge({ type }: { type: string | null | undefined }) {
  if (!type) return <span className="badge badge-neutral">Unclassified</span>
  return <span className={`badge ${classificationBadgeClass(type)}`}>{classificationLabel(type)}</span>
}

export function KeywordTags({ items, max = 8 }: { items: string[]; max?: number }) {
  if (!items.length) return null
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8 }}>
      {items.slice(0, max).map((k) => (
        <span key={k} className="badge badge-neutral">{k}</span>
      ))}
    </div>
  )
}

export function DetailGrid({ rows }: { rows: { label: string; value: ReactNode }[] }) {
  return (
    <dl className="detail-grid">
      {rows.map(({ label, value }) => (
        <div key={label} className="detail-grid-row">
          <dt>{label}</dt>
          <dd>{value ?? '—'}</dd>
        </div>
      ))}
    </dl>
  )
}
