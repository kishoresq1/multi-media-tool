export default function BaseTemplate({ data, accentColor, background, label }) {
  return (
    <div
      id="hyperframe-canvas"
      className="hyperframe-canvas"
      style={{ borderColor: accentColor, background }}
    >
      <div className="template-top">
        <strong>SQ1 SECURITY</strong>
        <span style={{ backgroundColor: accentColor }}>{data.severityLabel || label}</span>
      </div>
      {data.cveBadge && (
        <div className="cve-line" style={{ color: accentColor }}>
          {data.cveBadge}
        </div>
      )}
      <h2>{data.headline}</h2>
      <h3>{data.subheadline}</h3>
      {data.statHighlight && (
        <div className="stat-highlight" style={{ borderColor: accentColor, color: accentColor }}>
          {data.statHighlight}
        </div>
      )}
      <p>{data.bodyText}</p>
      <div className="template-bottom">
        <span>{(data.hashtags || []).map((tag) => `#${tag}`).join(' ')}</span>
        <strong style={{ backgroundColor: accentColor }}>{data.callToAction}</strong>
      </div>
    </div>
  );
}
