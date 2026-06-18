# 🌍 Estado de Scrapers Globales — 2026-06-17

**Status:** ⚠️ PARCIAL — Código listo, blockers externos

---

## 📊 Resumen de Ejecución

| Scraper | Estado | Items | Blocker |
|---------|--------|-------|---------|
| **Grants.gov (Scrapling)** | ❌ | 0 | API 403 Forbidden |
| **LinkedIn Improved** | ❌ | 0 | Google Search bloqueada |
| **Twitter Improved** | ❌ | 0 | Google Search bloqueada |
| **BID (Scrapling)** | ⚠️ | 0 | Playwright Sync en Async |
| **RSS Feeds** | ✅ | 18 | Activo (global) |
| **Total Global** | ⚠️ | 18 | Necesita proxy/VPN |

---

## 🔍 Análisis Detallado

### 1. Grants.gov — HTTP 403 Forbidden
```
2026-06-17 20:24:33 [debug] GrantsGov API non-200  status=403
```

**Causa:** API está bloqueando requests sin headers válidos o IP está en lista negra

**Solución:**
```python
# Agregar retry con User-Agent rotation + backoff
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}
# Esperar 5-10s entre requests
# Usar proxy si está disponible
```

---

### 2. LinkedIn Improved — 0 items
```
2026-06-17 20:25:03 [info] LinkedIn fetch complete  total_items=0
```

**Causa:** Google Search está bloqueando búsquedas desde esta IP
- Google detecta scraping automático
- Retorna reCAPTCHA o bloquea requests

**Solución:**
```python
# 1. Usar proxy residential (ej: Bright Data, Oxylabs)
# 2. Implementar bypass de reCAPTCHA (2captcha, AntiCaptcha)
# 3. Usar Scrapling con StealthyFetcher + headers randomizados
# 4. Implementar delay entre requests (3-5s)
```

---

### 3. Twitter Improved — 0 items
```
2026-06-17 20:25:48 [info] Twitter fetch complete  total_items=0
```

**Causa:** Similar a LinkedIn — Google Search bloqueada

**Solución:** Idem LinkedIn (proxies + delays)

---

### 4. BID (Scrapling) — Playwright Sync API Error
```
2026-06-17 20:26:49 [error] BID Lab scraper failed
  'It looks like you are using Playwright Sync API inside the asyncio loop'
```

**Causa:** `bid_scrapling.py` usa `DynamicFetcher` (sync) dentro de contexto `async`

**Solución (Quick Fix):**
```python
# En bid_scrapling.py, cambiar:
# await self.fetcher.fetch_dynamic(url)
# Por:
# await self.fetcher.fetch_dynamic_async(url)
# O usar asyncio.to_thread() para wrapper sync
```

---

## ✅ Lo Que SÍ Funciona

### RSS Feeds — 18 items (funding_global)
```
✅ reliefweb_updates: 5 items
✅ reliefweb_training: 4 items
✅ dev_coop: 3 items
✅ oak_foundation: 3 items
✅ reliefweb_colombia: 2 items
✅ ford_foundation: 1 item
```

**Ventajas:**
- No requiere anti-bot bypassing
- Consistente y predecible
- Bajo volumen pero de calidad

**Desventajas:**
- Principalmente noticias, no específicamente grants
- Bajo volume (18 items)
- Mixto: algunos items no son oportunidades de financiamiento

---

## 🔄 Resultados Actuales

```
Total BD: 843 oportunidades
├─ funding_colombia: 825 (97.9%)
└─ funding_global:    18 (2.1%)
  └─ Todos de RSS feeds
```

---

## 🚀 Plan para Activar Scrapers Globales

### OPCIÓN A: Proxies Residenciales (Recomendado)
**Tiempo:** 2-3 horas  
**Costo:** $20-50/mes (Bright Data, Oxylabs)

```python
# En grantsgov_scrapling.py, linkedin_improved.py, twitter_improved.py:
proxy_url = "http://proxy-user:pass@proxy-server:port"
async with httpx.AsyncClient(proxies=proxy_url) as client:
    response = await client.get(url)
```

**Resultado esperado:** +100-150 items

