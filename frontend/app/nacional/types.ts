// frontend/app/nacional/types.ts

export interface Opportunity {
  id: string
  title: string
  description: string | null
  funder_id: string
  funder_name: string
  amount_min_cop: number | null
  amount_max_cop: number | null
  deadline: string | null
  url_rfp: string | null
  source_name: string
  market_window: string
  capital_type: string
  score_total: number
  decision: 'go' | 'no_go' | 'pending'
  urgency: 'high' | 'medium' | 'low'
  status: 'detected' | 'reviewed' | 'in_crm' | 'discarded'
  detected_at: string
  updated_at: string
}

export interface Contact {
  id: string
  full_name: string
  title: string
  email: string
  email_verified: boolean
  linkedin_url: string | null
  funder_id: string
  funder_name: string
  source: 'apollo' | 'manual' | 'linkedin'
  fetched_at: string
}

export interface Alert {
  type: 'vencimiento' | 'cambio'
  opportunityId: string
  title: string
  urgency: 'high' | 'medium' | 'low'
  message: string
  timestamp: string
}

export interface FilterState {
  estado: 'detected' | 'reviewed' | 'in_crm' | 'cerrada' | ''
  urgencia: 'high' | 'medium' | 'low' | ''
  financiador: string // empty or funder_id
  sector: string // empty or sector name
}

export interface DashboardMetrics {
  detected: number
  reviewed: number
  in_crm: number
  cerrada: number
}
