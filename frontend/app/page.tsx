import { Suspense } from 'react'
import { getMetrics, getOpportunities } from './opportunities/data/opportunities-queries'
import RunScraperButton from './components/RunScraperButton'
import OpportunitiesSidebar from './opportunities/components/OpportunitiesSidebar'
import AlertasSection from './opportunities/components/AlertasSection'
import RadarSection from './opportunities/components/RadarSection'
import PipelineSection from './opportunities/components/PipelineSection'
import ContactosSection from './opportunities/components/ContactosSection'

interface OpportunitiesPageProps {
  searchParams: Promise<{ section?: string; decision?: string; window?: string; urgency?: string; capital_type?: string; score_min?: string; q?: string; page?: string }>
}

export default async function OpportunitiesPage({
  searchParams,
}: OpportunitiesPageProps) {
  const params = await searchParams
  const section = params.section || 'radar'

  // Fetch data server-side with error handling
  let metrics: any = null
  let list: any = null

  try {
    [metrics, list] = await Promise.all([
      getMetrics(),
      getOpportunities({}),
    ])
  } catch (error) {
    console.error('Error fetching Opportunities data:', error)
  }

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        {/* Top bar with scraper button */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Oportunidades Global</h1>
          <RunScraperButton
            source="grantsgov"
            label="▶ Ejecutar Scraper Global"
          />
        </div>

        {/* Section content */}
        <Suspense fallback={<div className="p-6">Cargando...</div>}>
          {section === 'alertas' && (
            <AlertasSection />
          )}
          {section === 'radar' && (
            <RadarSection initialList={list} />
          )}
          {section === 'pipeline' && (
            <PipelineSection />
          )}
          {section === 'contactos' && (
            <ContactosSection />
          )}
        </Suspense>
      </main>

      {/* Sidebar derecha */}
      <OpportunitiesSidebar metrics={metrics} />
    </div>
  )
}
