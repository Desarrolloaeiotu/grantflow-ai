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

  const opportunities = list?.items || []

  return (
    <div className="flex h-screen bg-gray-100">
      <main className="flex-1 overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Oportunidades Global</h1>
          <RunScraperButton
            source="grantsgov"
            label="▶ Ejecutar Scraper Global"
          />
        </div>

        <Suspense fallback={<div className="p-6">Cargando...</div>}>
          {section === 'alertas' && (
            <AlertasSection opportunities={opportunities} />
          )}
          {section === 'radar' && (
            <RadarSection initialList={list} />
          )}
          {section === 'pipeline' && (
            <PipelineSection opportunities={opportunities} />
          )}
          {section === 'contactos' && (
            <ContactosSection opportunities={opportunities} />
          )}
        </Suspense>
      </main>

      <OpportunitiesSidebar metrics={metrics} />
    </div>
  )
}
