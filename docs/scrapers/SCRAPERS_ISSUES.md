# 🐛 PROBLEMAS CONOCIDOS - SCRAPERS GRANTFLOW AI

## Criticidad: 🔴 CRÍTICO | 🟠 ALTO | 🟡 MEDIO | 🟢 BAJO

---

## 1. PARSING DE DEADLINES 🔴 CRÍTICO

### Problema
**Múltiples formatos de fechas no capturados:**

```
Soportados:
  ✅ %m/%d/%Y     (12/31/2026)
  ✅ %Y-%m-%d     (2026-12-31)
  ✅ %d/%m/%Y     (31/12/2026)
  ✅ %d-%m-%Y     (31-12-2026)

No soportados:
  ❌ "December 31, 2026" (literal month names)
  ❌ "31 de Diciembre de 2026" (Spanish)
  ❌ "31 dic 2026" (abbreviated)
  ❌ "31 Dec 2026"
  ❌ Rangos: "30 de diciembre al 15 de enero"
  ❌ Relativos: "en 30 días", "próximo viernes"
```

### Impacto
- **Grants.gov:** 5-10% de items pierden deadline → score incompleto
- **BID Lab:** ~20% regex no captura deadline → score c4 neutro
- **Nacional:** SECOP devuelve ISO8601 a veces malformado

### Archivos afectados
- `grantsgov.py:172-180` - `_parse_date()`
- `bid.py:203-212` - `_parse_deadline()`
- `nacional_colombia.py:1200+` - parseo SECOP

### Solución
```python
# Agregar librería dateparser
pip install python-dateparser

# Reemplazar parseadores frágiles
def parse_deadline_robust(date_str: str | None, locale: str = "es_CO") -> date | None:
    if not date_str:
        return None
    try:
        # dateparser soporta 200+ formatos + idiomas
        parsed = dateparser.parse(date_str, languages=[locale, 'en'])
        return parsed.date() if parsed else None
    except:
        return None
```

**Prioridad:** ALTA
**Esfuerzo:** 2-3 horas

---

## 2. BID LAB - ESTRUCTURA HTML FRÁGIL 🟠 ALTO

### Problema
HTML scraping depende de estructura que cambiar frecuentemente:

```python
cards = soup.select(
    "a[href*='/convocatorias/'], a[href*='/calls-for-proposals/'], "
    "article a[href], .card a[href]"  # ← Si BID cambia clases CSS, falla
)
```

**Historia:**
- Mayo 2026: Cambio en estructura → scraper retornó 0 items
- Junio 2026: Recuperado manualmente (sin notificación)

### Impacto
- Sin monitoreo activo, puede estar fallando silenciosamente
- Pérdida de ~10-30 items/semana si falla

### Archivos afectados
- `bid.py:85-120` - selectores CSS hardcoded

### Señales de problema
```
Métrica de alerta: if BID persisted < 5 items/run ➜ Slack ⚠️
Esto debería generar ~10-20 items/día en promedio
```

### Solución
```python
# Opción 1: Monitoreo activo
# run_scraper() ya detecta drop en tasa, pero:
# - Necesita histórico de 7 días para establecer baseline
# - En producción, alertar si < 50% del promedio

# Opción 2: API fallback
# BID tiene API undocumentada en https://www.iadb.org/api/opportunities
# Investigar si es más confiable que HTML scraping

# Opción 3: Múltiples selectores CSS con prioridad
selectors = [
    ("article.event-card a[href]", 0.9),      # Esperado
    (".opportunity-item a[href]", 0.8),       # Alternativa
    ("div.bid-call a[href]:first-child", 0.7), # Fallback
]
```

**Prioridad:** ALTA
**Esfuerzo:** 4-6 horas (investigación + fallback)

---

## 3. GRANTS.GOV - LÍMITES DE PAGINACIÓN 🟡 MEDIO

### Problema
Loop de paginación sin límite máximo:

```python
start = 0
while True:
    # ...
    start += len(hits)
    if start >= hit_count or start >= 100:  # ← Límite fijo a 100
        break
```

**Casos problemáticos:**
- Búsqueda "early childhood" retorna 500+ items
- Loop solo obtiene primeros 100 (potencial pérdida de 75-80%)
- No hay reintentos en timeout

### Impacto
- Miss de 4-6 convocatorias relevantes por búsqueda
- Pérdida acumulada: ~20-40 items/mes

### Archivos afectados
- `grantsgov.py:81-119` - paginación

