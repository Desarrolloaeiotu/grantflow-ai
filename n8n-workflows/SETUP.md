# Setup GrantFlow AI — n8n Community Edition Self-Hosted

## Prerequisitos

- n8n Community Edition corriendo localmente o en VPS: `http://localhost:5678` o `http://[VPS_IP]:5678`
- Backend GrantFlow AI corriendo: `http://localhost:8000` o `http://[BACKEND_IP]:8000`
- Variable de entorno `GRANTFLOW_API_KEY` configurada en el backend `.env`

---

## 1. Importar Workflow "scraper-9am"

### Opción A: Importación vía UI (recomendado)

1. **Abre n8n self-hosted** → `http://localhost:5678` (o tu VPS IP)
2. **Haz clic en el menú** (≡) → **"Workflows"**
3. **Haz clic en "+ New"** (botón azul superior derecho)
4. **Copia y pega el contenido de `scraper-9am.json`** en el editor (o arrastra el archivo)
5. **Haz clic en "Save"** (esquina superior derecha)

### Opción B: Copiar el JSON directamente

1. **Abre `scraper-9am.json`** en un editor de texto
2. **Copia TODO el contenido**
3. **En n8n**: Menú (≡) → "Workflows" → "+ New"
4. **Pega el JSON completo** en el área de editor
5. **Click "Save"**

---

## 2. Configurar credenciales en self-hosted

### Paso A: Configurar Header Auth para API Key

1. **En n8n self-hosted**: Abre el workflow
2. **Haz doble clic en el nodo "Run All Scrapers"** (el nodo HTTP que ejecuta `/api/v1/scrape/run`)
3. **En el panel derecho**, busca la sección **"Authentication"**
4. **Selecciona "Header Auth"** del dropdown
5. **Click en "Create New Credential"**:
   - **Nombre**: `grantflow-api-key`
   - **Headers** → Click "+ Add Header"
     - **Name**: `X-API-Key`
     - **Value**: `[copia aquí tu GRANTFLOW_API_KEY del .env del backend]`
6. **Click "Create"** y **"Save"** el nodo
7. **Repite los pasos 2-6 para el nodo "Run LLM Rescorer"** (también necesita la misma API Key)

### Paso B: Configurar Slack Webhook (Opcional)

Si quieres recibir alertas en Slack cuando los scrapers terminen:

1. **En Slack workspace**: Ve a "Apps" → "Custom Integrations" → "Incoming Webhooks"
2. **Click "Add New"** → Selecciona el canal (ej: `#dev-alerts`)
3. **Copia la Webhook URL completa**: `https://hooks.slack.com/services/[TEAM]/[BOT]/[TOKEN]`
4. **En n8n self-hosted**: Haz doble clic en el nodo **"Slack Alert"**
5. **Sección "Slack"** → Click en "Create New Credential"
   - **Webhook URL**: Pega la URL de Slack que copiaste
   - **Nombre**: `slack-webhook-grantflow`
6. **Click "Create"** y verifica que el **"Channel"** sea `#dev-alerts`
7. **Click "Save"** el nodo

---

## 3. Actualizar URLs de Backend (si es necesario)

Si tu backend **NO está en localhost:8000**, actualiza las URLs:

1. **Nodo "Run All Scrapers"**:
   - **URL actual**: `http://localhost:8000/api/v1/scrape/run`
   - **URL nueva** (si backend está en VPS): `http://[BACKEND_IP]:8000/api/v1/scrape/run`
   - Ejemplo: `http://192.168.1.100:8000/api/v1/scrape/run`

2. **Nodo "Run LLM Rescorer"**:
   - **URL actual**: `http://localhost:8000/api/v1/scrape/rescore`
   - **URL nueva**: `http://[BACKEND_IP]:8000/api/v1/scrape/rescore`

> **Nota**: Si n8n y el backend corren en la misma máquina, puedes dejar `localhost:8000`

---

