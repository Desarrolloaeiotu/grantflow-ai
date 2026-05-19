# Sprint S6 — Preparación (Semanas 11-12)

**Objetivo:** Metabase Dashboard + Exportación CSV para CRM  
**Duración estimada:** 2-3 sesiones de 2-3 horas  
**Fecha objetivo:** Finales de junio 2026

---

## 📋 Checklist Antes de S6

### ✅ Validación de S5 (Haz esto primero)

- [ ] Dashboard abierto en http://localhost:3000
- [ ] Ves 816 oportunidades en el grid
- [ ] Filtros funcionan (GO, Global, etc.)
- [ ] Backend activo en localhost:8000
- [ ] Ver documentación creada:
  - [ ] `SPRINT_S5_SUMMARY.md` (resumen ejecutivo)
  - [ ] `QUICKSTART_TEAM.md` (guía para Alianzas)
  - [ ] `TECHNICAL_REFERENCE.md` (docs técnicas)

### ✅ Preparación Backend

- [ ] `backend/docs/apollo_integration.md` leído
- [ ] API Key de Apollo.io obtenida (si aplica)
- [ ] `.env` actualizado con `APOLLO_API_KEY` (opcional Mes 5+)
- [ ] Backend compilado: `python -m py_compile app/api/opportunities.py`

### ✅ Preparación Frontend

- [ ] Frontend dev server corriendo en localhost:3000
- [ ] Acceso a `frontend/.env.local` confirmado
- [ ] CSS/styling validado en navegador (sin errores)

---

## 🚀 Tareas para S6

### Frente 1: Metabase Dashboard (Estimado: 6-8 horas)

**Objetivo:** Dashboard visual de oportunidades en Metabase

#### 1.1 — Instalar & Conectar Metabase
```bash
# Docker
docker run -d -p 3001:3000 --name metabase metabase/metabase

# O: descarga desde https://www.metabase.com/download
```

#### 1.2 — Conectar a Supabase/PostgreSQL
- Setup de Metabase → Database → PostgreSQL
- Connection string: `postgresql://postgres:password@db.supabase.co:5432/postgres`
- Test connection

#### 1.3 — Crear Dashboards (Presets recomendados)

**Dashboard 1: Pipeline Overview**
```
Título: "GrantFlow — Pipeline Activo"

Cards:
1. Gauge: Total GO (Métrica: COUNT donde decision='go')
2. Number: Promedio score (AVG(score_total) donde decision='go')
3. Gauge: Contactos verificados (SUM(org_email_verified + ceo_email_verified))
4. Bar Chart: Opps por ventana (COUNT GROUP BY market_window)
5. Line Chart: Opps detectadas por día (COUNT GROUP BY DATE(detected_at))
6. Table: Top 10 GO por score DESC
```

**Dashboard 2: Scoring Analysis**
```
Título: "Análisis de Scoring"

Cards:
1. Scatter plot: Score total vs Days to deadline
2. Bar chart: Distribution de scores (0-10)
3. Pie chart: Decision distribution (GO/Pending/No-Go)
4. Table: Opps por criterio C1-C5 (qué falla)
5. Heatmap: Score vs Ventana vs Urgencia
```

**Dashboard 3: Contacts**
```
Título: "Estado de Contactos"

Cards:
1. Number: Total emails verificados
2. Number: Total emails pendientes
3. Table: Opps sin CEO (para enriquecer con Apollo)
4. Pie chart: Email verification rate
5. Trend: Nuevos emails verificados por día
```

---

### Frente 2: Exportación CSV/Excel (Estimado: 4-6 horas)

**Objetivo:** Endpoint que exporte oportunidades para importar a CRM

#### 2.1 — Crear Endpoint
```python
# backend/app/api/opportunities.py

@router.get("/export")
async def export_opportunities(
    format: str = Query("csv", regex="^(csv|xlsx)$"),
    decision: str | None = Query("go"),
    verified_only: bool = Query(False),
    db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    """
    Exporta oportunidades a CSV o XLSX.
    
    Uso:
        GET /api/v1/opportunities/export?format=csv&decision=go
        GET /api/v1/opportunities/export?format=xlsx&verified_only=true
    """
    # Query opportunities
    # Format as CSV/XLSX
    # Return StreamingResponse
```