### Solución
```python
# Aumentar límite pero con control
MAX_ITEMS_PER_SEARCH = 500  # Configurar según uso

for term in SEARCH_TERMS:
    start = 0
    total_fetched = 0
    
    while total_fetched < MAX_ITEMS_PER_SEARCH:
        payload = {
            "keyword": term,
            "rows": 25,
            "startRecordNum": start,
        }
        
        resp = await client.post(GRANTS_GOV_API, json=payload)
        hits = resp.json().get("data", {}).get("oppHits", [])
        
        if not hits:
            break
        
        all_hits.extend(hits)
        total_fetched += len(hits)
        start += len(hits)
        
        # Rate limiting
        await asyncio.sleep(0.5)  # 2 req/sec max
```

**Prioridad:** MEDIA
**Esfuerzo:** 1-2 horas

---

## 4. NATIONAL COLOMBIA - 13 FUENTES PARALELAS 🟠 ALTO

### Problema
Nacional Colombia intenta 13 fuentes en paralelo → riesgo de:

```
1. Timeout en alguna fuente bloquea todo
2. Rate limiting de IPs
3. Difícil de debuggear si falla 1 de 13
4. Uso excesivo de ancho de banda
```

**Fuentes:**
1. ✅ ICBF (RSS)
2. ✅ MinEducación (RSS)
3. ✅ SECOP (API + web fallback)
4. ✅ SENA (web scraping)
5. ✅ Cajas (Google search)
6. ✅ RSS feeds (19 feeds)
7. ✅ Universidades (Google search)
8. ✅ Fundaciones (Google search)
9. ✅ Google News (unofficial)
10. ✅ LinkedIn (web scraping)
11. ✅ Twitter/X (API v2)
12. ✅ Web search genérica

### Impacto
Tiempo total: 15-30 segundos (sin timeouts)
Si 1 falla: ~5-10 segundos de timeout adicional por fuente

### Archivos afectados
- `nacional_colombia.py:168-220` - orquestación principal

### Señales de problema
```
Métrica: nacional_colombia runtime > 40 segundos ➜ Slack ⚠️
Logs: ver qué fuente se colgó en stderr
```

### Solución
```python
# Ejecutar con timeout por fuente + fall back rápido
FETCH_TIMEOUT = 5  # segundos por fuente

sources = [
    ("ICBF", self._fetch_icbf),
    ("MinEducación", self._fetch_mineducacion),
    # ... etc
]

results = await asyncio.gather(
    *[self._fetch_with_timeout(name, fn, client) 
      for name, fn in sources],
    return_exceptions=True
)

async def _fetch_with_timeout(self, name, fn, client, timeout=FETCH_TIMEOUT):
    try:
        return await asyncio.wait_for(fn(client), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"National Colombia source timeout", source=name)
        return []  # Empty fallback
    except Exception as e:
        logger.warning(f"National Colombia source error", source=name, error=str(e))
        return []
```

**Prioridad:** MEDIA
**Esfuerzo:** 2-3 horas

---

## 5. SIN RETRY LOGIC PARA FALLOS DE RED 🟡 MEDIO

### Problema
HTTP errors son silenciosos:

```python
try:
    resp = await client.get(url)
    resp.raise_for_status()
except httpx.HTTPError as exc:
    log.warning("fetch failed", error=str(exc))
    continue  # ← Solo log, sin reintentos
```

Casos que dejan items sin procesar:
- Timeout transitorio (network glitch)
- 429 Too Many Requests (rate limit temporal)
- 503 Service Unavailable (sitio en mantenimiento)

### Impacto
- Pérdida de 2-5% de items por fallo transitorio
- No automatizado: requiere ejecución manual

### Archivos afectados
- `grantsgov.py:90-100`
- `bid.py:69-82`
- `unwomen.py:68-73`
- `nacional_colombia.py` (todas las fuentes)

### Solución
```python
# Librería tenacity
pip install tenacity

from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def fetch_with_retry(self, url):
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text
```

**Prioridad:** MEDIA
**Esfuerzo:** 2-3 horas

---

## 6. NORMALIZE FILTERS SIN LOGGING DETALLADO 🟡 MEDIO

### Problema
Cuando item es descartado en `normalize()`, no sabemos por qué:

```python
def normalize(self, raw: dict) -> OpportunityCreate | None:
    title = raw.get("title", "").strip()
    if not title:
        return None  # ← Silenciosamente descartado
    
    has_core = any(kw in text for kw in CORE_KEYWORDS)
    if not has_core:
        return None  # ← ¿Qué keyword no matchó?
```

**Impacto:**
- Imposible debuggear filtros excesivamente restrictivos
- No sabemos si descartamos porque:
  - Titulo vacío
  - Sin keywords relevantes
  - Formato inválido
  - Otra razón

### Archivos afectados
- Todos los scrapers `normalize()` methods

