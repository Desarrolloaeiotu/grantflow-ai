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
    <aside className="w-64 bg-gray-900 text-white p-6 h-screen overflow-y-auto">
      <div className="mb-8">
        <h2 className="text-xl font-bold mb-2">Nacional Colombia</h2>
        <p className="text-xs text-gray-400">Prospección Estratégica</p>
      </div>

      <nav className="space-y-2">
        {sections.map((section) => (
          <Link
            key={section.id}
            href={`/nacional?section=${section.id}`}
            className={`flex items-center justify-between px-4 py-3 rounded-lg transition ${
              activeSection === section.id
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:bg-gray-800'
            }`}
          >
            <div className="flex items-center gap-2">
              <span className="text-lg">{section.icon}</span>
              <span className="font-medium">{section.label}</span>
            </div>
            {section.badge > 0 && (
              <span className="inline-flex items-center justify-center w-6 h-6 bg-red-600 text-white text-xs font-bold rounded-full">
                {section.badge}
              </span>
            )}
          </Link>
        ))}
      </nav>

      <div className="mt-8 pt-8 border-t border-gray-700">
        <h3 className="text-xs font-semibold text-gray-400 mb-4">RESUMEN</h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Detectadas:</span>
            <span className="font-semibold">{metrics.detected}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Revisadas:</span>
            <span className="font-semibold">{metrics.reviewed}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">En gestión:</span>
            <span className="font-semibold">{metrics.in_crm}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Cerradas:</span>
            <span className="font-semibold">{metrics.cerrada}</span>
          </div>
        </div>
      </div>
    </aside>
  )
}
