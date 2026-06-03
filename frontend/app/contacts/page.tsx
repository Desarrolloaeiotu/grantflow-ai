'use client'

import { useState, useEffect } from "react"
import { KeyContact, ApiListResponse } from "@/app/types"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function ContactsPage() {
  const [contacts, setContacts] = useState<KeyContact[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [roleFilter, setRoleFilter] = useState<string>("")

  useEffect(() => {
    fetchContacts()
  }, [page, roleFilter])

  async function fetchContacts() {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        size: "25",
      })

      if (roleFilter) params.append("role_category", roleFilter)

      const res = await fetch(`${API_URL}/api/v1/contacts?${params}`)
      const data: any = await res.json()

      setContacts(Array.isArray(data) ? data : (data.items || []))
      setTotal(data.total || 0)
    } catch (error) {
      console.error("Error fetching contacts:", error)
      setContacts([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }

  async function handleExport() {
    try {
      const res = await fetch(`${API_URL}/api/v1/contacts/export/csv`)
      const data = await res.json()
      const csv = atob(data.content_base64)
      const blob = new Blob([csv], { type: "text/csv" })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = data.filename
      a.click()
    } catch (error) {
      console.error("Error exporting:", error)
    }
  }

  return (
    <div className="page">
      <div className="section-hd" style={{ marginBottom: '20px' }}>
        <h2>Contactos Clave Globales</h2>
      </div>

      <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap' }}>
        <select
          value={roleFilter}
          onChange={(e) => {
            setRoleFilter(e.target.value)
            setPage(1)
          }}
          style={{
            padding: '6px 12px',
            border: '1px solid var(--border)',
            borderRadius: 'var(--r)',
            fontSize: '13px',
            background: 'var(--bg2)',
            color: 'var(--text)',
            cursor: 'pointer'
          }}
        >
          <option value="">Todos los roles</option>
          <option value="partnerships">Partnerships</option>
          <option value="grants">Grants Manager</option>
          <option value="cooperation">Cooperación</option>
          <option value="innovation">Innovación</option>
          <option value="development">Desarrollo</option>
        </select>

        <button
          onClick={handleExport}
          className="link-btn primary"
          style={{ marginLeft: 'auto' }}
        >
          📥 Exportar CSV
        </button>
      </div>

      {loading ? (
        <div className="empty-state">Cargando contactos...</div>
      ) : contacts.length === 0 ? (
        <div className="empty-state">No hay contactos que cumplan los criterios</div>
      ) : (
        <>
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Cargo</th>
                  <th>Rol</th>
                  <th>Email</th>
                  <th>LinkedIn</th>
                  <th>Organización</th>
                </tr>
              </thead>
              <tbody>
                {contacts.map((contact) => (
                  <tr key={contact.id}>
                    <td style={{ fontWeight: 500 }}>{contact.full_name}</td>
                    <td className="td-muted">{contact.title || "—"}</td>
                    <td><span className="badge-blue">{contact.role_category || "—"}</span></td>
                    <td className="td-link">
                      {contact.email ? (
                        <a href={`mailto:${contact.email}`} style={{ color: 'var(--blue)' }}>
                          {contact.email}
                        </a>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="td-link">
                      {contact.linkedin_url ? (
                        <a
                          href={contact.linkedin_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ color: 'var(--blue)' }}
                        >
                          Perfil ↗
                        </a>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="td-muted">{contact.funder_name || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '20px', fontSize: '12px', color: 'var(--muted)' }}>
            <span>
              Mostrando <strong>{contacts.length}</strong> de <strong>{total}</strong> contactos
            </span>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <button
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
                className="link-btn"
                style={{ opacity: page === 1 ? 0.5 : 1, cursor: page === 1 ? 'not-allowed' : 'pointer' }}
              >
                ← Anterior
              </button>
              <span style={{ padding: '4px 12px', fontSize: '12px' }}>Página {page}</span>
              <button
                disabled={page * 25 >= total}
                onClick={() => setPage(page + 1)}
                className="link-btn"
                style={{ opacity: page * 25 >= total ? 0.5 : 1, cursor: page * 25 >= total ? 'not-allowed' : 'pointer' }}
              >
                Siguiente →
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
