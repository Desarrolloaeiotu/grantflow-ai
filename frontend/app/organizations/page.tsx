'use client'

import { useState, useEffect } from "react"
import { Organization, ApiListResponse } from "@/app/types"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function OrganizationsPage() {
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState({
    invests_colombia: false,
    invests_latam: false,
  })

  useEffect(() => {
    fetchOrganizations()
  }, [page, filters])

  async function fetchOrganizations() {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        size: "25",
      })

      if (filters.invests_colombia) params.append("invests_colombia", "true")
      if (filters.invests_latam) params.append("invests_latam", "true")

      const res = await fetch(`${API_URL}/api/v1/organizations?${params}`)
      const data: ApiListResponse<Organization> = await res.json()

      setOrganizations(data.items)
      setTotal(data.total)
    } catch (error) {
      console.error("Error fetching organizations:", error)
    } finally {
      setLoading(false)
    }
  }

  async function handleExport() {
    try {
      const res = await fetch(`${API_URL}/api/v1/organizations/export/csv`)
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
        <h1 className="text-3xl font-bold mb-4">Organizaciones</h1>
        <div className="flex gap-4 items-end">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={filters.invests_colombia}
              onChange={(e) =>
                setFilters({ ...filters, invests_colombia: e.target.checked })
              }
            />
            <span>Invierte en Colombia</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={filters.invests_latam}
              onChange={(e) =>
                setFilters({ ...filters, invests_latam: e.target.checked })
              }
            />
            <span>Invierte en LatAm</span>
          </label>
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
                  <th className="text-left p-3 border-b">País</th>
                  <th className="text-left p-3 border-b">Tipo</th>
                  <th className="text-center p-3 border-b">CO</th>
                  <th className="text-center p-3 border-b">LatAm</th>
                  <th className="text-left p-3 border-b">Rol aeioTU</th>
                  <th className="text-left p-3 border-b">Contactos</th>
                </tr>
              </thead>
              <tbody>
                {organizations.map((org) => (
                  <tr key={org.id} className="border-b hover:bg-gray-50">
                    <td className="p-3">
                      <a
                        href={`/organizations/${org.id}`}
                        className="text-blue-600 hover:underline font-medium"
                      >
                        {org.name}
                      </a>
                    </td>
                    <td className="p-3">{org.country || "—"}</td>
                    <td className="p-3 text-sm">{org.org_type || "—"}</td>
                    <td className="p-3 text-center text-sm">
                      {org.invests_colombia ? "✓" : ""}
                    </td>
                    <td className="p-3 text-center text-sm">
                      {org.invests_latam ? "✓" : ""}
                    </td>
                    <td className="p-3 text-sm">{org.aeiotu_role || "—"}</td>
                    <td className="p-3 text-sm text-gray-600">
                      {org.contacts?.length || 0} contactos
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-4 flex justify-between items-center text-sm text-gray-600">
            <span>
              Mostrando {organizations.length} de {total} organizaciones
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
