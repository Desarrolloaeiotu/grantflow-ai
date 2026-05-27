import { Suspense } from 'react'
import {
  getOportunidadesNacionales,
  getDashboardMetrics,
  getContactosNacionales,
  generateAlerts,
} from './data/nacional-queries'
import { Opportunity, Contact, DashboardMetrics } from './types'
import NacionalSidebar from './components/NacionalSidebar'
import AlertasSection from './components/AlertasSection'
import RadarSection from './components/RadarSection'
import PipelineSection from './components/PipelineSection'
import ContactosSection from './components/ContactosSection'
import LoadingState from './components/shared/LoadingState'
import RunScraperButton from '../components/RunScraperButton'

interface NacionalPageProps {
  searchParams: Promise<{ section?: string }>
}

export default async function NacionalPage({
  searchParams,
}: NacionalPageProps) {
  const params = await searchParams
  const section = params.section || 'radar'

  // Fetch data server-side with error handling
  let opportunities: Opportunity[] = []
  let metrics: DashboardMetrics = { detected: 0, reviewed: 0, in_crm: 0, cerrada: 0 }
  let contacts: Contact[] = []

  try {
    const [opps, met, conts] = await Promise.all([
      getOportunidadesNacionales(),
      getDashboardMetrics(),
      getContactosNacionales(),
    ])
    opportunities = opps
    metrics = met
    contacts = conts
  } catch (error) {
    console.error('Error fetching Nacional data:', error)
  }

  const alerts = generateAlerts(opportunities)
  const alertCount = alerts.length

  return (
    <div style={{ display: 'flex', height: '100vh', background: 'var(--bg)' }}>
      {/* Main content */}
      <main style={{ flex: 1, overflowY: 'auto' }}>
        {/* Top bar with scraper button */}
        <div style={{ position: 'sticky', top: 0, background: 'var(--bg2)', borderBottom: '1px solid var(--border)', padding: '16px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--text)' }}>Nacional Colombia</h1>
          <RunScraperButton
            source="nacional_colombia"
            label="▶ Ejecutar Scraper Nacional"
          />
        </div>

        {/* Section content */}
        <Suspense fallback={<LoadingState />}>
          {section === 'alertas' && (
            <AlertasSection opportunities={opportunities} />
          )}
          {section === 'radar' && (
            <RadarSection opportunities={opportunities} />
          )}
          {section === 'pipeline' && (
            <PipelineSection opportunities={opportunities} />
          )}
          {section === 'contactos' && (
            <ContactosSection contacts={contacts} />
          )}
        </Suspense>
      </main>

      {/* Sidebar derecha */}
      <NacionalSidebar metrics={metrics} alertCount={alertCount} />
    </div>
  )
}
