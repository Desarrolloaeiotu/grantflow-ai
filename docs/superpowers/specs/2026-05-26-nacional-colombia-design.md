# Diseño: Página Nacional Colombia con 4 Secciones

**Fecha:** 26 de mayo de 2026  
**Usuario:** Equipo de Alianzas Internacionales  
**Objetivo:** Crear un centro de control para prospección y gestión de oportunidades nacionales colombianas

---

## 1. Resumen Ejecutivo

La página Nacional Colombia (`/nacional`) será refactorizada para incluir 4 secciones especializadas que permitan al equipo de Alianzas monitorear, analizar y gestionar oportunidades de financiamiento detectadas por el scraper nacional_colombia.

**Estructura:** Sidebar de navegación + contenido principal  
**Tecnología:** Next.js 15 Server Components + Server Actions  
**Datos:** API FastAPI ← Supabase (oportunidades, contactos del scraper)  
**Alcance:** Fase inicial con 4 secciones, extensible a acciones adicionales

---

## 2. Usuario Target

**Rol:** Equipo de Alianzas Internacionales (gestor de oportunidades, analista nacional)

**Necesidades:**
- Monitorear vencimientos críticos de convocatorias nacionales
- Ver panorama completo de oportunidades detectadas (cantidad, estado, distribución)
- Gestionar oportunidades en el pipeline (cambiar estado, agregar notas)
- Mantener contactos de financiadores nacionales y registrar interacciones

**Frecuencia de uso:** Diaria (revisión de alertas) a semanal (análisis de radar/pipeline)

---

## 3. Arquitectura Técnica

### 3.1 Stack Tecnológico
```
Frontend: Next.js 15 App Router (Server Components)
├─ Rendering: Server Components (datos frescos)
├─ Interacción: Server Actions (cambios de estado)
├─ Styling: Tailwind CSS + variables CSS existentes (globals.css)
└─ State: No hay estado persistente en cliente (servidor es fuente de verdad)

Backend: FastAPI
├─ GET /api/v1/opportunities (filtrar por market_window=funding_colombia)
├─ GET /api/v1/contacts (filtrar por región)
├─ PATCH /api/v1/opportunities/{id}/status
└─ POST /api/v1/opportunities/{id}/notes

Data: Supabase PostgreSQL
├─ opportunities (detectadas por scraper nacional_colombia)
├─ contacts (extraídos y verificados por Apollo.io)
└─ score_log (scoring automático con criterios aeioTU)
```

### 3.2 Flujo de Datos
```
1. Carga inicial: Server Component renderiza, fetcha datos frescos
2. Usuario interactúa: Server Action (cambiar estado, agregar nota)
3. Server Action: PATCH a FastAPI → Supabase actualiza
4. Revalidación: Next.js invalida caché → componente re-renderiza
5. Usuario ve cambios: datos frescos sin refetch manual
```

### 3.3 Estructura de Carpetas
```
frontend/app/nacional/
├── page.tsx                         # Página principal (renderiza sidebar + sección activa)
├── layout.tsx                       # Layout específico de nacional (hereda de root)
├── components/
│   ├── NacionalSidebar.tsx         # Navegación lateral (4 opciones + badges)
│   ├── AlertasSection.tsx          # Sección Alertas (vencimientos + cambios)
│   ├── RadarSection.tsx            # Sección Radar (overview + gráfico + tabla)
│   ├── PipelineSection.tsx         # Sección Pipeline (tabla + expandibles)
│   ├── ContactosSection.tsx        # Sección Contactos (tarjetas + tabla)
│   └── shared/
│       ├── FilterBar.tsx           # Barra de filtros (estado, urgencia, financiador, sector)
│       ├── OpportunityCard.tsx     # Tarjeta de oportunidad (reutilizable)
│       ├── ExpandableRow.tsx       # Fila expandible (notas, historial, acciones)
│       └── LoadingState.tsx        # Skeleton/loader mientras carga
├── actions/
│   └── nacional-actions.ts         # Server Actions (cambios de estado, notas, contactos)
└── data/
    └── nacional-queries.ts         # Funciones fetch para API (reutilizables)
```

