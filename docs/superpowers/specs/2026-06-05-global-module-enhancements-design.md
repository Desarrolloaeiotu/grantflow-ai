# Global Module Enhancements — Design Spec
**Date:** 2026-06-05  
**Scope:** 3 independent improvements to `/global` module  
**Status:** Approved for implementation

---

## Overview

Three parallel enhancements to the Global module:
1. **Advanced Filters** — Add org_type, strategic_obj, access_type dropdowns to `/global/organizations` list
2. **Real-time Strategic Analysis** — LLM-powered analysis in `/global/organizations/[id]` detail page (5 sections: Capital, Model Export, Network, Colombia, LatAm)
3. **Visual Alignment** — Update `/global/tenders` cards to match `/nacional/convocatorias` visual style

---

## 1. Advanced Filters — `/global/organizations`

### What Changes
- **Current state:** Two checkbox filters (invests_colombia, invests_latam)
- **New state:** Add 3 dropdown selects in a new row below checkboxes:
  - `org_type` (Filantropía | ONG | Multilateral | Público | Privado | EdTech)
  - `strategic_obj` (Capital | Exportación Modelo | Red | —Todos—)
  - `access_type` (Convocatoria | Mixto | Relacional | Invitación | —Todos—)

### Frontend (`frontend/app/global/organizations/page.tsx`)
- Add filter state for new dropdowns
- Build URLSearchParams with all 5 filters
- Pass to GET `/api/v1/organizations?org_type=...&strategic_obj=...&access_type=...&invests_colombia=...&invests_latam=...`
- Reset page to 1 when filters change

### Backend
- No changes required — endpoint `/api/v1/organizations` already supports these query params (verified in code)

### UI Layout
```
[Checkbox] Invierte en Colombia   [Checkbox] Invierte en Latam   [Exportar CSV]
[Dropdown org_type]   [Dropdown strategic_obj]   [Dropdown access_type]
```

---

## 2. Real-time Strategic Analysis — `/global/organizations/[id]`

### What Changes
- **New section** below "Historial" badge: "🔍 ANÁLISIS ESTRATÉGICO PARA AEIOTU"
- **5 subsections** (each with LLM-generated paragraph + explicit conclusion):
  1. **Capital** — Financia realmente? Tipo, montos, etapa → Conclusión: Alto/Medio/Bajo
  2. **Exportación del Modelo** — Interés en escalar/exportar? → Conclusión: SÍ/NO
  3. **Red (Posicionamiento)** — Asociarse posiciona? Articulación con quién? → Conclusión: SÍ (Alto/Medio/Bajo) / NO
  4. **Inversión en Colombia** — Proyectos activos? → Conclusión: Sí/No + proyecto + ciudad
  5. **Inversión en LatAm** — Qué países? Escala? → Conclusión: Prioridad Alta/Secundaria/Marginal
- **Role badge** at bottom: "🎯 ROL DOMINANTE: Capital | Exportación | Posicionamiento"

### Frontend (`frontend/app/global/organizations/[id]/page.tsx`)
- After fetching org data, trigger POST to `/api/v1/organizations/{id}/analyze`
- Show loading state: "🔍 Cargando análisis estratégico..."
- Render analysis in 5 subsections with:
  - Category title (bold)
  - Paragraph text (max 2 lines, critical tone)
  - Conclusión (bold, explicit)
