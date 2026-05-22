# Sprint S6 — Dashboard Metabase

## Especificación Técnica

**Componente:** Metabase self-hosted (Docker)  
**Datasource:** Supabase PostgreSQL  
**Refresh:** 1 hora automático  
**Objetivo:** Dashboard ejecutivo para Gerencia de Alianzas  

---

## 1. SETUP METABASE

### Instalación (Docker)

```bash
docker run -d \
  --name metabase \
  -p 3001:3000 \
  -v metabase_data:/metabase-data \
  -e MB_DB_TYPE=postgres \
  -e MB_DB_DBNAME=metabase \
  -e MB_DB_HOST=db.supabase.co \
  -e MB_DB_USER=postgres \
  -e MB_DB_PASS=$SUPABASE_PASSWORD \
  -e MB_DB_PORT=5432 \
  metabase/metabase:latest

# Acceder a: http://localhost:3001
```

### Configuración Inicial

1. Crear cuenta admin (email + password)
2. Conectar datasource Supabase:
   - **Tipo:** PostgreSQL
   - **Host:** `db.xxxxx.supabase.co`
   - **Port:** 5432
   - **Database:** postgres
   - **User:** postgres
   - **Password:** [SUPABASE_PASSWORD]

---

## 2. DASHBOARDS A CREAR

### Dashboard 1: "RADAR — Pipeline Principal"

**Audiencia:** Gerente de Alianzas, Director Ejecutivo  
**Refresh:** Cada hora  
**URL:** `/metabase/dashboard/1-radar-pipeline`

#### Tarjetas (Cards)

**Fila 1 — KPIs Principales**
```
┌─────────────────┬──────────────────┬──────────────┬─────────────────┐
│ Total Opps      │ Opps GO (Score>6)│ Revenue Pot  │ Promedio Score  │
│ (contador)      │ (contador)       │ (suma COP)   │ (media)         │
│ 37              │ 12               │ $2.4B        │ 5.8/10          │
└─────────────────┴──────────────────┴──────────────┴─────────────────┘
```

**Query:**
```sql
-- Total opps
SELECT COUNT(*) FROM opportunities WHERE status != 'discarded';

-- Opps GO
SELECT COUNT(*) FROM opportunities WHERE decision = 'go';

-- Revenue potential
SELECT SUM(amount_max_cop) FROM opportunities WHERE decision = 'go';

-- Avg score
SELECT AVG(score_total) FROM opportunities WHERE score_total IS NOT NULL;
```

---

**Fila 2 — Distribución por Ventana de Mercado**

```
Gráfico de barras horizontal:
├── funding_colombia:  15 opps (40%)
├── funding_global:     8 opps (22%)
├── strategic:          10 opps (27%)
└── latam:              4 opps (11%)
```

**Query:**
```sql
SELECT 
  market_window,
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM opportunities), 1) as pct
FROM opportunities
WHERE status != 'discarded'
GROUP BY market_window
ORDER BY count DESC;
```

---

**Fila 3 — Distribución de Scores (Histograma)**

```
Histograma: Score 0-10 en buckets de 2
├── 0-2:   4 opps
├── 2-4:   8 opps
├── 4-6:   13 opps
├── 6-8:   9 opps
├── 8-10:  3 opps
```

**Query:**
```sql
SELECT 
  CASE 
    WHEN score_total < 2 THEN '0-2'
    WHEN score_total < 4 THEN '2-4'
    WHEN score_total < 6 THEN '4-6'
    WHEN score_total < 8 THEN '6-8'
    ELSE '8-10'
  END as score_bucket,
  COUNT(*) as count
FROM opportunities
WHERE score_total IS NOT NULL AND status != 'discarded'
GROUP BY score_bucket
ORDER BY score_bucket;
```

---

**Fila 4 — Tendencia Temporal (Línea)**

```
Línea temporal: Opps detectadas por día (últimos 30 días)
Y: Cantidad de opps
X: Fecha
```

**Query:**
```sql
SELECT 
  DATE(detected_at) as date,
  COUNT(*) as opps_detected,
  COUNT(*) FILTER (WHERE decision = 'go') as opps_go
FROM opportunities
WHERE detected_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(detected_at)
ORDER BY date DESC;
```

---

### Dashboard 2: "ALERTAS — Vencimientos Críticos"

**Audiencia:** Ejecutor de propuestas, Gerente de Alianzas  
**Refresh:** Cada 6 horas  
**URL:** `/metabase/dashboard/2-alertas-vencimientos`

#### Tarjetas

**Vencimientos Próximos (Tabla)**

```
Columnas:
├── Título (clickeable → RFP)
├── Financiador
├── Deadline (en rojo si <7 días)
├── Score
├── Días para cierre
└── Acción (Botón "Revisar")

Filtrado por:
├── Decision = 'go' (solo opps GO)
└── Deadline BETWEEN NOW() AND NOW() + 30 DAYS
```

