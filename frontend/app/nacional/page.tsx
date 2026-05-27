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
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <NacionalSidebar metrics={metrics} alertCount={alertCount} />

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        {/* Top bar with scraper button */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Nacional Colombia</h1>
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
    </div>
  )
}
