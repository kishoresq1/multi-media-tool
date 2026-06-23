/**
 * Full API client for Zero Day Radar backend
 */

function resolveApiBase(): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL?.trim()
  if (fromEnv) return fromEnv.replace(/\/$/, '')
  if (import.meta.env.DEV) return '/api/v1'
  return 'http://127.0.0.1:8009/api/v1'
}

export const API_BASE = resolveApiBase()

export class ApiError extends Error {
  status: number
  url: string

  constructor(message: string, status: number, url: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.url = url
  }
}

const REQUEST_TIMEOUT_MS = 30_000

type RequestOptions = RequestInit & { timeoutMs?: number }

async function request<T>(path: string, init?: RequestOptions): Promise<T> {
  const url = `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`
  const timeoutMs = init?.timeoutMs ?? REQUEST_TIMEOUT_MS
  const { timeoutMs: _timeoutMs, ...fetchInit } = init ?? {}
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), timeoutMs)
  let res: Response
  try {
    res = await fetch(url, {
      ...fetchInit,
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
        ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
        ...init?.headers,
      },
    })
  } catch (err) {
    const aborted = err instanceof DOMException && err.name === 'AbortError'
    throw new ApiError(
      aborted
        ? `API timed out after ${timeoutMs / 1000}s — backend may be stuck. Restart: uvicorn app.main:app --port 8009`
        : `Cannot reach API. Start backend: uvicorn app.main:app --reload --port 8009`,
      0,
      url,
    )
  } finally {
    clearTimeout(timeout)
  }
  if (!res.ok) {
    let detail = await res.text()
    try {
      const json = JSON.parse(detail) as { detail?: string }
      if (json.detail) detail = typeof json.detail === 'string' ? json.detail : JSON.stringify(json.detail)
    } catch { /* */ }
    throw new ApiError(detail || `HTTP ${res.status}`, res.status, url)
  }
  return res.json() as Promise<T>
}

function qs(params: Record<string, string | number | boolean | undefined | null>) {
  const p = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') p.set(k, String(v))
  }
  const s = p.toString()
  return s ? `?${s}` : ''
}

// ── Types ───────────────────────────────────────────────────────────

export interface Health {
  status: string
  version: string
  sources_configured: number
  sources_enabled: number
  database: string
}

export interface WorkerHealth {
  celery_enabled: boolean
  redis_ok: boolean
  redis_error: string | null
  beat_interval_minutes: number
  scheduled_task: string
}

export interface SourceInfo {
  id: string
  name: string
  category: string
  url: string
  primary_method: string
  fallback_method: string | null
  trust_weight: number
  requires_api_key: boolean
  enabled: boolean
  feed_url: string | null
}

export interface IntelPost {
  id: string
  platform: string
  source_name: string
  collection_method: string
  title: string
  content: string
  url: string | null
  author: string | null
  published_at: string | null
  search_query: string | null
  matched_vendors: string[]
  matched_vuln_keywords: string[]
  matched_threat_keywords: string[]
  cves: string[]
  has_poc: boolean
  active_exploitation: boolean
  confidence_score: number
  keyword_match_score: number
  recency_score: number
  threat_score: number
  created_at: string | null
}

export interface Advisory {
  id: string
  source_id: string
  source_name: string
  vendor: string | null
  collection_method: string
  title: string
  content: string
  url: string | null
  published_at: string | null
  matched_vendors: string[]
  matched_vuln_keywords: string[]
  cves: string[]
  severity: string | null
  has_poc: boolean
  active_exploitation: boolean
  confidence_score: number
  source_trust_score: number
  created_at: string | null
}

export interface VulnIntel {
  id: string
  source_id: string
  source_name: string
  collection_method: string
  title: string
  content: string
  url: string | null
  author: string | null
  cve_id: string | null
  cvss_score: number | null
  severity: string | null
  published_at: string | null
  matched_vuln_keywords: string[]
  cves: string[]
  in_cisa_kev: boolean
  has_poc: boolean
  has_exploit: boolean
  active_exploitation: boolean
  confidence_score: number
  created_at: string | null
}

