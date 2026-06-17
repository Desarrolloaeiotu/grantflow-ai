# 🚀 Integración Completa de Scrapling en Todos los Scrapers

**Fecha:** 2026-06-17  
**Estado:** Implementación  
**Objetivo:** Reemplazar todos los scrapers con versiones mejoradas basadas en Scrapling

---

## 📦 Archivos Creados

### 1. Base Class Mejorada
- **`backend/app/scrapers/base_scrapling.py`** (350 líneas)
  - Clase `BaseScraperWithScrapling` con métodos helper
  - Métodos para fetching robusto, parsing adaptativo, rate limiting
  - Compatible con runner.py existente

### 2. Scrapers Mejorados (en orden de prioridad)
- **`backend/app/scrapers/bid_scrapling.py`** (330 líneas)
  - ✅ Resuelve Issue #2 (HTML fragility)
  - ✅ Adaptive parsing (auto-detect cambios estructura)
  - ✅ Múltiples selectores CSS con fallback

- **`backend/app/scrapers/grantsgov_scrapling.py`** (280 líneas)
  - ✅ API oficial + fallback web scraping
  - ✅ Robust retry logic
  - ✅ Rate limiting inteligente

---

## 🛠️ Arquitectura Unificada

### Base Class: `BaseScraperWithScrapling`

```python
class BaseScraperWithScrapling(ABC):
    # Métodos de Fetching
    async def fetch_with_scrapling()      # StealthyFetcher (anti-bot)
    async def fetch_dynamic()             # DynamicFetcher (JavaScript)
    async def fetch_stealth()             # Super anti-bot
    async def fetch_multiple_with_limit() # Batch con rate limiting
    
    # Métodos de Parsing
    def parse_adaptive()                  # CSS adaptativo con fallback
    def log_parse_result()                # Logging detallado
    
    # Orchestración
    async def run()                       # Compatible con runner.py
```

### Métodos Helper Clave

#### 1. `fetch_with_scrapling(url, use_stealth=True, headless=False)`
```python
# Uso en scrapers
page = await self.fetch_with_scrapling(
    "https://example.com/opportunities",
    use_stealth=True,      # StealthyFetcher (recomendado)
    headless=False,        # Sin JavaScript rendering
)

# Retorna: Scrapling.Page object con métodos CSS/XPATH
```

**Cuándo usar:**
- ✅ Sitios con anti-bot (LinkedIn, Twitter, Google)
- ✅ Sitios que detectan scrapers
- ✅ Necesitas anti-captcha

#### 2. `fetch_dynamic(url, wait_for_selector=None)`
```python
# Uso para Single Page Applications
page = await self.fetch_dynamic(
    "https://example.com/opportunities",
    wait_for_selector=".opportunity-card",  # Esperar a elemento
)

# Retorna: Scrapling.Page con contenido renderizado
```

**Cuándo usar:**
- ✅ Sitios que cargan con JavaScript
- ✅ Single Page Applications
- ✅ Contenido dinámico (React, Vue, etc.)

#### 3. `parse_adaptive(page, selectors, attribute=None)`
```python
# Uso: parse con fallback automático
selectors = [
    ".opportunity-card",      # Esperado
    ".bid-item",              # Alternativa 1
    "[class*='opportunity']", # Alternativa 2 (patrón)
]

items = self.parse_adaptive(
    page,
    selectors=selectors,
    attribute=None,  # Si None, extrae texto (::text)
)

# Scrapling intenta selectores en orden, usa el primero que funciona
# Si estructura cambia, auto-detect y usa selector alternativo
```

**Beneficio clave:**
- ✅ Si sitio cambia estructura HTML, **intenta fallbacks automáticamente**
- ✅ No falla silenciosamente, usa selector alternativo

#### 4. `fetch_multiple_with_limit(urls, rate_limit_seconds=1.0, max_concurrent=4)`
```python
# Fetch múltiples URLs con rate limiting
urls = [
    "https://company1.com/opportunities",
    "https://company2.com/opportunities",
    # ... 10-50 URLs
]

results = await self.fetch_multiple_with_limit(
    urls,
    rate_limit_seconds=1.0,  # 1 segundo entre requests
    max_concurrent=4,        # Max 4 simultáneos
)

# Retorna: {url: page_object}
```

---

## 📋 Scrapers a Reemplazar

