export interface Opportunity {
  id: string
  title: string
  description: string | null
  funder_name: string | null
  funder_id: string | null
  score_total: number | null
  decision: string | null
  urgency: string | null
  deadline: string | null
  source_name: string | null
  url_rfp: string | null
  url_tor: string | null
  url_form: string | null
  org_website: string | null
  org_email: string | null
  org_email_verified: boolean
  ceo_name: string | null
  ceo_title?: string | null
  ceo_email: string | null
  ceo_email_verified: boolean
  ceo_linkedin_url: string | null
  market_window: string | null
  capital_type: string | null
  amount_min_cop: number | null
  amount_max_cop: number | null
  tender_type: string | null
  open_date: string | null
  score_details: {
    c1?: number
    c2?: number
    c3?: number
    c4?: number
    c5?: number
    llm_justification?: string
    confidence?: string
  } | null
}

export interface OpportunityList {
  items: Opportunity[]
  total: number
  page: number
  size: number
}

export interface Metrics {
  total_detected: number
  total_go: number
  total_pending: number
  total_no_go: number
}

export interface FilterState {
  decision?: string
  window?: string
  urgency?: string
  capital_type?: string
  score_min?: string
  q?: string
}
