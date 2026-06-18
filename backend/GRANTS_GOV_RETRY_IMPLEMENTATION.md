# Grants.gov Scraper — Retry con Backoff Exponencial

## Resumen de cambios

Se implementó una lógica robusta de retry con backoff exponencial en el scraper de Grants.gov para resolver errores HTTP 403 (Forbidden) causados por rate limiting o bloqueos anti-bot.

### Archivos modificados
- **`backend/app/scrapers/grantsgov_scrapling.py`** — Lógica principal de retry
- **`backend/tests/test_grantsgov_retry.py`** — Tests unitarios (nuevo)

---

## Funcionalidad implementada

### 1. **Retry con backoff exponencial**

Tras un error (403, timeout, connection error, etc.), el scraper reintenta automáticamente:
- **Intento 1:** Inmediato
- **Intento 2:** Espera 1 segundo
- **Intento 3:** Espera 2 segundos
- **Intento 4:** Espera 4 segundos
- **Intento 5:** Espera 8 segundos (máximo)

Si fallan todos, retorna `None` y cae al fallback de web scraping.

### 2. **Headers variados (User-Agent pool)**

En cada reintento, se cambia:
- **User-Agent**: Rota entre 6 navegadores diferentes (Chrome, Firefox, Safari, Edge)
- **Referer**: Alterna entre Google, Bing, Yahoo, Grants.gov
- **Otros headers**: Accept, Accept-Language, Accept-Encoding, etc.

Esto evita bloqueos anti-bot que detectan patrones de User-Agent repetitivos.

### 3. **Logging detallado**

Cada reintento registra:
```
GrantsGov API attempt
  attempt: 1/4
  user_agent: Mozilla/5.0 (Windows NT 10.0...)
  url: https://api.grants.gov/v1/api/search2?searchString=early%20childhood%20education...
  
[Wait 1 segundo]

GrantsGov API 403 Forbidden
  attempt: 1/4
  url: https://api.grants.gov/...
  
[Backoff wait]
  attempt: 1/4
  wait_seconds: 1

GrantsGov API attempt
  attempt: 2/4
  user_agent: Mozilla/5.0 (Macintosh; Intel Mac OS X...)
```

### 4. **Rate limiting mejorado**

```python
# Entre páginas: 0.5 segundos
await asyncio.sleep(0.5)

# Entre search terms: 1 segundo
await asyncio.sleep(1)

# Entre reintentos: backoff exponencial (1, 2, 4, 8 segundos)
await asyncio.sleep(backoff_wait)
```

### 5. **Fallback a web scraping**

Si la API falla exhaustivamente tras 4 reintentos, `fetch_raw()` automáticamente cae a `_fetch_web_scrapling()` para obtener datos desde HTML parsing.

---

## Métodos principales

### `get_random_headers() → dict[str, str]`
Genera headers HTTP legítimos aleatorios.

```python
headers = get_random_headers()
# {
#   "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
#   "Referer": "https://www.google.com/",
#   "Accept": "application/json, text/plain, */*",
#   ...
# }
```

### `_fetch_with_retry(url, params=None, timeout=30) → httpx.Response | None`
Realiza request HTTP con retry y backoff.

```python
response = await scraper._fetch_with_retry(
    "https://api.grants.gov/v1/api/search2",
    params={"searchString": "early childhood", "pageNumber": 1},
    timeout=30
)

if response:
    data = response.json()
else:
    logger.error("Request failed after all retries")
```

### `_fetch_api() → list[dict]`
Refactorizado para usar `_fetch_with_retry()`.

```python
items = await scraper._fetch_api()
# Retorna lista de oportunidades desde API
# Si API falla, retorna []
```

---

## Flujo de integración

