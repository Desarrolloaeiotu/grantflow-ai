# Sprint S6 — CSV Export para CRM

## Especificación Técnica

**Componente:** Endpoint REST + UI export button  
**Formato:** CSV (Excel-compatible)  
**Objetivo:** Integración manual con CRM (Salesforce, Pipedrive, etc.)  

---

## 1. ENDPOINT API

### GET `/api/v1/opportunities/export`

**Descripción:** Exporta oportunidades en CSV basado en filtros

**Request Parameters:**

```
GET /api/v1/opportunities/export?format=csv&window=funding_colombia&decision=go&score_min=6&limit=100

Query Parameters:
├── format: "csv" (default) | "excel" | "json"
├── window: "funding_colombia" | "funding_global" | "strategic" | "latam" | "" (all)
├── decision: "go" | "no_go" | "pending" | "" (all)
├── urgency: "high" | "medium" | "low" | "" (all)
├── score_min: 0-10 (default: 0)
├── source: "grantsgov" | "bid" | "unwomen" | "nacional_colombia" | "" (all)
├── status: "detected" | "reviewed" | "in_crm" | "discarded" | "" (all)
├── limit: 1-1000 (default: 100)
└── offset: 0+ (default: 0, para paginación)
```

**Response:**

```
HTTP/1.1 200 OK
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="grantflow_export_2026-05-26.csv"

Title,Funder Name,Deadline,Amount Min COP,Amount Max COP,Score,Decision,Urgency,Window,URL RFP,Source,Status,CEO Name,CEO Email,Org Website,Detected At
"CDI Improvement Grant","ICBF","2026-06-30",100000000,500000000,8,"go","high","funding_colombia","https://icbf.gov.co/rfp/123","nacional_colombia","reviewed","María García","maria@icbf.gov.co","www.icbf.gov.co","2026-05-19"
...
```

---

## 2. ESQUEMA CSV

### Columnas (en orden)

```csv
# Identificación
ID*
Title*
Funder Name*

# Financiero
Amount Min COP
Amount Max COP
Currency
Capital Type

# Cronograma
Deadline*
Days to Deadline

# Clasificación
Decision*
Urgency*
Score Total*
Score C1
Score C2
Score C3
Score C4
Score C5

# Ubicación y Sector
Market Window*
Eligible Countries
Sectors
Source

# URLs
URL RFP
URL Source
Org Website

# Contacto
CEO Name
CEO Email
CEO Email Verified
Org Email
Org Email Verified

# Metadata
Status*
Detected At*
Updated At
CRM Status (vacío para export)

# Columnas adicionales (para audit)
Source Scraper
Raw Content (truncado a 100 chars)
```

**Leyenda:**
- `*` = campo obligatorio
- Campos sin `*` = opcionales/pueden estar vacíos

---

## 3. FILTROS SOPORTADOS

### Lógica de Filtrado

```python
# Pseudocódigo
filtered_opps = opportunities.filter(
    window in [window] if window else ALL,
    decision in [decision] if decision else ALL,
    urgency in [urgency] if urgency else ALL,
    score_total >= score_min,
    source in [source] if source else ALL,
    status in [status] if status else ALL
)
```

### Ejemplos

```
# 1. Todas las opps GO en funding_colombia con score >= 6
GET /api/v1/opportunities/export?window=funding_colombia&decision=go&score_min=6

# 2. Opps urgentes (high) que vencen pronto
GET /api/v1/opportunities/export?urgency=high&score_min=5

# 3. Solo opps que ya están "in_crm" (para audit)
GET /api/v1/opportunities/export?status=in_crm

# 4. Últimas 50 opps detectadas (por fecha)
GET /api/v1/opportunities/export?limit=50&offset=0
```

---

## 4. IMPLEMENTACIÓN BACKEND

### Nuevo Archivo: `backend/app/api/export.py`

