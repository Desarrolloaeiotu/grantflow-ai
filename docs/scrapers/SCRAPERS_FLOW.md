# 🔄 FLUJO COMPLETO DE SCRAPERS - GrantFlow AI

## 📊 ARQUITECTURA GENERAL

```
┌─────────────────────────────────────────────────────────────┐
│                    RUNNER (Orquestador)                     │
│              (app/scrapers/runner.py)                       │
└────────────┬────────────────────────────────┬───────────────┘
             │                                │
    ┌────────▼────────────┐         ┌────────▼──────────┐
    │ NACIONAL COLOMBIA   │         │ SECUNDARIOS       │
    │ (Prioritario 5am)   │         │ (Paralelo MAX=4)  │
    │                     │         │                   │
    │ - ICBF              │         │ - Grants.gov      │
    │ - MinEducación      │         │ - BID Lab         │
    │ - SECOP             │         │ - ONU Mujeres     │
    │ - Cajas             │         │ - DevelopmentAid  │
    │                     │         │ - RSS Feeds       │
    └────────┬────────────┘         └────────┬──────────┘
             │                                │
             └────────────┬───────────────────┘
                          │
          ┌───────────────▼───────────────┐
          │     CADA SCRAPER EJECUTA:     │
          │  1. fetch_raw() (HTTP/HTML)   │
          │  2. normalize() (Validación)  │
          │  3. filter() (Keywords)       │
          │  4. return OpportunityCreate  │
          └───────────────┬───────────────┘
                          │
          ┌───────────────▼───────────────┐
          │   PERSISTENCIA A BD (async)   │
          │  1. Check duplicados (URL)    │
          │  2. Resolver funder_id        │
          │  3. Crear Opportunity         │
          │  4. Flush a DB                │
          └───────────────┬───────────────┘
                          │
         ┌────────────────▼────────────────┐
         │  SCORING (Opcional/Async)      │
         │  1. LLM Criterios 1-2          │
         │  2. Regla Criterio 3 (Ticket)  │
         │  3. Regla Criterio 4 (Viability)
         │  4. Regla Criterio 5 (Relational)
         │  5. Score Total + Decision     │
         │  6. Persist ScoreLog           │
         └───────────────┬───────────────┘
                          │
         ┌────────────────▼────────────────┐
         │   MÉTRICAS Y MONITOREO         │
         │  1. Guardar run stats          │
         │  2. Detectar caída en tasa     │
         │  3. Alert a Slack si anomalía  │
         └────────────────────────────────┘
```

---

## 🔍 PASO A PASO DETALLADO

### **PASO 1: Orquestación (runner.py)**

```python
# Entrada: python -m app.scrapers.runner [--source nombre] [--score]

# 1. Nacional Colombia PRIMERO (prioridad máxima)
nacional_count = await run_scraper("nacional_colombia", do_score=False)

# 2. Secundarios en PARALELO (máx 4 concurrentes)
secondary_scrapers = ["grantsgov", "bid", "unwomen", "developmentaid", "rss"]
asyncio.gather(*[run_with_semaphore(name) for name in secondary_scrapers])

# 3. Consolidar resultados
total_persisted = nacional_count + secondary_count
```

**Objetivo:** Gestionar concurrencia, priorizar Nacional, evitar bloqueos.

---

### **PASO 2: Fetch Raw (Cada Scraper)**

**Base class:** `BaseScraper.fetch_raw()` (abstracto)

Cada scraper implementa su propia fuente:

#### **Nacional Colombia** (`nacional_colombia.py`)
```python
async def fetch_raw(self) -> list[dict]:
    # 1. Buscar en ICBF (RSS/HTML scraping)
    # 2. Buscar en MinEducación (RSS)
    # 3. Buscar en SECOP (JSON API)
    # 4. Buscar en Cajas de Compensación (web scraping)
    # 5. Buscar en Fundaciones locales (búsqueda genérica)
    return list[dict]  # items crudos
```
**Retorna:** Lista de 100-500 items crudos por fuente

#### **Grants.gov** (`grantsgov.py`)
```python
async def fetch_raw(self) -> list[dict]:
    # POST a https://api.grants.gov/v1/api/search2
    # SEARCH_TERMS: [
    #   "early childhood development scalable",
    #   "teacher training early childhood",
    #   "women early childhood development",
    #   ...
    # ]
    # Paginar resultados (max 100 por término)
    return list[dict]  # oppHits de Grants.gov
```
**Retorna:** 20-50 items por búsqueda

#### **BID Lab** (`bid.py`)
```python
async def fetch_raw(self) -> list[dict]:
    # HTML scraping de https://bidlab.org/es/convocatorias
    # Parsear con BeautifulSoup
    # Extraer: titulo, link, descripción, deadline
    return list[dict]
```
**Retorna:** 10-30 items

