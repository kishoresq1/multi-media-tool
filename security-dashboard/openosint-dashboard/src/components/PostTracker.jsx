import { useState } from 'react'
import { Search, ExternalLink } from 'lucide-react'

function parseRedditResults(raw) {
  if (!raw) return []
  const rows = []
  for (const line of raw.split('\n')) {
    if (!line.startsWith('[+]')) continue
    const content = line.slice(4)
    const platform = content.match(/\[([^\]]+)\]/)?.[1] || 'Unknown'
    const subMatch = content.match(/\[r\/([^\]]+)\]/)
    const subreddit = subMatch ? `r/${subMatch[1]}` : '—'
    const postedMatch = content.match(/Posted:\s*([^|]+)/)
    const posted = postedMatch ? postedMatch[1].trim() : '—'
    const scoreMatch = content.match(/Score:\s*(-?\d+)/)
    const score = scoreMatch ? parseInt(scoreMatch[1]) : 0
    const commentsMatch = content.match(/Comments:\s*(\d+)/)
    const comments = commentsMatch ? parseInt(commentsMatch[1]) : 0
    const authorMatch = content.match(/Author:\s*u\/([^\s|]+)/)
    const author = authorMatch ? `u/${authorMatch[1]}` : '—'
    const urlMatch = content.match(/URL:\s*(\S+)$/)
    const url = urlMatch ? urlMatch[1] : ''
    rows.push({ platform, subreddit, posted, score, comments, author, url })
  }
  return rows
}

export default function PostTracker() {
  const [query, setQuery] = useState('')
  const [cve, setCve] = useState('')
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(false)
  const [rawMsg, setRawMsg] = useState('')

  async function search() {
    if (!query && !cve) return
    setLoading(true)
    setRawMsg('')
    try {
      const params = new URLSearchParams()
      if (query) params.set('story', query)
      if (cve) params.set('cve', cve)
      const res = await fetch(`/api/tracker/posts?${params}`)
      const data = await res.json()
      const parsed = parseRedditResults(data.raw || '')
      setRows(parsed)
      if (!parsed.length) setRawMsg(data.raw || 'No results found.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="tracker-controls">
        <label className="field">
          <span className="field-label">Story title or headline</span>
          <input
            className="input-control"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && search()}
            placeholder="Example: vendor breach disclosure"
          />
        </label>
        <label className="field">
          <span className="field-label">CVE identifier</span>
          <input
            className="input-control"
            value={cve}
            onChange={e => setCve(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && search()}
            placeholder="CVE-YYYY-XXXXX"
          />
        </label>
        <button
          onClick={search}
          disabled={loading}
          className="btn primary"
        >
          <Search size={15} /> {loading ? 'Searching' : 'Track posts'}
        </button>
      </div>

      {rows.length > 0 ? (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                {['Platform', 'Sub/Channel', 'Posted', 'Score', 'Comments', 'Author', 'Link'].map(h => (
                  <th key={h}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={`${r.url}-${i}`}>
                  <td className="risk-text risk-elevated">{r.platform}</td>
                  <td className="company-domain">{r.subreddit}</td>
                  <td className="row-subtext">{r.posted}</td>
                  <td className={`risk-text ${r.score > 100 ? 'risk-watch' : ''}`}>{r.score}</td>
                  <td className="row-subtext">{r.comments}</td>
                  <td className="row-subtext">{r.author}</td>
                  <td>
                    {r.url && (
                      <a href={r.url} target="_blank" rel="noreferrer"
                        className="table-link">
                        <ExternalLink size={11} /> Open
                      </a>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : rawMsg ? (
        <div className="empty-state compact-empty">{rawMsg}</div>
      ) : null}
    </div>
  )
}
