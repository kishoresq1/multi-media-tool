function SkeletonLine({ width = '100%', compact = false }) {
  return <span className={compact ? 'skeleton-line compact' : 'skeleton-line'} style={{ width }} />;
}

function SkeletonChip({ width = 72 }) {
  return <span className="skeleton-chip" style={{ width }} />;
}

export function GenerationSkeleton({ type = 'visual' }) {
  const rows = type === 'video' ? ['92%', '76%', '84%'] : ['68%', '88%', '52%'];

  return (
    <div className={`loading-skeleton generation-skeleton ${type}`} aria-label="Loading generated content">
      <div className="skeleton-header">
        <SkeletonChip width={type === 'video' ? 96 : 82} />
        <SkeletonChip width={54} />
      </div>
      <div className="skeleton-frame">
        <span className="skeleton-signal" />
        <div>
          <SkeletonLine width="42%" />
          <SkeletonLine width="72%" />
        </div>
        <div className="skeleton-grid">
          <SkeletonLine />
          <SkeletonLine />
          <SkeletonLine />
          <SkeletonLine />
        </div>
      </div>
      <div className="skeleton-stack">
        {rows.map((width) => (
          <SkeletonLine key={width} width={width} compact />
        ))}
      </div>
    </div>
  );
}

export function ActionPanelSkeleton({ rows = 3, labelWidth = 90 }) {
  return (
    <div className="loading-skeleton action-skeleton" aria-label="Loading action panel">
      <div className="skeleton-header">
        <SkeletonChip width={labelWidth} />
        <SkeletonChip width={46} />
      </div>
      {Array.from({ length: rows }).map((_, index) => (
        <div className="skeleton-row" key={index}>
          <span className="skeleton-dot" />
          <div>
            <SkeletonLine width={index % 2 === 0 ? '78%' : '64%'} compact />
            <SkeletonLine width={index % 2 === 0 ? '48%' : '58%'} compact />
          </div>
        </div>
      ))}
    </div>
  );
}

export function PayloadSkeleton() {
  return (
    <div className="loading-skeleton payload-skeleton" aria-label="Preparing alert payload">
      <SkeletonLine width="36%" compact />
      <SkeletonLine width="88%" compact />
      <SkeletonLine width="74%" compact />
      <SkeletonLine width="92%" compact />
      <SkeletonLine width="54%" compact />
    </div>
  );
}
