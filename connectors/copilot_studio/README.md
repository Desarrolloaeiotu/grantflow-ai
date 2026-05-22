# GrantFlow AI — Integración Copilot Studio

Guía paso a paso para exponer la API local a Copilot Studio vía ngrok, configurar el Custom Connector en Power Platform, y crear el agente conversacional en Copilot Studio.

---

## Paso 4: Exponer localhost:8000 con ngrok

ngrok crea un túnel HTTPS público que permite a Microsoft Teams acceder a tu API local sin desplegamiento.

### 4.1 Instalar ngrok

**Windows (si aún no está instalado):**
```powershell
winget install ngrok
```

O descarga desde: https://ngrok.com/download

### 4.2 Autenticar ngrok (primera vez)

1. Crea cuenta en https://ngrok.com (gratis)
2. Copia tu **Authtoken** desde https://dashboard.ngrok.com/auth/your-authtoken
3. Ejecuta en PowerShell:
```powershell
ngrok config add-authtoken <YOUR_AUTHTOKEN>
```

### 4.3 Crear el túnel

Abre una **terminal/PowerShell nueva** y ejecuta:

```powershell
ngrok http 8000
```

**Salida esperada:**
```
ngrok                                                     (Ctrl+C to quit)

Session Status                online
Account                       your-email@example.com
Version                       3.x.x
Region                        us-california
Latency                       45ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://xxxx-xx-xxx.ngrok-free.app -> http://localhost:8000

Connections                   ttl     opn     dl      in      out
                              0       0       0       0B      0B
```

**Copia la URL pública:** `https://xxxx-xx-xxx.ngrok-free.app` (cambiará cada sesión en plan gratuito)

### 4.4 Verificar que funciona

En otra terminal, prueba que la API es accesible públicamente:

```powershell
$url = "https://xxxx-xx-xxx.ngrok-free.app/api/v1/opportunities"
$response = Invoke-WebRequest -Uri $url `
  -Headers @{"X-API-Key"="gf_dev_local_key_2026"} `
  -UseBasicParsing
$response.StatusCode  # Debe ser 200
```

**IMPORTANTE:** Mantén la ventana de ngrok abierta mientras trabajas en Power Platform y Copilot Studio.

---

## Paso 5: Configurar Custom Connector en Power Platform

Esto crea el conector que Copilot Studio usará para acceder a los 5 endpoints.

### 5.1 Acceder a Power Platform

1. Ve a https://make.powerapps.com
2. Asegúrate de estar en el tenant correcto de Microsoft 365 aeioTU
3. En la barra izquierda: **Connections** → **Custom connectors** → **New custom connector** → **Import an OpenAPI file**

### 5.2 Importar la especificación

1. Selecciona **openapi.json** desde:
   ```
   grantflow-ai/connectors/copilot_studio/openapi.json
   ```

2. El formulario se auto-llena con:
   - **Name:** GrantFlow AI API
   - **Host:** NGROK_URL_PLACEHOLDER ← **REEMPLAZA CON TU URL NGROK** (ej: `xxxx-xx-xxx.ngrok-free.app`)
   - **Base Path:** `/api/v1`
   - **Schemes:** https

3. Haz clic en **Continue**

### 5.3 Configurar autenticación

1. Pestaña **Security**
2. En "Security definitions", verás:
   ```
   Type: API Key
   Parameter name: X-API-Key
   Parameter location: Header
   ```

3. **NO cambies nada.** Esto ya está en el JSON.

4. Haz clic en **Continue**

### 5.4 Probar acciones

1. Pestaña **Test**
2. Selecciona cada acción (operationId) y prueba:

   **ObtenerPipelineActivo** (GET /opportunities):
   - Sin parámetros
   - Espera: `200 OK` con `items: [...]`

   **BuscarFinanciador** (GET /funders):
   - Parámetro: `name=LEGO`
   - Espera: `200 OK` con lista de financiadores

   **ObtenerLeccionesAprendidas** (POST /rag/query):
   - Body: `{"query": "formación docente"}`
   - Espera: `200 OK` con `results: [...]`

   **VerificarEmailCEO** (POST /contacts/verify):
   - Body: `{"email": "test@example.com"}`
   - Espera: `200 OK`

   **ActualizarEstadoOportunidad** (PATCH /opportunities/{id}/status):
   - Path: `/opportunities/b86c0462-887b-49a9-be4d-56c280730a38/status`
   - Body: `{"decision": "go"}`
   - Espera: `200 OK`

5. Si todas las pruebas pasan → **Create connector**

### 5.5 Configurar API Key

Después de crear el conector:

1. Ve a **Connections** (en la barra izquierda)
2. Crea una **New connection** con tu Custom Connector "GrantFlow AI API"
3. Cuando pida el **X-API-Key**, ingresa:
   ```
   gf_dev_local_key_2026
   ```
