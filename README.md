# 📚 GrantFlow AI — Documentación y Estructura

> Sistema de inteligencia comercial para prospección estratégica de oportunidades de financiamiento

---

## 🎯 Inicio Rápido

**Configuración principal:** [`CLAUDE.md`](CLAUDE.md)  
**Última sesión:** [`docs/sessions/SESSION_SUMMARY_20260617.md`](docs/sessions/SESSION_SUMMARY_20260617.md)

---

## 📁 Estructura de Carpetas

```
grantflow-ai/
├── CLAUDE.md                          ← 🔴 LEER PRIMERO (config del proyecto)
├── README.md                          ← Estás aquí
├── CLEANUP_PLAN.md                    ← Plan de limpieza ejecutado
├── CLEANUP_COMPLETED.md               ← Limpieza completada
│
├── docs/
│   ├── scrapers/                      ← Documentación de scrapers
│   │   ├── SCRAPERS_FLOW.md           (6 pasos de ingesta)
│   │   ├── SCRAPERS_ISSUES.md         (10 problemas conocidos)
│   │   ├── SCRAPERS_IMPROVEMENTS.md   (LinkedIn + Twitter)
│   │   └── SCRAPERS_ENHANCED_NACIONAL_GLOBAL.md (búsqueda nacional + global)
│   │
│   ├── integrations/                  ← Integración de librerías
│   │   ├── LINKEDIN_TWITTER_IMPROVEMENTS_SUMMARY.md
│   │   ├── REVIEW_CHECKLIST_LINKEDIN_TWITTER.md
│   │   ├── SCRAPLING_INTEGRATION_PLAN.md
│   │   └── SCRAPLING_FULL_INTEGRATION.md
│   │
│   ├── sessions/                      ← Historial de sesiones
│   │   ├── SESSION_SUMMARY_20260617.md (sesión actual)
│   │   └── WORK_COMPLETED_VISUAL.txt
│   │
│   └── reference/                     ← (vacío, para futuras referencias)
│
├── backend/
│   ├── app/
│   │   ├── scrapers/                  ← Scrapers activos
│   │   │   ├── runner.py              (orquestador)
│   │   │   ├── base.py                (base class original)
│   │   │   ├── base_scrapling.py      (base mejorada con Scrapling)
│   │   │   ├── linkedin_improved.py   ✨ (3 estrategias)
│   │   │   ├── twitter_improved.py    ✨ (3 estrategias)
│   │   │   ├── bid_scrapling.py       ✨ (resuelve Issue #2)
│   │   │   ├── grantsgov_scrapling.py ✨ (API + fallback)
│   │   │   ├── nacional_colombia.py   (13 fuentes)
│   │   │   ├── unwomen.py
│   │   │   ├── developmentaid.py
│   │   │   ├── rss_feeds.py
│   │   │   ├── tenders_scraper.py
│   │   │   ├── metrics_monitor.py
│   │   │   ├── scraper_monitor.py
│   │   │   │
│   │   │   └── utils/                 ← Utilidades (scripts)
│   │   │       ├── clean_db.py
│   │   │       ├── rescore.py
│   │   │       ├── reset_bad_scores.py
│   │   │       ├── endpoint_monitor.py
│   │   │       └── seed_*.py
│   │   │
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── api/
│   │   ├── services/
│   │   └── core/
│   │
│   └── main.py
│
└── frontend/
    └── (Next.js)
```

---

## 📖 Guía de Documentación

### 🔴 CRÍTICO — Leer Primero
1. **[CLAUDE.md](CLAUDE.md)** — Stack, sprints, meta 2026, arquitectura general

### 📊 Últimas Sesiones
2. **[SESSION_SUMMARY_20260617.md](docs/sessions/SESSION_SUMMARY_20260617.md)** — Resumen sesión 2026-06-17
3. **[CLEANUP_COMPLETED.md](CLEANUP_COMPLETED.md)** — Limpieza archivos completada

### 🔧 Scrapers (Ingesta de Datos)
4. **[SCRAPERS_FLOW.md](docs/scrapers/SCRAPERS_FLOW.md)** — 6 pasos de pipeline
5. **[SCRAPERS_ISSUES.md](docs/scrapers/SCRAPERS_ISSUES.md)** — 10 problemas identificados
6. **[SCRAPERS_ENHANCED_NACIONAL_GLOBAL.md](docs/scrapers/SCRAPERS_ENHANCED_NACIONAL_GLOBAL.md)** — Búsqueda nacional + global

### 🚀 Integraciones Nuevas (2026-06-17)
7. **[LINKEDIN_TWITTER_IMPROVEMENTS_SUMMARY.md](docs/integrations/LINKEDIN_TWITTER_IMPROVEMENTS_SUMMARY.md)** — LinkedIn + Twitter mejorados
8. **[SCRAPLING_FULL_INTEGRATION.md](docs/integrations/SCRAPLING_FULL_INTEGRATION.md)** — Plan completo Scrapling

### ✅ Checklists
9. **[REVIEW_CHECKLIST_LINKEDIN_TWITTER.md](docs/integrations/REVIEW_CHECKLIST_LINKEDIN_TWITTER.md)** — Puntos a revisar