---

## 4. Secciones (Detalle)

### 4.1 Alertas
**Propósito:** Ver qué requiere acción inmediata

**Dos subsecciones:**

#### A) Vencimientos próximos
- Agrupar por urgencia:
  - 🔴 Vence en 7 días
  - 🟠 Vence en 15 días
  - 🟡 Vence en 30 días
- Cada tarjeta muestra: `[Oportunidad] [Financiador] [Fecha vencimiento] [Estado] [Botón "Revisar"]`
- Ordenadas por fecha (más próximas primero)

#### B) Cambios recientes
- Timeline de eventos:
  - 🟢 Nueva oportunidad detectada
  - 🔵 Estado cambió a "revisada"
  - 🟣 Contacto verificado por Apollo.io
  - ⚪ Nota agregada
- Últimas 10 eventos, con timestamp
- Filtrable por tipo de evento

**Acciones:**
- Clic en tarjeta/evento → abre modal de detalle con opción de cambiar a "revisada"

**Componentes:**
- `VencimientosCard.tsx` (tarjeta individual)
- `EventTimeline.tsx` (lista de cambios)

---

### 4.2 Radar
**Propósito:** Ver panorama completo de oportunidades nacionales detectadas

**Tres capas:**

#### A) Cards de resumen (4 cards principales)
```
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│  Detectadas     │   Revisadas     │  En Gestión     │   Cerradas      │
│      45         │       12        │       8         │        2        │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
```

#### B) Gráfico principal (seleccionable)
- Vista 1: Distribución por Financiador (pie chart)
  - ICBF | MinEducación | CAFAM | Cajas de Compensación | Gobernaciones | Otros
- Vista 2: Distribución por Sector (bar chart)
  - Educación privada | Tercer sector/Educación | Gobierno | Otros
- Toggle para cambiar entre vistas

#### C) Tabla interactiva con filtros
**Columnas:** Oportunidad | Financiador | Estado | Urgencia | Monto COP | Deadline

**Filtros operativos:**
- Estado: Detectada | Revisada | En gestión
- Urgencia: 7 días | 15 días | 30 días
- Financiador: dropdown (ICBF, MinEducación, CAFAM, etc.)
- Sector: Educación privada | Tercer sector | Gobierno

**Fila expandible:**
```
[Oportunidad Name]  [ICBF]  [Revisada]  [7 días]  [$400M]  [15 ago]  [▼]
└─ Descripción: ...
   Notas: ...
   [Botón "Cambiar estado"] [Botón "Agregar nota"] [Botón "Marcar prioridad"]
```

**Acciones:**
- Cambiar estado: Detectada → Revisada → En gestión
- Agregar notas con timestamp
- Marcar como prioridad (⭐)

---

### 4.3 Pipeline
**Propósito:** Ver oportunidades en gestión activa (seguimiento detallado)

**Tabla principal:**
**Columnas:** Oportunidad | Financiador | Monto | Deadline | Estado | % Avance | Responsable

**Estados del Pipeline:**
1. Revisada (inicial)
2. Propuesta (enviada)
3. Negociación (en conversaciones)
4. Cierre (documento final)

**Fila expandible (click para expandir):**
```
[Oportunidad]  [Financiador]  [$2.5B]  [30 ago]  [Propuesta]  [60%]  [Luis M.]  [▼]
├─ Descripción completa
├─ Notas internas (historial de cambios):
│  - 20 ago: Cambió a "Propuesta" por Luis M.
│  - 18 ago: Nota: "Enviada propuesta v2"
│  - 15 ago: Cambió a "Revisada" por María G.
├─ Próximos pasos: Esperar feedback del ICBF
└─ Botones de acción:
   [Cambiar estado ▼] [Agregar nota] [Asignar responsable ▼]
```

**Filtros operativos:**
- Estado: Revisada | Propuesta | Negociación | Cierre
- Urgencia: 7 días | 15 días | 30 días
- Financiador: dropdown
- Sector: dropdown

