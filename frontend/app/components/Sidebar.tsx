'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'

const NAV_STRUCTURE = [
  {
    id: 'oportunidades',
    label: 'Oportunidades',
    href: '/',
    icon: '◈',
    subsections: [
      { label: 'Alertas', href: '/?section=alertas', icon: '!' },
      { label: 'Radar', href: '/?section=radar', icon: '◎' },
      { label: 'Pipeline', href: '/?section=pipeline', icon: '▱' },
      { label: 'Contactos', href: '/?section=contacts', icon: '·' },
    ],
  },
  {
    id: 'nacional',
    label: 'Nacional Colombia',
    href: '/nacional',
    icon: '◆',
    count: '4',
    subsections: [
      { label: 'Alertas', href: '/nacional?section=alertas', icon: '!' },
      { label: 'Radar', href: '/nacional?section=radar', icon: '◎' },
      { label: 'Pipeline', href: '/nacional?section=pipeline', icon: '▱' },
      { label: 'Contactos', href: '/nacional?section=contactos', icon: '·' },
    ],
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
        <div className="nav-section">Principal</div>
        {NAV_STRUCTURE.map((section) => (
          <div key={section.id}>
            <Link
              href={section.href}
              className={`nav-item ${pathname === section.href || pathname.startsWith(section.href + '?') ? 'active' : ''}`}
            >
              <span className="nav-icon">{section.icon}</span>
              {section.label}
              {section.count && (
                <span className="nav-count">{section.count}</span>
              )}
            </Link>

            {/* Subsecciones indentadas */}
            <div className="nav-subsections">
              {section.subsections.map((sub) => (
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
          </div>
        ))}

        <div className="nav-section" style={{ marginTop: 8 }}>Sistema</div>
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
