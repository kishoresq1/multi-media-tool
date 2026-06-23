interface StatCardProps {
  label: string
  value: string | number
  meta?: string
}

export function StatCard({ label, value, meta }: StatCardProps) {
  return (
    <div className="stat-card">
      <div className="stat-card-label">{label}</div>
      <div className="stat-card-value">{value}</div>
      {meta && <div className="stat-card-meta">{meta}</div>}
    </div>
  )
}
