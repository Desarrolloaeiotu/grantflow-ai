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
    <div style={{ display: 'flex', height: '100vh', backgroundColor: 'var(--bg)' }}>
      <main style={{ flex: 1, overflowY: 'auto' }}>
        <div style={{
          position: 'sticky',
          top: 0,
          backgroundColor: 'var(--bg2)',
          borderBottom: '1px solid var(--border)',
          padding: '16px 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          zIndex: 10,
        }}>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text)' }}>Oportunidades Global</h1>
          <RunScraperButton
            source="grantsgov"
            label="▶ Ejecutar Scraper Global"
          />
        </div>

        <Suspense fallback={<div style={{ padding: '24px', color: 'var(--muted)' }}>Cargando...</div>}>
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
