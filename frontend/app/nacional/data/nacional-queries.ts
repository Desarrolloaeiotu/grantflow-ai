// frontend/app/nacional/data/nacional-queries.ts

import { Opportunity, Contact, Alert, DashboardMetrics } from '../types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || ''

// Helper function to create fetch headers with API key
function getFetchHeaders() {
  const headers: HeadersInit = {}
  if (API_KEY) {
    headers['X-API-Key'] = API_KEY
  }
  return headers
}

// Fetch all national opportunities (filtered by market_window=funding_colombia)
export async function getOportunidadesNacionales(
  filters?: {
    estado?: string
    urgencia?: string
    financiador?: string
    sector?: string
  }
): Promise<Opportunity[]> {
  try {
    const params = new URLSearchParams()
    params.append('window', 'funding_colombia')

    if (filters?.estado) params.append('status', filters.estado)
    if (filters?.urgencia) params.append('urgency', filters.urgencia)
    // Note: financiador and sector filtering happens on frontend for now

    const res = await fetch(`${API_URL}/api/v1/opportunities?${params.toString()}`, {
      cache: 'no-store', // Always fresh data for Server Components
      headers: getFetchHeaders(),
    })

    if (!res.ok) throw new Error('Failed to fetch opportunities')
    const data = await res.json()
    return data.items || []
  } catch (error) {
    console.error('Error fetching opportunities:', error)
    return []
  }
}

// Fetch dashboard metrics for national opportunities
export async function getDashboardMetrics(): Promise<DashboardMetrics> {
  try {
    const res = await fetch(`${API_URL}/api/v1/dashboard/metrics`, {
      cache: 'no-store',
      headers: getFetchHeaders(),
    })

    if (!res.ok) throw new Error('Failed to fetch metrics')
    return res.json()
  } catch (error) {
    console.error('Error fetching metrics:', error)
    return { total: 0, go: 0, no_go: 0, pending: 0, high_urgency: 0, medium_urgency: 0, low_urgency: 0 }
  }
}

// Fetch contacts for national funders
export async function getContactosNacionales(): Promise<Contact[]> {
  try {
    const res = await fetch(`${API_URL}/api/v1/contacts`, {
      cache: 'no-store',
      headers: getFetchHeaders(),
      signal: AbortSignal.timeout(5000),
    })

    if (!res.ok) {
      console.warn(`Contacts endpoint returned ${res.status}`)
      return []
    }
    const data = await res.json()
    return Array.isArray(data) ? data : (data.items || data.contacts || [])
  } catch (error) {
    console.error('Error fetching contacts:', error instanceof Error ? error.message : error)
    return []
  }
}

// Fetch a single opportunity by ID
export async function getOportunidad(id: string): Promise<Opportunity> {
  try {
    const res = await fetch(`${API_URL}/api/v1/opportunities/${id}`, {
      cache: 'no-store',
      headers: getFetchHeaders(),
    })

    if (!res.ok) throw new Error(`Failed to fetch opportunity ${id}`)
    return res.json()
  } catch (error) {
    console.error(`Error fetching opportunity ${id}:`, error)
    throw error
  }
}

// Helper: calculate alerts from opportunities
export function generateAlerts(opportunities: Opportunity[]): Alert[] {
  const alerts: Alert[] = []
  const now = new Date()

  opportunities.forEach((opp) => {
    if (!opp.deadline) return

    const daysUntil = Math.ceil(
      (new Date(opp.deadline).getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
    )

    if (daysUntil <= 30 && daysUntil > 0) {
      alerts.push({
        type: 'vencimiento',
        opportunityId: opp.id,
        title: opp.title,
        urgency: daysUntil <= 7 ? 'high' : daysUntil <= 15 ? 'medium' : 'low',
        message: `Vence en ${daysUntil} días`,
        timestamp: now.toISOString(),
      })
    }
  })

  return alerts.sort((a, b) =>
    a.urgency === 'high' ? -1 : b.urgency === 'high' ? 1 : 0
  )
}
