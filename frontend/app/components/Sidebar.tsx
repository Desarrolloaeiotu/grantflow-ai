'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'

const NAV_STRUCTURE = [
  // ── MÓDULO GLOBAL v2 ────────────────────────────────────────────────
  {
    id: 'global',
    label: 'GLOBAL',
    icon: '▶',
    isSection: true,
  },
  {
    id: 'organizations',
    label: 'Organizaciones',
    href: '/organizations',
    icon: '◆',
    subsections: [],
  },
  {
    id: 'convocatorias',
    label: 'Convocatorias',
    href: '/convocatorias',
    icon: '◇',
    subsections: [
      { label: '≥ COP $100M', href: '/convocatorias', icon: '✓' },
    ],
  },
  {
    id: 'contacts',
    label: 'Contactos',
    href: '/contacts',
    icon: '·',
    subsections: [],
  },

  // ── MÓDULO NACIONAL v2 ──────────────────────────────────────────────
  {
    id: 'nacional-header',
    label: 'NACIONAL',
    icon: '▶',
    isSection: true,
  },
  {
    id: 'nacional-home',
    label: 'Módulo Colombia',
    href: '/nacional/home',
    icon: '🇨🇴',
    subsections: [],
  },
  {
    id: 'nacional-organizations',
    label: 'Organizaciones',
    href: '/nacional/organizations',
    icon: '◆',
    subsections: [],
  },
  {
    id: 'nacional-convocatorias',
    label: 'Convocatorias',
    href: '/nacional/convocatorias',
    icon: '◇',
    subsections: [
      { label: '≥ COP $50M', href: '/nacional/convocatorias', icon: '✓' },
    ],
  },
  {
    id: 'nacional-contacts',
    label: 'Contactos',
    href: '/nacional/contacts',
    icon: '·',
    subsections: [],
  },
]

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-logo">GrantFlow <span>AI</span></div>
        <div className="brand-org">aeioTU · Alianzas</div>
      </div>

      <nav className="nav">
        {NAV_STRUCTURE.map((item: any) => {
          // Items de sección (headers)
          if (item.isSection) {
            return (
              <div key={item.id} className="nav-section" style={{ marginTop: 12 }}>
                {item.label}
              </div>
            )
          }

          // Items normales con href
          if (!item.href) return null

          return (
            <div key={item.id}>
              <Link
                href={item.href}
                className={`nav-item ${pathname === item.href || pathname?.startsWith(item.href + '?') ? 'active' : ''}`}
              >
                <span className="nav-icon">{item.icon}</span>
                {item.label}
                {item.count && (
                  <span className="nav-count">{item.count}</span>
                )}
              </Link>

              {/* Subsecciones indentadas */}
              {item.subsections && item.subsections.length > 0 && (
                <div className="nav-subsections">
                  {item.subsections.map((sub: any) => (
                    <Link
                      key={sub.href}
                      href={sub.href}
                      className="nav-subitem"
                    >
                      <span className="nav-icon" style={{ fontSize: 12 }}>{sub.icon}</span>
                      <span style={{ fontSize: 13 }}>{sub.label}</span>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )
        })}

        <div className="nav-section" style={{ marginTop: 12 }}>Sistema</div>
        <Link
          href="/"
          className="nav-item"
          style={{ opacity: 0.6, fontSize: 12 }}
        >
          <span className="nav-icon">↓</span>
          Exportar CRM
        </Link>
      </nav>

      <div className="sidebar-footer">
        <span className="sync-dot"></span>Backend activo
        <div style={{ marginTop: 4, fontSize: 10 }}>
          FastAPI · localhost:8000
        </div>
      </div>
    </aside>
  )
}