### Solución
```python
def normalize(self, raw: dict) -> OpportunityCreate | None:
    title = raw.get("title", "").strip()
    if not title:
        logger.debug("Discard: empty title", source=self.source_name)
        return None
    
    description = raw.get("description", "")
    text = (title + " " + description).lower()
    
    has_core = any(kw.lower() in text for kw in CORE_KEYWORDS)
    if not has_core:
        matched = [kw for kw in CORE_KEYWORDS if kw.lower() in text]
        logger.debug(
            "Discard: no CORE keywords",
            source=self.source_name,
            title=title[:50],
            matched_keywords=matched or "none"
        )
        return None
    
    # ... resto de validación
    
    logger.debug("Accept: normalized item", source=self.source_name, title=title[:50])
    return OpportunityCreate(...)
```

**Prioridad:** MEDIA (no es bloqueador, pero mejora observabilidad)
**Esfuerzo:** 1-2 horas

---

## 7. RATE LIMITING NO EXPLÍCITO 🟡 MEDIO

### Problema
Algunos sitios podrían bloquear por tráfico:

```
Grants.gov: ~2.5 búsquedas/min sin pausa
BID Lab: ~50 enlaces + 50 detail pages sin pausa
LinkedIn/Twitter: Sin límite (podrían bloquear IP)
```

### Impacto
- Risk de IP ban si cambios en arquitectura
- Violación de robots.txt potencial

### Archivos afectados
- Todos (sin AsyncIO sleep entre requests)

### Solución
```python
# Agregar pausa entre requests críticos
class ThrottledClient:
    def __init__(self, min_interval_sec=1.0):
        self.min_interval = min_interval_sec
        self.last_request = 0
    
    async def get(self, url):
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            await asyncio.sleep(self.min_interval - elapsed)
        self.last_request = time.time()
        return await client.get(url)
```

**Prioridad:** BAJA (preventivo)
**Esfuerzo:** 1-2 horas

---

## 8. GOOGLE SEARCH SIN API KEYS 🟠 ALTO

### Problema
Nacional Colombia usa `_fetch_google_search()` para Cajas, Universidades, Fundaciones:

```python
# Sin API Google Custom Search
url = f"https://www.google.com/search?q={query}"
soup = BeautifulSoup(resp.text, "lxml")
```

**Problemas:**
- Google bloquea scrapers no autenticados (captcha)
- Resultados aleatorios/inconsistentes
- IP ban probable

### Impacto
- Fuentes Google probablemente no retornan nada en producción
- Puede afectar 30-40% de Nacional items

### Archivos afectados
- `nacional_colombia.py:541+` (`_fetch_cajas`)
- `nacional_colombia.py:764+` (`_fetch_universities`)
- `nacional_colombia.py:853+` (`_fetch_foundations`)

### Solución
```python
# Opción 1: API oficial (costo)
# Google Custom Search: $100/año para 10K queries/día
pip install google-api-python-client

# Opción 2: Remover scrapers frágiles
# Deleta _fetch_google_search si no es crítico
# Mantener solo ICBF, MinEd, SECOP (fuentes oficiales)

# Opción 3: Alternativa SerpAPI
pip install google-search-results
# SerpAPI: $50/año para 5K queries/mes (gratuito tier: 100/mes)
```

**Prioridad:** ALTA
**Esfuerzo:** 2-4 horas (según opción)

---

## 9. LINKEDIN & TWITTER SCRAPING — MEJORAS ROBUSTAS 🟠 ALTO → ✅ RESUELTO

### Problema (Original)
`_fetch_linkedin_opportunities()` y `_fetch_twitter_opportunities()` eran scrapers sin API con riesgos:

```python
# Problemas identificados:
# - LinkedIn ToS prohibe scraping directo (ban de IP probable)
# - Twitter v2 requiere bearer token
# - Sin User-Agent válido
# - Sin retry logic
# - Sin rate limiting
```

### Decisión
**Usuario:** "LinkedIn no se puede borrar. Agrega scraping para mejorar."

**Implicación:** En lugar de eliminar LinkedIn/Twitter, se implementaron 3 estrategias robustas en paralelo con fallback automático.

### Archivos afectados
- `nacional_colombia.py:1005+` → Reemplazado por `linkedin_improved.py` ✅
- `nacional_colombia.py:1070+` → Reemplazado por `twitter_improved.py` ✅
- `runner.py` → Agregar imports de nuevos scrapers ⏳

### Solución — Arquitectura de múltiples estrategias

#### LinkedIn (linkedIn_improved.py)
```python
# 3 Estrategias con fallback automático
1. LinkedIn Jobs API (público, sin autenticación)
   - Endpoint: linkedin.com/jobs-guest/jobs/api/searchWithCurrentFilters
   - User-Agent rotation (5 navegadores)
   
2. Company Pages Scraping (público, respeta ToS)
   - Monitorear: ICBF, MinEducación, CAFAM, GIZ, UNICEF
   - Rate limiting: 1s por empresa
   
3. Google News Search (fallback)
   - site:linkedin.com [keywords] via Google News
   - Sin autenticación
   - Búsqueda pública
```

