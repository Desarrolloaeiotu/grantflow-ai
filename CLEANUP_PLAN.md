# 🧹 Plan de Limpieza — Archivos Obsoletos

**Fecha:** 2026-06-17  
**Estado:** Planificación

---

## 📁 Archivos Raíz (Documentación)

### ✅ MANTENER (Actuales y necesarios)
- `CLAUDE.md` — Configuración del proyecto (CRÍTICO)
- `LINKEDIN_TWITTER_IMPROVEMENTS_SUMMARY.md` — Resumen ejecutivo LinkedIn + Twitter
- `SCRAPERS_ENHANCED_NACIONAL_GLOBAL.md` — Búsqueda nacional + global
- `SCRAPERS_IMPROVEMENTS.md` — Detalles técnicos
- `SCRAPERS_FLOW.md` — Flujo de 6 pasos de scrapers
- `SCRAPERS_ISSUES.md` — Issues y soluciones
- `SCRAPLING_FULL_INTEGRATION.md` — Plan Scrapling completo
- `SCRAPLING_INTEGRATION_PLAN.md` — Estrategia Scrapling
- `SESSION_SUMMARY_20260617.md` — Resumen de sesión actual
- `REVIEW_CHECKLIST_LINKEDIN_TWITTER.md` — Checklist de revisión
- `WORK_COMPLETED_VISUAL.txt` — Resumen visual

### 🗑️ ELIMINAR (Obsoletos/históricos)
- `CODE_REVIEW_ANALYSIS_SERVICE.md` — Antiguo
- `EXECUTIVE_SUMMARY.md` — Antiguo
- `NEXT_STEPS_S6.md` — Información histórica (S6 completado)
- `QUICKSTART_TEAM.md` — Duplicado de documentación
- `SPRINT_S5_OPTIMIZACION.md` — Histórico (S5 completado)
- `SPRINT_S5_SUMMARY.md` — Histórico (S5 completado)
- `TASK_2_COMPLETION.md` — Tarea completada histórica
- `TECHNICAL_REFERENCE.md` — Redundante con CLAUDE.md

---

## 📂 Backend Scrapers (`backend/app/scrapers/`)

