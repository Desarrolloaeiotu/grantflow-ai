# GrantFlow Asistente — Guía de Configuración

> Para desarrolladores y DevOps  
> Mayo 2026

---

## 📋 Requisitos Previos

### Sistema
- **OS:** Windows 10+, macOS, Linux
- **Python:** 3.11+
- **Node.js:** 18+
- **npm:** 8+

### Servicios Externos
- **Anthropic API:** API key de https://console.anthropic.com/
- **Supabase:** Database configurada (ya existe en el proyecto)
- **Google Gemini:** API key (ya configurada para embeddings)

---

## 🔑 Paso 1: Obtener API Key de Anthropic

### En Windows / macOS / Linux:

1. **Abre:** https://console.anthropic.com/

2. **Inicia sesión** (crea cuenta si es necesario — es gratis)

3. **Ve a "API Keys"** en el menú izquierdo

4. **Haz clic en "Create Key"**

5. **Copia la key** (comienza con `sk-ant-`)

6. **Guárdalo en un lugar seguro** (la única vez que se muestra)

---

## 🔧 Paso 2: Configurar Variables de Entorno

### Backend

**Archivo:** `backend/.env`

```bash
# Reemplaza esta línea:
ANTHROPIC_API_KEY=

# Con esto (pega tu key):
ANTHROPIC_API_KEY=sk-ant-[tu-key-aqui]
```

**Ejemplo completo de `.env` actualizado:**
```bash
# Base de datos
DATABASE_URL=postgresql://...
SUPABASE_URL=https://...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_KEY=...

# IA
ANTHROPIC_API_KEY=sk-ant-v7XzYpQWqZ1234567890abcdefghijk
GOOGLE_API_KEY=AIzaSyBWbOaIqfYvByY5M887I1pWuZPzIQu-DrY

# App
NEXT_PUBLIC_API_URL=http://localhost:8000
JWT_SECRET=dev_secret_grantflow_2026_change_in_production
ENVIRONMENT=development

# ... resto de variables
```

### Frontend

**Archivo:** `frontend/.env.local` (crear si no existe)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🚀 Paso 3: Iniciar Servicios

### Terminal 1: Backend

```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

**Salida esperada:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started server process
INFO:     Waiting for application startup.
2026-05-21 22:50:22 [info] GrantFlow AI starting environment=development
INFO:     Application startup complete.
```

### Terminal 2: Frontend

```bash
cd frontend
npm run dev
```

**Salida esperada:**
```
Next.js 15.3.0
- Local:        http://localhost:3001
- Network:      http://172.30.240.1:3001
✓ Ready in 3.6s
```

---

## ✅ Paso 4: Verificar Setup

### Comprobación 1: Backend responde

```bash
curl -X GET http://localhost:8000/health
```

**Respuesta esperada:**
```json
{"status":"ok","version":"0.1.0"}
```

### Comprobación 2: Endpoint de chat funciona

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hola","history":[]}'
```

**Respuesta esperada:**
```json
{"reply":"Hola, soy GrantFlow Asistente..."}
```

### Comprobación 3: Frontend carga

Abre en navegador:
```
http://localhost:3001
```

Deberías ver el dashboard de GrantFlow. En la esquina inferior derecha debe estar el botón 💬.

### Comprobación 4: Agent funciona end-to-end

1. Haz clic en botón 💬
2. Escribe: `¿Qué oportunidades GO tenemos?`
3. Presiona Enter
4. Espera 2-5 segundos
5. Deberías ver una respuesta del asistente

---

## 📁 Estructura de Archivos Nuevos

```
grantflow-ai/
├── backend/
│   ├── app/
│   │   └── api/
│   │       └── chat.py                    ← Nuevo: Endpoint del agente
│   ├── main.py                            ← Modificado: Registra chat router
│   └── .env                               ← Modificado: ANTHROPIC_API_KEY
│
├── frontend/
│   ├── app/
│   │   ├── api/
│   │   │   └── chat/
│   │   │       └── route.ts               ← Nuevo: Proxy API
│   │   ├── components/
│   │   │   └── AgentPanel.tsx             ← Nuevo: UI del panel
│   │   ├── layout.tsx                     ← Modificado: Importa AgentPanel
│   │   └── globals.css                    ← Modificado: Estilos del panel
│   └── .env.local                         ← Nuevo: Configuración frontend
│
└── docs/
    ├── AGENT_INTEGRATION.md               ← Nuevo: Documentación técnica
    ├── AGENT_QUICKSTART.md                ← Nuevo: Guía para usuarios
    └── AGENT_SETUP.md                     ← Este archivo
