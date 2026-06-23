function normalize(value) {
  return String(value || 'info').toLowerCase()
}

export default function ThreatBadge({ severity = 'INFO', classification = '' }) {
  const severityKey = normalize(severity)
  const classificationKey = normalize(classification)
  const className = `threat-badge ${severityKey} ${classificationKey}`
  const label = [severity, classification].filter(Boolean).join(' / ')

  return <span className={className}>{label || 'INFO'}</span>
}
