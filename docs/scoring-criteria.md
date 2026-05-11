# Criterios de scoring — GrantFlow AI

**Regla de oro:** Una oportunidad es **Go** si `score_total >= 6` (de 10 posibles).

## Los 5 criterios

| Criterio | Nombre | Método | Peso |
|----------|--------|--------|------|
| C1 | Alineación estratégica | LLM (Claude) | 0–2 pts |
| C2 | Ajuste del modelo | LLM (Claude) | 0–2 pts |
| C3 | Coherencia del ticket | Regla | 0–2 pts |
| C4 | Viabilidad operativa | Regla | 0–2 pts |
| C5 | Potencial relacional | Regla | 0–2 pts |

## Detalle por criterio

### C1 — Alineación estratégica
- **2:** Financiador apoya claramente educación inicial, primera infancia o ECD
- **1:** Alineación parcial (educación general, desarrollo social, infancia)
- **0:** Sin alineación con el mandato de aeioTU

### C2 — Ajuste del modelo
- **2:** Prioriza explícitamente modelos escalables, replicables o de transferencia
- **1:** Apertura implícita a modelos sistémicos o de impacto estructural
- **0:** Proyectos puntuales sin escala o transferencia

### C3 — Coherencia del ticket
Rango viable aeioTU: **COP $400M – $5.000M**
- **2:** Dentro del rango ideal
- **1:** ±30% del rango (COP $280M–$6.500M)
- **0:** Fuera del rango

### C4 — Viabilidad operativa
- **2:** Más de 60 días para el cierre
- **1:** 30–60 días para el cierre
- **0:** Menos de 30 días

### C5 — Potencial relacional
- **2:** Financiador tiene historial con aeioTU (`has_history = true`)
- **1:** Financiador está en la lista de objetivos estratégicos 2026
- **0:** Financiador nuevo/desconocido

## Tabla de decisión

| Score total | Decisión |
|------------|---------|
| 6–10 | **Go** — aplicar |
| 4–5 | **Pending** — revisar manualmente |
| 0–3 | **No Go** — descartar |

## Financiadores estratégicos 2026 (C5 = 1 pt)
LEGO Foundation, Grand Challenges Canada, Fundación Hilton, Fundación Cargill, BID, IADB, Fundación Ford, USAID, GIZ, ONU Mujeres, UNICEF, Fundación Gates, Luminate