#### 2.2 — Campos a Incluir en Export
```
Columnas recomendadas:
- title
- funder_name
- market_window
- amount_max_cop
- deadline
- days_to_deadline (calculado)
- ceo_name
- ceo_email
- ceo_email_verified ✓/✗
- ceo_title
- ceo_linkedin_url
- org_email
- org_email_verified ✓/✗
- org_website
- score_total
- decision (GO/Pending/No-Go)
- urgency
- url_rfp (link a convocatoria)
- detected_at
- status
```

#### 2.3 — Testing
```bash
# Test CSV
curl http://localhost:8000/api/v1/opportunities/export?format=csv > opp.csv

# Test XLSX
curl http://localhost:8000/api/v1/opportunities/export?format=xlsx > opp.xlsx

# Abrir en Excel y validar
```

---

## 🎯 Para Hacer Después de S6

### S7 — QA & Ajustes (2-3 semanas)
- [ ] Pruebas con equipo de Alianzas
- [ ] Validar scoring retrospectivo (recall ≥70%)
- [ ] Prueba real de Apollo.io (con API key)
- [ ] Feedback y ajustes
- [ ] Documentación de lecciones aprendidas

### S8 — Lanzamiento MVP
- [ ] Onboarding oficial del equipo
- [ ] Capacitación en dashboard y exports
- [ ] Setup de n8n workflows automáticos
- [ ] Monitoreo en producción

---

## 📚 Recursos Útiles

### Documentación Generada en S5
- `SPRINT_S5_SUMMARY.md` — Qué se completó
- `QUICKSTART_TEAM.md` — Manual de usuario
- `TECHNICAL_REFERENCE.md` — APIs y arquitectura
- `backend/docs/apollo_integration.md` — Apollo.io detalles

### Librerías para S6
```python
# Para Metabase
# (Integración nativa — solo configurar)

# Para Excel/CSV
pip install pandas openpyxl
# O usar librería FastAPI nativa
```

### Comandos útiles
```bash
# Backend
cd backend && python -m uvicorn app.main:app --reload

# Frontend
cd frontend && npm run dev

# Metabase
docker run -d -p 3001:3000 metabase/metabase

# Testing
make test  # (si existe Makefile)
```

---

## 🔗 Links Importantes

- **Dashboard:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **Metabase (S6):** http://localhost:3001
- **Supabase:** https://supabase.com/dashboard
- **Apollo.io:** https://app.apollo.io (Mes 5+)
- **GitHub:** (repo del proyecto)

---

## 📝 Notas de Diseño para S6

### Metabase
- Usar tema oscuro para consistencia con dashboard
- Filtros dinámicos por ventana/decisión/urgencia
- Auto-refresh cada 1 hora (no más — economizar recursos)
- Crear alertas para: "Nuevas opps GO detectadas"

### Exportación
- Default: Solo GO verificados
- Opción: Incluir Pending (para revisión interna)
- Nunca exportar No-Go (menos ruido)
- Incluir link directo a RFP en cada fila

---

## 🚦 Puntos de Decisión S6

**Pregunta 1:** ¿Metabase self-hosted o SaaS?  
→ Recomendación: Self-hosted (control total, economía)

**Pregunta 2:** ¿Excel solo o también Google Sheets?  
→ Recomendación: Excel/CSV (simplicidad); Sheets requiere API Google

**Pregunta 3:** ¿Exportación manual o automática (email weekly)?  
→ Recomendación: Manual + opción de mail vía n8n (S8)

---

## ✉️ Próxima Sesión

**Cuando estés listo para S6:**
1. Lee estos 3 documentos:
   - `SPRINT_S5_SUMMARY.md`
   - `QUICKSTART_TEAM.md`
   - `TECHNICAL_REFERENCE.md`
2. Valida que todo funcione (checklist arriba)
3. Avísame y comenzamos S6

**Estimado:** 2-3 sesiones de 2-3 horas c/u

---

**Documentación generada:** 12 mayo 2026  
**Autor:** Claude Code + Development Team  
**Estado:** Listo para S6