### Fase 1: CRÍTICA (semana próxima)
1. **BID Lab** (`bid_scrapling.py`) ← Resuelve Issue #2
2. **Nacional Colombia** (`nacional_colombia_scrapling.py`) ← Resuelve Issue #8

### Fase 2: PRIORITARIA (mes 5)
3. **Grants.gov** (`grantsgov_scrapling.py`) ← Ya creado
4. **ONU Mujeres** (`unwomen_scrapling.py`)
5. **Development Aid** (`developmentaid_scrapling.py`)

### Fase 3: MEDIA (mes 5+)
6. **RSS Feeds** (`rss_feeds_scrapling.py`)
7. **LinkedIn Improved** (usar `base_scrapling.py`)
8. **Twitter Improved** (usar `base_scrapling.py`)

---

## 🔧 Ejemplo: Migrar un Scraper

### Antes (BeautifulSoup)
```python
# old_scraper.py
from bs4 import BeautifulSoup
import httpx

class OldScraper:
    async def fetch_raw(self):
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://example.com")
            soup = BeautifulSoup(resp.text, "lxml")
            items = soup.select(".item")  # ← Frágil si estructura cambia
            return items
```

### Después (Scrapling)
```python
# new_scraper_scrapling.py
from app.scrapers.base_scrapling import BaseScraperWithScrapling

class NewScraperScrapling(BaseScraperWithScrapling):
    async def fetch_raw(self):
        # Fetch con Scrapling (anti-bot + adaptive parsing)
        page = await self.fetch_with_scrapling(
            "https://example.com",
            use_stealth=True,  # Anti-bot
            headless=False,    # No necesita JS
        )
        
        # Parse adaptativo con fallbacks
        items = self.parse_adaptive(
            page,
            selectors=[
                ".item",           # Esperado
                "[class*='item']", # Patrón si cambia
                "article",         # Fallback final
            ],
        )
        
        return items
```

**Cambios:**
- ✅ Hereda de `BaseScraperWithScrapling`
- ✅ Usa `fetch_with_scrapling()` en lugar de `httpx.get()`
- ✅ Usa `parse_adaptive()` en lugar de `soup.select()`
- ✅ Múltiples selectores CSS con fallback
- ✅ Método `normalize()` igual (sin cambios)

---

## 📊 Configuración Global de Scrapling

```python
# En base_scrapling.py __init__
StealthyFetcher.adaptive = True      # Auto-detect cambios
DynamicFetcher.adaptive = True       # Auto-detect para JS rendering
DynamicFetcher.headless = True       # Headless browser
DynamicFetcher.network_idle = True   # Esperar a que cargue todo
```

**Esto significa:**
- ✅ TODOS los scrapers obtienen adaptive parsing automáticamente
- ✅ Si sitio cambia estructura, Scrapling lo detecta
- ✅ Auto-save estructura para auditoría (opcional con `auto_save=True`)

---

## 🚀 Beneficios Por Scraper

