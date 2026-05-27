// frontend/app/nacional/components/NacionalSidebar.tsx

'use client'

import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { DashboardMetrics } from '../types'

interface NacionalSidebarProps {
  metrics: DashboardMetrics
  alertCount: number
}

export default function NacionalSidebar({
  metrics,
  alertCount,
}: NacionalSidebarProps) {
  const searchParams = useSearchParams()
  const activeSection = searchParams.get('section') || 'radar'

  const sections = [
    {
      id: 'alertas',
      label: 'Alertas',
      badge: alertCount,
      icon: '🔔',
    },
    {
      id: 'radar',
      label: 'Radar',
      badge: metrics.detected,
      icon: '📊',
    },
    {
      id: 'pipeline',
      label: 'Pipeline',
      badge: metrics.in_crm,
      icon: '📋',
    },
    {
      id: 'contactos',
      label: 'Contactos',
      badge: 0, // TODO: fetch contact count
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
            href={`/nacional?section=${section.id}`}
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
      <div className="pt-6 border-t border-gray-200 space-y-3 text-sm">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Resumen</h3>
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Detectadas</span>
            <span className="font-semibold text-gray-900">{metrics.detected}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Revisadas</span>
            <span className="font-semibold text-gray-900">{metrics.reviewed}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600">En gestión</span>
            <span className="font-semibold text-gray-900">{metrics.in_crm}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Cerradas</span>
            <span className="font-semibold text-gray-900">{metrics.cerrada}</span>
          </div>
        </div>
      </div>
    </aside>
  )
}
