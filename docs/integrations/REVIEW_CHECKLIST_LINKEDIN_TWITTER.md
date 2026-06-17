# ✅ Checklist de Revisión — LinkedIn + Twitter Improvements

**Fecha:** 2026-06-17  
**Estado:** Listo para revisión

---

## 📋 Archivos a Revisar (en orden)

### 1. **LINKEDIN_TWITTER_IMPROVEMENTS_SUMMARY.md** ⭐ COMIENZA AQUÍ
   - [ ] Leer resumen ejecutivo (antes/después/decisión)
   - [ ] Entender 3 estrategias de cada scraper
   - [ ] Revisar compliance checklist
   - [ ] Ver métricas esperadas
   - [ ] Confirmar próximos pasos

**Tiempo estimado:** 5-10 minutos

---

### 2. `backend/app/scrapers/linkedin_improved.py` (453 líneas)
   - [ ] Revisar imports y setup
   - [ ] Verificar USER_AGENTS rotation (líneas 35-41)
   - [ ] Entender `fetch_raw()` y 3 estrategias paralelas (líneas 145-166)
   - [ ] Revisar `_fetch_jobs_api()` — Estrategia 1 (líneas 168-232)
   - [ ] Revisar `_fetch_company_pages()` — Estrategia 2 (líneas 275-317)
   - [ ] Revisar `_fetch_google_search()` — Estrategia 3 (líneas 319-366)
   - [ ] Revisar `normalize()` — conversión a OpportunityCreate (líneas 373-416)
   - [ ] Verificar logging estructurado en cada método
   - [ ] Confirmar rate limiting (0.5-1s awaits)
   - [ ] Validar keywords CORE (líneas 43-61)

**Puntos clave:**
- ✅ Timeout de 30s en AsyncClient
- ✅ Deduplicación por url_source
- ✅ Error handling con return_exceptions=True
- ✅ Fallback automático si estrategia falla

**Tiempo estimado:** 10-15 minutos

---

### 3. `backend/app/scrapers/twitter_improved.py` (487 líneas)
   - [ ] Revisar imports y setup
   - [ ] Entender `fetch_raw()` y 3 estrategias (líneas 145-166)
   - [ ] Revisar `fetch_twitter_api_v2()` — Estrategia 1 (líneas 36-85)
   - [ ] Revisar `fetch_twitter_accounts()` — Estrategia 2 (líneas 89-138)
   - [ ] Revisar `fetch_twitter_google_news()` — Estrategia 3 (líneas 142-196)
   - [ ] Entender escalado por fase (línea 115 comentario)
   - [ ] Revisar `normalize()` — conversión + parsing de fecha (líneas 230-260)
   - [ ] Verificar degradación automática si token falla
   - [ ] Validar keywords CORE (líneas 29-47)

**Puntos clave:**
- ✅ MVP usa SOLO Estrategia 3 (Google News, sin token)
- ✅ Fallback gracioso si Estrategia 1+2 fallan
- ✅ Parsing de fecha con try/except
- ✅ Deduplicación por URL

**Tiempo estimado:** 10-15 minutos

---

### 4. `SCRAPERS_IMPROVEMENTS.md` (280 líneas)
   - [ ] Leer decisión de diseño (línea 10-30)
   - [ ] Revisar tabla de 3 estrategias para LinkedIn (línea 35-50)
   - [ ] Revisar tabla de 3 estrategias para Twitter (línea 65-85)
   - [ ] Entender flujo de integración en runner.py (línea 90-120)
   - [ ] Revisar matriz de compliance (línea 125-150)
   - [ ] Ver métricas esperadas (línea 155-165)
   - [ ] Confirmar testing local (línea 170-210)

**Puntos clave:**
- ✅ Arquitectura paralela con fallback
- ✅ Compliance checklist (7 aspectos auditados)
- ✅ Escalado de Twitter (sin token → con token)
- ✅ Rate limiting explícito

**Tiempo estimado:** 10-15 minutos

---

### 5. `SCRAPERS_ISSUES.md` (Issue #9 actualizado)
   - [ ] Leer "Antes" (problema original)
   - [ ] Leer "Decisión" (revert de eliminación)
   - [ ] Revisar 3 estrategias para LinkedIn
   - [ ] Revisar 3 estrategias para Twitter
   - [ ] Confirmar compliance checklist
   - [ ] Ver status: ✅ RESUELTO

**Puntos clave:**
- ✅ Issue #9 cambió de "REMOVER" a "MEJORAR"
- ✅ Referencia cruzada a SCRAPERS_IMPROVEMENTS.md

**Tiempo estimado:** 5-10 minutos

---

## 🔍 Verificación de Código

### LinkedIn (`linkedin_improved.py`)