```python
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
import csv
import io
from datetime import datetime
from app.core.database import AsyncSessionLocal
from app.models import Opportunity
from sqlalchemy import and_, or_

router = APIRouter(prefix="/api/v1/opportunities", tags=["export"])

@router.get("/export")
async def export_opportunities(
    format: str = Query("csv", regex="^(csv|excel|json)$"),
    window: str | None = Query(None),
    decision: str | None = Query(None),
    urgency: str | None = Query(None),
    score_min: int = Query(0, ge=0, le=10),
    source: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """
    Exporta oportunidades en CSV/Excel/JSON.
    
    Filtros opcionales: window, decision, urgency, score_min, source, status
    """
    
    async with AsyncSessionLocal() as session:
        # Construir query con filtros
        query = session.query(Opportunity)
        
        if window:
            query = query.filter(Opportunity.market_window == window)
        if decision:
            query = query.filter(Opportunity.decision == decision)
        if urgency:
            query = query.filter(Opportunity.urgency == urgency)
        if score_min:
            query = query.filter(Opportunity.score_total >= score_min)
        if source:
            query = query.filter(Opportunity.source_name == source)
        if status:
            query = query.filter(Opportunity.status == status)
        
        # Paginar
        total = await session.execute(
            query.statement.with_only_columns(Opportunity.id)
        )
        total_count = len(total.scalars().all())
        
        opps = (await session.execute(
            query.offset(offset).limit(limit).statement
        )).scalars().all()
        
        if not opps:
            raise HTTPException(status_code=404, detail="No opportunities found")
        
        # Generar CSV
        if format == "csv" or format == "excel":
            return generate_csv_response(opps, total_count, offset, limit)
        elif format == "json":
            return {"opportunities": [opp.to_dict() for opp in opps], "total": total_count}


def generate_csv_response(opps, total_count, offset, limit):
    """Genera respuesta CSV con streaming"""
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "ID", "Title", "Funder Name",
        "Amount Min COP", "Amount Max COP", "Currency", "Capital Type",
        "Deadline", "Days to Deadline",
        "Decision", "Urgency", "Score Total", "Score C1", "Score C2", "Score C3", "Score C4", "Score C5",
        "Market Window", "Eligible Countries", "Sectors", "Source",
        "URL RFP", "URL Source", "Org Website",
        "CEO Name", "CEO Email", "CEO Email Verified", "Org Email", "Org Email Verified",
        "Status", "Detected At", "Updated At", "CRM Status"
    ])
    
    writer.writeheader()
    
    for opp in opps:
        days_to = None
        if opp.deadline:
            from datetime import datetime, timezone
            days_to = (opp.deadline - datetime.now(timezone.utc).date()).days
        
        score_details = opp.score_details or {}
        
        writer.writerow({
            "ID": str(opp.id),
            "Title": opp.title,
            "Funder Name": opp.funder_name,
            "Amount Min COP": opp.amount_min_cop or "",
            "Amount Max COP": opp.amount_max_cop or "",
            "Currency": "COP",
            "Capital Type": opp.capital_type or "grant",
            "Deadline": opp.deadline.isoformat() if opp.deadline else "",
            "Days to Deadline": days_to or "",
            "Decision": opp.decision or "pending",
            "Urgency": opp.urgency or "",
            "Score Total": opp.score_total or "",
            "Score C1": score_details.get("c1", ""),
            "Score C2": score_details.get("c2", ""),
            "Score C3": score_details.get("c3", ""),
            "Score C4": score_details.get("c4", ""),
            "Score C5": score_details.get("c5", ""),
            "Market Window": opp.market_window or "",
            "Eligible Countries": ", ".join(opp.eligible_countries or []),
            "Sectors": ", ".join(opp.sectors or []),
            "Source": opp.source_name or "",
            "URL RFP": opp.url_rfp or "",
            "URL Source": opp.url_source or "",
            "Org Website": opp.org_website or "",
            "CEO Name": opp.ceo_name or "",
            "CEO Email": opp.ceo_email or "",
            "CEO Email Verified": "Yes" if opp.ceo_email_verified else "No",
            "Org Email": opp.org_email or "",
            "Org Email Verified": "Yes" if opp.org_email_verified else "No",
            "Status": opp.status,
            "Detected At": opp.detected_at.isoformat() if opp.detected_at else "",
            "Updated At": opp.updated_at.isoformat() if opp.updated_at else "",
            "CRM Status": ""  # Campo para que usuario rellene en CRM
        })
    
    # Cabecera HTTP para descargar
    filename = f"grantflow_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
```

### Agregar a `backend/app/main.py`:

```python
from app.api import export

app.include_router(export.router)
```

---

## 5. INTEGRACIÓN EN FRONTEND

### Botón en `/frontend/app/nacional/page.tsx`

