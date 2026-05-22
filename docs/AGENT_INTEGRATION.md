# GrantFlow Asistente — Integración en Aplicación Web

> Documentación de la integración del agente conversacional en el dashboard Next.js  
> Sprint S5+ | Mayo 2026 | Versión 1.0

---

## 1. Resumen Ejecutivo

El **GrantFlow Asistente** ahora está disponible directamente en la aplicación web como panel lateral conversacional. Los usuarios pueden:

- 💬 Consultar oportunidades GO del pipeline
- 🔍 Buscar historial de financiadores  
- 📚 Recuperar lecciones aprendidas
- ✉️ Verificar emails de contactos
- 📎 Cargar documentos para análisis (futuro)

**Arquitectura:**
```
Frontend (Next.js)
  → AgentPanel.tsx (Client Component)
    → /api/chat (API Route)
      → FastAPI Backend
        → Claude API (claude-haiku-4-5)
          → Tools (get_opportunities, search_funders, search_knowledge, generate_proposal)
```

---

## 2. Componentes Técnicos

### 2.1 Backend: `backend/app/api/chat.py`

**Responsabilidades:**
- Recibe solicitudes POST en `/api/v1/chat`
- Orquesta con Claude Haiku usando `tool_use`
- Ejecuta 4 herramientas disponibles
- Retorna respuestas procesadas

**Herramientas disponibles:**

| Herramienta | Descripción | Uso |
|------------|-------------|-----|
| `get_opportunities` | Lista oportunidades con filtros | "¿Qué oportunidades GO tenemos?" |
| `search_funders` | Busca financiadores por nombre | "¿Historial con LEGO?" |
| `search_knowledge` | RAG semántica en base de conocimiento | "¿Qué aprendimos de X?" |
| `generate_proposal` | Prepara borrador de propuesta | "Genera propuesta para Y" |

**Ejemplo de request:**
```json
{
  "message": "¿Qué oportunidades GO tenemos que vencen esta semana?",
  "history": [
    {"role": "user", "content": "Hola"},
    {"role": "assistant", "content": "Hola, soy GrantFlow Asistente..."}
  ]
}
```

**Ejemplo de response:**
```json
{
  "reply": "Tienes 2 oportunidades GO con cierre esta semana:\n1. LEGO Foundation Innovation Grant — USD $850K\n2. MinEducación FECE 2026 — COP $2.1B"
}
```

**Loop agentic:**
- Máximo 5 iteraciones
- Si Claude decide usar herramientas: ejecuta, agrega resultados, continúa
- Si Claude responde: extrae texto, retorna

---

### 2.2 Frontend: `frontend/app/components/AgentPanel.tsx`

**Responsabilidades:**
- UI del panel conversacional
- Gestión de estado (mensajes, input, loading)
- Comunicación con `/api/chat`
- Manejo de archivos (📎)

**Estados:**
- `isOpen`: panel abierto/cerrado
- `messages`: historial conversacional
- `input`: texto siendo editado
- `isLoading`: esperando respuesta del backend

**Características:**
- ✅ Botón flotante 💬 en esquina inferior derecha
- ✅ Panel lateral con animación
- ✅ Scroll automático al último mensaje
- ✅ Input de texto con Enter para enviar
- ✅ Botón 📎 para cargar archivos (UI completo, procesamiento en desarrollo)
- ✅ Mensajes con estilos diferenciados (usuario vs asistente)
- ✅ Estado loading mientras espera respuesta
- ✅ Manejo de errores

**Estructura del componente:**
```typescript
interface Message {
  role: 'user' | 'assistant'
  content: string
}

// Estado
const [isOpen, setIsOpen] = useState(false)
const [messages, setMessages] = useState<Message[]>([])
const [input, setInput] = useState('')
const [isLoading, setIsLoading] = useState(false)

// Funciones
const handleSend() // Envía mensaje
const handleFileClick() // Abre diálogo de archivo
const handleFileChange() // Procesa archivo seleccionado
const scrollToBottom() // Auto-scroll de mensajes
```

---

### 2.3 Next.js API Route: `frontend/app/api/chat/route.ts`

**Responsabilidades:**
- Proxy entre frontend y FastAPI
- Valida request
- Maneja errores de backend
- Retorna response formateada

**Endpoint:**
```
POST /api/chat
Content-Type: application/json

Body: {
  "message": string,
  "history": Array<{ role: "user"|"assistant", content: string }>
}

Response: {
  "reply": string
}
```

---

### 2.4 Estilos CSS: `frontend/app/globals.css`

