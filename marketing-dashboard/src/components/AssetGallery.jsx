import { useEffect, useState } from 'react';
import { HardDrive, RefreshCw, Search, X } from 'lucide-react';
import { searchAssets } from '../api/marketingApi.js';

const KIND_LABELS = { email: 'Email', video: 'Video', hyperframe: 'Visual' };
const KIND_OPTIONS = [
  { value: '', label: 'All types' },
  { value: 'hyperframe', label: 'Visuals' },
  { value: 'video', label: 'Videos' }
];

export default function AssetGallery({ assets: initialAssets, campaigns = [], onRefresh }) {
  const [query, setQuery] = useState('');
  const [kind, setKind] = useState('');
  const [results, setResults] = useState(null); // null = show all
  const [searching, setSearching] = useState(false);

  // Merge campaigns into a unified item list for the "all" view
  const allItems = [
    ...campaigns.map((c) => ({
      id: c.id,
      kind: 'email',
      createdAt: c.createdAt,
      intel: { title: c.intelTitle, classification: 'EMAIL' },
      localFile: null,
      localPng: null
    })),
    ...[...initialAssets].reverse()
  ];

  const displayItems = results !== null ? results : allItems;

  async function runSearch() {
    if (!query.trim() && !kind) {
      setResults(null);
      return;
    }
    setSearching(true);
    try {
      const data = await searchAssets(query.trim(), kind);
      setResults(data.assets || []);
    } catch {
      setResults([]);
    } finally {
      setSearching(false);
    }
  }

  function clearSearch() {
    setQuery('');
    setKind('');
    setResults(null);
  }

  useEffect(() => {
    if (!query.trim() && !kind) {
      setResults(null);
    }
  }, [query, kind]);

  function handleKeyDown(e) {
    if (e.key === 'Enter') runSearch();
    if (e.key === 'Escape') clearSearch();
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Asset Gallery</p>
          <h2>Created Content</h2>
        </div>
        <button className="secondary-action" onClick={onRefresh}>
          <RefreshCw size={15} />
          Refresh
        </button>
      </div>

      {/* Search bar */}
      <div className="search-bar" style={{ display: 'flex', gap: 8, marginBottom: 16, alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ position: 'relative', flex: '1 1 220px' }}>
          <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', opacity: 0.5, pointerEvents: 'none' }} />
          <input
            type="search"
            placeholder="Search by title, classification, severity…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            style={{ width: '100%', paddingLeft: 32, paddingRight: 10, height: 36, borderRadius: 6, border: '1px solid rgba(255,255,255,0.12)', background: 'rgba(255,255,255,0.04)', color: 'inherit', fontSize: 13 }}
          />
        </div>
        <select
          value={kind}
          onChange={(e) => setKind(e.target.value)}
          style={{ height: 36, borderRadius: 6, border: '1px solid rgba(255,255,255,0.12)', background: 'rgba(255,255,255,0.04)', color: 'inherit', fontSize: 13, padding: '0 10px' }}
        >
          {KIND_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <button className="primary-action" onClick={runSearch} disabled={searching} style={{ height: 36, padding: '0 14px' }}>
          <Search size={14} />
          {searching ? 'Searching…' : 'Search'}
        </button>
        {results !== null && (
          <button className="secondary-action" onClick={clearSearch} style={{ height: 36, padding: '0 14px' }}>
            <X size={14} />
            Clear
          </button>
        )}
      </div>

      {results !== null && (
        <p className="eyebrow" style={{ marginBottom: 12 }}>
          {results.length} result{results.length !== 1 ? 's' : ''} for &ldquo;{query || kind}&rdquo;
        </p>
      )}

      {displayItems.length === 0 ? (
        <div className="empty-state">
          {results !== null ? 'No assets match your search.' : 'No assets created yet.'}
        </div>
      ) : (
        <div className="gallery-grid">
          {displayItems.map((asset) => (
            <article className="gallery-card" key={asset.id}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 6 }}>
                <span className="source-chip">{KIND_LABELS[asset.kind] || asset.kind}</span>
                {(asset.localFile || asset.localPng) && (
                  <span title={asset.localPng || asset.localFile} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, opacity: 0.6 }}>
                    <HardDrive size={12} />
                    saved
                  </span>
                )}
              </div>
              <h3>{asset.intel?.title || asset.content?.title || 'Marketing asset'}</h3>
              <p style={{ fontSize: 12, opacity: 0.6 }}>{asset.intel?.classification || 'SQ1'}</p>
              {asset.intel?.severity && (
                <p style={{ fontSize: 11, opacity: 0.5 }}>{asset.intel.severity}</p>
              )}
              <time style={{ fontSize: 11, opacity: 0.45 }}>{new Date(asset.createdAt).toLocaleString()}</time>
              {asset.localPng && (
                <img
                  src={pngUrl(asset.id)}
                  alt={asset.intel?.title || 'asset preview'}
                  style={{ marginTop: 8, width: '100%', borderRadius: 4, objectFit: 'cover', maxHeight: 120 }}
                  onError={(e) => { e.currentTarget.style.display = 'none'; }}
                />
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function pngUrl(assetId) {
  return `/mkt/assets/files/images/${encodeURIComponent(assetId)}.png`;
}
