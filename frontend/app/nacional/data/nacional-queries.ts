// frontend/app/nacional/data/nacional-queries.ts

import { Opportunity, Contact, Alert, DashboardMetrics } from '../types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Fetch all national opportunities (filtered by market_window=funding_colombia)
export async function getOportunidadesNacionales(
  filters?: {
    estado?: string
    urgencia?: string
    financiador?: string
    sector?: string
  }
): Promise<Opportunity[]> {
  const params = new URLSearchParams()
  params.append('window', 'funding_colombia')

  if (filters?.estado) params.append('status', filters.estado)
  if (filters?.urgencia) params.append('urgency', filters.urgencia)
  // Note: financiador and sector filtering happens on frontend for now

  const res = await fetch(`${API_URL}/api/v1/opportunities?${params.toString()}`, {
    cache: 'no-store', // Always fresh data for Server Components
  })

  if (!res.ok) throw new Error('Failed to fetch opportunities')
  const data = await res.json()
  return data.items || []
}

// Fetch dashboard metrics for national opportunities
export async function getDashboardMetrics(): Promise<DashboardMetrics> {
  const res = await fetch(`${API_URL}/api/v1/dashboard/metrics?region=colombia`, {
    cache: 'no-store',
  })

  if (!res.ok) throw new Error('Failed to fetch metrics')
  return res.json()
}

// Fetch contacts for national funders
export async function getContactosNacionales(): Promise<Contact[]> {
  const res = await fetch(`${API_URL}/api/v1/contacts?region=colombia`, {
    cache: 'no-store',
  })

  if (!res.ok) throw new Error('Failed to fetch contacts')
  const data = await res.json()
  return data.contacts || []
}

// Fetch a single opportunity by ID
export async function getOportunidad(id: string): Promise<Opportunity> {
  const res = await fetch(`${API_URL}/api/v1/opportunities/${id}`, {
    cache: 'no-store',
  })

  if (!res.ok) throw new Error(`Failed to fetch opportunity ${id}`)
  return res.json()
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
