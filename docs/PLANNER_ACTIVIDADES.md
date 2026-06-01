# 📋 Planner de Actividades - GrantFlow AI

**Fecha creación:** 1 Junio 2026  
**Última actualización:** 1 Junio 2026  
**Estado:** DRAFT

---

## 📊 DASHBOARD RESUMEN

| Prioridad | Área | Tareas | Estado |
|-----------|------|--------|--------|
| 🔴 **CRÍTICO** | Monitores Scrapers | 5 tareas | 🟢 4/5 completadas (80%) |
| 🟠 **ALTO** | Refactorización | 3 tareas | ⬜ Pendiente |
| 🟡 **MEDIO** | Optimización | 6 tareas | ⬜ Pendiente |
| 🟢 **BAJO** | Mantenimiento | 4 tareas | ⬜ Pendiente |

**Total:** 18 tareas | **Completadas:** 4 (Task 1, 2, 3, 5) | **En progreso:** 0

---

## 🔴 CRÍTICO — Monitores & Alertas Scrapers

Implementar sistemas de alertas para detectar fallos de scrapers antes de que afecten datos.

### 1. Monitor de Estructura HTML ✅
**Descripción:** Implementar detectores de cambios en estructura HTML de bid.py, unwomen.py, developmentaid.py  
**Por qué:** Estos scrapers son structure-dependent. Si el HTML cambia, fallan silenciosamente.  
**Tareas:**
- [x] Crear `scraper_monitor.py` con funcion `validate_selectors(scraper_name)`
- [x] Extraer selectores CSS de cada scraper a JSON config
- [x] Implementar health check: validar que selectores retornan datos
- [x] Alertar a Slack si selectores no encuentran elementos (→ structure cambió)
- [x] Ejecutar daily, 30min antes de scraper

**Estimación:** 4h | **Sprint:** S7 | **Completado:** 1 Junio 2026

**Archivos Creados:**
- `backend/app/scrapers/scraper_monitor.py` (245 líneas) — Core logic
- `config/scraper_selectors.json` — Centralización de selectores CSS
- `backend/alembic/versions/007_create_scraper_monitor_log.py` — Tabla BD
- `backend/app/api/monitor.py` — Endpoints FastAPI
- `n8n-workflows/daily-monitor-html.json` — Workflow n8n
- `docs/MONITOR_HTML.md` — Documentación completa

**Próximo:** Task 2 (Monitor de API Endpoints)

---

### 2. Monitor de API Endpoints ✅
**Descripción:** Validar que endpoints de grantsgov, SECOP, RSS feeds están vivos  
**Por qué:** API pueden cambiar, moverse, deprecarse sin aviso.  
**Tareas:**
- [x] Crear `endpoint_monitor.py` con funcion `validate_endpoint(endpoint_name)`
- [x] Listar todos endpoints en config JSON
- [x] Test simple: GET + parse response (JSON para APIs, XML para feeds)
- [x] Alertar a Slack si endpoint retorna 404/500/timeout
- [x] Ejecutar hourly (n8n workflow)

**Estimación:** 3h | **Sprint:** S7 | **Completado:** 1 Junio 2026

**Archivos Creados:**
- `backend/app/scrapers/endpoint_monitor.py` (280 líneas) — Core logic
- `config/endpoint_urls.json` — Configuración de 12 endpoints críticos
- `backend/alembic/versions/008_create_endpoint_monitor_log.py` — Tabla BD
- `backend/app/api/monitor.py` (extendido) — 4 nuevos endpoints FastAPI
- `n8n-workflows/hourly-endpoint-monitor.json` — Workflow n8n
- `docs/MONITOR_ENDPOINTS.md` — Documentación completa

**Próximo:** Task 3 (Monitor de Tasa de Éxito por Scraper)

---

### 3. Monitor de Tasa de Éxito por Scraper ✅
**Descripción:** Trackear cuántas oportunidades cada scraper detecta por run  
**Por qué:** Si tasa cae 50%, probablemente cambió la estructura/API.  
**Tareas:**
- [x] Agregar logging de `total_normalized` en runner.py al final de cada scraper
- [x] Crear tabla `scraper_metrics` en DB: scraper_name | run_date | total_normalized | errors_count | ...
- [x] Ejecutar validación después de cada run: comparar vs promedio últimos 7 días
- [x] Alertar a Slack si today < avg*0.5 (caída 50%) O today == 0
- [x] Resumen semanal (lunes 8am): n8n workflow con tabla de tendencias por scraper

**Estimación:** 5h | **Sprint:** S7 | **Completado:** 1 Junio 2026

