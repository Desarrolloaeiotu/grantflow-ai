# GrantFlow AI — Documentación Completa

> Centro de documentación para GrantFlow AI  
> Actualizado: Mayo 21, 2026

---

## 📚 Guías por Rol

### 👥 Para Usuarios Finales

**[AGENT_QUICKSTART.md](./AGENT_QUICKSTART.md)** — *10 minutos de lectura*

Cómo usar GrantFlow Asistente en el dashboard:
- ✅ Dónde encontrar el botón 💬
- ✅ Ejemplos de preguntas por categoría
- ✅ Cómo cargar archivos
- ✅ FAQ y solución de problemas

**Ideal para:** Usuarios del dashboard, gerentes de Alianzas, analistas

---

### 💻 Para Desarrolladores

**[AGENT_INTEGRATION.md](./AGENT_INTEGRATION.md)** — *20 minutos de lectura*

Arquitectura y componentes técnicos:
- ✅ Stack tecnológico completo
- ✅ Componentes: backend, frontend, API routes
- ✅ Flujos de orquestación agentic
- ✅ API reference de todos los endpoints
- ✅ Herramientas disponibles (tool_use)
- ✅ Troubleshooting técnico
- ✅ Próximas fases

**Ideal para:** Developers full-stack, arquitectos, tech leads

**[AGENT_SETUP.md](./AGENT_SETUP.md)** — *15 minutos de lectura*

Configuración del ambiente de desarrollo:
- ✅ Requisitos previos
- ✅ Obtener API key de Anthropic
- ✅ Paso a paso: backend + frontend
- ✅ Verificación del setup
- ✅ Debug mode
- ✅ Comandos útiles

**Ideal para:** Desarrolladores nuevos, DevOps, QA, CI/CD

---

### 📊 Para Project Managers / Product Owners

**[SPRINT_S5_AGENT_WEB.md](./SPRINT_S5_AGENT_WEB.md)** — *15 minutos de lectura*

Resumen del sprint S5+:
- ✅ Objetivo y completados
- ✅ Cambios por archivo
- ✅ Métricas del proyecto
- ✅ Limitaciones conocidas
- ✅ Próximas fases (S6, S7, etc.)
- ✅ Timeline estimado

**Ideal para:** Product managers, project leads, stakeholders

---

## 📖 Documentación por Módulo

### Backend