**Acciones:**
- Cambiar estado: Revisada → Propuesta → Negociación → Cierre
- Agregar nota con timestamp
- Asignar responsable (usuario del equipo)

---

### 4.4 Contactos
**Propósito:** Mantener red de decisores nacionales y registrar interacciones

**Estructura: Tarjetas por financiador con tabla dentro**

```
┌─ Financiador: ICBF ───────────────────────────────┐
│  Directora: María López                           │
│  Email: maria.lopez@icbf.gov.co ✓ (verificado)  │
│  Cargo: Directora de Innovación                  │
│  Última interacción: 15 ago (Llamada)            │
│  [Botón: Contactar] [Agregar nota] [Historial]  │
│                                                   │
│  Especialista: Carlos Ruiz                       │
│  Email: carlos.ruiz@icbf.gov.co ✓                │
│  Cargo: Especialista en ECD                      │
│  Última interacción: 20 ago (Email)              │
│  [Botón: Contactar] [Agregar nota] [Historial]  │
└───────────────────────────────────────────────────┘

┌─ Financiador: MinEducación ───────────────────────┐
│  ... (similar)
└───────────────────────────────────────────────────┘
```

**Por contacto:**
- Nombre | Cargo | Email (con verificación Apollo.io ✓/✗) | LinkedIn (si disponible)
- Última interacción: tipo (Llamada | Email | Reunión) + fecha
- Historial expandible: todas las interacciones registradas

**Filtros:**
- Financiador: dropdown (ICBF, MinEducación, CAFAM, etc.)
- Verificación: Solo verificados | Todos
- Sector: dropdown

**Acciones:**
- Marcar como "Contactado" (registra timestamp y tipo)
- Agregar/editar email alternativo
- Agregar nota sobre interacción (con timestamp)
- Ver historial de interacciones

---

## 5. Server Actions (Interacciones)

**Archivo:** `frontend/app/nacional/actions/nacional-actions.ts`

```typescript
// 1. Cambiar estado de oportunidad
export async function cambiarEstadoOportunidad(
  opportunityId: string,
  nuevoEstado: 'detectada' | 'revisada' | 'in_crm' | 'cerrada'
): Promise<{ success: boolean; error?: string }>

// 2. Agregar nota a oportunidad
export async function agregarNotaOportunidad(
  opportunityId: string,
  nota: string
): Promise<{ success: boolean; error?: string }>

// 3. Marcar oportunidad como prioridad
export async function marcarPrioridad(
  opportunityId: string,
  isPriority: boolean
): Promise<{ success: boolean; error?: string }>

// 4. Marcar contacto como "contactado"
export async function marcarContactado(
  contactId: string,
  tipoInteraccion: 'llamada' | 'email' | 'reunion',
  nota?: string
): Promise<{ success: boolean; error?: string }>

// 5. Agregar email alternativo a contacto
export async function agregarEmailAlternativo(
  contactId: string,
  email: string
): Promise<{ success: boolean; error?: string }>

// 6. Asignar responsable a oportunidad
export async function asignarResponsable(
  opportunityId: string,
  responsableEmail: string
): Promise<{ success: boolean; error?: string }>
```

**Flujo de ejecución:**
```
1. Usuario hace clic en botón (ej. "Cambiar a Revisada")
2. Form client-side submite → invoca Server Action
3. Server Action hace PATCH a FastAPI backend
4. Backend valida y actualiza Supabase
5. Next.js invalida caché (revalidatePath)
6. Component re-renderiza con datos frescos
7. Usuario ve cambio reflejado al instante
```

---

## 6. Navegación y URLs

**Base:** `http://localhost:3000/nacional`

**Parámetro de query:** `?section=<nombre>`

- `?section=alertas` → Alertas
- `?section=radar` → Radar (default)
- `?section=pipeline` → Pipeline
- `?section=contactos` → Contactos

**Ejemplo:** `http://localhost:3000/nacional?section=pipeline`

---

## 7. Fuente de Datos (Scraper)

