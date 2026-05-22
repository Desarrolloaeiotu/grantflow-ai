'use client'

import RunScraperButton from './RunScraperButton'

interface ScraperControlsProps {
  source?: string
  title?: string
}

export default function ScraperControls({
  source = 'grantsgov',
  title = 'Ejecutar Scraper'
}: ScraperControlsProps) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
      <RunScraperButton source={source} label={`▶ ${title}`} showStatus={true} />
    </div>
  )
}
