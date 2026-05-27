import { Opportunity } from '../types'

interface ContactosSectionProps {
  opportunities: Opportunity[]
}

export default function ContactosSection({ opportunities }: ContactosSectionProps) {
  const withContacts = opportunities.filter(
    o => o.ceo_email || o.org_email || o.ceo_name
  )

  return (
    <div className="page">
      {withContacts.length === 0 ? (
        <div className="empty-state">
          <strong>Sin contactos disponibles.</strong><br />
          Los contactos aparecerán aquí cuando las oportunidades sean enriquecidas con Apollo.io.
        </div>
      ) : (
        <>
          <div className="section-hd">
            <h2>
              Contactos <em>({withContacts.length} oportunidad{withContacts.length !== 1 ? 'es' : ''} con datos)</em>
            </h2>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {withContacts.map(opp => (
              <ContactCard key={opp.id} opp={opp} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function ContactCard({ opp }: { opp: Opportunity }) {
  const title = opp.title.length > 80 ? opp.title.slice(0, 80) + '…' : opp.title

  const hasOrg = opp.org_email || opp.org_website
  const hasCeo = opp.ceo_name  || opp.ceo_email

  return (
    <div className="opp-card">
      <div className="opp-title" style={{ marginBottom: 10 }}>{title}</div>

      <div className="opp-info-grid">
        {hasOrg && (
          <div className="opp-info-block">
            <div className="info-role">Organización</div>
            <div className="info-name">{opp.source_name ?? 'Organización'}</div>
            {opp.org_email && (
              <div className="info-detail">
                {opp.org_email}
                {opp.org_email_verified && (
                  <span style={{ color: 'var(--go)', marginLeft: 4 }}>✓</span>
                )}
                {!opp.org_email_verified && (
                  <span style={{ color: 'var(--amber)', marginLeft: 4 }}>⚠</span>
                )}
              </div>
            )}
            {opp.org_website && (
              <div className="info-detail">{opp.org_website}</div>
            )}
          </div>
        )}

        {hasCeo && (
          <div className="opp-info-block">
            <div className="info-role">{opp.ceo_title ?? 'CEO / Representante'}</div>
            <div className="info-name">{opp.ceo_name ?? '—'}</div>
            {opp.ceo_email && (
              <div className="info-detail">
                {opp.ceo_email}
                {opp.ceo_email_verified && (
                  <span style={{ color: 'var(--go)', marginLeft: 4 }}>✓</span>
                )}
                {!opp.ceo_email_verified && (
                  <span style={{ color: 'var(--amber)', marginLeft: 4 }}>⚠</span>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="opp-links">
        {opp.ceo_email && (
          <a href={`mailto:${opp.ceo_email}`} className="link-btn primary">
            ✉ Contactar CEO
          </a>
        )}
        {!opp.ceo_email && opp.org_email && (
          <a href={`mailto:${opp.org_email}`} className="link-btn primary">
            ✉ Contactar org
          </a>
        )}
        {opp.ceo_linkedin_url && (
          <a
            href={opp.ceo_linkedin_url}
            target="_blank"
            rel="noopener noreferrer"
            className="link-btn"
          >
            LinkedIn
          </a>
        )}
        {opp.url_rfp && (
          <a
            href={opp.url_rfp}
            target="_blank"
            rel="noopener noreferrer"
            className="link-btn"
          >
            ↗ Ver convocatoria
          </a>
        )}
      </div>
    </div>
  )
}
