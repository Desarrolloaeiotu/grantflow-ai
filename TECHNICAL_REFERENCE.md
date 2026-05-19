# GrantFlow AI — Referencia Técnica Completa

**Para:** Equipo técnico y desarrolladores  
**Actualizado:** 12 mayo 2026  
**Versión:** S5 Completo

---

## 🏗️ Arquitectura Actual

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 15)                    │
│                   localhost:3000                            │
│  Dashboard + Filtros + Búsqueda + Grid de oportunidades   │
└────────────────────────┬────────────────────────────────────┘
                         │
                    REST API (FastAPI)
                    localhost:8000
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼────┐   ┌──────▼──────┐   ┌────▼──────┐
   │Database │   │Apollo.io    │   │  n8n      │
   │Supabase │   │Service      │   │Workflows  │
   │PostgreSQL   │(S5 Nuevo)   │   │(S4)       │
   └─────────┘   └─────────────┘   └───────────┘
```

---

## 📡 Endpoints Principales

### Scrapers (S5+)

#### **POST /api/v1/scrape/run**
Ejecuta todos los scrapers activos y persiste oportunidades nuevas.

**Query Parameters:**
```
?source=nacional_colombia|grantsgov|bid|unwomen|developmentaid|rss  (opcional)
?score=true|false  (opcional, default: false — scoring se hace en paso aparte)
```

**Response:**
```json
{
  "total_persisted": 25,
  "per_source": {
    "nacional_colombia": 5,
    "grantsgov": 8,
    "bid": 7,
    "unwomen": 5,
    "developmentaid": 0,
    "rss": 0
  },
  "errors": [],
  "started_at": "2026-05-13T06:00:00Z",
  "completed_at": "2026-05-13T06:08:32Z",
  "duration_sec": 512
}
```

**Orden de ejecución (prioridad):**
1. `nacional_colombia` — Fuentes nacionales colombianas (ICBF, MinEducación, SECOP, Cajas)
2. `grantsgov` — Grants.gov (USA federal)
3. `bid` — BID Lab (Latinoamérica)
4. `unwomen` — ONU Mujeres (global)
5. `developmentaid` — DevelopmentAid (global)
6. `rss` — RSS feeds genéricos

---

### Dashboard & Oportunidades

#### **GET /api/v1/dashboard/metrics**
Obtiene KPIs principales.

**Request:**
```http
GET /api/v1/dashboard/metrics HTTP/1.1
Host: localhost:8000
```

**Response:**
```json
{
  "total_detected": 816,
  "total_go": 5,
  "total_pending": 45,
  "total_no_go": 42,
  "total_in_crm": 0,
  "avg_score_go": 7.8,
  "by_window": {
    "funding_colombia": 5,
    "funding_global": 38,
    "strategic": 5
  },
  "by_urgency": {
    "medium": 226,
    "high": 64,
    "low": 91
  }
}
```

---

#### **GET /api/v1/opportunities**
Lista oportunidades con filtros.

**Query Parameters:**
```
?window=funding_colombia|funding_global|strategic|latam
&decision=go|no_go|pending
&urgency=high|medium|low
&score_min=0-10
&days_to_deadline=N
&source=grantsgov|bid|unwomen|rss|manual
&status=detected|reviewed|in_crm|discarded
&q=search_term (full-text)
&page=1
&size=25 (max 100)
```

**Response:**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "LEGO Foundation Innovation Grant",
      "description": "...",
      "score_total": 8,
      "decision": "go",
      "urgency": "medium",
      "deadline": "2026-06-30",
      "ceo_name": "Rasmus Nyrup",
      "ceo_email": "rasmus@legofoundation.org",
      "ceo_email_verified": false,
      "org_email": "info@legofoundation.org",
      "org_email_verified": false,
      "market_window": "funding_global",
      "amount_max_cop": 5000000000
    }
  ],
  "total": 816,
  "page": 1,
  "size": 25
}
```

---

#### **GET /api/v1/opportunities/{id}**
Detalle de una oportunidad específica.