#### **ONU Mujeres, DevelopmentAid, RSS** (similar)

---

### **PASO 3: Normalize (Validación y Filtrado)**

**Base class:** `BaseScraper.normalize(raw)` (abstracto)

Cada scraper convierte item crudo → `OpportunityCreate`

```python
def normalize(self, raw: dict) -> OpportunityCreate | None:
    # 1. VALIDAR datos básicos (title, url)
    if not raw.get("title"):
        return None  # Descartar
    
    # 2. FILTRO DE KEYWORDS (AND logic)
    text = (raw["title"] + " " + raw["description"]).lower()
    
    # ✅ Debe tener AL MENOS 1 CORE_KEYWORD
    has_core = any(kw in text for kw in CORE_KEYWORDS)
    if not has_core:
        return None
    
    # ✅ Debe tener AL MENOS 1 GEO_KEYWORD (si aplica por región)
    has_geo = any(kw in text for kw in GEO_KEYWORDS)
    if region == "nacional" and not has_geo:
        return None
    
    # 3. PARSEAR montos, deadlines, URLs
    deadline = _parse_date(raw.get("closeDate"))
    amount_max_cop = _convert_to_cop(raw.get("amount"))
    
    # 4. RETORNAR OpportunityCreate (schema validado)
    return OpportunityCreate(
        title=raw["title"],
        description=raw["description"][:5000],
        funder_name="BID",
        amount_min_cop=None,
        amount_max_cop=amount_max_cop,
        deadline=deadline,
        url_rfp="https://...",
        url_source="https://...",
        source_name="bid",
        org_website="https://www.iadb.org",
        eligible_countries=["Colombia"],
        sectors=["education"],
        capital_type="grant",
        market_window="funding_global",
        raw_content=json.dumps(raw),  # Guardar original
    )
```

**Retorna:** 
- ✅ `OpportunityCreate` si pasa filtros
- ❌ `None` si debe descartarse

**Filtros aplicados:**
1. Validación de datos requeridos
2. Keywords CORE (AND logic)
3. Keywords GEO (si aplica)
4. Parsing seguro de montos/fechas

---

### **PASO 4: Persistencia en BD**

**Ubicación:** `runner.py::run_scraper()`

```python
async with AsyncSessionLocal() as db:
    for opp_create in opportunities:  # Todos post-normalize
        
        # 4a. DEDUPLICACIÓN por URL
        existing = await db.execute(
            select(Opportunity).where(
                Opportunity.url_source == opp_create.url_source
            )
        ).scalar_one_or_none()
        
        if existing:
            skipped += 1
            continue  # ← No persistir
        
        # 4b. RESOLVER funder_id
        funder = await db.execute(
            select(Funder).where(
                Funder.name.ilike(f"%{opp_create.funder_name}%")
            )
        ).scalar_one_or_none()
        
        if not funder:
            # Crear nuevo funder si no existe
            funder = Funder(name=opp_create.funder_name)
            db.add(funder)
            await db.flush()
        
        funder_id = funder.id
        
        # 4c. CREAR oportunidad
        opp = Opportunity(
            title=opp_create.title,
            description=opp_create.description,
            funder_id=funder_id,  # ← Foreign key resuelta
            amount_min_cop=opp_create.amount_min_cop,
            amount_max_cop=opp_create.amount_max_cop,
            deadline=opp_create.deadline,
            url_rfp=opp_create.url_rfp,
            url_source=opp_create.url_source,
            source_name=opp_create.source_name,
            market_window=opp_create.market_window,
            status="detected",  # Estado inicial
            raw_content=opp_create.raw_content,
        )
        
        db.add(opp)
        await db.flush()  # ← Obtener ID antes de scoring
        
        persisted += 1
        
        # 4d. GUARDAR a BD
        await db.commit()
```

**Métricas:**
- `persisted`: Oportunidades nuevas guardadas
- `skipped`: Duplicados descartados
- `total_normalized`: Pasaron filtros normalize()

---

### **PASO 5: Scoring (Opcional)**

**Ubicación:** `app/services/scoring_engine.py`

Se ejecuta SOLO si `--score` se pasa al runner.

