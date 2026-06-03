import Link from 'next/link'

export default function HomePage() {
  return (
    <div className="page" style={{ padding: '48px 40px' }}>
      <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '48px' }}>
          <h1 style={{ fontSize: '32px', fontWeight: 700, color: 'var(--text)', marginBottom: '16px' }}>
            GrantFlow AI
          </h1>
          <p style={{ fontSize: '16px', color: 'var(--muted)', lineHeight: '1.6' }}>
            Sistema de inteligencia comercial para prospección estratégica de oportunidades de financiamiento.
            Transforma la búsqueda manual de grants en un proceso automatizado, estandarizado y escalable.
          </p>
        </div>

        {/* Modules Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px', marginBottom: '48px' }}>
          {/* Global Module */}
          <div style={{ padding: '32px', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r)' }}>
            <div style={{ marginBottom: '24px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text)', marginBottom: '8px' }}>
                Módulo Global
              </h2>
              <p style={{ fontSize: '13px', color: 'var(--muted)' }}>
                Convocatorias internacionales ≥ COP $100M
              </p>
            </div>

            <style>{`
              .nav-link {
                display: block;
                padding: 12px 16px;
                background: var(--bg3);
                border: 1px solid var(--border);
                border-radius: var(--r);
                color: var(--blue);
                text-decoration: none;
                font-size: 14px;
                font-weight: 500;
                transition: background 0.2s;
              }
              .nav-link:hover {
                background: var(--bg);
              }
            `}</style>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <Link href="/organizations" className="nav-link">
                ◆ Organizaciones
              </Link>
              <Link href="/convocatorias" className="nav-link">
                ◇ Convocatorias (≥ COP $100M)
              </Link>
              <Link href="/contacts" className="nav-link">
                · Contactos Clave
              </Link>
            </div>
          </div>

          {/* Nacional Module */}
          <div style={{ padding: '32px', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r)' }}>
            <div style={{ marginBottom: '24px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text)', marginBottom: '8px' }}>
                Módulo Nacional
              </h2>
              <p style={{ fontSize: '13px', color: 'var(--muted)' }}>
                Inteligencia de oportunidades en Colombia
              </p>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <Link href="/nacional" className="nav-link">
                ▶ Radar de Oportunidades
              </Link>
              <Link href="/nacional/convocatorias" className="nav-link">
                ◇ Convocatorias (≥ COP $50M)
              </Link>
              <Link href="/nacional/contacts" className="nav-link">
                · Contactos Clave Colombia
              </Link>
            </div>
          </div>
        </div>

        {/* Info */}
        <div style={{ padding: '24px', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: 'var(--r)', fontSize: '13px', color: 'var(--muted)', lineHeight: '1.6' }}>
          <strong style={{ color: 'var(--text)' }}>GrantFlow v2.0</strong> — Módulos independientes para prospección estratégica.
          Selecciona un módulo en la barra lateral o navega desde los enlaces de arriba.
        </div>
      </div>
    </div>
  )
}