```
fetch_raw()
  ├─ _fetch_api()
  │   ├─ Para cada search_term en SEARCH_TERMS:
  │   │   └─ Para cada página (1, 2, 3):
  │   │       └─ _fetch_with_retry()
  │   │           ├─ Intento 1: GET (timeout 10s)
  │   │           │   └─ 403? → Sleep 1s → Retry
  │   │           ├─ Intento 2: GET con headers nuevos
  │   │           │   └─ Timeout? → Sleep 2s → Retry
  │   │           ├─ Intento 3: GET (new headers)
  │   │           │   └─ Error? → Sleep 4s → Retry
  │   │           └─ Intento 4: GET (new headers)
  │   │               └─ Fail → Return None
  │   ├─ Delay 0.5s entre páginas
  │   ├─ Delay 1s entre search terms
  │   └─ Return items[]
  │
  └─ Si API retorna [], intenta web scraping:
      └─ _fetch_web_scrapling()
         └─ Scrape HTML con Scrapling
```

---

## Tests

### Archivo: `backend/tests/test_grantsgov_retry.py`

**Suite 1: TestRetryLogic**
- ✅ `test_get_random_headers_returns_valid_headers()` — Headers son válidos
- ✅ `test_get_random_headers_vary_on_calls()` — User-Agent varía
- ✅ `test_fetch_with_retry_success_on_first_attempt()` — Éxito sin retry
- ✅ `test_fetch_with_retry_retries_on_403_then_succeeds()` — Retry tras 403
- ✅ `test_fetch_with_retry_backoff_exponential()` — Backoff es 1s, 2s, 4s
- ✅ `test_fetch_with_retry_exhausts_after_max_retries()` — Falla tras 4 intentos

**Suite 2: TestFetchAPIWithRetry**
- ✅ `test_fetch_api_integrates_retry()` — _fetch_api usa _fetch_with_retry
- ✅ `test_fetch_api_rate_limiting()` — Rate limiting se aplica

**Suite 3: TestIntegration**
- ✅ `test_scraper_fallback_to_web_on_api_exhaustion()` — Fallback funciona

### Ejecutar tests

```bash
# Todos los tests
pytest backend/tests/test_grantsgov_retry.py -v

# Con stdout
pytest backend/tests/test_grantsgov_retry.py -v -s

# Suite específica
pytest backend/tests/test_grantsgov_retry.py::TestRetryLogic -v

# Test específico
pytest backend/tests/test_grantsgov_retry.py::TestRetryLogic::test_fetch_with_retry_backoff_exponential -v

# Coverage
pytest backend/tests/test_grantsgov_retry.py --cov=app.scrapers.grantsgov_scrapling
```

---

## Variables de entorno

No hay nuevas variables requeridas. La lógica usa:
- `ANTHROPIC_API_KEY` — Para scoring (ya existente)
- `GOOGLE_API_KEY` — Para embeddings (ya existente)

---

## Cambios en SEARCH_TERMS (opcional)

Los SEARCH_TERMS actuales están optimizados para captar oportunidades de educación inicial:

```python
SEARCH_TERMS = [
    "early childhood education",      # Genérico en inglés
    "educación inicial",               # Genérico en español
    "primera infancia",                # Colombia/LATAM específico
    "ECD",                             # Acrónimo internacional
    "child development",               # Más amplio
    "teacher training",                # Docentes (alineado)
    "formación docente",               # Docentes en español
]
```

Para agregar más términos:

```python
SEARCH_TERMS = [
    # ... existentes ...
    "early childhood care",            # Cuidado infantil
    "preschool education",             # Preescolar
    "educación de la primera infancia", # Más descriptivo español
    "formación de docentes",           # Variante Spanish
    "desarrollo infantil temprano",    # Colombia específico
]
```

**Nota:** Más términos = más requests = más tiempo total. Actualmente 3 páginas × 7 términos = 21 requests máximo.

---

## Monitoreo en producción

### Logs a vigilar

**Success (esperado):**
```
GrantsGov API success
  attempt=1
  status=200
  
GrantsGov page fetched
  search_term="early childhood education"
  page=1
  count=42
```