**Clases principales:**
- `.agent-btn` — Botón flotante (fixed, z-index: 99)
- `.agent-panel` — Panel lateral (fixed, z-index: 98, transform)
- `.agent-panel.open` — Panel visible
- `.agent-header` — Encabezado con título y botón cerrar
- `.agent-messages` — Área de scroll de mensajes
- `.agent-msg` — Contenedor de mensaje
- `.agent-msg.user` — Burbuja usuario (verde, derecha)
- `.agent-msg.assistant` — Burbuja asistente (gris, izquierda)
- `.agent-welcome` — Mensaje de bienvenida
- `.agent-input-area` — Footer con input + botones
- `.agent-input` — Campo de texto
- `.agent-file-btn` — Botón carga archivos (📎)
- `.agent-send` — Botón enviar (→)

---

## 3. Flujo de Uso

### Caso 1: Consultar oportunidades GO

```
Usuario escribe: "¿Qué oportunidades GO tenemos?"
     ↓
Frontend envía POST /api/chat
     ↓
Next.js route proxea a http://localhost:8000/api/v1/chat
     ↓
FastAPI recibe request
     ↓
Claude Haiku decide usar tool: get_opportunities()
     ↓
Backend ejecuta: SELECT * FROM opportunities WHERE decision='go'
     ↓
Claude procesa resultados, genera respuesta en español
     ↓
Response vuelve a Next.js → Frontend
     ↓
AgentPanel muestra respuesta en burbuja asistente
```

### Caso 2: Buscar financiador

```
Usuario: "¿Tenemos historial con LEGO Foundation?"
     ↓
Claude usa tool: search_funders(name="LEGO Foundation")
     ↓
SELECT * FROM funders WHERE name ILIKE '%LEGO%'
     ↓
Claude analiza: "Sí, tiene_history=TRUE. Financed 2 projects 2020-2023"
     ↓
Respuesta al usuario con detalles
```

### Caso 3: Cargar archivo (en desarrollo)

```
Usuario hace click en 📎
     ↓
Se abre diálogo de selección (soporta: PDF, DOC, DOCX, TXT, XLSX)
     ↓
Usuario selecciona archivo
     ↓
AgentPanel muestra: "📎 Archivo cargado: documento.pdf"
     ↓
Respuesta: "He recibido tu archivo. Puedo ayudarte a procesarlo..."
     ↓
[FUTURO] Enviar archivo al backend para análisis con RAG
```

---

## 4. Instalación y Configuración

### 4.1 Configuración del Backend

**1. Obtén tu API key de Anthropic:**
   - Ve a https://console.anthropic.com/
   - Crea una cuenta (gratis)
   - Ve a "API Keys" y copia tu key (comienza con `sk-ant-`)

**2. Actualiza `backend/.env`:**
   ```bash
   ANTHROPIC_API_KEY=sk-ant-[tu-key-aqui]
   ```

**3. Inicia el backend:**
   ```bash
   cd backend
   python -m uvicorn main:app --reload --port 8000
   ```

### 4.2 Configuración del Frontend

**1. Inicia el servidor de desarrollo:**
   ```bash
   cd frontend
   npm run dev
   ```
   (Nota: Si puerto 3000 está en uso, usa puerto 3001)

**2. Abre en navegador:**
   ```
   http://localhost:3001
   ```

**3. Busca el botón 💬 en esquina inferior derecha**

---

## 5. API Reference

### POST /api/v1/chat

Endpoint de chat con orquestación agentic.

**Request:**
```json
{
  "message": "¿Qué oportunidades GO tenemos?",
  "history": [
    {
      "role": "user",
      "content": "Hola"
    },
    {
      "role": "assistant", 
      "content": "Hola, soy GrantFlow Asistente..."
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "reply": "Tienes actualmente 12 oportunidades en estado GO, con un score promedio de 7.2/10. Las principales son..."
}
```

**Response (400 Bad Request):**
```json
{
  "error": "Message is required"
}
```

**Response (500 Internal Server Error):**
```json
{
  "error": "Backend error: ..."
}
```

---

## 6. Herramientas Disponibles (Tool Use)

### get_opportunities

Obtiene oportunidades filtradas del pipeline.

**Parámetros:**
- `decision` (string, enum): "go" | "no_go" | "pending" (opcional)
- `window` (string): ventana de mercado (opcional)
- `limit` (int): cantidad de resultados (default: 10)

**Response:**
```json
{
  "count": 2,
  "opportunities": [
    {
      "id": "uuid-1",
      "title": "LEGO Foundation Innovation Grant",
      "funder": "LEGO Foundation",
      "score": 8,
      "decision": "go",
      "deadline": "2026-06-15"
    }
  ]
}
```

### search_funders

Busca financiadores por nombre.

**Parámetros:**
- `name` (string, required): nombre del financiador

**Response:**
```json
{
  "count": 1,
  "funders": [
    {
      "name": "LEGO Foundation",
      "country": "Denmark",
      "has_history": true,
      "ticket_range": "500000 - 5000000 USD"
    }
  ]
}
```

### search_knowledge

