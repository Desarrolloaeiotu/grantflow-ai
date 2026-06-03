'use client'

import { useState, useEffect } from "react"
import { KeyContact, ApiListResponse } from "@/app/types"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function ContatosNacionalPage() {
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
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-4">Contactos Clave Colombia</h1>
        <div className="flex gap-4 items-end">
          <select
            value={roleFilter}
            onChange={(e) => {
              setRoleFilter(e.target.value)
              setPage(1)
            }}
            className="px-3 py-2 border rounded"
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
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Exportar CSV
          </button>
        </div>
      </div>

      {loading ? (
        <p className="text-gray-600">Cargando...</p>
      ) : (
        <>
          <div className="overflow-x-auto border rounded-lg">
            <table className="w-full border-collapse">
              <thead className="bg-gray-100">
                <tr>
                  <th className="text-left p-3 border-b">Nombre</th>
                  <th className="text-left p-3 border-b">Cargo</th>
                  <th className="text-left p-3 border-b">Rol</th>
                  <th className="text-left p-3 border-b">Email</th>
                  <th className="text-left p-3 border-b">LinkedIn</th>
                  <th className="text-left p-3 border-b">Organización</th>
                </tr>
              </thead>
              <tbody>
                {contacts.map((contact) => (
                  <tr key={contact.id} className="border-b hover:bg-gray-50">
                    <td className="p-3 font-medium">{contact.full_name}</td>
                    <td className="p-3 text-sm text-gray-700">{contact.title || "—"}</td>
                    <td className="p-3 text-sm">
                      <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                        {contact.role_category || "—"}
                      </span>
                    </td>
                    <td className="p-3 text-sm text-blue-600">
                      {contact.email ? (
                        <a href={`mailto:${contact.email}`}>{contact.email}</a>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="p-3 text-sm">
                      {contact.linkedin_url ? (
                        <a
                          href={contact.linkedin_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline"
                        >
                          Perfil →
                        </a>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="p-3 text-sm text-gray-700">{contact.funder_name || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {contacts.length === 0 && (
            <p className="text-gray-600 text-center py-8">
              No hay contactos que cumplan los criterios
            </p>
          )}

          <div className="mt-6 flex justify-between items-center text-sm text-gray-600">
            <span>
              Mostrando {contacts.length} de {total} contactos
            </span>
            <div className="flex gap-2">
              <button
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
                className="px-3 py-1 border rounded hover:bg-gray-100 disabled:opacity-50"
              >
                Anterior
              </button>
              <span className="px-3 py-1">Página {page}</span>
              <button
                disabled={page * 25 >= total}
                onClick={() => setPage(page + 1)}
                className="px-3 py-1 border rounded hover:bg-gray-100 disabled:opacity-50"
              >
                Siguiente
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