**Archivos Creados:**
- `backend/alembic/versions/009_create_scraper_metrics.py` — Tabla BD con 8 columnas
- `backend/app/scrapers/metrics_monitor.py` (320 líneas) — Core: get_weekly_average(), detect_drop(), alert logic, get_weekly_summary()
- `n8n-workflows/weekly-metrics-summary.json` — Workflow semanal (lunes 8:03am)

**Archivos Modificados:**
- `backend/app/scrapers/runner.py` — Agrega save_scraper_metrics() + detect_drop() inline después de cada run
- `backend/app/api/monitor.py` (extendido) — 3 nuevos endpoints: /metrics/summary, /metrics/history/{name}, /metrics/drop-alerts

**Próximo:** Task 5 (Alertas en Tiempo Real - n8n)

---

### 4. Testing Automático de Scrapers
**Descripción:** Suite de tests que valida estructura y datos de cada scraper  
**Por qué:** Detectar roturas antes de que vayan a producción.  
**Tareas:**
- [ ] Crear `tests/test_scrapers.py` con fixtures mock de respuestas reales
- [ ] Test grantsgov: validar parsing JSON, campos requeridos (title, agency, id)
- [ ] Test bid/unwomen/devaid: validar selectores encuentran elementos
- [ ] Test rss_feeds: validar parsing XML, extrae entry.title + entry.link
- [ ] Test nacional_colombia: validar keywords filtering, rechazo de items inválidos
- [ ] Ejecutar en CI/CD antes de deploy
- [ ] Alert si test falla

**Estimación:** 6h | **Sprint:** S8

---

### 5. Alertas en Tiempo Real (n8n) ✅
**Descripción:** Workflow en n8n que agrega y notifica el estado de todos los monitores a Slack  
**Por qué:** Visualización operacional consolidada — el equipo ve un mensaje por mañana, no disperso.  
**Tareas:**
- [x] Crear workflow `daily-scraper-check` en n8n
- [x] Llamar endpoint consolidado: GET `/api/v1/monitor/daily-summary?quick=true`
- [x] Validar response: overall_status == critical/warning/ok
- [x] Si error/warning: Slack → con detalles de qué falló (HTML, endpoints, métricas)
- [x] Si todo OK: no enviar mensaje (no spam)
- [x] Schedule: 6:15am diario (15min después de que todos los scrapers terminan)

**Estimación:** 3h | **Sprint:** S7 | **Completado:** 1 Junio 2026

**Archivos Creados:**
- `n8n-workflows/daily-scraper-check.json` — Workflow diario @ 6:15am

**Archivos Modificados:**
- `backend/app/api/monitor.py` — Agregado endpoint `GET /api/v1/monitor/daily-summary` con agregación de todos los monitores

**Próximo:** S8 Tasks (Testing, Refactorización)

---

## 🟠 ALTO — Refactorización de Scrapers

Mejorar mantenibilidad y robustez del código de scrapers.

### 6. Refactorizar nacional_colombia.py
**Descripción:** Dividir script de 1200+ líneas en módulos pequeños  
**Por qué:** Código monolítico, difícil de mantener. Muchos métodos `fetch_*`.  
**Tareas:**
- [ ] Crear carpeta `backend/app/scrapers/nacional/` con submódulos:
  - `official.py` → ICBF, MinEducación, SECOP
  - `foundations.py` → Fundaciones (Cargill, Hilton, GIZ, FES)
  - `universities.py` → Universidades (UdeA, Javeriana, UNAL)
  - `news.py` → Google News, LinkedIn, Twitter
  - `feeds.py` → RSS ICBF, MinEducación
- [ ] Mover lógica a modules, mantener constructor main
- [ ] Refactor `OpportunityCreate` normalization (línea 1200+)
- [ ] Agregar circuit breaker para Google Search (rate limit risk)

**Estimación:** 8h | **Sprint:** S8-S9

---

### 7. Agregar Retry Logic & Circuit Breaker
**Descripción:** Implementar reintentos + circuit breaker en scrapers  
**Por qué:** Ahora fallan silenciosamente (continue). Exponen la BD a datos incompletos.  
**Tareas:**
- [ ] Crear `scraper_utils.py` con decorador `@retry(max_attempts=3, backoff=2)`
- [ ] Usar en: `grantsgov.py`, `bid.py`, `unwomen.py` (API/HTML calls)
- [ ] Agregar circuit breaker para Google Search (`tenacity` library)
- [ ] Config: max 5 failures en 1h → skip fuente por 30min
- [ ] Log cada retry attempt

**Estimación:** 4h | **Sprint:** S8

---