```python
# Entrada: Opportunity (ya en BD con ID)
# Salida: ScoreResult + persist en ScoreLog

async def score_and_persist(opportunity_id, db):
    opp = await db.get(Opportunity, opportunity_id)
    funder = await db.get(Funder, opp.funder_id)
    
    # Cálculo de 5 criterios
    result = await self.score(opp, funder)
    
    # ① Criterios LLM (1 llamada combina C1 + C2 + ventana de mercado)
    c1, c2 = await self._score_llm(opp, funder)
    # Prompt: evalúa alineación estratégica + ajuste del modelo
    # Provider: Anthropic (Claude Sonnet 4.5) o Google Gemini (fallback)
    # Timeout: 30 seg
    
    # ② Criterio 3 — Coherencia del Ticket (REGLA DETERMINISTA)
    c3 = self._score_ticket(opp.amount_min_cop, opp.amount_max_cop)
    # 2 = COP $400M–$5.000M (ideal)
    # 1 = ±30% adyacente
    # 0 = fuera de rango
    
    # ③ Criterio 4 — Viabilidad Operativa (REGLA DETERMINISTA)
    c4 = self._score_viability(opp.deadline)
    # 2 = >30 días al cierre
    # 1 = 15–30 días
    # 0 = <15 días (muy urgente)
    
    # ④ Criterio 5 — Potencial Relacional (REGLA DETERMINISTA)
    c5 = self._score_relational(funder)
    # 2 = Financiador histórico de aeioTU
    # 1 = En lista estratégica (LEGO, Ford, Gates, etc)
    # 0 = Nuevo/desconocido
    
    # ⑤ SCORE TOTAL
    total = c1 + c2 + c3 + c4 + c5  # 0–10
    
    # ⑥ DECISION
    decision = (
        "go" if total >= 6 else
        "no_go" if total <= 3 else
        "pending"
    )
    
    # ⑦ URGENCY
    urgency = self._classify_urgency(opp.deadline)
    # "high": <30 días
    # "medium": 30–60 días
    # "low": >60 días
    
    # ⑧ PERSISTENCIA
    opp.score_total = total
    opp.score_details = {
        "c1": c1, "c2": c2, "c3": c3, "c4": c4, "c5": c5,
        "llm_justification": "C1: [...] | C2: [...]",
        "confidence": "high|medium|low",
    }
    opp.decision = decision
    opp.urgency = urgency
    
    # Guardar log de scoring
    log_entry = ScoreLog(
        opportunity_id=opp.id,
        criterion_1=c1, criterion_2=c2, criterion_3=c3,
        criterion_4=c4, criterion_5=c5,
        llm_reasoning=reasoning,
        scored_at=datetime.now(),
        scored_by="auto",
    )
    db.add(log_entry)
    await db.commit()
```

**Regla de Oro:**
```
✅ GO        → score ≥ 6 (enviar a pipeline activo)
⏳ PENDING   → score 4–5 (revisar manualmente)
❌ NO_GO     → score ≤ 3 (descartar)
```

**Manejo de Errores:**
- Si LLM devuelve 429 (quota exceeded) → abort scoring pero continuar persistiendo
- Si LLM falla (conexión) → score 0 pero no fallar todo el batch

---

### **PASO 6: Monitoreo y Alertas**

**Ubicación:** `app/scrapers/metrics_monitor.py`

```python
# Después de cada scraper run:

# 6a. GUARDAR MÉTRICAS
await save_scraper_metrics({
    "scraper_name": "grantsgov",
    "total_normalized": 42,      # Post-normalize
    "total_persisted": 38,       # Post-dedup
    "total_skipped": 4,          # Duplicados
    "errors_count": 0,
    "duration_sec": 3.2,
    "run_date": date.today(),
})

# 6b. DETECTAR CAÍDA ANORMAL
if await detect_drop("grantsgov", 38):  # ← vs promedio semanal
    avg = await get_weekly_average("grantsgov")
    await alert_metrics_drop_to_slack(
        scraper="grantsgov",
        current=38,
        avg=120,
        message="⚠️ Grants.gov: 38 items (normal 120) — revisar filtros"
    )
```

**Alertas a Slack:**
- Drop > 50% vs promedio semanal
- Scraper timeout/error
- Quota LLM exceeded

---

## 📋 TABLA RESUMEN: FUENTES Y SCHEDULES

| Scraper | URL | Schedule | Keywords | Retorna | Status |
|---------|-----|----------|----------|---------|--------|
| **nacional_colombia** | ICBF, MinEd, SECOP, Cajas | 5:00 AM | 40+ CORE | 100-500 | ✅ Activo |
| **grantsgov** | api.grants.gov/v1 | 6:00 AM | 15 CORE | 20-50 | ✅ Activo |
| **bid** | bidlab.org/es | 7:00 AM | 15 CORE | 10-30 | ✅ Activo |
| **unwomen** | unwomen.org | 8:00 AM | 15 CORE | 5-15 | ✅ Activo |
| **developmentaid** | developmentaid.org | 9:00 AM | 15 CORE | 10-20 | ✅ Activo |
| **rss_feeds** | 19 RSS feeds | 10:00 AM | 15 CORE | 20-50 | ✅ Activo |

---