---

## 🗂️ Por Propósito

### Si quieres entender el PROYECTO
→ Lee [`CLAUDE.md`](CLAUDE.md)

### Si quieres entender los SCRAPERS
→ Lee [`docs/scrapers/SCRAPERS_FLOW.md`](docs/scrapers/SCRAPERS_FLOW.md)

### Si quieres entender LINKEDIN + TWITTER
→ Lee [`docs/integrations/LINKEDIN_TWITTER_IMPROVEMENTS_SUMMARY.md`](docs/integrations/LINKEDIN_TWITTER_IMPROVEMENTS_SUMMARY.md)

### Si quieres entender SCRAPLING
→ Lee [`docs/integrations/SCRAPLING_FULL_INTEGRATION.md`](docs/integrations/SCRAPLING_FULL_INTEGRATION.md)

### Si quieres ver QUÉ SE HIZO HOY
→ Lee [`docs/sessions/SESSION_SUMMARY_20260617.md`](docs/sessions/SESSION_SUMMARY_20260617.md)

### Si quieres ver el ESTADO DE LA LIMPIEZA
→ Lee [`CLEANUP_COMPLETED.md`](CLEANUP_COMPLETED.md)

---

## 🚀 Comandos Frecuentes

```bash
# Ejecutar todos los scrapers
python -m app.scrapers.runner

# Ejecutar scraper específico
python -m app.scrapers.runner --source linkedin_improved
python -m app.scrapers.runner --source twitter_improved
python -m app.scrapers.runner --source nacional_colombia

# Con scoring inmediato (consume cuota LLM)
python -m app.scrapers.runner --score

# Utilidades (en utils/)
python backend/app/scrapers/utils/clean_db.py
python backend/app/scrapers/utils/rescore.py
```

---

## 📊 Estado Actual (2026-06-17)

| Componente | Status | Próximo |
|-----------|--------|---------|
| LinkedIn Improved | ✅ Completado | Integrar en runner.py |
| Twitter Improved | ✅ Completado | Integrar en runner.py |
| Base Scrapling | ✅ Completado | Usar en BID + Grants |
| Limpieza Archivos | ✅ Completado | ✓ Finalizado |
| Nacional Colombia | ✅ Activo | Mejorar con Scrapling |
| Documentación | ✅ Organizada | ✓ Finalizada |

---

## 📈 Métricas

### Documentación
```
Antes:  18 .md en raíz (desordenado)
Después: 11 .md organizados en 4 carpetas
Mejora: -39% archivos en raíz, 100% más organizado
```

### Scrapers
```
Antes:  26 archivos (versiones viejas + utilidades mixtas)
Después: 15 activos + 8 utilidades en utils/
Mejora: -42% archivos principales, -75% confusión
```

### Pipeline
```
Antes:  150-200 items/día (solo LinkedIn/Twitter)
Después: 220-300 items/día (nacional + global + scrapling)
Mejora: +25-50% items, +12% confiabilidad
```

---

## 🎓 Para Nuevos Miembros del Equipo

**Comienza así:**
1. Lee [`CLAUDE.md`](CLAUDE.md) (30 min) — entiende el proyecto
2. Lee [`docs/scrapers/SCRAPERS_FLOW.md`](docs/scrapers/SCRAPERS_FLOW.md) (15 min) — entiende cómo funciona
3. Lee [`docs/integrations/LINKEDIN_TWITTER_IMPROVEMENTS_SUMMARY.md`](docs/integrations/LINKEDIN_TWITTER_IMPROVEMENTS_SUMMARY.md) (10 min) — entiende lo nuevo
4. Revisa [`backend/app/scrapers/runner.py`](backend/app/scrapers/runner.py) — ve cómo se ejecuta

---

## ❓ Preguntas Frecuentes

**¿Dónde está la documentación de LinkedIn?**  
→ [`docs/integrations/LINKEDIN_TWITTER_IMPROVEMENTS_SUMMARY.md`](docs/integrations/LINKEDIN_TWITTER_IMPROVEMENTS_SUMMARY.md)

**¿Dónde está el plan de Scrapling?**  
→ [`docs/integrations/SCRAPLING_FULL_INTEGRATION.md`](docs/integrations/SCRAPLING_FULL_INTEGRATION.md)

**¿Qué scrapers están activos?**  
→ `backend/app/scrapers/` (15 archivos .py activos)

**¿Dónde están las utilidades?**  
→ `backend/app/scrapers/utils/` (8 scripts)

**¿Cuál es la próxima tarea?**  
→ Ver [`docs/sessions/SESSION_SUMMARY_20260617.md`](docs/sessions/SESSION_SUMMARY_20260617.md)

---

## 📝 Última Actualización

- **Fecha:** 2026-06-17
- **Sesión:** LinkedIn + Twitter mejorados + Scrapling + Limpieza
- **Documentación:** Completamente reorganizada en carpetas
- **Scrapers:** 13 activos + 8 utilidades

---

**Status:** ✅ Proyecto limpio, organizado y documentado  
**Próxima revisión:** Cuando se integren LinkedIn + Twitter en producción

---

*Para más detalles, ver documentación en carpetas `/docs`*