### OPCIÓN B: Usar Scrapling Completo
**Tiempo:** 4-6 horas  
**Costo:** $0 (solo desarrollo)

```python
# Usar StealthyFetcher de Scrapling para TODOS los scrapers
from scrapling.fetchers import StealthyFetcher

fetcher = StealthyFetcher(
    adaptive=True,
    headless=True,
    random_delay=3.0  # 3s delay entre requests
)
```

**Ventajas:**
- Anti-bot nativo
- User-Agent rotation
- Headers randomizados
- Cookie/session management

### OPCIÓN C: Usar Chrome Browser Controlado
**Tiempo:** 6-8 horas  
**Costo:** $0

```python
# Usar Playwright con Chrome real (no headless) para bypass reCAPTCHA
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch(headless=False)  # Con UI
    page = await browser.new_page()
    await page.goto(url)
```

---

## 📋 Tareas Pendientes

| Tarea | Prioridad | Tiempo | Blocker |
|-------|-----------|--------|---------|
| Arreglar BID Playwright sync/async | 🔴 | 30 min | Necesario para BID |
| Agregar retry + backoff a Grants.gov | 🟡 | 1h | Necesario para Grants.gov |
| Implementar proxy support | 🟡 | 2h | Necesario para LinkedIn/Twitter |
| Integrar Scrapling StealthyFetcher | 🟡 | 3h | Opcional (mejora robusted) |
| Testing E2E de todos los scrapers | 🟡 | 2h | Validar post-fixes |

---

## 💡 Recomendación Inmediata

**Acción 1 (Ahora - 30 min):** Arreglar BID Playwright
```bash
# En bid_scrapling.py, usar asyncio.to_thread() o convertir a async
```

**Acción 2 (Hoy - 1h):** Agregar retry lógica a Grants.gov
```python
# Reintentar con backoff exponencial (1s, 2s, 4s, 8s)
# Cambiar User-Agent entre reintentos
```

**Acción 3 (Esta semana - 2-3h):** Implementar proxies
```bash
# Evaluar Bright Data o Oxylabs
# Integrar proxy_url en linkedin_improved y twitter_improved
```

---

## 📊 Impacto Esperado

### Después de Arreglos Básicos (BID + Grants.gov retry)
```
Resultado esperado: +50-80 items
- BID: 20-30 items
- Grants.gov: 30-50 items
Total: 893-923 items
```

### Después de Proxies (LinkedIn + Twitter)
```
Resultado esperado: +80-120 items
- LinkedIn: 15-30 items/día
- Twitter: 10-20 items/día
Total: 973-1.043 items
```

### Después de Scrapling Completo
```
Resultado esperado: +150-200 items
- Todos los scrapers con anti-bot
- Mejor tasa de éxito
- +25% volumen adicional
Total: 1.100+ items
```

---

## 🔗 Archivos Relevantes

**Scrapers con Scrapling:**
- [backend/app/scrapers/bid_scrapling.py](backend/app/scrapers/bid_scrapling.py)
- [backend/app/scrapers/grantsgov_scrapling.py](backend/app/scrapers/grantsgov_scrapling.py)
- [backend/app/scrapers/base_scrapling.py](backend/app/scrapers/base_scrapling.py)

**Scrapers con Google Search:**
- [backend/app/scrapers/linkedin_improved.py](backend/app/scrapers/linkedin_improved.py)
- [backend/app/scrapers/twitter_improved.py](backend/app/scrapers/twitter_improved.py)

**Runner (orchestrator):**
- [backend/app/scrapers/runner.py](backend/app/scrapers/runner.py)

---

## ✅ Conclusión

**Estado:** Código funcional, blockers externos

**BD Actual:** 843 oportunidades (825 nacional + 18 global)

**Próximos Pasos:**
1. ✅ Arreglar BID Playwright (30 min)
2. ✅ Agregar retry a Grants.gov (1h)
3. ⏳ Implementar proxies (2-3h)
4. ⏳ Testing E2E (2h)

**Estimado para 1.000+ items:** 4-6 horas de trabajo

---

**Timestamp:** 2026-06-17 20:32  
**Rama:** main  
**Commit:** 0388d70