## 🎯 FLUJO DECISIONAL: NORMALIZE()

```
┌─ RAW ITEM ─────────────────────────────────────────┐
│ {title, description, url, amount, deadline, ...}   │
└────────────────┬─────────────────────────────────┘
                 │
        ┌────────▼────────┐
        │ Validar básicos │
        │ (title, url)    │
        └────────┬────────┘
                 │
            ❌ Falta?  ➜ return None (descartar)
            ✅ Tiene?  ➜ continuar
                 │
        ┌────────▼──────────────────────┐
        │ Filtro KEYWORDS (AND logic)   │
        │ 1. Has CORE_KEYWORD?          │
        │ 2. Has GEO_KEYWORD? (si aplica)
        └────────┬──────────────────────┘
                 │
       ❌ NO CORE?  ➜ return None
       ✅ Tiene core + (geo si aplica) ➜ continuar
                 │
        ┌────────▼─────────────────┐
        │ Parsear & Normalizar     │
        │ - Parsedate(deadline)    │
        │ - Convert amount → COP   │
        │ - Limpiar URLs           │
        └────────┬─────────────────┘
                 │
        ┌────────▼───────────────────┐
        │ return OpportunityCreate   │
        │ (schema validado)          │
        └────────────────────────────┘
```

---

## 🔄 CICLO COMPLETO DIARIO

```
05:00 AM ► nacional_colombia    [0–3 min]  → 100–500 items → 38 persistidos
06:00 AM ┬─ grantsgov          [0–2 min]  → 20–50 items → 15 persistidos
         │
07:00 AM ├─ bid                [0–1 min]  → 10–30 items → 8 persistidos
         │
08:00 AM ├─ unwomen            [0–1 min]  → 5–15 items → 4 persistidos
         │
09:00 AM ├─ developmentaid     [0–1 min]  → 10–20 items → 7 persistidos
         │
10:00 AM └─ rss_feeds          [0–2 min]  → 20–50 items → 12 persistidos
                                             ─────────────────────────
                 TOTAL DIARIO                ~165–635 items → 84 persistidos

11:00 AM ► Scoring (opcional, consume cuota LLM)
         └─ Claude Sonnet 4.5: 50–60 items (150 tokens promedio)
            1–2 min de latencia

12:00 PM ► Alertas Slack
         └─ Resume daily run, detecta anomalías
```

---

## 📊 ESTADÍSTICAS TÍPICAS

```
Métricas por ciclo completo (todos scrapers):

Entrada:
  - 50–100 búsquedas distintas
  - ~800–1.500 items crudos

Post-normalize:
  - ~300–600 items (40–50% pasan filtros)

Post-dedup:
  - ~80–150 items nuevos (13–30% duplicados)

Post-scoring (si activado):
  - ~40–60 items scored (~27–80% quota LLM consumida)

Decisiones:
  - ~15–25 "go" (18–30%)
  - ~5–15 "pending" (6–20%)
  - ~20–30 "no_go" (25–40%)

Pipeline activo (>= GO):
  - COP $8B–$15B

Tiempo total:
  - Sin scoring: 5–10 min
  - Con scoring: 10–15 min
```

---

## ⚠️ CASOS ESPECIALES

### **Duplicados**
Detectados por `url_source`. Si existe ➜ skip (no reingesta).

### **Funder desconocido**
Auto-crear en tabla Funders con `name` y `org_type = null`.

### **Montos/Deadlines null**
Permitido. Scoring asigna puntos neutros (c3=1, c4=2 sin deadline).

### **Quota LLM excedida**
- Logging: `"429 quota exceeded"`
- Acción: detener scoring, continuar persistiendo el resto
- Alerta: Slack `⚠️ Quota LLM agotada para hoy`

---

## 🚀 COMANDOS ÚTILES

```bash
# Ejecutar TODO
python -m app.scrapers.runner

# Ejecutar solo una fuente
python -m app.scrapers.runner --source grantsgov

# Ejecutar con scoring inmediato (consume LLM quota)
python -m app.scrapers.runner --score

# Re-scorear oportunidades detectadas ayer
python -m app.scrapers.rescore

# Ver últimas métricas
python -m app.scrapers.metrics_monitor

# Limpiar oportunidades duplicadas (desarrollo)
python -m app.scrapers.clean_db
```

---

## 📈 PRÓXIMAS MEJORAS (S7+)

- [ ] Enriquecimiento automático de CEOs/contactos post-ingesta
- [ ] Predicción probabilística (no solo binaria go/no_go)
- [ ] Scrapers incrementales (detectar cambios en oportunidades existentes)
- [ ] WebSocket live updates cuando nueva oportunidad "go" detectada
- [ ] Dashboard de métricas de scraper (tasa de éxito, latencia, cuota LLM)