**Response:** Mismo schema que items[] arriba, con campos adicionales:
- `raw_content`: Texto original sin procesar
- `embedding`: Vector (768 dims) para búsqueda semántica
- `score_details`: Desglose C1-C5
- `detected_at`, `updated_at`

---

### Apollo.io Integration (S5)

#### **POST /api/v1/contacts/verify**
Verifica si un email es válido y obtiene info de contacto.

**Request:**
```json
{
  "email": "ceo@fundacion.org",
  "name": "John Doe" (optional)
}
```

**Response:**
```json
{
  "verified": true,
  "confidence": "high",  // high|medium|low|unknown
  "email": "ceo@fundacion.org",
  "first_name": "John",
  "last_name": "Doe",
  "title": "Chief Executive Officer",
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "company": "Fundación XYZ",
  "raw_response": { ... } // Full Apollo.io response
}
```

**Notas:**
- Sin `APOLLO_API_KEY`: retorna `verified: false, confidence: "unknown"`
- Cada verificación consume ~1 credit en Apollo.io ($49 = 10k credits)
- Recomendado: máximo 10 req/min para no sobrecargar

---

#### **POST /api/v1/contacts/enrich**
Busca contactos en una organización.

**Query Parameters:**
```
?funder_id={uuid}  (obligatorio)
&limit=10          (opcional, default 10)
```

**Request:**
```http
POST /api/v1/contacts/enrich?funder_id=550e8400-e29b-41d4-a716-446655440000&limit=5
```

**Response:**
```json
{
  "status": "success",
  "funder_id": "550e8400-e29b-41d4-a716-446655440000",
  "funder_name": "LEGO Foundation",
  "contacts_found": 3,
  "contacts": [
    {
      "email": "rasmus@legofoundation.org",
      "first_name": "Rasmus",
      "last_name": "Nyrup",
      "title": "President",
      "linkedin_url": "https://linkedin.com/in/rasmusnyrup",
      "company": "LEGO Foundation",
      "verified": true
    },
    // ... más contactos
  ]
}
```

---

#### **POST /api/v1/opportunities/{id}/enrich-contacts**
Automáticamente verifica emails y busca info de CEO para una oportunidad específica.

**Request:**
```http
POST /api/v1/opportunities/550e8400-e29b-41d4-a716-446655440000/enrich-contacts
```

**Response:**
```json
{
  "opportunity_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success",
  "enhancements": [
    "org_email_verified",
    "ceo_email_verified",
    "ceo_name_enriched",
    "ceo_title_enriched",
    "ceo_linkedin_enriched"
  ],
  "enhancements_count": 5
}
```

**Campos actualizados en la oportunidad:**
- `ceo_email_verified` → true
- `ceo_email_verified_at` → timestamp UTC
- `ceo_name` → Si faltaba y Apollo encontró
- `ceo_title` → Si faltaba
- `ceo_linkedin_url` → Si faltaba
- Mismo con `org_email_*`

---

## 🔧 Instalación & Configuración

### Requisitos
```
Python 3.12+
PostgreSQL 16+ (o Supabase)
Node.js 18+ (frontend)
API keys: ANTHROPIC_API_KEY, GOOGLE_API_KEY
```

### Backend
```bash
cd backend
pip install -e .
export DATABASE_URL="postgresql://user:pass@localhost/grantflow"
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="AIza..."
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev  # http://localhost:3000
```

### Activar Apollo.io (Mes 5+)
```bash
# 1. Obtener API Key en https://app.apollo.io/settings/api
# 2. Agregar a .env:
export APOLLO_API_KEY="your_api_key_here"
# 3. Reiniciar backend
```

---

## 📚 Estructuras de Datos Clave