```

---

## 🔍 Troubleshooting de Setup

### Error: "ModuleNotFoundError: No module named 'anthropic'"

**Causa:** SDK de Anthropic no instalado

**Solución:**
```bash
cd backend
pip install anthropic
```

### Error: "ANTHROPIC_API_KEY not set"

**Causa:** Variable de entorno vacía

**Solución:**
1. Abre `backend/.env`
2. Verifica que `ANTHROPIC_API_KEY` tenga tu key (no esté vacío)
3. Reinicia el servidor

### Error: "Connection refused" (frontend no conecta con backend)

**Causa:** Backend no está corriendo

**Solución:**
```bash
# Terminal 1
cd backend
python -m uvicorn main:app --reload --port 8000
```

### Error: "Port 3000 is in use, using available port 3001 instead"

**Causa:** Algo más está usando puerto 3000

**Solución:** Es normal. El frontend usará puerto 3001. Abre:
```
http://localhost:3001
```

### El chat responde lentamente (>10 segundos)

**Posibles causas:**
- Conexión a internet lenta
- Servidor Anthropic sobrecargado
- Computadora con pocos recursos

**Solución:**
- Intenta preguntas más simples
- Espera unos minutos e intenta de nuevo
- Verifica que el backend esté en `--reload` (modo desarrollo es más lento)

---

## 🐛 Debug Mode

### Habilitar logs detallados en backend

Modifica `backend/main.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

### Ver requests HTTP en frontend

Abre DevTools (F12) → Tab "Network" → Recarga la página → Haz una pregunta → Verás la request POST a `/api/chat`

### Ver respuestas de Claude

En `backend/app/api/chat.py`, modifica para loguear:

```python
logger.info("Claude response", response=response.content)
```

---

## 📊 Monitoreo

### Health Check Periódico

```bash
# Verificar que el backend sigue activo
curl -s http://localhost:8000/health | jq .
```

### Ver logs en tiempo real

```bash
# Backend (si está corriendo con --reload)
tail -f backend.log

# Frontend
npm run dev  # Muestra logs en consola
```

### Verificar base de datos

```bash
# Conectar a Supabase desde psql
psql postgresql://postgres:PASSWORD@aws-1-sa-east-1.pooler.supabase.com:5432/postgres

# Ver oportunidades
SELECT COUNT(*) FROM opportunities;

# Ver si la tabla tiene datos
SELECT id, title, score_total FROM opportunities LIMIT 5;
```

---

## 🔐 Seguridad

### En Desarrollo (Actual)

✅ **Aceptable:**
- ANTHROPIC_API_KEY en `.env` local
- Sin autenticación de usuario
- CORS permisivo

⚠️ **Vigilar:**
- `.env` NO commitear a git (verificar `.gitignore`)
- API key debe ser específica para desarrollo

### En Producción (Futuro)

Implementar:
- API key almacenada en Azure Key Vault o similar
- JWT authentication para usuarios
- Rate limiting
- CORS restringido a dominio específico
- HTTPS obligatorio
- Auditoría de logs

---

## 📚 Archivos de Configuración Importantes

### `backend/main.py`
```python
# Línea ~7: Importa chat router
from app.api import chat

# Línea ~44: Registra router
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
```

### `frontend/app/layout.tsx`
```typescript
// Línea ~4: Importa AgentPanel
import AgentPanel from './components/AgentPanel'

// Línea ~19: Lo renderiza en el layout
<AgentPanel />
```

### `backend/.env`
```bash
# Línea ~13: Tu API key
ANTHROPIC_API_KEY=sk-ant-...
```

---

## ✨ Comandos Útiles

```bash
# Backend: Reiniciar
Ctrl+C en la terminal, luego:
python -m uvicorn main:app --reload --port 8000

# Frontend: Reiniciar
Ctrl+C en la terminal, luego:
npm run dev

# Limpiar caché de Next.js
rm -rf .next

# Verificar que los puertos estén libres
netstat -an | grep -E ":(3000|8000)"

# Matar proceso en puerto específico (si está ocupado)
# Windows:
netstat -ano | findstr :8000
taskkill /PID [PID] /F

# macOS/Linux:
lsof -ti:8000 | xargs kill -9
```

---

## 📈 Próximas Fases

### Fase 2: Producción Ready
- [ ] Tests automatizados
- [ ] CI/CD pipeline
- [ ] Monitoreo con Sentry
- [ ] Rate limiting
- [ ] Caché distribuido (Redis)

### Fase 3: Escalabilidad
- [ ] Load balancing
- [ ] Database read replicas
- [ ] Vector store distribuido
- [ ] Queue de procesamiento (Celery)

---

**Versión:** 1.0  
**Última actualización:** Mayo 21, 2026  
**Mantenedor:** Equipo de Desarrollo GrantFlow