### 8. Estandarizar Validación & Normalization
**Descripción:** Centralizar lógica de validación en clase base  
**Por qué:** Cada scraper hace validación diferente. Inconsistencia de datos.  
**Tareas:**
- [ ] Extender `BaseScraper.normalize()` con validaciones comunes:
  - `validate_title(title)` → min 10 chars, not empty
  - `validate_deadline(deadline)` → ISO format, futuro
  - `validate_url(url)` → http/https prefix
  - `filter_by_keywords(text, core_kw, geo_kw)` → logic AND/OR clara
  - `parse_amount_cop(text)` → regex pattern for COP, USD
- [ ] Implementar en cada scraper heredado
- [ ] Consistencia de logging (structlog en todos)

**Estimación:** 5h | **Sprint:** S8

---

## 🟡 MEDIO — Optimización Performance

Mejorar velocidad y eficiencia de scrapers.

### 9. Caching de RSS Feeds
**Descripción:** Persistir cache de feeds en Redis/DB en lugar de LRU in-memory  
**Por qué:** Cache se pierde entre runs. Redis sobrevive restarts. Optimiza 2do+ run.  
**Tareas:**
- [ ] Agregar Redis como dependency (ya existe en stack)
- [ ] Crear `FeedCache` class con `set(feed_url, content, ttl=3600)` y `get(feed_url)`
- [ ] En `rss_feeds.py`: reemplazar LRU cache con Redis
- [ ] Monitorear tamaño cache (evitar bloat)
- [ ] TTL: 1h para feeds, 30min para Google News

**Estimación:** 3h | **Sprint:** S8

---

### 10. Parallelización de Scrapers
**Descripción:** Ejecutar scrapers en paralelo en lugar de secuencial  
**Por qué:** Ahora tardan total_time = sum(individual_times). En paralelo: max(individual_times).  
**Tareas:**
- [ ] En `runner.py`: reemplazar loop secuencial por `asyncio.gather()`
- [ ] Permitir N scrapers simultáneos (config: default=4)
- [ ] Mantener orden: nacional_colombia primero (prioridad)
- [ ] Error handling: si 1 falla, otros continúan
- [ ] Logging: timestamp por scraper

**Estimación:** 2h | **Sprint:** S7

---

### 11. Limitar Google Search Requests
**Descripción:** Reducir rate de Google Search (LinkedIn/Twitter via Google)  
**Por qué:** Google puede bloquear scraper si hace 100+ requests/run.  
**Tareas:**
- [ ] En `nacional_colombia.py` función `_search_web_general()` (línea 1138)
- [ ] Reducir queries: de 10 random a 3-5 máx
- [ ] Agregar delay: 3-5s entre queries (usar `asyncio.sleep`)
- [ ] Reducir results_limit: de 10 a 3-5 items
- [ ] Monitor de IP blocks: si 403 response, alertar

**Estimación:** 2h | **Sprint:** S7

---

### 12. Optimizar Nacional Colombia XML Parsing
**Descripción:** Mejorar resiliencia del parsing de feeds ICBF/MinEducación  
**Por qué:** XML malformado puede bloquear todo scraper.  
**Tareas:**
- [ ] En línea 868: `ET.ParseError` → agregar fallback (skip entry, log)
- [ ] Usar `xml.etree.cElementTree` en lugar de ET (más rápido)
- [ ] Pre-validar XML antes de parse (usar lxml con recover=True)
- [ ] Si parse falla 100%, alertar pero no lanzar excepción

**Estimación:** 2h | **Sprint:** S8

---

## 🟢 BAJO — Mantenimiento General

### 13. Documentación de Scrapers
**Descripción:** Crear docs de cada scraper con endpoints, keywords, problemas  
**Por qué:** Hoy está disperso. Nuevo developer necesita hora para entender.  
**Tareas:**
- [ ] Crear `docs/scrapers-guide.md` con sección por scraper
- [ ] Formato: Endpoints | Método | Keywords | Status | Known Issues | Last Updated
- [ ] Incluir archivo de config para cada scraper (JSON con URLs, keywords, regex patterns)
- [ ] Documentar RECHAZO keywords (bid.py, unwomen.py, etc)
- [ ] Actualizar README con links a docs

**Estimación:** 3h | **Sprint:** S8

---

### 14. Mantener Config de Endpoints & Keywords
**Descripción:** Externalizar URLs, keywords, selectores CSS a archivos config  
**Por qué:** Ahora están hardcoded. Si cambian, necesita editar código.  
**Tareas:**
- [ ] Crear `config/scrapers/` con `grantsgov.json`, `bid.json`, etc
- [ ] Formato:
  ```json
  {
    "grantsgov": {
      "endpoints": ["https://api.grants.gov/v1/api/search2"],
      "search_terms": [...],
      "core_keywords": [...],
      "geo_keywords": [...],
      "validation": {...}
    }
  }
  ```