**El scraper `nacional_colombia.py`:**
- Detecta oportunidades de: ICBF, MinEducación, SECOP, CAFAM, Cajas de Compensación
- Guarda con `market_window = 'funding_colombia'` y `source_name = 'nacional_colombia'`
- Extrae contactos (CEO, especialistas) y los verifica con Apollo.io
- Genera embeddings para búsqueda semántica

**Las 4 secciones consumen:**
- **Alertas:** Oportunidades donde `deadline <= NOW() + 30 días`
- **Radar:** Todas las oportunidades con `market_window = 'funding_colombia'`
- **Pipeline:** Oportunidades con `status IN ('revisada', 'in_crm', 'cerrada')`
- **Contactos:** Contactos con `funder` en lista de financiadores nacionales

---

## 8. Componentes Reutilizables

```
shared/FilterBar.tsx
├─ Props: activeFilters, onFilterChange, availableOptions
├─ Renderiza: 4 dropdowns (Estado | Urgencia | Financiador | Sector)
└─ Callback: notifica cambios de filtros al parent

shared/ExpandableRow.tsx
├─ Props: content, expandedContent, actions
├─ Renderiza: fila + chevron para expandir
└─ Callback: invoca Server Actions al hacer clic en botones

shared/OpportunityCard.tsx
├─ Props: opportunity, onStateChange, onPriority
└─ Renderiza: tarjeta con badges (urgencia, estado, prioridad)

shared/LoadingState.tsx
├─ Skeleton loaders para tabla, cards, gráficos
└─ Renderiza durante fetch inicial
```

---

## 9. Estilos y Diseño

**Color scheme (aeioTU):**
- Primario: azul celeste (#0099cc)
- Alertas: rojo (#e63946) para 7 días, naranja (#f77f00) para 15 días, amarillo (#fcbf49) para 30 días
- Success: verde (#06a77d)
- Fondo: blanco + gris perla (#f5f5f5)

**Componentes existentes a reutilizar:**
- Variables CSS de `globals.css` (--go, --nogo, --text, --bg3, etc.)
- Tipografía: Inter (body), JetBrains Mono (data)
- Breakpoints: responsive en tablet + mobile

**Responsive:**
- Sidebar: ocultar en mobile (hamburger menu)
- Tablas: scroll horizontal en mobile
- Gráficos: adaptarse a width disponible

---

## 10. Errores y Manejo

**Server Actions pueden fallar. Manejamos:**
```
try {
  PATCH /api/v1/opportunities/{id}/status
} catch (error) {
  return { success: false, error: error.message }
}

UI muestra: "❌ Error al cambiar estado. Intenta de nuevo."
```

**No se replica cambio sin confirmación del servidor.**

---

## 11. Testing (Enfoque)

**Manual (fase inicial):**
- Verificar que Alertas muestra vencimientos correctos
- Verificar que Radar calcula distribuciones correctamente
- Verificar que cambiar estado actualiza Pipeline
- Verificar que marcar "contactado" registra timestamp

**Automatizado (futura):**
- Tests de Server Actions (cambios de estado, notas)
- Tests de queries (filtros funcionan)
- Tests de UI (filtros responden correctamente)

---

## 12. Próximos Pasos (Fuera de Alcance Inicial)

- [ ] Exportar datos de Pipeline a CSV/Excel para CRM
- [ ] Dashboard Metabase conectado a métricas nacionales
- [ ] Notificaciones en tiempo real (Slack) de vencimientos
- [ ] Integración con calendario (Google Calendar) para deadlines
- [ ] Búsqueda full-text en oportunidades y contactos

---

## 13. Dependencias y Supuestos

**Dependencias:**
- FastAPI backend con endpoints de oportunidades, contactos, scoring
- Supabase con tablas `opportunities`, `contacts`, `score_log` pobladas
- Scraper `nacional_colombia` activo y ejecutándose diariamente

**Supuestos:**
- El equipo de Alianzas tiene permisos para editar estado y notas
- Contactos ya están verificados por Apollo.io (email_verified = true/false)
- Monto en COP es disponible para filtrado y visualización
- URL del modal/detalle de oportunidad está documentada

---

**Documento finalizado. Listo para implementación.**