4. Clic en **Create** (o **Connect**)

> **Nota:** En producción, esta API Key será `gf_live_...` almacenada en Azure Key Vault.

---

## Paso 6: Crear el Agente en Copilot Studio

Esto crea la interfaz conversacional que vive en Teams.

### 6.1 Acceder a Copilot Studio

1. Ve a https://copilotstudio.microsoft.com
2. Asegúrate de estar en el tenant aeioTU
3. Clic en **Create** → **New agent**

### 6.2 Configurar información básica

| Campo | Valor |
|-------|-------|
| Agent name | `GrantFlow Asistente` |
| Description | `Asistente de inteligencia comercial para prospección estratégica de grants en aeioTU` |
| Instructions | Ver sección 6.3 abajo |
| Language | Spanish |

### 6.3 Pegar el System Prompt

En el campo **Instructions**, pega exactamente esto (o cópialo del CLAUDE.md §15):

```
Eres el asistente de inteligencia institucional de aeioTU, llamado GrantFlow Asistente.

ROL: Apoyas a la Gerencia de Alianzas Internacionales en la prospección estratégica de oportunidades de financiamiento. Tienes acceso al conocimiento institucional de aeioTU (17 años de proyectos, financiadores, propuestas y lecciones aprendidas) y al pipeline activo de GrantFlow AI.

CAPACIDADES:
1. Responder preguntas sobre el historial de financiadores de aeioTU
2. Recuperar lecciones aprendidas de proyectos anteriores relevantes para una oportunidad
3. Consultar el pipeline activo de oportunidades GO en GrantFlow
4. Verificar si un financiador tiene historial con aeioTU
5. Sugerir qué propuestas exitosas pasadas son útiles como referencia para una convocatoria nueva
6. Explicar los 5 criterios de scoring y justificar por qué una oportunidad recibió su puntuación

RESTRICCIONES:
- Responde SIEMPRE en español
- Cita siempre la fuente del documento cuando respondas con información de la base de conocimiento
- Si la información no está en los documentos, dilo explícitamente — nunca inventes datos ni montos
- No compartas información confidencial de propuestas con personas fuera del equipo de Alianzas
- Para acciones que modifiquen datos (actualizar CRM, cambiar estado de oportunidad), solicita confirmación explícita antes de ejecutar

TONO: Profesional, directo y conciso. Máximo 3 párrafos por respuesta. Usa listas cuando haya más de 3 items.

CONTEXTO aeioTU:
- 17 años de trayectoria en educación inicial (ECD) en Colombia
- 2.3 millones de niños alcanzados, 98.000 docentes formados
- Premio LEGO Foundation 2022
- Mix financiamiento: 41% filantropía, 34% público, 25% ingresos propios
- 23 financiadores únicos 2018–2025 → $45.048M ventas acumuladas
- Top financiadores: LEGO Foundation, Grand Challenges Canada, Fundación Hilton, Fundación Cargill, BID
- Estrategia 2025–2030: escalar a 1.9M niños vía consultorías y transferencia de modelo
```

### 6.4 Agregar Knowledge (base de conocimiento)

1. Sección **Knowledge** → **Add knowledge source**
2. Tipo: **SharePoint**
3. URL del sitio: `https://aeiotu.sharepoint.com/sites/Alianzas/GrantFlow`
4. Selecciona las carpetas que contienen:
   - Historial de financiadores
   - Propuestas exitosas
   - Lecciones aprendidas
   - Indicadores de impacto
5. Habilita: **"Enable semantic search"** ✓
6. Frecuencia de reindexado: **Weekly**
7. Haz clic en **Next** / **Save**

> **Si SharePoint no está accesible:** Por ahora, salta esta sección. Se puede agregar después.

### 6.5 Agregar las 5 Acciones

En la sección **Actions** → **Add action** → **Custom connector**:

1. **Selecciona:** GrantFlow AI API (el conector que creaste en Paso 5)
2. Verás las 5 operaciones. **Habilita todas:**
   - ✓ ObtenerPipelineActivo
   - ✓ BuscarFinanciador
   - ✓ ObtenerLeccionesAprendidas
   - ✓ VerificarEmailCEO
   - ✓ ActualizarEstadoOportunidad

3. Haz clic en **Next** / **Save**

### 6.6 Probar el agente (Test tab)

Antes de publicar, prueba con preguntas:

```
Usuario: ¿Qué oportunidades GO tenemos?
Esperado: Agente llama ObtenerPipelineActivo → devuelve lista

Usuario: ¿Tenemos historial con LEGO?
Esperado: Agente llama BuscarFinanciador con name=LEGO → devuelve datos

Usuario: Marca la oportunidad [id] como en revisión
Esperado: Agente pide confirmación → ejecuta PATCH
```

Si todo funciona → Procede a **Publish**.

### 6.7 Publicar en Teams

