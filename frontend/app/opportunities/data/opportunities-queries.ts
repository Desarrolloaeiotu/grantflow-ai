import { Opportunity, OpportunityList, Metrics } from '../types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || ''

function getFetchHeaders() {
  const headers: HeadersInit = {}
  if (API_KEY) {
    headers['X-API-Key'] = API_KEY
  }
  return headers
}

export async function getMetrics(): Promise<Metrics | null> {
  try {
    const res = await fetch(`${API_URL}/api/v1/dashboard/metrics`, {
      cache: 'no-store',
      headers: getFetchHeaders()
    })
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

export async function getOpportunities(
  filters?: Record<string, string>,
  page = 1
): Promise<OpportunityList | null> {
  try {
    const params = new URLSearchParams({ size: '12', page: String(page) })
    if (filters) {
      for (const [k, v] of Object.entries(filters)) {
        if (v && v !== 'all') params.set(k, v)
      }
    }
    const res = await fetch(
      `${API_URL}/api/v1/opportunities?${params.toString()}`,
      {
        cache: 'no-store',
        headers: getFetchHeaders()
      }
    )
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}
