'use client'

import { useState, useEffect } from "react"
import { Tender, ApiListResponse, formatCOP, formatDate, daysUntilDeadline, getUrgencyLabel, getUrgencyColor } from "@/app/types"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function ConvocatoriasGlobalPage() {
  const [tenders, setTenders] = useState<Tender[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [decision, setDecision] = useState<string>("")

  useEffect(() => {
    fetchTenders()
  }, [page, decision])

  async function fetchTenders() {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        size: "25",
        region: "global",
      })

      if (decision) params.append("decision", decision)

      const res = await fetch(`${API_URL}/api/v1/tenders?${params}`)
      const data: ApiListResponse<Tender> = await res.json()

      setTenders(data.items)
      setTotal(data.total)
    } catch (error) {
      console.error("Error fetching tenders:", error)
    } finally {
      setLoading(false)
    }
  }

  async function handleExport() {
    try {
      const res = await fetch(`${API_URL}/api/v1/tenders/export/csv?region=global`)
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
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-3xl font-bold">Convocatorias Globales</h1>
          <div className="text-sm text-gray-600 bg-blue-50 px-3 py-2 rounded">
            Monto mínimo: COP $100M (~USD 24K)
          </div>
        </div>

        <div className="flex gap-4 items-end">
          <select
            value={decision}
            onChange={(e) => {
              setDecision(e.target.value)
              setPage(1)
            }}
            className="px-3 py-2 border rounded"
          >
            <option value="">Todas las decisiones</option>
            <option value="go">GO</option>
            <option value="no_go">NO GO</option>
            <option value="pending">PENDING</option>
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
          <div className="grid gap-4">
            {tenders.map((tender) => {
              const daysLeft = daysUntilDeadline(tender.deadline)
              const urgency = getUrgencyLabel(daysLeft)
              const urgencyColor = getUrgencyColor(daysLeft)

              return (
                <div key={tender.id} className="border rounded-lg p-4 hover:shadow-md transition">
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex-1">
                      <h3 className="font-bold text-lg mb-1">{tender.title}</h3>
                      <p className="text-sm text-gray-600">
                        Financiador: <span className="font-medium">{tender.funder_name || "—"}</span>
                      </p>
                    </div>
                    <div className="flex gap-2">
                      {tender.deadline && (
                        <span className={`text-xs font-medium px-2 py-1 rounded whitespace-nowrap ${urgencyColor}`}>
                          {urgency}
                        </span>
                      )}
                      {tender.decision && (
                        <span
                          className={`text-xs font-medium px-2 py-1 rounded whitespace-nowrap ${
                            tender.decision === "go"
                              ? "bg-green-100 text-green-800"
                              : tender.decision === "no_go"
                                ? "bg-red-100 text-red-800"
                                : "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {tender.decision.toUpperCase()}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm mb-3">
                    <div>
                      <p className="text-gray-600">Monto máximo</p>
                      <p className="font-medium">{formatCOP(tender.amount_max_cop)}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Apertura</p>
                      <p className="font-medium">{formatDate(tender.open_date)}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Cierre</p>
                      <p className="font-medium">{formatDate(tender.deadline)}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Días restantes</p>
                      <p className="font-medium">{daysLeft !== null ? daysLeft : "—"}</p>
                    </div>
                  </div>

                  {tender.description && (
                    <p className="text-sm text-gray-700 mb-3 line-clamp-2">{tender.description}</p>
                  )}

                  <div className="flex gap-2">
                    {tender.url_rfp && (
                      <a
                        href={tender.url_rfp}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-600 hover:underline"
                      >
                        RFP →
                      </a>
                    )}
                    {tender.url_tor && (
                      <a
                        href={tender.url_tor}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-600 hover:underline"
                      >
                        ToR →
                      </a>
                    )}
                    {tender.url_form && (
                      <a
                        href={tender.url_form}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-600 hover:underline"
                      >
                        Formulario →
                      </a>
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          {tenders.length === 0 && (
            <p className="text-gray-600 text-center py-8">
              No hay convocatorias que cumplan los criterios
            </p>
          )}

          <div className="mt-6 flex justify-between items-center text-sm text-gray-600">
            <span>
              Mostrando {tenders.length} de {total} convocatorias
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
