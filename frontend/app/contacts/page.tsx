export default function ContactsPage() {
  return (
    <div className="page">

      <div className="topbar" style={{ margin: '-20px -24px 0', width: 'calc(100% + 48px)' }}>
        <div className="topbar-title">
          Contactos <span>— verificados por Apollo.io</span>
        </div>
        <span className="chip chip-muted">Disponible Sprint S5</span>
      </div>

      <div className="section-hd" style={{ marginTop: 20 }}>
        <h2>Contactos por financiador <em>— CEOs y representantes de programa</em></h2>
      </div>

      <div className="data-table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Nombre / Cargo</th>
              <th>Organización</th>
              <th>Email</th>
              <th>LinkedIn</th>
              <th style={{ textAlign: 'center' }}>Verificado</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colSpan={5}>
                <div style={{ padding: '32px', textAlign: 'center', color: 'var(--muted)', fontSize: 12 }}>
                  Los contactos se cargarán aquí cuando Apollo.io esté configurado (Sprint S5 · mes 5).<br />
                  <span style={{ fontSize: 11, marginTop: 6, display: 'block' }}>
                    Configura <span style={{ fontFamily: 'var(--mono)', color: 'var(--amber)' }}>APOLLO_API_KEY</span> en el .env para activar la verificación de emails.
                  </span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--r-lg)', padding: 18 }}>
        <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 12 }}>
          Campos que se almacenarán por contacto
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
          {[
            ['Nombre completo', 'Nombre del CEO o rep.'],
            ['Cargo exacto', 'CEO, Director, Program Officer'],
            ['Email directo', 'Verificado por Apollo.io'],
            ['Email verificado', 'Confidence ≥ "high"'],
            ['LinkedIn URL', 'Perfil del contacto'],
            ['Apollo ID', 'ID interno para re-consulta'],
            ['Org. website', 'Sitio oficial del financiador'],
            ['Org. email', 'Email institucional general'],
            ['Historial aeioTU', 'Si hay relación previa'],
          ].map(([label, desc]) => (
            <div key={label} style={{ background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: 8, padding: '10px 12px' }}>
              <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--text)', marginBottom: 2 }}>{label}</div>
              <div style={{ fontSize: 11, color: 'var(--muted)' }}>{desc}</div>
            </div>
          ))}
        </div>
      </div>

    </div>
  )
}