| Documento | Descripción | Lectura |
|-----------|-------------|---------|
| [AGENT_INTEGRATION.md#backend](./AGENT_INTEGRATION.md#21-backend-backendappapichatpy) | Endpoint `/api/v1/chat` con orquestación agentic | 5 min |
| [AGENT_INTEGRATION.md#herramientas](./AGENT_INTEGRATION.md#6-herramientas-disponibles-tool-use) | 4 herramientas disponibles: get_opportunities, search_funders, search_knowledge, generate_proposal | 5 min |
| [AGENT_SETUP.md#backend](./AGENT_SETUP.md#2-paso-2-configurar-variables-de-entorno) | Configurar ANTHROPIC_API_KEY | 2 min |

### Frontend

| Documento | Descripción | Lectura |
|-----------|-------------|---------|
| [AGENT_INTEGRATION.md#frontend](./AGENT_INTEGRATION.md#22-frontend-frontendappcomponentsagentpaneltsx) | Componente AgentPanel: UI, estado, flujo | 8 min |
| [AGENT_INTEGRATION.md#api-route](./AGENT_INTEGRATION.md#23-nextjs-api-route-frontendappchatroutets) | Proxy API Route | 2 min |
| [AGENT_INTEGRATION.md#estilos](./AGENT_INTEGRATION.md#24-estilos-css-frontendappglobalscss) | Clases CSS del panel | 3 min |

### Configuración

| Documento | Descripción | Lectura |
|-----------|-------------|---------|
| [AGENT_SETUP.md](./AGENT_SETUP.md) | Setup completo: obtener key, configurar .env, iniciar servicios | 15 min |
| [AGENT_SETUP.md#verificar](./AGENT_SETUP.md#-paso-4-verificar-setup) | Checklist de verificación | 5 min |
| [AGENT_SETUP.md#troubleshooting](./AGENT_SETUP.md#-troubleshooting-de-setup) | Solución de problemas comunes | 3 min |

---

## 🎯 Guías Rápidas

### "Quiero usar el agente ahora"

1. Lee: [AGENT_QUICKSTART.md](./AGENT_QUICKSTART.md) (5 min)
2. Abre: http://localhost:3001
3. Haz clic en botón 💬
4. Escribe una pregunta

### "Quiero entender la arquitectura"

1. Lee: [AGENT_INTEGRATION.md#arquitectura](./AGENT_INTEGRATION.md#1-resumen-ejecutivo) (3 min)
2. Lee: [AGENT_INTEGRATION.md#componentes](./AGENT_INTEGRATION.md#2-componentes-técnicos) (10 min)
3. Revisa: Código en `backend/app/api/chat.py` (10 min)

### "Quiero configurar el ambiente"

1. Obtén API key: [AGENT_SETUP.md#paso-1](./AGENT_SETUP.md#-paso-1-obtener-api-key-de-anthropic)
2. Configura: [AGENT_SETUP.md#paso-2](./AGENT_SETUP.md#-paso-2-configurar-variables-de-entorno)
3. Inicia: [AGENT_SETUP.md#paso-3](./AGENT_SETUP.md#-paso-3-iniciar-servicios)
4. Verifica: [AGENT_SETUP.md#paso-4](./AGENT_SETUP.md#-paso-4-verificar-setup)

### "Algo no funciona"

1. Revisa: [AGENT_SETUP.md#troubleshooting](./AGENT_SETUP.md#-troubleshooting-de-setup)
2. O lee: [AGENT_QUICKSTART.md#faq](./AGENT_QUICKSTART.md#-preguntas-frecuentes)
3. O revisa: [AGENT_INTEGRATION.md#troubleshooting](./AGENT_INTEGRATION.md#7-troubleshooting)

---

## 🔗 Índice de Archivos Documentados

### Backend

```
backend/
├── main.py                        ← Registra chat router (2 líneas modificadas)
└── app/
    └── api/
        ├── chat.py               ← Nuevo: Endpoint agentic (244 líneas)
        ├── opportunities.py       ← Usado por: get_opportunities tool
        ├── contacts.py           ← Usado por: verify_email tool
        └── rag.py                ← Usado por: search_knowledge tool
```

### Frontend

```
frontend/
├── app/
│   ├── layout.tsx                ← Importa AgentPanel (2 líneas modificadas)
│   ├── globals.css               ← Estilos del panel (114 líneas nuevas)
│   ├── api/
│   │   └── chat/
│   │       └── route.ts          ← Nuevo: Proxy API (35 líneas)
│   └── components/
│       └── AgentPanel.tsx        ← Nuevo: Componente UI (143 líneas)
```

### Documentación

```
docs/
├── README.md                      ← Este archivo
├── AGENT_INTEGRATION.md           ← Guía técnica completa (400+ líneas)
├── AGENT_QUICKSTART.md            ← Guía para usuarios (200+ líneas)
├── AGENT_SETUP.md                 ← Setup guide (300+ líneas)
└── SPRINT_S5_AGENT_WEB.md         ← Sprint summary (300+ líneas)
```

---

## 🔐 Requisitos Antes de Usar

**Absolutamente necesario:**
- [ ] ANTHROPIC_API_KEY configurada en `backend/.env`
- [ ] Backend corriendo: `python -m uvicorn main:app --reload --port 8000`
- [ ] Frontend corriendo: `npm run dev` (puerto 3000 o 3001)

**Recomendado:**
- [ ] Haber leído [AGENT_QUICKSTART.md](./AGENT_QUICKSTART.md)
- [ ] Haber ejecutado el checklist en [AGENT_SETUP.md#paso-4](./AGENT_SETUP.md#-paso-4-verificar-setup)

---

## 🚀 Próximas Fases Documentadas

### Sprint S6 (Mes 6)

- [ ] Procesamiento de documentos (PDF upload + RAG)
- [ ] Generación completa de propuestas
- [ ] Persistencia de chat history
- [ ] Dashboard Metabase

**Documentación:** Ver [AGENT_INTEGRATION.md#próximos-pasos](./AGENT_INTEGRATION.md#8-próximos-pasos)

### Sprint S7 (Mes 7)

- [ ] Autenticación JWT
- [ ] Historiales por usuario
- [ ] Rate limiting
- [ ] Integración CRM

**Documentación:** Ver [AGENT_SETUP.md#producción](./AGENT_SETUP.md#-en-producción-futuro)

---

## 📊 Estadísticas de Documentación

| Métrica | Valor |
|---------|-------|
| Documentos nuevos | 4 |
| Líneas de documentación | 1200+ |
| Guías de usuario | 1 |
| Guías técnicas | 1 |
| Guías de setup | 1 |
| Sprint summaries | 1 |
| Ejemplos de código | 30+ |
| Diagramas ASCII | 3 |
| Checklists | 5+ |
| FAQs | 10+ |

---

## 🎨 Convenciones de Documentación

### Encabezados

```markdown
# H1 — Título del documento (1 por doc)
## H2 — Secciones principales
### H3 — Subsecciones
#### H4 — Detalles (raramente usado)
```

### Bloques Especiales

```markdown
> **Nota:** Información adicional o contexto
> **Advertencia:** Algo a tener en cuenta
> **Importante:** Crítico para entender

🎯 Objetivos
✅ Completado/Checklist
⚠️ Advertencias
📚 Referencias
💡 Tips
```

### Código

```markdown
# Comandos de terminal
bash/powershell code

# JSON examples
{"example": "value"}

# TypeScript/Python snippets
export default function Component() { }
```

---

## 🔍 Cómo Encontrar Información

### Por Pregunta

**"¿Cómo uso el asistente?"**
→ [AGENT_QUICKSTART.md](./AGENT_QUICKSTART.md)

**"¿Cómo está hecho?"**
→ [AGENT_INTEGRATION.md](./AGENT_INTEGRATION.md)

**"¿Cómo configuro mi ambiente?"**
→ [AGENT_SETUP.md](./AGENT_SETUP.md)

**"¿Qué se hizo en este sprint?"**
→ [SPRINT_S5_AGENT_WEB.md](./SPRINT_S5_AGENT_WEB.md)

### Por Rol

| Rol | Documento | Lectura |
|-----|-----------|---------|
| Usuario final | AGENT_QUICKSTART | 10 min |
| Developer backend | AGENT_INTEGRATION | 20 min |
| Developer frontend | AGENT_INTEGRATION | 20 min |
| DevOps / Setup | AGENT_SETUP | 15 min |
| Project Manager | SPRINT_S5_AGENT_WEB | 15 min |

### Por Componente

| Componente | Documento | Sección |
|------------|-----------|---------|
| AgentPanel.tsx | AGENT_INTEGRATION | #2.2 |
| chat.py | AGENT_INTEGRATION | #2.1 |
| /api/chat route | AGENT_INTEGRATION | #2.3 |
| CSS | AGENT_INTEGRATION | #2.4 |
| Setup | AGENT_SETUP | Pasos 1-4 |

---

## 📝 Control de Versiones

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | Mayo 21, 2026 | Release inicial: integración completa del agente en web |

---

## 👥 Contribuidores

- **Claude Code** — Implementación, documentación
- **Luis Mendez** — Validación, feedback, testing
- **aeioTU Equipo de Alianzas** — Contexto, requerimientos

---

## 📞 Soporte y Contacto

### Encontraste un error en la documentación?

1. Abre el archivo en `docs/`
2. Identifica el error
3. Reporta o corrige directamente

### Tienes preguntas?

1. Revisa el documento relevante para tu rol
2. Busca la palabra clave en el documento
3. Si no encuentras, contacta al equipo

### Quieres contribuir?

1. Lee la guía relevante
2. Propón cambios
3. Sigue la estructura de documentación existente

---

**Última actualización:** Mayo 21, 2026  
**Mantenedor:** Equipo de Desarrollo GrantFlow AI  
**Estado:** Versión 1.0 — Completa y actualizada
