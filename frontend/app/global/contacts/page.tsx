'use client'

import { useState, useEffect } from "react"
import { Contact, ApiListResponse } from "@/app/types"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function GlobalContactsPage() {
  const [contacts, setContacts] = useState<Contact[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState("")

  useEffect(() => {
    fetchContacts()
  }, [page, search])

  async function fetchContacts() {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        size: "25",
      })

      if (search) params.append("search", search)

      const res = await fetch(`${API_URL}/api/v1/contacts?${params}`)
      const data: ApiListResponse<Contact> = await res.json()

      setContacts(data.items)
      setTotal(data.total)
    } catch (error) {
      console.error("Error fetching contacts:", error)
    } finally {
      setLoading(false)
    }
  }

  async function handleExport() {
    try {
      const res = await fetch(`${API_URL}/api/v1/contacts/export`)
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

  const getRoleColor = (category: string | undefined): string => {
    switch (category) {
      case "partnerships": return "#4CAF50"
      case "grants": return "#2196F3"
      case "cooperation": return "#FF9800"
      case "innovation": return "#9C27B0"
      case "development": return "#F44336"
      default: return "var(--muted)"
    }
  }

  return (
    <div className="page">
      <div className="section-hd" style={{ marginBottom: '20px' }}>
        <h2>Contactos Clave GLOBAL</h2>
        <p style={{ color: 'var(--muted)', fontSize: '13px', marginTop: '4px' }}>
          {total} profesionales en roles estratégicos (partnerships, grants, cooperación, innovación)
        </p>
      </div>

      <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap' }}>
        <input
          type="text"
          placeholder="Buscar por nombre, organización, cargo..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value)
            setPage(1)
          }}
          style={{
            padding: '8px 12px',
            fontSize: '13px',
            border: '1px solid var(--border)',
            borderRadius: '4px',
            backgroundColor: 'var(--bg)',
            flex: 1,
            minWidth: '200px',
          }}
        />

        <button
          onClick={handleExport}
          className="link-btn primary"
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
                  <th>Organización</th>
                  <th>Email</th>
                  <th>LinkedIn</th>
                  <th style={{ textAlign: 'center' }}>Prioridad</th>
                </tr>
              </thead>
              <tbody>
                {contacts.map((contact) => (
                  <tr key={contact.id}>
                    <td style={{ fontWeight: 500 }}>
                      {contact.full_name} {contact.last_name}
                    </td>
                    <td className="td-muted" style={{ fontSize: '12px' }}>
                      {contact.title || "—"}
                    </td>
                    <td>
                      {contact.role_category ? (
                        <span style={{
                          fontSize: '11px',
                          padding: '4px 8px',
                          backgroundColor: getRoleColor(contact.role_category),
                          color: 'white',
                          borderRadius: '3px',
                          fontWeight: 500,
                        }}>
                          {contact.role_category}
                        </span>
                      ) : (
                        <span className="td-muted">—</span>
                      )}
                    </td>
                    <td className="td-muted" style={{ fontSize: '12px' }}>
                      {contact.funder_name || "—"}
                    </td>
                    <td className="td-link" style={{ fontSize: '12px' }}>
                      {contact.email ? (
                        <a href={`mailto:${contact.email}`} style={{ color: 'var(--primary)' }}>
                          {contact.email}
                        </a>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td style={{ fontSize: '12px' }}>
                      {contact.linkedin_url ? (
                        <a href={contact.linkedin_url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--primary)' }}>
                          Perfil →
                        </a>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td style={{ textAlign: 'center', fontSize: '12px' }}>
                      {contact.priority_score ? (
                        <span style={{ color: 'var(--go)', fontWeight: 600 }}>
                          {"★".repeat(contact.priority_score)}
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
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