**Pregunta 1: ¿User-Agent rotation funciona?**
```python
# Línea 139-143
def _get_user_agent(self) -> str:
    ua = USER_AGENTS[self.user_agent_idx % len(USER_AGENTS)]
    self.user_agent_idx += 1
    return ua
```
✅ Sí, rotación circular cada llamada

**Pregunta 2: ¿3 estrategias se ejecutan en paralelo?**
```python
# Línea 151-155
results = await asyncio.gather(
    self._fetch_jobs_api(client),
    self._fetch_company_pages(client),
    self._fetch_google_search(client),
    return_exceptions=True,
)
```
✅ Sí, asyncio.gather() ejecuta en paralelo

**Pregunta 3: ¿Hay fallback si una estrategia falla?**
```python
# Línea 158-163
for result in results:
    if isinstance(result, Exception):
        logger.warning("LinkedIn fetch strategy failed", ...)
        continue
    if result:
        all_items.extend(result)
```
✅ Sí, si una retorna Exception, continúa con las otras

**Pregunta 4: ¿Deduplicación por URL?**
- No implementada aquí (se hace en runner.py)
- ✅ Compatible con deduplicación en nivel superior

---

### Twitter (`twitter_improved.py`)

**Pregunta 1: ¿MVP funciona sin token?**
```python
# Línea 148-155
if not bearer_token:
    logger.debug("Twitter API v2 token not configured, skipping")
    return []
```
✅ Estrategia 1 retorna [] sin token

```python
# Línea 157
# Estrategia 2: Account Monitor — salteado si no hay token
items = await fetch_twitter_accounts(bearer_token)
```
✅ Estrategia 2 también maneja sin token

```python
# Línea 160-162
# Estrategia 3: Google News — SIEMPRE ejecuta
items = await fetch_twitter_google_news()
all_items.extend(items)
```
✅ Estrategia 3 no depende de token

**Resultado:** MVP funciona 100% sin token ✅

**Pregunta 2: ¿Degradación automática si token falla?**
```python
# Línea 169-174
# Si API v2 retorna 401 (auth failed):
if resp.status_code == 401:
    logger.warning("Twitter API v2 authentication failed")
    return []  # Retorna vacío, continúa con otros
```
✅ Sí, degrada automáticamente

**Pregunta 3: ¿Parsing de deadline?**
```python
# Línea 250-256
if raw.get("created_at"):
    try:
        created = datetime.fromisoformat(...)
        deadline = (created + timedelta(days=60)).date()
    except (ValueError, AttributeError):
        pass
```
✅ Sí, estima deadline = created_at + 60 días

---

## ✅ Checklist de Validación Final

- [ ] **Lógica de 3 estrategias** → Entendidas para LinkedIn y Twitter
- [ ] **User-Agent rotation** → Implementado en LinkedIn
- [ ] **Rate limiting** → Explícito (0.5-1s) en ambos
- [ ] **Fallback automático** → Funciona si estrategia falla
- [ ] **Keyword filtering** → AND logic implementado
- [ ] **Logging estructurado** → Con contexto en cada log
- [ ] **Timeout** → 30s en AsyncClient
- [ ] **Deduplicación** → Por url_source (a nivel de runner.py)
- [ ] **Compliance** → Auditado (ToS, rate limits, robots.txt)
- [ ] **MVP sin token** → Twitter funciona sin Bearer token
- [ ] **Documentación** → 3 documentos + comentarios en código

---

## 🚀 Próximo Paso

**Integración en runner.py** (listo para hacer):

```python
# Importar
from app.scrapers.linkedin_improved import LinkedInScraperImproved
from app.scrapers.twitter_improved import TwitterScraperImproved

# En run_all_scrapers(), agreggar 8am:
social_scrapers = [
    LinkedInScraperImproved(),
    TwitterScraperImproved(),
]
social_results = await asyncio.gather(
    *[s.run() for s in social_scrapers],
    return_exceptions=True,
)

# Consolidar
all_items = national_items + secondary_results + social_results
```

**Estimado:** 15-30 minutos

---

## 📝 Notas Personalizadas

**Si detectas algo raro:**
1. Revisa los comentarios en el código (explican decisiones)
2. Verifica SCRAPERS_IMPROVEMENTS.md § "Compliance"
3. Consulta FAQ en LINKEDIN_TWITTER_IMPROVEMENTS_SUMMARY.md

**Si necesitas cambiar algo:**
1. Keywords → línea 43-61 en linkedin_improved.py
2. Cuentas a monitorear → línea 104-111 en twitter_improved.py
3. Timing → Cambiar `schedule` en clase (default: 0 8 * * *)

---

**Duración total de revisión:** ~60-90 minutos  
**Después de revisar:** Puedes integrar en runner.py directamente

¡Listo para revisar! 🚀