```tsx
'use client'

import { useState } from 'react'
import { Download } from 'lucide-react'

export function ExportButton() {
  const [loading, setLoading] = useState(false)

  const handleExport = async (filters: {
    window?: string
    decision?: string
    score_min?: number
  }) => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filters.window) params.append('window', filters.window)
      if (filters.decision) params.append('decision', filters.decision)
      if (filters.score_min) params.append('score_min', filters.score_min.toString())

      const response = await fetch(`/api/v1/opportunities/export?${params}`)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `grantflow_${new Date().toISOString().split('T')[0]}.csv`
      a.click()
    } catch (error) {
      console.error('Export failed:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <button
      onClick={() => handleExport({ window: 'funding_colombia', decision: 'go' })}
      disabled={loading}
      className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
    >
      <Download size={18} />
      {loading ? 'Exportando...' : 'Descargar CSV'}
    </button>
  )
}
```

---

## 6. VALIDACIÓN DE DATOS

### Pre-export Check

```python
def validate_export_data(opp):
    """Validar que el CSV sea válido para CRM"""
    
    errors = []
    
    # Campo obligatorio
    if not opp.title:
        errors.append(f"Opp {opp.id}: missing title")
    
    # Email debe ser válido o estar vacío
    if opp.ceo_email and "@" not in opp.ceo_email:
        errors.append(f"Opp {opp.id}: invalid CEO email")
    
    # Fecha debe ser válida
    if opp.deadline and opp.deadline < date.today():
        errors.append(f"Opp {opp.id}: deadline in past")
    
    return errors
```

---

## 7. TESTING

### Test Cases

```python
# test_export.py

def test_export_csv_all():
    """GET /export sin filtros retorna todas las opps"""
    response = client.get("/api/v1/opportunities/export?format=csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv"
    # Verificar que hay header + datos

def test_export_filter_window():
    """GET /export?window=funding_colombia retorna solo esa ventana"""
    response = client.get("/api/v1/opportunities/export?window=funding_colombia&format=csv")
    assert response.status_code == 200
    # Parsear CSV y verificar todas las filas tengan window=funding_colombia

def test_export_filter_score():
    """GET /export?score_min=6 retorna solo opps con score>=6"""
    response = client.get("/api/v1/opportunities/export?score_min=6&format=csv")
    assert response.status_code == 200
    # Verificar scores

def test_export_limit():
    """GET /export?limit=10 retorna máximo 10 filas"""
    response = client.get("/api/v1/opportunities/export?limit=10&format=csv")
    lines = response.text.strip().split('\n')
    assert len(lines) <= 11  # header + 10 data rows

def test_export_pagination():
    """Offset funciona correctamente"""
    resp1 = client.get("/api/v1/opportunities/export?limit=5&offset=0&format=csv")
    resp2 = client.get("/api/v1/opportunities/export?limit=5&offset=5&format=csv")
    # Verificar que resp1 y resp2 tienen datos diferentes
```

---

## 8. IMPORTACIÓN EN CRM

### Salesforce

```
1. Data > Import > Leads/Accounts
2. Mapear columnas CSV a campos Salesforce:
   ├── Title → Lead.Company (o Account.Name)
   ├── Funder Name → Lead.Company
   ├── Amount Max COP → Amount
   ├── Deadline → Close Date
   ├── Score Total → Lead Score
   ├── CEO Name → Lead.FirstName + LastName
   ├── CEO Email → Lead.Email
   └── URL RFP → Description
3. Importar
```

### Pipedrive

```
1. Leads > Import Leads
2. Mapear a Custom Fields (crear si no existen):
   ├── grantflow_title
   ├── grantflow_funder
   ├── grantflow_amount_max
   ├── grantflow_deadline
   ├── grantflow_score
   └── grantflow_url_rfp
3. Importar
```

### Manual (Excel)

```
1. Descargar CSV desde GrantFlow
2. Copiar a Excel
3. Ajustar formato/validaciones según necesidad
4. Crear registro manualmente o importar a CRM
```

---

## 9. CONSIDERACIONES DE PRIVACIDAD

```
⚠️ El CSV contiene:
├── Emails de contactos (pueden ser públicos)
├── URLs de RFP (públicos)
└── Scores (análisis interno)

✅ El CSV NO contiene:
├── API keys
├── Datos de usuario aeioTU
└── Información sensible
```

---

## 10. DEPLOYMENT

```bash
# 1. Implementar backend/app/api/export.py
# 2. Agregar a main.py
# 3. Testar localmente: curl http://localhost:8000/api/v1/opportunities/export?format=csv
# 4. Agregar botón en frontend
# 5. Deploy

# Test en producción:
curl https://api.grantflow.aeiotu.org/api/v1/opportunities/export?window=funding_colombia&decision=go > test.csv
```

---

**Responsable:** Dev Backend  
**ETA:** 2-3 días (Semana 2, S6)  
**Dependencia:** API opportunities endpoint funcional