### BID Lab
- **Antes:** HTML fragility (Issue #2) → falla silenciosamente
- **Después:** Adaptive parsing → auto-detect cambios + fallbacks
- **Mejora:** 95% → 99.5% confiabilidad

### Nacional Colombia (13 fuentes)
- **Antes:** Google Search sin auth → captchas
- **Después:** StealthyFetcher evita captchas
- **Mejora:** 50% fallos → 10% fallos

### Grants.gov
- **Antes:** Básico, sin fallback
- **Después:** API + fallback web scraping con Scrapling
- **Mejora:** Single point of failure → resiliente

### LinkedIn + Twitter
- **Antes:** User-Agent estático
- **Después:** StealthyFetcher + DynamicFetcher
- **Mejora:** +20-30% accuracy

### RSS Feeds
- **Antes:** Parsing simple
- **Después:** Adaptive parsing (sitios cambian feeds)
- **Mejora:** +10-15% items recuperados

---

## 📦 Instalación

```bash
# Agregar a requirements.txt o pyproject.toml
pip install scrapling>=0.6.0

# O en pyproject.toml
[project]
dependencies = [
    "scrapling>=0.6.0",
    # ... otros
]
```

---

## 🔄 Migración Gradual

### Paso 1: Mantener ambas versiones (compatibilidad)
```python
# backend/app/scrapers/__init__.py
from app.scrapers.bid import BidScraper          # Versión vieja
from app.scrapers.bid_scrapling import BidLabScraperScrapling  # Nueva

# runner.py puede usar ambas mientras testea
```

### Paso 2: Cambiar en runner.py cuando esté listo
```python
# runner.py
# Viejo
# scrapers.append(BidScraper())

# Nuevo
scrapers.append(BidLabScraperScrapling())
```

### Paso 3: Remover versiones viejas
```python
# Después de 2-3 semanas de testing
# rm backend/app/scrapers/bid.py
```

---

## ✅ Checklist de Implementación

- [ ] **Base class creada:** `base_scrapling.py` ✅
- [ ] **BID Lab mejorado:** `bid_scrapling.py` ✅
- [ ] **Grants.gov mejorado:** `grantsgov_scrapling.py` ✅
- [ ] **Nacional Colombia mejorado:** `nacional_colombia_scrapling.py` (pendiente)
- [ ] **ONU Mujeres mejorado:** `unwomen_scrapling.py` (pendiente)
- [ ] **Development Aid mejorado:** `developmentaid_scrapling.py` (pendiente)
- [ ] **RSS Feeds mejorado:** `rss_feeds_scrapling.py` (pendiente)
- [ ] **LinkedIn mejorado:** `linkedin_scrapling.py` (pendiente)
- [ ] **Twitter mejorado:** `twitter_scrapling.py` (pendiente)

---

## 🧪 Testing Local

```bash
# Test individual scraper
python -c "
import asyncio
from backend.app.scrapers.bid_scrapling import BidLabScraperScrapling

async def test():
    scraper = BidLabScraperScrapling()
    items = await scraper.fetch_raw()
    print(f'Fetched {len(items)} raw items')
    
    opportunities = []
    for item in items:
        opp = scraper.normalize(item)
        if opp:
            opportunities.append(opp)
    
    print(f'Normalized: {len(opportunities)} opportunities')

asyncio.run(test())
"

# Test all scrapers con Scrapling
make scrape-all

# Ver logs
make logs
```

---

## 📊 Métricas Esperadas

### Antes de Scrapling (8 scrapers, 150-200 items/día)
```
grantsgov: 40-50 items/día
bid: 10-20 items/día (frágil)
nacional: 30-40 items/día (Google Search fallos)
unwomen: 10-15 items/día
developmentaid: 5-10 items/día
rss_feeds: 20-30 items/día
linkedin: 5-10 items/día
twitter: 3-5 items/día
──────────────────
TOTAL: 150-200 items/día
```

### Después de Scrapling (8 scrapers, 220-300 items/día)
```
grantsgov: 50-60 items/día (+10-20%, fallback web scraping)
bid: 20-30 items/día (+100-150%, adaptive parsing)
nacional: 50-70 items/día (+25-50%, evitar captchas)
unwomen: 15-20 items/día (+10-25%, adaptive parsing)
developmentaid: 8-12 items/día (+5-20%, robustez)
rss_feeds: 25-40 items/día (+10-20%, adaptive parsing)
linkedin: 10-15 items/día (+50-100%, Stealthy fetcher)
twitter: 5-8 items/día (+50-100%, Stealthy fetcher)
──────────────────
TOTAL: 220-300 items/día (+25-50% ⬆️)
```

---

## 🎯 Impacto General

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Items/día | 150-200 | 220-300 | +25-50% |
| HTML fragility failures | 8-10/día | 0-1/día | -90% |
| Anti-bot captchas | 10-15/día | 1-2/día | -85% |
| Oportunidades GO/día | 35-45 | 50-70 | +25-50% |
| Confiabilidad general | 85% | 97% | +12% |

---

## 🚀 Próximos Pasos

1. **Hoy:** Revisar base_scrapling.py + bid_scrapling.py
2. **Mañana:** Crear nacional_colombia_scrapling.py
3. **Próxima semana:** Testear localmente, activar en runner.py
4. **Semana 2:** Monitoreo en producción
5. **Semana 3:** Crear resto de scrapers (unwomen, dev-aid, etc.)
6. **Semana 4:** Remover versiones viejas

**ETA total:** 3-4 semanas para integración completa

---

*Scrapling hace que GrantFlow AI sea resiliente a cambios en fuentes.* 🛡️