## 4. Guardar y Activar

1. **Verifica que el horario es correcto**:
   - Haz doble clic en el nodo **"Schedule Trigger"**
   - **Trigger**: `every`
   - **Unit**: `day`
   - **Value**: `1`
   - **Trigger at Hour**: `9` (9:00 AM)
   - **Trigger at Minute**: `0`
   - Click **"Done"**

2. **Haz clic en "Save"** (esquina superior derecha, botón azul)

3. **Activa el workflow**: 
   - En la parte superior, busca el toggle **"Active"** (debe estar en color azul/on)
   - Si está gris, haz clic para activarlo

4. **Confirma la activación**: Debería aparecer un mensaje verde "Workflow is now active"

El workflow se ejecutará automáticamente **todos los días a las 9:00 AM**

---

## 5. Probar el Workflow

### Prueba manual antes de activar

1. **En n8n self-hosted**: Abre el workflow que acabas de importar
2. **Haz clic en "Execute Workflow"** (botón play azul en la esquina superior derecha)
3. **Verifica que TODOS los pasos se ejecuten correctamente**:
   - ✓ **"Run All Scrapers"**: Debe retornar JSON con `total_persisted` (número de oportunidades encontradas)
   - ✓ **"Run LLM Rescorer"**: Debe retornar JSON con `succeeded` y `failed`
   - ✓ **"Slack Alert"**: Si configuraste Slack, debería llegar un mensaje a `#dev-alerts`

4. **Si hay errores**: Revisa la pestaña "Executions" (lado derecho) para ver logs detallados

### Verificar ejecuciones automáticas

Una vez activado el workflow:
1. **En n8n**: Abre el workflow → **"Executions"** (pestaña en la parte inferior o lateral)
2. Deberías ver una línea por cada ejecución a las **09:00:00**
3. Si no ves ejecuciones después de esperar hasta las 9am:
   - Verifica que el toggle "Active" esté encendido
   - Verifica el timezone del servidor: `date` (si está en una VPS)

---

## 6. Estructura del Workflow

```
Schedule (9:00 AM)
  ↓
Run All Scrapers [POST /api/v1/scrape/run]
  ↓
Run LLM Rescorer [POST /api/v1/scrape/rescore]
  ↓
Slack Notification (#dev-alerts)
```

### Qué hace cada paso:

| Nodo | Acción | Esperado |
|------|--------|----------|
| **Schedule** | Dispara a las 9:00 AM diarias | - |
| **Scrapers** | Ejecuta: nacional_colombia, grantsgov, bid, etc. | `total_persisted` ≥ 0 |
| **Rescorer** | Ejecuta LLM scoring en opps sin score | `succeeded` ≥ 0 |
| **Slack** | Envía resumen a `#dev-alerts` | ✓ Mensaje recibido |

---

## 7. Monitoreo y Alertas

### Ver logs y ejecuciones en self-hosted

1. **Abre el workflow** en n8n
2. **Click en la pestaña "Executions"** (lado derecho o inferior)
3. **Haz clic en una ejecución** para ver detalles:
   - Logs de cada nodo
   - Inputs y outputs
   - Tiempo de ejecución
   - Errores específicos

### Verificar que el backend está activo

Antes de los 9am, asegúrate que el backend está corriendo:

```bash
# En PowerShell (Windows)
curl http://localhost:8000/health

# O directamente en el navegador:
# Navega a: http://localhost:8000/health
# Debería devolver 200 OK
```

### Si hay errores en el workflow

1. **Error 401 Unauthorized**: Verifica que `GRANTFLOW_API_KEY` sea correcto en:
   - Archivo `.env` del backend
   - Credencial "Header Auth" en n8n
   
2. **Error 404 Not Found**: Verifica que la URL del backend sea correcta:
   - Ejemplo: `http://localhost:8000/api/v1/scrape/run`
   
3. **Error de Slack**: Verifica que el Webhook URL sea válido y el canal exista