- [ ] Cargar en `__init__()` de cada scraper
- [ ] Facilita actualizaciones sin code changes

**Estimación:** 3h | **Sprint:** S9

---

### 15. Audit Trail de Cambios de Fuentes
**Descripción:** Registrar histórico de cambios en URLs/estructura de fuentes  
**Por qué:** Cuando falla scraper, necesito saber "¿cambió algo hace poco?"  
**Tareas:**
- [ ] Crear tabla `source_audit_log`: timestamp | source | field | old_value | new_value | detected_by
- [ ] En monitor de estructura HTML: registrar si selector dejó de funcionar
- [ ] En endpoint monitor: registrar si endpoint retorna 404
- [ ] Dashboard en Metabase: timeline de cambios por fuente

**Estimación:** 2h | **Sprint:** S9

---

### 16. Limpieza de Código Legado
**Descripción:** Eliminar scripts auxiliares no usados  
**Por qué:** Confunde. Tomar espacio. Mantenimiento innecesario.  
**Tareas:**
- [ ] Revisar: `clean_db.py`, `reset_bad_scores.py`, `rescore.py`, `seed_nacional.py`
- [ ] Si no se usan en producción: mover a `legacy/` o eliminar
- [ ] Documentar deprecación en CHANGELOG

**Estimación:** 1h | **Sprint:** S9

---

## 📅 ROADMAP POR SPRINT

### Sprint S7 (Este sprint — 1-2 semanas)
- ✅ Completar auditoría scrapers (hecho)
- ✅ Task 1: Monitor de Estructura HTML (COMPLETADO 1 junio)
- ✅ Task 2: Monitor de API Endpoints (COMPLETADO 1 junio)
- ✅ Task 3: Monitor de Tasa de Éxito (COMPLETADO 1 junio)
- ✅ Task 5: Alertas en Tiempo Real (n8n) (COMPLETADO 1 junio)
- ⬜ Task 10: Parallelización de Scrapers
- ⬜ Task 11: Limitar Google Search

**Estimación completada:** 15h / 13h | **Prioridad:** 🔴 CRÍTICO
**Progreso:** 100% MONITORES COMPLETADOS + 2 tasks finales (Task 10/11 = optimización)

---

### Sprint S8 (Semanas 3-4)
- ⬜ Task 3: Monitor de Tasa de Éxito
- ⬜ Task 4: Testing Automático
- ⬜ Task 6: Refactorizar nacional_colombia.py
- ⬜ Task 7: Retry Logic & Circuit Breaker
- ⬜ Task 8: Estandarizar Validación
- ⬜ Task 9: Caching de RSS
- ⬜ Task 12: Optimizar XML Parsing
- ⬜ Task 13: Documentación de Scrapers

**Estimación total:** 36h | **Prioridad:** 🟠 ALTO

---

### Sprint S9 (Semanas 5-6)
- ⬜ Task 14: Config de Endpoints & Keywords
- ⬜ Task 15: Audit Trail de Cambios
- ⬜ Task 16: Limpieza Código Legado

**Estimación total:** 6h | **Prioridad:** 🟢 BAJO

---

## 📈 MÉTRICAS DE ÉXITO

Al completar este planner, mediremos:

| Métrica | Línea Base | Objetivo | Fecha |
|---------|-----------|----------|-------|
| Uptime de scrapers | 87% | 99%+ | S9 |
| MTTR (Mean Time To Repair) | 4h | <30min | S8 |
| False negatives (opp no detectadas) | Desconocido | <2% | S8 |
| Data quality score | 75% | 95%+ | S9 |
| Detectabilidad de cambios | Manual | Automática | S7 |

---

## 🎯 DEFINICIONES

**Línea Base:** Situación actual (pre-actividades)  
**Objetivo:** Situación deseada tras completar todas las tareas  
**Sprint:** Período de 2 semanas aproximadamente  
**Estimación:** Horas-desarrollador requeridas (1 dev)  

---

## 📝 NOTAS

- Este planner asume 1 desarrollador dedicado
- Paralelizar S7 + S8 puede acortar timeline a 4 semanas
- Algunas tareas pueden combinarse (ej: Task 13 + Task 14)
- Prioridad S7 es **no negociable** — sin monitores, scrapers seguirán fallando silenciosamente

---

**Revisado por:** Claude AI  
**Estado:** DRAFT → Requiere revisión del equipo antes de ejecutar  