export interface BreachIntel {
  id: string
  source_id: string
  source_name: string
  source_tier: number
  collection_method: string
  title: string
  content: string
  url: string | null
  author: string | null
  published_at: string | null
  affected_company: string | null
  breach_type: string | null
  matched_breach_keywords: string[]
  matched_vendors: string[]
  matched_vuln_keywords: string[]
  matched_threat_keywords: string[]
  cves: string[]
  has_poc: boolean
  active_exploitation: boolean
  is_ransomware: boolean
  confidence_score: number
  risk_level: string
  score_breakdown: Record<string, unknown>
  score_reason: string
  source_trust_score: number
  keyword_match_score: number
  recency_score: number
  created_at: string | null
}

export interface UnifiedIntel {
  id: string
  company_name: string | null
  vendor_name: string
  product_name: string
  version_name: string | null
  latest_date: string | null
  title: string
  summary: string
  cves: string[]
  frameworks: string[]
  threat_score: number
  compliance_score: number
  confidence_score: number
  risk_level: string
  classification: string | null
  classification_confidence: number
  classification_reason: string | null
  score_breakdown: Record<string, unknown>
  score_reason: string
  source_count: number
  source_refs: Record<string, unknown>[]
  llm_summary: string | null
  llm_model: string | null
  llm_enriched: boolean
  created_at: string | null
  updated_at: string | null
}

export interface ComplianceIntel {
  id: string
  source_id: string
  source_name: string
  organization: string | null
  source_tier: number
  source_subtype: string
  collection_method: string
  title: string
  content: string
  url: string | null
  author: string | null
  published_at: string | null
  matched_compliance_keywords: string[]
  matched_privacy_keywords: string[]
  matched_audit_keywords: string[]
  matched_ai_keywords: string[]
  matched_framework_keywords: string[]
  frameworks: string[]
  framework_versions: string[]
  effective_dates: string[]
  compliance_deadlines: string[]
  impacted_controls: string[]
  is_new_requirement: boolean
  is_framework_update: boolean
  confidence_score: number
  risk_level: string
  score_breakdown: Record<string, unknown>
  score_reason: string
  source_trust_score: number
  keyword_match_score: number
  recency_score: number
  created_at: string | null
}

export interface ComplianceKeywordsResponse {
  priority: string
  primary: string[]
  fallback: {
    privacy: string[]
    audit: string[]
    ai_governance: string[]
    frameworks: string[]
  }
  tier_1_sources: string[]
  tier_2_sources: string[]
  source_scores: Record<string, number>
}

export interface ComplianceSource {
  id: string
  name: string
  organization: string | null
  tier: number
  url: string
  primary_method: string
  fallback_method: string | null
  feed_url: string | null
  trust_weight: number
}

export interface LinkedInStatus {
  configured: boolean
  connected: boolean
  display_name: string | null
  member_urn: string | null
  post_mode: string
  scopes: string
  login_url: string | null
}

export interface LinkedInPostPreview {
  unified_id: string
  title: string
  commentary: string
  char_count: number
}

export interface LinkedInPostResult {
  status: string
  linkedin_post_id: string | null
  unified_id: string
  author: string
  media_type: string
  media_urn: string | null
  commentary_preview: string
}

export function linkedinLoginUrl(status?: LinkedInStatus | null): string {
  if (status?.login_url) return status.login_url
  const base = import.meta.env.VITE_API_PROXY_TARGET?.trim() || 'http://127.0.0.1:8009'
  return `${base.replace(/\/$/, '')}/auth/linkedin/login`
}

export interface ThreatClassification {
  incident_type: string
  company_name: string
  vendor_name: string
  product_name: string
  cve: string
  incident_title: string
  classification_confidence: number
  reason: string
}