---

## 8. Personalización

### Cambiar horario

**Modificar el nodo "Schedule Trigger"**:
```json
"triggerAtHour": 9,        // Cambiar a la hora deseada
"triggerAtMinute": 0       // Cambiar a minuto
```

### Cambiar canal Slack

**Modificar el nodo "Slack Alert"**:
```json
"channel": "#nombre-canal"
```

### Agregar más scrapers

**En el nodo "Run All Scrapers"**, agregar query params:
```
url: http://localhost:8000/api/v1/scrape/run?score=true
```
(Agregar `score=true` para hacer scoring automático en el scraper, sin esperar al rescorer)

---

## 9. Troubleshooting (n8n self-hosted)

### Error 401: Invalid API Key
```
Error: "Invalid API key" en nodo "Run All Scrapers"
```
- **Solución**:
  1. Verifica que `GRANTFLOW_API_KEY` esté en el `.env` del backend
  2. Reinicia el backend para que cargue la variable
  3. En n8n: Double-click en "Run All Scrapers" → Authentication → Verifica el valor en Header Auth
  4. Debe ser exactamente igual al `.env` del backend

### Error 404: Not Found
```
Error: "Not found" en nodo "Run All Scrapers"
```
- **Solución**:
  1. Verifica que el backend esté activo:
     ```bash
     curl http://localhost:8000/health
     ```
  2. Si falla, reinicia el backend
  3. Verifica la URL del nodo (localhost vs VPS IP)
  4. Prueba acceder a la URL directamente en el navegador

### Slack no recibe mensajes
```
Error en nodo "Slack Alert"
```
- **Solución**:
  1. Verifica que el Webhook URL sea válido (cópialo directo de Slack)
  2. Verifica que el canal `#dev-alerts` exista
  3. Prueba hacer clic en "Execute Workflow" manualmente para ver el error exacto

### Workflow no se ejecuta a las 9am (self-hosted)
```
El workflow está "Active" pero no se ejecuta automáticamente
```
- **Solución**:
  1. **En n8n self-hosted**: Verifica que el toggle "Active" esté **azul/encendido**
  2. **Verifica el timezone de tu máquina**:
     ```bash
     date  # PowerShell: Get-Date
     ```
  3. **Si n8n está en Docker**, verifica que el container tenga el timezone correcto
  4. **Revisa "Executions"**: Si no ves ejecutaciones después de pasadas las 9am, hay un problema
  5. **Reinicia n8n**: Detén y vuelve a iniciar el servicio de n8n

---

## 10. Iniciar n8n self-hosted (si no está corriendo)

### Opción A: n8n en Docker

```bash
# Iniciar n8n en Docker (si lo tienes instalado)
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  -e N8N_HOST=localhost \
  n8nio/n8n

# Ver si está corriendo:
docker ps | grep n8n

# Acceder a: http://localhost:5678
```

### Opción B: n8n instalado localmente (Windows)

```powershell
# Si lo instalaste con npm globalmente:
n8n start

# Debería aparecer algo como:
# ▲ n8n ready on http://localhost:5678
```

### Opción C: n8n en VPS (DigitalOcean / Hetzner)

Si n8n está en una VPS, usa `ssh` para conectarte y verifica que el servicio esté activo:

```bash
ssh usuario@vps-ip

# Ver si n8n está corriendo:
ps aux | grep n8n

# Si no está corriendo y usas systemd:
sudo systemctl start n8n

# Verificar status:
sudo systemctl status n8n
```

---

## Próximos pasos

✅ Workflow importado en n8n self-hosted  
✅ Credenciales configuradas (API Key + Slack)  
✅ Horario verificado (9:00 AM diario)  
✅ Toggle "Active" encendido  

→ **Monitorear ejecuciones por 3 días** (verifica Executions cada mañana)  
→ Agregar webhook a CRM para sync automático (v2.0, futuro)