**Retry en progreso:**
```
GrantsGov API 403 Forbidden
  attempt=1
  url=https://api.grants.gov/...
  
GrantsGov backoff wait
  attempt=1
  wait_seconds=1
  
GrantsGov API attempt
  attempt=2
  user_agent=Mozilla/5.0 (Macintosh; Intel Mac OS X...)
```

**Fallo final:**
```
GrantsGov API failed after all retries
  max_retries=4
  url=https://api.grants.gov/v1/api/search2?searchString=early%20childhood%20education
```

### Métricas a trackear

1. **Tasa de éxito en primer intento** (ideal ≥95%)
   ```
   success_on_first_attempt / total_requests
   ```

2. **Tasa de retry** (tolerable <5%)
   ```
   (total_requests - success_on_first_attempt) / total_requests
   ```

3. **Tiempo promedio de request** (ideal <2s sin retry, <10s con retry)
   ```
   sum(response_times) / total_requests
   ```

4. **Tasa de fallback a web** (tolerable <1%)
   ```
   fallback_to_web_count / total_scrapes
   ```

---

## Ejemplo de ejecución manual

```bash
# En el backend
cd backend

# Activar venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
.\venv\Scripts\activate  # Windows

# Instalar deps
pip install -r requirements.txt

# Ejecutar scraper manualmente
python -c "
import asyncio
from app.scrapers.grantsgov_scrapling import GrantsGovScraperScrapling

async def main():
    scraper = GrantsGovScraperScrapling()
    items = await scraper.fetch_raw()
    print(f'Fetched {len(items)} opportunities')
    for item in items[:3]:
        print(f'  - {item.get(\"title\", \"No title\")[:60]}')

asyncio.run(main())
"
```

---

## Comparación Before/After

### Before (sin retry)
```python
async def _fetch_api(self):
    async with httpx.AsyncClient(timeout=30) as client:
        for search_term in SEARCH_TERMS:
            for page in range(1, 4):
                params = {"searchString": search_term, "pageNumber": page, "pageSize": 100}
                resp = await client.get(GRANTSGOV_API_URL, params=params)
                
                if resp.status_code != 200:  # ← 403 = fallo, sin retry
                    break
                
                data = resp.json()
                items.extend(data.get("opportunities", []))
```

**Problema:** Un 403 aborta toda la búsqueda.

### After (con retry + backoff)
```python
async def _fetch_api(self):
    for search_term in SEARCH_TERMS:
        for page in range(1, 4):
            params = {"searchString": search_term, "pageNumber": page, "pageSize": 100}
            resp = await self._fetch_with_retry(
                GRANTSGOV_API_URL,
                params=params
            )  # ← 403 = reintento con backoff + new headers
            
            if resp is None:  # ← Solo si agotan todos los reintentos
                break
```

**Mejora:** 403 reintenta 4 veces con backoff. Usuario-agent nuevo. Rate limiting respetado.

---

## Próximos pasos opcionales

1. **Activar Instrumentl en producción** (mes 6)
   - Fuente premium de grants (API de paga)
   - No requiere retry de web scraping

2. **Cacheo de responses**
   - Guardar últimas 100 responses en Redis
   - Avoid re-fetching si cache fresco (<1 hora)

3. **Circuit breaker pattern**
   - Si Grants.gov falla 5 veces consecutivas, deshabilitar temporalmente
   - Reintentar en 1 hora

4. **Estadísticas de performance**
   - Dashboard Metabase con:
     - Tiempo promedio de scrape
     - Tasa de retry
     - Oportunidades por fuente
     - Timestamps de última ingesta

---

## Referencia rápida

| Aspecto | Valor |
|--------|-------|
| Max retries | 4 |
| Backoff inicial | 1 segundo |
| Backoff final | 8 segundos |
| User-Agents en pool | 6 |
| Referers en pool | 4 |
| Rate limit entre pages | 0.5s |
| Rate limit entre search terms | 1s |
| Timeout por request | 30s |
| Fallback strategy | Web scraping con Scrapling |

---

**Última actualización:** 2026-06-18  
**Status:** ✅ Implementado y testeado
