'use client'

import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { Metrics } from '../types'

interface OpportunitiesSidebarProps {
  metrics: Metrics | null
}

export default function OpportunitiesSidebar({ metrics }: OpportunitiesSidebarProps) {
  const searchParams = useSearchParams()
  const activeSection = searchParams.get('section') || 'radar'

  const sections = [
    {
      id: 'alertas',
      label: 'Alertas',
      icon: '🔔',
    },
    {
      id: 'radar',
      label: 'Radar',
      icon: '📊',
    },
    {
      id: 'pipeline',
      label: 'Pipeline',
      icon: '📋',
    },
    {
      id: 'contactos',
      label: 'Contactos',
      icon: '👥',
    },
  ]

  return (
    <aside className="w-56 bg-white border-l border-gray-200 p-6 h-screen overflow-y-auto flex flex-col">
      {/* Secciones de navegación */}
      <nav className="space-y-1 mb-8">
        {sections.map((section) => (
          <Link
            key={section.id}
            href={`/?section=${section.id}`}
            className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition ${
              activeSection === section.id
                ? 'bg-blue-50 text-blue-600 font-medium'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            <span className="text-base">{section.icon}</span>
            <span>{section.label}</span>
          </Link>
        ))}
      </nav>

      {/* Resumen */}
      {metrics && (
        <div className="pt-6 border-t border-gray-200 space-y-3 text-sm">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Resumen</h3>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Detectadas</span>
              <span className="font-semibold text-gray-900">{metrics.total_detected}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">GO</span>
              <span className="font-semibold text-gray-900">{metrics.total_go}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Pendiente</span>
              <span className="font-semibold text-gray-900">{metrics.total_pending}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">No-Go</span>
              <span className="font-semibold text-gray-900">{metrics.total_no_go}</span>
            </div>
          </div>
        </div>
      )}
    </aside>
  )
}
