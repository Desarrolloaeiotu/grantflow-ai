'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'

const NAV_ITEMS = [
  { label: 'Oportunidades', href: '/',          icon: '◈', count: null },
  { label: 'Alertas',        href: '/alertas',   icon: '!', count: null },
  { label: 'Radar',          href: '/radar',     icon: '◎', count: null },
  { label: 'Pipeline',       href: '/pipeline',  icon: '▱', count: null },
  { label: 'Contactos',      href: '/contacts',  icon: '·', count: null },
]

const NAV_NATIONAL = [
  { label: 'Nacional Colombia', href: '/nacional', icon: '◆', count: '4' },
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
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`nav-item ${pathname === item.href ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
            {item.count !== null && (
              <span className="nav-count">{item.count}</span>
            )}
          </Link>
        ))}

        <div className="nav-section" style={{ marginTop: 8 }}>Mercado Local</div>
        {NAV_NATIONAL.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`nav-item ${pathname === item.href ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
            {item.count && <span className="nav-count">{item.count}</span>}
          </Link>
        ))}

        <div className="nav-section" style={{ marginTop: 8 }}>Sistema</div>
        <Link
          href="/pipeline"
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