Búsqueda semántica en base de conocimiento (RAG).

**Parámetros:**
- `query` (string, required): tema a buscar
- `top_k` (int): número de resultados (default: 5)

**Response:**
```json
{
  "query": "formación docente en zonas rurales",
  "results_found": 3,
  "results": [
    {
      "document": "Proyecto Nariño 2021",
      "relevance": 0.89,
      "content": "Articulación con alcaldías redujo tiempos de implementación..."
    }
  ]
}
```

### generate_proposal

Genera borrador de propuesta para una oportunidad.

**Parámetros:**
- `opportunity_title` (string, required): título de la oportunidad
- `opportunity_description` (string, optional)
- `opportunity_id` (string, optional)

**Response:**
```json
{
  "status": "ready",
  "opportunity": "LEGO Foundation Innovation Grant",
  "instruction": "Se generará un borrador de propuesta en la siguiente respuesta"
}
```

---

## 7. Troubleshooting

### Error: "Backend error: Internal Server Error"

**Causa más probable:** `ANTHROPIC_API_KEY` no está configurada

**Solución:**
1. Ve a https://console.anthropic.com/
2. Copia tu API key
3. Agrega a `backend/.env`: `ANTHROPIC_API_KEY=sk-ant-...`
4. Reinicia el backend

### Error: "Error de conexión"

**Causa:** Backend no está corriendo

**Solución:**
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

### El botón 💬 no aparece

**Causa:** Frontend no recargado después de cambios

**Solución:**
- Hard refresh: `Ctrl+Shift+R` (Windows) o `Cmd+Shift+R` (Mac)
- Reinicia el servidor Next.js

### Mensajes lentos / timeouts

**Causa:** Llamada a Claude API tardada

**Solución:**
- Verifica conexión a internet
- Revisa que API key sea válida
- Intenta preguntas más simples

---

## 8. Próximos Pasos

### Fase 2: Procesamiento de Documentos

```python
# backend/app/services/document_processor.py
async def process_document(file: UploadFile) -> dict:
    """
    1. Recibe PDF/DOC
    2. Extrae texto con PyPDF2/python-docx
    3. Chunks el contenido
    4. Embeds con Gemini
    5. Guarda en pgvector
    6. Disponible para RAG queries
    """
```

### Fase 3: Generación Automática de Propuestas

```python
# backend/app/services/proposal_generator.py
async def generate_proposal_full(opportunity_id: UUID) -> str:
    """
    1. Consulta oportunidad + financiador
    2. Busca propuestas similares exitosas (RAG)
    3. Claude genera borrador completo (2-3 páginas)
    4. Retorna como string formateado
    5. Frontend permite descargar como DOCX
    """
```

### Fase 4: Integración CRM

```python
# backend/app/api/crm.py
async def sync_to_crm(opportunity_id: UUID) -> dict:
    """
    1. Exporta oportunidad con scoring
    2. Crea/actualiza en Salesforce CRM
    3. Log de sincronización
    4. Webhooks bidireccionales
    """
```

---

## 9. Notas de Producción

### Antes de ir a producción (mes 8+)

**1. API Security:**
   - [ ] Reemplazar dev API key con key de producción (más restrictiva)
   - [ ] Implementar rate limiting en `/api/v1/chat`
   - [ ] Añadir autenticación JWT para usuarios

**2. Escala:**
   - [ ] Implementar caching de embeddings (Redis)
   - [ ] Implementar queue para procesamiento de archivos (Celery)
   - [ ] Monitoreo y alertas (Sentry, DataDog)

**3. Costo:**
   - [ ] Monitorar uso de Claude API (puede crecer rápido)
   - [ ] Implementar quotas por usuario
   - [ ] Log de todas las queries para análisis de uso

**4. UX:**
   - [ ] Persistencia de chat history en BD (por usuario)
   - [ ] Exportar historial como PDF
   - [ ] Dark mode
   - [ ] Soporte multi-idioma (inglés)

---

## 10. Referencias

**Documentación oficial:**
- Claude API: https://docs.anthropic.com/
- Next.js App Router: https://nextjs.org/docs/app
- FastAPI: https://fastapi.tiangolo.com/

**Código fuente:**
- `backend/app/api/chat.py` — Endpoint del agente
- `frontend/app/components/AgentPanel.tsx` — UI del panel
- `frontend/app/api/chat/route.ts` — Proxy API

**Configuración:**
- `backend/.env` — Variables de entorno backend
- `backend/main.py` — Registro de routers
- `frontend/app/layout.tsx` — Integración en layout root
- `frontend/app/globals.css` — Estilos del panel

---

**Última actualización:** Mayo 21, 2026  
**Versión:** 1.0  
**Autor:** Claude Code (con aeioTU)  
**Estado:** Funcional (requiere ANTHROPIC_API_KEY)