### Opportunity Model
```python
class Opportunity(Base):
    # Identificación
    id: UUID
    title: str
    description: str | None
    
    # Contacto
    ceo_name: str | None
    ceo_email: str | None
    ceo_email_verified: bool = False
    ceo_email_verified_at: datetime | None
    ceo_title: str | None
    ceo_linkedin_url: str | None
    ceo_apollo_id: str | None
    
    org_email: str | None
    org_email_verified: bool = False
    org_email_verified_at: datetime | None
    org_website: str | None
    
    # Oportunidad
    amount_min_cop: int | None
    amount_max_cop: int | None
    deadline: date | None
    
    # Scoring
    score_total: int | None  # 0-10
    score_details: dict | None  # {c1, c2, c3, c4, c5, llm_justification}
    decision: str | None  # go|no_go|pending
    urgency: str | None  # high|medium|low
    market_window: str | None
    capital_type: str | None  # grant|loan|investment|contract
    
    # Metadata
    status: str  # detected|reviewed|in_crm|discarded
    source_name: str | None  # grantsgov|bid|unwomen|rss|manual
    embedding: Vector(768)  # Gemini embeddings para búsqueda semántica
    detected_at: datetime
    updated_at: datetime
```

---

## 🔌 Integración con n8n

### Recomendación: Workflow `enrich-on-scoring`

```
Trigger: HTTP POST /api/v1/opportunities/{id}/score
   ↓
Fetch Opportunity desde DB
   ↓
IF decision == 'go' THEN:
   ├─ HTTP POST /api/v1/opportunities/{id}/enrich-contacts
   │  (Apollo.io verifica emails + busca CEO)
   │
   └─ Slack: "@alianzas ✅ Nueva opp GO: {title}"
       "CEO: {ceo_name} ({ceo_email})"
       "Deadline: {deadline}"
   
ELSE:
   └─ Log: Opp no es GO, skip enriquecimiento
```

### Nodos recomendados:
1. **HTTP Request** → Trigger (POST request)
2. **PostgreSQL** → Fetch opportunity
3. **If** → Condicional `decision == 'go'`
4. **HTTP Request** → POST enrich-contacts
5. **Slack** → Notificación

**Rate limiting:** Apollo.io permite 10 req/min naturalmente — no agregar sleeps artificiales.

---

## 📊 Monitoreo

### Logs (backend)
```bash
# Ver logs en tiempo real
docker logs -f grantflow_backend

# O directamente:
tail -f backend/logs/grantflow.log
```

### Métricas importantes
- **Apollo.io credit usage:** Monitor en https://app.apollo.io/dashboard
- **DB size:** `SELECT pg_size_pretty(pg_database_size('grantflow'));`
- **API latency:** Ver respuesta de `/api/v1/dashboard/metrics`

---

## 🧪 Testing

### Test Apollo.io localmente
```bash
# Verificar email (sin API key, retorna mock)
curl -X POST http://localhost:8000/api/v1/contacts/verify \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Expected: {"verified": false, "confidence": "unknown", ...}

# Con API key real, verifica email realmente
```

### Test frontend
```bash
# Dashboard carga 816 opp
curl http://localhost:3000/ | grep -o "816\|GO\|opp-"
```

---

## 🚀 Deployment (Producción)

### Variables de entorno requeridas
```bash
# Base de datos
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...

# IA
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...

# Apollo.io (Mes 5+)
APOLLO_API_KEY=your_key_here

# App
JWT_SECRET=generate_secure_random_string
ENVIRONMENT=production
NEXT_PUBLIC_API_URL=https://api.grantflow.aeiotu.org
```

### Deployment checklist
- [ ] Tests pasando (`make test`)
- [ ] Build sin errores (`npm run build`)
- [ ] Variables de entorno configuradas
- [ ] Database migrations ejecutadas (`alembic upgrade head`)
- [ ] HTTPS habilitado en producción
- [ ] Logs centralizados (recomendado: Datadog o similar)
- [ ] Backup de base de datos automático

---

## 📞 Support

**Para preguntas técnicas:**
- Swagger docs: `http://localhost:8000/docs`
- GitHub issues: (link al repo)
- Slack: #dev-grantflow

---

**Última actualización:** 12 mayo 2026  
**Siguiente revisión:** Después de S6 (Metabase)
