/**
 * Tipos compartidos para módulo v2 (Global + Nacional)
 */

export interface Organization {
  id: string
  name: string
  country: string | null
  org_type: string | null
  website: string | null
  has_history: boolean
  access_type: string | null
  strategic_obj: string | null
  invests_colombia: boolean
  invests_latam: boolean
  aeiotu_role: string | null
  general_objective: string | null
  focus_sectors: string[] | null
  ticket_min_usd: number | null
  ticket_max_usd: number | null
  created_at: string
  contacts: KeyContact[]
}

export interface Tender {
  id: string
  title: string
  description: string | null
  funder_name: string | null
  tender_type: string | null
  amount_min_cop: number | null
  amount_max_cop: number | null
  open_date: string | null
  deadline: string | null
  url_rfp: string | null
  url_tor: string | null
  url_form: string | null
  org_website: string | null
  score_total: number | null
  decision: string | null
  status: string
  market_window: string | null
  detected_at: string
  updated_at: string
}

export interface KeyContact {
  id: string
  full_name: string
  last_name: string | null
  title: string | null
  email: string | null
  linkedin_url: string | null
  role_category: string | null
  funder_name: string | null
  aeiotu_connection: boolean
  source: string
  fetched_at: string
}

export interface ApiListResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
}

/**
 * Utility functions
 */

export function formatCOP(amount: number | null | undefined): string {
  if (!amount) return "—"
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    minimumFractionDigits: 0,
  }).format(amount)
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "—"
  return new Date(dateStr).toLocaleDateString("es-CO", {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}

export function daysUntilDeadline(deadline: string | null | undefined): number | null {
  if (!deadline) return null
  const today = new Date()
  const deadlineDate = new Date(deadline)
  const diff = deadlineDate.getTime() - today.getTime()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

export function getUrgencyLabel(days: number | null): "URGENTE" | "PRÓXIMO" | "ABIERTO" {
  if (days === null) return "ABIERTO"
  if (days <= 7) return "URGENTE"
  if (days <= 30) return "PRÓXIMO"
  return "ABIERTO"
}

export function getUrgencyColor(days: number | null): string {
  const label = getUrgencyLabel(days)
  switch (label) {
    case "URGENTE":
      return "bg-red-100 text-red-800"
    case "PRÓXIMO":
      return "bg-yellow-100 text-yellow-800"
    default:
      return "bg-gray-100 text-gray-800"
  }
}