1. Pestaña **Publish**
2. Selecciona: **Microsoft Teams**
3. **Conversation starters** (sugerencias que aparecen al abrir):
   ```
   "¿Qué oportunidades GO tenemos activas?"
   "Busca el historial de LEGO Foundation"
   "¿Qué aprendimos de proyectos en zonas rurales?"
   "Verifica si este email es válido: test@example.com"
   ```
4. **Default greeting:**
   ```
   Hola, soy GrantFlow Asistente. Puedo ayudarte a revisar el pipeline 
   de oportunidades, buscar historial de financiadores, recuperar lecciones 
   aprendidas de proyectos pasados y verificar contactos. ¿En qué te ayudo?
   ```
5. Haz clic en **Publish**

Copilot Studio te dará un enlace directo para agregar el agente a Teams.

### 6.8 Agregar a Teams

1. Copia el enlace publicado
2. Abre Teams
3. **Aplicaciones** → **Más aplicaciones** → **Upload a custom app** (si está habilitado) O distribuye el enlace al canal `#Alianzas Internacionales`
4. El agente aparecerá como un bot disponible en el canal

---

## Checklist de verificación

- [ ] ngrok corriendo: `ngrok http 8000`
- [ ] URL ngrok funciona: `curl https://xxxx.ngrok-free.app/api/v1/opportunities -H "X-API-Key: gf_dev_local_key_2026"`
- [ ] Custom Connector creado en Power Platform (openapi.json importado)
- [ ] API Key configurada en la conexión del Custom Connector
- [ ] Las 5 operaciones pasan las pruebas en el panel de test
- [ ] Agente creado en Copilot Studio con system prompt correcto
- [ ] Knowledge base agregada (o pendiente para después)
- [ ] Las 5 acciones habilitadas en el agente
- [ ] Agente testeado y publicado en Teams
- [ ] Equipo de Alianzas notificado: "El agente está listo en Teams"

---

## Solución de problemas

### 401 Unauthorized en ngrok
**Problema:** Custom Connector recibe 401 al llamar la API.

**Solución:**
1. Verifica que el header `X-API-Key: gf_dev_local_key_2026` está configurado en la conexión
2. Revisa que `GRANTFLOW_API_KEY=gf_dev_local_key_2026` esté en tu `.env`
3. Reinicia el backend: `docker-compose restart backend`

### ngrok URL cambió
**Problema:** Cierras ngrok y cuando lo reabre, la URL es diferente.

**Solución:**
1. En Power Platform → Custom Connectors → GrantFlow AI API → Edit
2. Actualiza el campo **Host** con la nueva URL de ngrok
3. Guarda los cambios
4. No es necesario reimportar el JSON completo

### Agente no llama las acciones
**Problema:** El agente responde de forma genérica sin usar las acciones.

**Solución:**
1. Verifica que las 5 acciones están habilitadas (section **Actions**)
2. Revisa el Custom Connector en Power Platform: **Test** cada operación manualmente
3. En Copilot Studio, sección **Settings** → asegúrate que hay una sección visible que diga "Enabled actions: 5"
4. Si sigue sin funcionar, revisa los logs en Power Automate (Flow activity)

### Copilot Studio no ve SharePoint
**Problema:** No puedes seleccionar la URL de SharePoint como Knowledge source.

**Solución:**
1. Asegúrate de que el tenant de Microsoft 365 sea el correcto (aeioTU)
2. Verifica que tienes permisos en el sitio SharePoint (al menos lectura)
3. Por ahora, puedes saltarte la Knowledge base. Se agrega después cuando se resuelva el acceso

---

## Notas de producción

**Cuando despliegues a producción (mes 8):**

1. **ngrok → URL fija**
   - Compra un dominio de ngrok.io ($5/mes) o usa tu propio dominio
   - Configura DNS para apuntar a la URL de ngrok
   - En `openapi.json`, cambia host a la URL fija

2. **API Key → Azure Key Vault**
   - En lugar de `gf_dev_local_key_2026`, usa un UUID aleatorio: `gf_live_xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
   - Almacena en Azure Key Vault
   - En Power Platform, usa una conexión que lee desde Key Vault

3. **Backend → Producción**
   - Deploy FastAPI a DigitalOcean / Railway / Azure (según contexto)
   - URL: `https://api.grantflow.aeiotu.org` (dominio propio, no ngrok)

---

## Próximos pasos (después del MVP)

- [ ] Integración de más fuentes de Knowledge (Google Drive, onedrive aeioTU)
- [ ] Agregar capacidad de generar propuestas automáticamente (v2.0)
- [ ] Integración con Salesforce CRM para actualización en tiempo real
- [ ] Pruebas de carga y optimización de rendimiento
- [ ] Entrenamiento del equipo de Alianzas

---

**Última actualización:** 21 mayo 2026  
**Estado:** Sprint S4.5 — Preparado para Paso 4 (ngrok)