### ✅ MANTENER (Versiones nuevas con Scrapling)
- `base.py` — Base class original
- `base_scrapling.py` — Base class mejorada con Scrapling
- `linkedin_improved.py` — LinkedIn mejorado (3 estrategias)
- `twitter_improved.py` — Twitter mejorado (3 estrategias)
- `bid_scrapling.py` — BID mejorado con Scrapling (resuelve Issue #2)
- `grantsgov_scrapling.py` — Grants.gov mejorado
- `nacional_colombia.py` — Nacional (ya existe)
- `unwomen.py` — ONU Mujeres
- `developmentaid.py` — Development Aid
- `rss_feeds.py` — RSS Feeds
- `runner.py` — Orquestador principal
- `tenders_scraper.py` — Tenders v2
- `metrics_monitor.py` — Monitoreo de métricas
- `scraper_monitor.py` — Monitor de scrapers

### 🗑️ ELIMINAR (Versiones viejas)
- `bid.py` — REEMPLAZADO por `bid_scrapling.py`
- `grantsgov.py` — REEMPLAZADO por `grantsgov_scrapling.py`
- `tenders_global_scraper.py` — REEMPLAZADO por `tenders_scraper.py`

### 📦 MOVER A `backend/app/scrapers/utils/`
- `clean_db.py` — Utilidad de limpieza
- `rescore.py` — Utilidad de re-scoring
- `reset_bad_scores.py` — Utilidad de reset
- `endpoint_monitor.py` — Monitor de endpoints
- `seed_global_organizations.py` — Seed de datos
- `seed_nacional.py` — Seed de datos
- `seed_organizations.py` — Seed de datos
- `contacts_scraper.py` — Scraper obsoleto

---

## 🎯 Acciones Específicas

### PASO 1: Eliminar documentos obsoletos raíz
```bash
rm CLAUDE.md  # NO! MANTENER
rm CODE_REVIEW_ANALYSIS_SERVICE.md
rm EXECUTIVE_SUMMARY.md
rm NEXT_STEPS_S6.md
rm QUICKSTART_TEAM.md
rm SPRINT_S5_OPTIMIZACION.md
rm SPRINT_S5_SUMMARY.md
rm TASK_2_COMPLETION.md
rm TECHNICAL_REFERENCE.md
```

### PASO 2: Crear carpeta `backend/app/scrapers/utils/`
```bash
mkdir backend/app/scrapers/utils
mv backend/app/scrapers/clean_db.py utils/
mv backend/app/scrapers/rescore.py utils/
mv backend/app/scrapers/reset_bad_scores.py utils/
mv backend/app/scrapers/endpoint_monitor.py utils/
mv backend/app/scrapers/seed_*.py utils/
mv backend/app/scrapers/contacts_scraper.py utils/
```

### PASO 3: Eliminar scrapers viejos
```bash
rm backend/app/scrapers/bid.py
rm backend/app/scrapers/grantsgov.py
rm backend/app/scrapers/tenders_global_scraper.py
```

### PASO 4: Crear carpeta `docs/` para documentación histórica
```bash
mkdir docs/historical
mv CODE_REVIEW_ANALYSIS_SERVICE.md docs/historical/
mv EXECUTIVE_SUMMARY.md docs/historical/
# ... etc
```

---

## 📊 Resultado Después de Limpieza

### Raíz del proyecto
```
✅ CLAUDE.md (config)
✅ LINKEDIN_TWITTER_IMPROVEMENTS_SUMMARY.md
✅ SCRAPERS_ENHANCED_NACIONAL_GLOBAL.md
✅ SCRAPERS_IMPROVEMENTS.md
✅ SCRAPERS_FLOW.md
✅ SCRAPERS_ISSUES.md
✅ SCRAPLING_FULL_INTEGRATION.md
✅ SESSION_SUMMARY_20260617.md
✅ REVIEW_CHECKLIST_LINKEDIN_TWITTER.md
✅ WORK_COMPLETED_VISUAL.txt

Total: 10 documentos (era 18, -8 archivos)
```

### Scrapers actuales
```
backend/app/scrapers/:
✅ Base class: base.py, base_scrapling.py
✅ LinkedIn: linkedin_improved.py
✅ Twitter: twitter_improved.py
✅ BID: bid_scrapling.py
✅ Grants: grantsgov_scrapling.py
✅ Nacional: nacional_colombia.py
✅ Otros: unwomen.py, developmentaid.py, rss_feeds.py
✅ Orquestador: runner.py
✅ Utilidades: tenders_scraper.py, metrics_monitor.py

Total: 11 scrapers (era 26, -15 archivos)

backend/app/scrapers/utils/:
📦 clean_db.py, rescore.py, reset_bad_scores.py
📦 endpoint_monitor.py, seed_*.py, contacts_scraper.py
(Utilidades separadas)
```

---

## ✅ Checklist de Limpieza

- [ ] Eliminar 8 documentos obsoletos raíz
- [ ] Crear carpeta `backend/app/scrapers/utils/`
- [ ] Mover 6 scripts de utilidad a `utils/`
- [ ] Eliminar 3 scrapers viejos (bid.py, grantsgov.py, tenders_global_scraper.py)
- [ ] Crear carpeta `docs/historical/` para archivos históricos
- [ ] Actualizar `runner.py` si hay imports rotos
- [ ] Verificar que todo funciona: `python -m app.scrapers.runner`

---

## 📝 Notas

**Por qué esta limpieza:**
- Reducir confusión (archivos duplicados/obsoletos)
- Mejorar navegación del proyecto
- Separar scrapers activos de utilidades
- Archivar información histórica

**Seguridad:**
- No se elimina nada crítico
- Se archiva antes de eliminar
- Se puede restaurar si es necesario

---

**Status:** Listo para ejecutar limpieza