export interface BlogPost {
  id: string
  source_id: string
  source_name: string
  collection_method: string
  title: string
  content: string
  url: string | null
  author: string | null
  published_at: string | null
  matched_vendors: string[]
  matched_vuln_keywords: string[]
  cves: string[]
  confidence_score: number
  created_at: string | null
}

export interface ScoredPost {
  id: string
  title: string
  summary: string
  url: string | null
  published_at: string | null
  vendors: string[]
  cves: string[]
  confidence_score: number
  has_poc: boolean
  active_exploitation: boolean
  in_cisa_kev: boolean
}

export interface KeywordsResponse {
  priority: string
  primary: string[]
  fallback: {
    vendors: string[]
    vulnerability: string[]
    threat_activity: string[]
  }
}

export interface JobTriggerResponse {
  task_id: string
  pipeline: string
  status: string
  message: string
}

export interface JobStatusResponse {
  task_id: string
  status: string
  ready: boolean
  successful: boolean | null
  result: Record<string, unknown> | null
  error: string | null
}

export interface SearchResultBase {
  duration_seconds: number
  source_stats: Record<string, Record<string, unknown>>
}

// ── API ─────────────────────────────────────────────────────────────

export const api = {
  health: () => request<Health>('/health'),
  workerHealth: () => request<WorkerHealth>('/health/worker'),
  sources: () => request<SourceInfo[]>('/sources'),
  keywords: () => request<KeywordsResponse>('/keywords'),

  // Social
  socialQueries: (vendors?: string, maxQueries = 40) =>
    request<{ total: number; queries: string[] }>(
      `/social/queries${qs({ vendors, max_queries: maxQueries })}`,
    ),
  socialSearch: (body: Record<string, unknown>) =>
    request<SearchResultBase & { posts_found: number; posts_saved: number; posts: IntelPost[] }>(
      '/social/search',
      { method: 'POST', body: JSON.stringify(body) },
    ),
  socialPosts: (params: { platform?: string; min_score?: number; limit?: number; offset?: number } = {}) =>
    request<{ total: number; posts: IntelPost[] }>(
      `/social/posts${qs({ platform: params.platform, min_score: params.min_score ?? 0, limit: params.limit ?? 50, offset: params.offset ?? 0 })}`,
    ),
  socialPost: (id: string) => request<IntelPost>(`/social/posts/${id}`),

  // Advisories
  advisorySources: () => request<{ total: number; sources: Record<string, unknown>[] }>('/advisories/sources'),
  advisorySearch: (body: Record<string, unknown>) =>
    request<SearchResultBase & { advisories_found: number; advisories_saved: number; advisories: Advisory[] }>(
      '/advisories/search',
      { method: 'POST', body: JSON.stringify(body) },
    ),
  advisories: (params: { vendor?: string; source_id?: string; min_score?: number; limit?: number; offset?: number } = {}) =>
    request<{ total: number; advisories: Advisory[] }>(
      `/advisories${qs({ vendor: params.vendor, source_id: params.source_id, min_score: params.min_score ?? 0, limit: params.limit ?? 50, offset: params.offset ?? 0 })}`,
    ),
  advisory: (id: string) => request<Advisory>(`/advisories/${id}`),

  // Vulnerabilities
  vulnerabilitySources: () =>
    request<{ total: number; sources: Record<string, unknown>[] }>('/vulnerabilities/sources'),
  vulnerabilitySearch: (body: Record<string, unknown>) =>
    request<SearchResultBase & { items_found: number; items_saved: number; items: VulnIntel[] }>(
      '/vulnerabilities/search',
      { method: 'POST', body: JSON.stringify(body) },
    ),
  vulnerabilities: (params: { source_id?: string; cve_id?: string; min_score?: number; limit?: number; offset?: number } = {}) =>
    request<{ total: number; items: VulnIntel[] }>(
      `/vulnerabilities${qs({ source_id: params.source_id, cve_id: params.cve_id, min_score: params.min_score ?? 0, limit: params.limit ?? 50, offset: params.offset ?? 0 })}`,
    ),
  vulnerability: (id: string) => request<VulnIntel>(`/vulnerabilities/${id}`),

  // Company breaches
  breachSources: () =>
    request<{ total: number; tier_1: string[]; sources: Record<string, unknown>[] }>('/breaches/sources'),
  breachSearch: (body: Record<string, unknown>) =>
    request<SearchResultBase & { items_found: number; items_saved: number; items: BreachIntel[] }>(
      '/breaches/search',
      { method: 'POST', body: JSON.stringify(body) },
    ),
  breaches: (params: { source_id?: string; breach_type?: string; min_score?: number; limit?: number; offset?: number } = {}) =>
    request<{ total: number; items: BreachIntel[] }>(
      `/breaches${qs({ source_id: params.source_id, breach_type: params.breach_type, min_score: params.min_score ?? 0, limit: params.limit ?? 50, offset: params.offset ?? 0 })}`,
    ),
  breach: (id: string) => request<BreachIntel>(`/breaches/${id}`),

  // Compliance intelligence
  complianceSources: () =>
    request<{ total: number; sources: ComplianceSource[] }>('/compliance/sources'),
  complianceKeywords: () => request<ComplianceKeywordsResponse>('/compliance/keywords'),
  complianceSearch: (body: Record<string, unknown>) =>
    request<SearchResultBase & { items_found: number; items_saved: number; items: ComplianceIntel[] }>(
      '/compliance/search',
      { method: 'POST', body: JSON.stringify(body) },
    ),
  compliance: (params: {
    source_id?: string
    organization?: string
    framework?: string
    source_tier?: number
    min_score?: number
    limit?: number
    offset?: number
  } = {}) =>
    request<{ total: number; items: ComplianceIntel[] }>(
      `/compliance${qs({
        source_id: params.source_id,
        organization: params.organization,
        framework: params.framework,
        source_tier: params.source_tier,
        min_score: params.min_score ?? 0,
        limit: params.limit ?? 50,
        offset: params.offset ?? 0,
      })}`,
    ),
  complianceItem: (id: string) => request<ComplianceIntel>(`/compliance/${id}`),

  // Unified intel (SAINT classification + scoring)
  unified: (params: {
    classification?: string
    vendor?: string
    product?: string
    unclassified_only?: boolean
    min_score?: number
    limit?: number
    offset?: number
  } = {}) =>
    request<{ total: number; items: UnifiedIntel[] }>(
      `/unified${qs({
        classification: params.classification,
        vendor: params.vendor,
        product: params.product,
        unclassified_only: params.unclassified_only,
        min_score: params.min_score ?? 0,
        limit: params.limit ?? 50,
        offset: params.offset ?? 0,
      })}`,
    ),
  unifiedItem: (id: string) => request<UnifiedIntel>(`/unified/${id}`),
  unifiedRun: (body: { run_collections?: boolean; use_llm?: boolean; lookback_days?: number } = {}) =>
    request<{
      run_id: string
      items_saved: number
      total_in_database: number
      duration_seconds: number
      clusters_processed: number
    }>('/unified/run', { method: 'POST', body: JSON.stringify(body) }),
  unifiedStatus: () =>
    request<{
      ollama_enabled: boolean
      ollama_available: boolean
      ollama_model: string | null
      classification_values: string[]
    }>('/unified/status'),
  classify: (body: { title: string; content?: string; source_table?: string }) =>
    request<ThreatClassification>('/classify', { method: 'POST', body: JSON.stringify(body) }),

  // LinkedIn (personal profile posting)
  linkedinStatus: () => request<LinkedInStatus>('/linkedin/status'),
  linkedinPreview: (unifiedId: string, mediaType: 'text' | 'image' | 'video' = 'text') =>
    request<LinkedInPostPreview>(
      `/linkedin/preview/${unifiedId}?${new URLSearchParams({ media_type: mediaType }).toString()}`,
    ),
  linkedinPost: (body: {
    unified_id: string
    human_verified: boolean
    commentary?: string
    media_type?: 'text' | 'image' | 'video'
  }) =>
    request<LinkedInPostResult>('/linkedin/post', {
      method: 'POST',
      body: JSON.stringify(body),
      timeoutMs:
        body.media_type === 'video' ? 240_000 : body.media_type === 'image' ? 120_000 : 30_000,
    }),
  linkedinMediaImageUrl: (unifiedId: string) =>
    `${API_BASE}/linkedin/media/${unifiedId}/image`,
  linkedinMediaVideoUrl: (unifiedId: string) =>
    `${API_BASE}/linkedin/media/${unifiedId}/video`,
  linkedinDisconnect: () =>
    request<{ status: string }>('/linkedin/disconnect', { method: 'POST' }),

  // Blogs
  blogSources: () => request<{ total: number; sources: Record<string, unknown>[] }>('/blogs/sources'),
  blogSearch: (body: Record<string, unknown>) =>
    request<SearchResultBase & { posts_found: number; posts_saved: number; posts: BlogPost[] }>(
      '/blogs/search',
      { method: 'POST', body: JSON.stringify(body) },
    ),
  blogs: (params: { source_id?: string; min_score?: number; limit?: number; offset?: number } = {}) =>
    request<{ total: number; posts: BlogPost[] }>(
      `/blogs${qs({ source_id: params.source_id, min_score: params.min_score ?? 0, limit: params.limit ?? 50, offset: params.offset ?? 0 })}`,
    ),
  blog: (id: string) => request<BlogPost>(`/blogs/${id}`),

  // Jobs
  jobsConfig: () => request<Record<string, unknown>>('/jobs/config'),
  triggerJob: (pipeline: string, lookback_days = 30) =>
    request<JobTriggerResponse>(`/jobs/run/${pipeline}`, {
      method: 'POST',
      body: JSON.stringify({ lookback_days }),
    }),
  jobStatus: (taskId: string) => request<JobStatusResponse>(`/jobs/status/${taskId}`),

  // Pipeline / scored
  scoredPosts: (params: { min_confidence?: number; limit?: number; offset?: number } = {}) =>
    request<{ total: number; posts: ScoredPost[] }>(
      `/posts${qs({ min_confidence: params.min_confidence ?? 0, limit: params.limit ?? 50, offset: params.offset ?? 0 })}`,
    ),
  scoredPost: (id: string) => request<ScoredPost>(`/posts/${id}`),

  ping: async () => {
    try {
      await request<Health>('/health')
      return { ok: true as const, base: API_BASE }
    } catch (e) {
      return { ok: false as const, base: API_BASE, error: e instanceof Error ? e.message : 'Error' }
    }
  },

  dashboardBundle: async () => {
    const safe = async <T,>(fn: () => Promise<T>, fb: T) => {
      try { return await fn() } catch { return fb }
    }
    const [health, worker, social, advisories, vulns, blogs, breaches, compliance, unified, unifiedStatus] = await Promise.all([
      safe(() => api.health(), null),
      safe(() => api.workerHealth(), null),
      safe(() => api.socialPosts({ limit: 6 }), { total: 0, posts: [] }),
      safe(() => api.advisories({ limit: 6 }), { total: 0, advisories: [] }),
      safe(() => api.vulnerabilities({ limit: 6 }), { total: 0, items: [] }),
      safe(() => api.blogs({ limit: 4 }), { total: 0, posts: [] }),
      safe(() => api.breaches({ limit: 6, min_score: 0 }), { total: 0, items: [] }),
      safe(() => api.compliance({ limit: 6, min_score: 0 }), { total: 0, items: [] }),
      safe(() => api.unified({ limit: 6, min_score: 0 }), { total: 0, items: [] }),
      safe(() => api.unifiedStatus(), null),
    ])
    return { health, worker, social, advisories, vulns, blogs, breaches, compliance, unified, unifiedStatus }
  },
}