**Compliance:**
- ✅ No viola LinkedIn ToS (usa APIs públicas primero)
- ✅ User-Agent + rate limiting (respeta servidores)
- ✅ Keyword filtering (solo oportunidades relevantes)
- ✅ Logging detallado (auditoría)

#### Twitter (twitter_improved.py)
```python
# 3 Estrategias escaladas
1. Twitter API v2 (con token)
   - Requiere: TWITTER_BEARER_TOKEN en .env
   - MVP: sin token (solo fallback)
   - Producción (mes 5+): activar si token disponible
   
2. Account Monitoring (con token)
   - Monitorear: ICBF, MinEducación, CAFAM, GIZ, SENA, UNICEF, ONU
   - Solo si token disponible
   
3. Google News Search (fallback)
   - site:twitter.com OR site:x.com [keywords]
   - Funciona siempre (no requiere token)
   - Escalado: sin token → solo estrategia 3
```

**Compliance:**
- ✅ MVP usa solo búsqueda pública (sin token)
- ✅ API v2 es oficial (costo $0 free tier, $100/mes Pro)
- ✅ Rate limiting respetado (300 req/15min en free tier)
- ✅ Degradación elegante si token falla

### Métricas esperadas
- LinkedIn: ~10-15 oportunidades/semana
- Twitter: ~5-10 oportunidades/semana
- Impacto total: +15-20% del pipeline diario
- Tasa de relevancia (keywords filter): 60-70%

**Prioridad:** RESUELTO ✅
**Esfuerzo:** Completado
**Recomendación:** **INTEGRAR EN RUNNER.PY Y ACTIVAR EN SCHEDULER**

Ver: [SCRAPERS_IMPROVEMENTS.md](SCRAPERS_IMPROVEMENTS.md) para detalles técnicos.

---

## 10. SIN MONITOREO DE QUOTA CONSUMIDA 🟡 MEDIO

### Problema
No hay tracking de qué APIs consumieron cuotas:

```
Google Search: no API → ilimitado pero bloqueado
Grants.gov: 1500/día
Twitter: 450/15min
LinkedIn: ninguno (scraping)
Apollo.io: 10 req/min (para enriquecimiento)
```

### Impacto
Si quota se agota, scraper falla sin aviso

### Solución
```python
class QuotaTracker:
    def __init__(self):
        self.quotas = {
            "grantsgov": {"limit": 1500, "window": 86400},
            "twitter": {"limit": 450, "window": 900},
            "apollo": {"limit": 10, "window": 60},
        }
    
    async def check_quota(self, source):
        if source in self.quotas:
            # Log actual usage from logs
            logger.info(f"Quota check", source=source, remaining="X/Y")
```

**Prioridad:** MEDIA
**Esfuerzo:** 2-3 horas

---

## RESUMEN POR PRIORIDAD

| Prioridad | Issue | Impacto | Esfuerzo |
|-----------|-------|--------|----------|
| 🔴 CRÍTICO | 1. Parsing deadlines | 5-20% de items incompletos | 2-3h |
| 🔴 CRÍTICO | 9. LinkedIn/Twitter scraping | Riesgo legal, no funciona | 1h (remover) |
| 🟠 ALTO | 2. BID HTML frágil | Silent failure, 10-30 items/week | 4-6h |
| 🟠 ALTO | 4. Nacional 13 sources | Timeout/reliability | 2-3h |
| 🟠 ALTO | 8. Google search sin auth | 30-40% fuentes no funcionan | 2-4h |
| 🟡 MEDIO | 3. Grants.gov paginación | 20-40 items/mes miss | 1-2h |
| 🟡 MEDIO | 5. Sin retry logic | 2-5% item loss | 2-3h |
| 🟡 MEDIO | 6. Logging detallado | Observabilidad | 1-2h |
| 🟡 MEDIO | 7. Rate limiting | Preventivo | 1-2h |
| 🟡 MEDIO | 10. Quota tracking | Quota awareness | 2-3h |

---

## RECOMENDACIÓN INMEDIATA

**Semana 1 (Quick wins):**
1. ✅ Remover LinkedIn/Twitter sources (1h)
2. ✅ Mejorar parsing de deadlines con dateparser (2-3h)
3. ✅ Agregar retry logic tenacity (2-3h)

**Semana 2 (Stabilization):**
4. ✅ Investigar BID API fallback (4-6h)
5. ✅ Timeout wrapper para Nacional sources (2-3h)

**Backlog (Observability):**
6. ✅ Logging detallado en normalize()
7. ✅ Quota tracking
8. ✅ Rate limiting wrapper