**Query:**
```sql
SELECT 
  id,
  title,
  funder_name,
  deadline,
  score_total,
  EXTRACT(DAY FROM deadline - NOW())::INT as days_to_deadline,
  decision,
  url_rfp
FROM opportunities
WHERE decision = 'go'
  AND deadline IS NOT NULL
  AND deadline BETWEEN NOW() AND NOW() + INTERVAL '30 days'
ORDER BY deadline ASC;
```

---

### Dashboard 3: "FINANCIADORES — Análisis Relacional"

**Audiencia:** Gerente de Alianzas (relaciones)  
**Refresh:** Cada día  
**URL:** `/metabase/dashboard/3-financiadores`

#### Tarjetas

**Top 10 Financiadores (Tabla con ranking)**

```
Columnas:
├── Rank
├── Financiador
├── Opps detectadas
├── Opps GO
├── Avg Score
├── Historial aeioTU (Sí/No)
└── Contacto CEO
```

**Query:**
```sql
SELECT 
  ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) as rank,
  funder_name,
  COUNT(*) as total_opps,
  COUNT(*) FILTER (WHERE decision = 'go') as opps_go,
  ROUND(AVG(score_total)::numeric, 1) as avg_score,
  MAX(f.has_history) as has_history,
  MAX(ceo_name) as ceo_name
FROM opportunities o
LEFT JOIN funders f ON o.funder_name = f.name
WHERE o.status != 'discarded'
GROUP BY o.funder_name
ORDER BY total_opps DESC
LIMIT 10;
```

---

**Oportunidades por Financiador (Gráfico de barras)**

```
Top 5 financiadores + volumen de opps en cada ventana
```

---

## 3. FILTROS GLOBALES (Aplicables a todos los dashboards)

```
┌─────────────────────────────────────────────────────┐
│ Filtros:                                            │
│ ☐ Ventana: [funding_colombia▼] [funding_global▼]  │
│ ☐ Score Min: [________] (0-10)                     │
│ ☐ Decision: [All▼] [Go▼] [No Go▼] [Pending▼]      │
│ ☐ Status: [All▼] [Detected▼] [Reviewed▼] [In CRM▼]│
│ ☐ Días para cierre: [________] días                │
└─────────────────────────────────────────────────────┘
```

**Implementación:** Métodos de Metabase → Dashboard Parameters

---

## 4. PERMISOS Y ACCESO

```
Grupos Metabase:
├── Admins (Dev)
│   └── Acceso completo (crear, editar dashboards)
│
├── Alianzas (Equipo)
│   └── Ver dashboards en lectura
│   └── Descargar datos (CSV/Excel)
│   └── NO: crear/editar dashboards
│
└── Ejecutivos (Dirección)
    └── Solo RADAR dashboard (KPIs)
```

---

## 5. ALERTAS AUTOMÁTICAS

**Integración con Slack (opcional pero recomendada)**

```
Cuando:
├── Opp GO vence en 7 días → Slack #alianzas
├── >5 opps detectadas en 1 día → Slack #dev-alerts
└── Score promedio baja <5.0 → Slack #analytics

Implementación: Metabase Alerts (Pulses)
```

---

## 6. CÁLCULOS Y REGLAS

### Score Distribution
- Colores: Verde (8-10), Amarillo (6-8), Naranja (4-6), Rojo (<4)
- Tooltip: Mostrar criterios (C1, C2, C3, C4, C5)

### Financiador con Historial
- `has_history = TRUE` → Badge "Aliado histórico"
- Permite filtrar por "Solo financiadores conocidos"

### Deadline Crítico
- Rojo si: `days_to_deadline < 7`
- Amarillo si: `7 <= days_to_deadline <= 15`
- Verde si: `days_to_deadline > 15`

---

## 7. TESTING ANTES DE PRODUCCIÓN

```
Checklist:
☐ Queries ejecutan en <3 segundos
☐ Dashboards cargan en <10 segundos
☐ Filtros funcionan sin errores
☐ Números coinciden con DB directa (SELECT COUNT)
☐ Equipo puede navegar sin help
☐ Refresh automático (1h) funciona
☐ No hay datos sensibles expuestos (solo oportunidades públicas)
```

---

## 8. DEPLOYMENT

```bash
# 1. Setup Metabase (ver sección 1)
# 2. Importar datasource Supabase
# 3. Crear dashboards (UI Metabase)
# 4. Configurar refresh (cron cada 1h)
# 5. Compartir URL con equipo
# 6. Crear grupo "Alianzas" y permisos

# Backup:
docker exec metabase pg_dump metabase > metabase_backup.sql
```

---

## 9. ITERACIONES FUTURAS

Post-MVP:
- [ ] Exportar dashboard a PDF (reportes mensuales)
- [ ] Email digest semanal (top 5 opps)
- [ ] Integración con Salesforce (sync automático)
- [ ] Predictive scoring (cuál va a ser GO antes del scoring)

---

**Responsable:** Dev Principal  
**ETA:** 4-5 días (Semana 1, S6)  
**Dependencia:** Backend API + Supabase activos