- On error: show fallback "No se pudo generar análisis" (don't break page)
- Cache result in React state (don't regenerate on re-renders)

### Backend (New Endpoint)
**POST `/api/v1/organizations/{id}/analyze`**

**Input:**
```json
{
  "org_id": "uuid"
}
```

**Process:**
1. Fetch org from DB (with all fields: name, country, org_type, website, strategic_obj, access_type, general_objective, aeiotu_role, has_history, invests_colombia, invests_latam)
2. Build context string (org data + aeioTU mission brief)
3. Call Claude with structured prompt (see Prompt below)
4. Parse response JSON
5. Return 5 sections + primary_role

**Prompt Structure (to Claude):**
```
You are a strategic analyst for aeioTU (early childhood education + innovation).

ORGANIZATION DATA:
[name, country, type, objective, strategic_obj, access_type, investments, projects, etc.]

AEITU PROFILE:
[17 years, 2.3M children, 98k teachers, focus: first infancy, scaling models, policy influence, Latin America]

ANALYZE this organization for potential alliance with aeioTU.

OUTPUT (JSON only):
{
  "capital": {
    "text": "[max 2 lines, critical analysis: does it finance? grants/loans/blended? amounts? stage?]",
    "conclusion": "Alto|Medio|Bajo"
  },
  "model_export": {
    "text": "[max 2 lines: interest in scaling/exporting models beyond own country?]",
    "conclusion": "SÍ|NO"
  },
  "network": {
    "text": "[max 2 lines: does association position well? articulation with multilaterals/govs/NGOs/private?]",
    "conclusion": "SÍ (Alto|Medio|Bajo)|NO"
  },
  "colombia": {
    "text": "[max 2 lines: active projects in Colombia? if YES: name, type, location (city/dept). if NO: write explicitly 'No se evidencia presencia activa']",
    "conclusion": "Sí|No"
  },
  "latam": {
    "text": "[max 2 lines: which countries? program type, scale?]",
    "conclusion": "Prioridad|Secundaria|Marginal"
  },
  "primary_role": "capital|exportacion|posicionamiento",
  "confidence": "high|medium|low"
}
```

**Response:**
```json
{
  "org_id": "uuid",
  "analysis": {
    "capital": {...},
    "model_export": {...},
    "network": {...},
    "colombia": {...},
    "latam": {...},
    "primary_role": "capital"
  },
  "generated_at": "2026-06-05T12:34:56Z"
}
```

**Error Handling:**
- If org not found → 404
- If Claude call fails → return `{"error": "Could not generate analysis"}` (frontend shows fallback)
- Timeout: 10 seconds per request

**Rate Limiting:** No special limiting (rely on general API rate limit)

---

## 3. Visual Alignment — `/global/tenders`

### What Changes (CRITICAL — Complete Redesign)
**Current `/global/tenders` layout is table-like with minimal styling. Must transform to CARD-BASED grid matching `/nacional/convocatorias` exactly.**

#### Current Problems
- Cards are table-style (compact, list-like) instead of card grid
- No decision badges (GO/NO GO/PENDING)
- No "Afinidad aeioTU" score bar visible
- Days to deadline not prominently displayed
- No hover effects or interactivity styling
- Layout doesn't match design system

#### Target Design (Replicate Nacional)
Per card in a 3-column responsive grid:

```
┌──────────────────────────────────────┐
│                             [GO]     │  ← Badge: green (GO) / red (NO GO) / gray (PENDING)
│ LEGO Foundation Early Learning...    │  ← Title: 18px bold, dark
│ Financiador: LEGO Foundation         │  ← Funder: 12px gray
│ Lorem ipsum dolor sit amet...        │  ← Description: 12px gray, 1-2 lines max
│                                      │
│ Monto Min: $500M   Monto Max: $3B   │  ← Amounts: 2-column row, 12px
│ Cierre: 30/12/2026          178d    │  ← Deadline + days in green/orange/red
│ Afinidad aeioTU: ▓▓▓▓▓░░░░  9/10    │  ← Score bar + number
└──────────────────────────────────────┘
```

#### Exact Changes Required

**Layout Grid:**
- Change from current table/list view to: `display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))'`
- Gap: 16px between cards
- Padding per card: 20px

**Card Structure (in order):**
1. **Header Row:** Badge (top-right corner) + Decision color (GO=green, NO GO=red, PENDING=orange)
2. **Title:** 16px, fontWeight 600, color var(--text), margin 0
3. **Funder:** 12px, color var(--muted), text "Financiador: [name]"
4. **Description:** 12px, color var(--muted), max 120 chars with "..."
5. **Amounts Row:** Two columns, 12px
   - Left: "Monto Min: $[formatted]"
   - Right: "Monto Max: $[formatted]"
6. **Deadline Row:** borderTop/borderBottom 1px var(--border), padding 8px 0
   - Left: "Cierre: [date]"
   - Right: Days in colored text (green if >60, orange if 30-60, red if <30)
7. **Score Bar:** "Afinidad aeioTU:" + visual bar + number
   - Bar color: green if score >= 7, orange if 5-6, red if < 5
   - Width represents score percentage

**Styling:**
- Border: 1px var(--border)
- BorderRadius: 8px
- Background: var(--bg-subtle)
- Cursor: pointer
- Transition: all 0.2s ease
- **Hover:** borderColor → var(--primary), boxShadow → 0 4px 12px rgba(0,0,0,0.1)

**Color Functions (reuse from nacional):**
```
getTenderTypeColor(type) → #2196F3 (grant) | #FF6F00 (premio) | #9C27B0 (evento) | #4CAF50 (curso)
getDecisionColor(decision) → var(--go) | var(--no-go) | var(--info)
daysToDeadline(date) → number or null
formatCOP(amount) → string ($XXM or $XXB)
```

### Frontend Implementation
**File:** `frontend/app/global/tenders/page.tsx`

**Strategy:** Copy the card rendering logic from `/nacional/convocatorias/page.tsx` (lines 163-317) and adapt:
1. Use same grid structure and styling
2. Use same color/format functions
3. Ensure onClick routes to `/global/tenders/{id}`
4. Keep filtering/pagination logic intact (no changes)

**Key code sections to copy:**
- Card container div with grid styling
- Header with badge (decision)
- Title, funder, description
- Amounts row (Monto Min/Max)
- Deadline row with days calculation
- Score bar visualization
- Hover effects (onMouseEnter/onMouseLeave)

### No Logic Changes
- Filtering, pagination, export all remain the same
- Only visual/styling transformation

---

## Data Model Changes

### New Backend Endpoint Required
- `POST /api/v1/organizations/{id}/analyze` (see Backend section above)

### No DB Schema Changes
- Analysis is generated on-the-fly, not persisted
- If future caching needed, add `organizations.analysis_cache` (JSON) + TTL field

---

## Testing Checklist

- [ ] **Filters:** Test each filter combination (org_type + strategic_obj + access_type + geo)
- [ ] **Analysis:** Verify LLM output format is correct JSON (5 sections + role)
- [ ] **Analysis Loading:** Check loading state shows while Claude processes
- [ ] **Analysis Error:** Test with invalid org_id, network failure → fallback shows
- [ ] **Visual:** Compare `/global/tenders` side-by-side with `/nacional/convocatorias` — cards identical
- [ ] **Pagination & Export:** Verify these still work after visual changes

---

## Success Criteria

- ✅ Filters in `/global/organizations` are functional and reset page on change
- ✅ Strategic analysis appears in `/global/organizations/[id]` with 5 sections + conclusions
- ✅ Analysis loads within 5-10 seconds (Claude latency acceptable)
- ✅ Analysis error doesn't crash page
- ✅ `/global/tenders` visually matches `/nacional/convocatorias`
- ✅ All 3 features deployed and tested in dev

---

## Implementation Order (Parallel)

**Stream 1 (Filters):** Frontend filters + verify backend
**Stream 2 (Analysis):** Backend endpoint + Claude integration + Frontend display
**Stream 3 (Visual):** Copy/adapt tenders cards

All 3 can happen in parallel — no dependencies.

---

## File Changes Summary

### Frontend
- `frontend/app/global/organizations/page.tsx` — Add filter dropdowns
- `frontend/app/global/organizations/[id]/page.tsx` — Add analysis section + fetch
- `frontend/app/global/tenders/page.tsx` — Update card visual (copy from nacional)

### Backend
- `backend/app/api/organizations.py` — Add POST `/analyze` endpoint
- `backend/app/services/analysis_service.py` — New module for Claude integration + prompt

---

## Notes

- Analysis is **not cached** (generated fresh each page load) — acceptable for MVP, add caching in v2 if needed
- Prompt to Claude is deterministic but not guaranteed identical output each time
- If org data is sparse/incomplete, Claude analysis will note gaps explicitly (as per design requirement)
