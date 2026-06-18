# Proxy Setup Guide — LinkedIn & Twitter Scrapers

## Overview

Los scrapers mejorados de LinkedIn y Twitter ahora soportan proxies para bypass de Google Search y otros bloqueos de IP. Este documento explica cómo configurar proxies para la ingesta de datos.

---

## ¿Por qué usar proxy?

- **Bypass de bloqueos**: Google, LinkedIn y Twitter pueden bloquear IPs por exceso de requests
- **Rate limiting**: Proxies permiten distribuir requests entre múltiples IPs
- **Privacidad**: Oculta la IP del servidor de origen
- **Geografía**: Simula ubicación en diferentes países

---

## Quick Start

### 1. Configurar variable de entorno

Agrega a tu `.env`:

```bash
# Proxy con credenciales
PROXY_URL=http://user:password@proxy-server.com:8080

# O proxy sin credenciales
PROXY_URL=http://192.168.1.100:3128

# O SOCKS5
PROXY_URL=socks5://proxy.example.com:1080
```

### 2. Verificar que los scrapers usen proxy

```python
from app.scrapers.linkedin_improved import LinkedInScraperImproved

scraper = LinkedInScraperImproved()
config = scraper._get_proxy_config()
print(config)  # {"proxies": "http://..."}
```

### 3. Ejecutar con proxy

```bash
# Asegurar que PROXY_URL está en .env
make scrape SOURCE=linkedin_improved

# O ejecutar todos los scrapers con proxy
make scrape-all
```

---

## Formatos soportados

| Tipo | Formato | Ejemplo |
|------|---------|---------|
| HTTP | `http://proxy:port` | `http://proxy.example.com:8080` |
| HTTP + Auth | `http://user:pass@proxy:port` | `http://admin:secret@proxy.local:3128` |
| SOCKS5 | `socks5://proxy:port` | `socks5://proxy.example.com:1080` |
| SOCKS5 + Auth | `socks5://user:pass@proxy:port` | `socks5://admin:pwd@proxy.local:1080` |

---

## Behavior sin proxy (fallback)

Si `PROXY_URL` no está configurado:

1. **Logging**: Se emite warning `PROXY_URL not configured...`
2. **Conexión**: Se usa conexión directa (sin proxy)
3. **Riesgo**: Requests pueden ser bloqueados por rate limiting

Ejemplo en logs:

```
WARNING: PROXY_URL not configured - LinkedIn scraping without proxy may be blocked
```

---

## Rate limiting con proxy

Los scrapers aplican delay aleatorio **2-5 segundos** entre requests:

```python
# En linkedin_improved.py y twitter_improved.py
await asyncio.sleep(random.uniform(2, 5))  # Delay entre cada request
```

Este delay se aplica de forma independiente del proxy. Razones:

- **Evita bloqueos**: Simula tráfico humano
- **Rate limit compliance**: Respeta límites de APIs
- **Distribuye carga**: Previene picos de requests

---

## Testing con Proxy Mock

Para probar sin proxy real, usa el comando:

```bash
# Test unitarios con mocks
python -m pytest backend/tests/test_proxy_support.py -v

# Test específico de proxy LinkedIn
python -m pytest backend/tests/test_proxy_support.py::TestLinkedInProxyIntegration -v

# Test de configuración de proxy
python -m pytest backend/tests/test_proxy_support.py::TestProxyConfiguration -v
```

---

## Proveedores de proxy recomendados

### Free / Trial
- **Bright Data** (ex Luminati): Free tier 500MB/mes, $10/GB adicional
- **Proxy6**: $5/mes starter, 1GB/mes
- **Free-Proxy-List.net**: Público pero lento (solo para testing)

### Pagado
- **Bright Data**: Enterprise-grade, $50+/mes
- **Smartproxy**: $20/mes, 10GB/mes
- **Oxylabs**: API-first, $79+/mes

### Self-hosted
- **Squid Proxy**: Gratis, auto-hospedado en VPS ($5/mes)
- **Tinyproxy**: Ligero, open-source
- **3Proxy**: Múltiples protocolos (HTTP, SOCKS5)

---

## Troubleshooting

### Proxy no responde

```
Error: httpx.ConnectError: [Errno 111] Connection refused
```

Solución:
1. Verificar que `PROXY_URL` es correcto
2. Probar conectividad: `curl -x http://proxy:port http://example.com`
3. Revisar credenciales (user/password)
4. Consultar logs del proxy server

### Autenticación fallida

```
Error: httpx.ProxyError: 407 Proxy Authentication Required
```

Solución:
1. Verificar que user y password en `PROXY_URL` son correctos
2. Verificar formato: `http://user:password@proxy:port` (no invertir)
3. Revisar caracteres especiales (escapar `@` como `%40`)

### Rate limiting aún con proxy

Aumentar delay:

```python
# En linkedin_improved.py, línea ~196
await asyncio.sleep(random.uniform(5, 10))  # Aumentar delay a 5-10s
```

### Proxy lento

Aumentar timeout:

```python
# En twitter_improved.py
async with httpx.AsyncClient(timeout=30, **proxy_config) as client:  # Aumentar de 15s a 30s
```

---

## Monitoreo en producción

### Logs para auditar uso de proxy

```python
logger.info("Using proxy for LinkedIn scraping", proxy=proxy_url[:20] + "...")
logger.warning("PROXY_URL not configured - scraping without proxy may be blocked")
```

### Métricas clave

Monitorear en n8n workflows:

```
- Requests bloqueados: status_code 403/429
- Requests exitosos: status_code 200
- Latencia con proxy vs sin proxy
- Downtime del proxy
```

### Alertas sugeridas

```
Si status_code 403 > 10 en última hora
→ Alerta: Proxy no funciona, cambiar a directa
```

---

## Cambios en el código

### LinkedIn Scraper (`backend/app/scrapers/linkedin_improved.py`)

**Líneas modificadas:**
- `16-18`: Importar `os`, `random`
- `167-177`: Método `_get_proxy_config()`
- `182-188`: Pasar `**proxy_config` a `AsyncClient`
- `206`, `315`, `369`: Agregar `await asyncio.sleep(random.uniform(2, 5))`

### Twitter Scraper (`backend/app/scrapers/twitter_improved.py`)

**Líneas modificadas:**
- `16-18`: Importar `os`, `random`
- `31-43`: Función `_get_proxy_config()`
- `57`: Agregar `await asyncio.sleep(random.uniform(2, 5))` en `fetch_twitter_api_v2`
- `216`: Agregar `proxy_config = _get_proxy_config()` en `fetch_twitter_accounts`
- `225`: Pasar `**proxy_config` a `AsyncClient`
- `225`, `301`: Agregar `await asyncio.sleep(random.uniform(2, 5))`

### Variables de entorno (`.env.example`)

**Línea añadida:**
```bash
# Proxy configuration — Opcional para bypass de Google Search
PROXY_URL=http://proxy-server:8080
```

---

## Expected Impact Timeline

### Inmediato (24-48 horas)
- Menos errores 403 (Forbidden) en Google Search
- Menos errores 429 (Too Many Requests)
- Mejor throughput en ingesta de LinkedIn/Twitter

### Corto plazo (1-2 semanas)
- Aumento en volumen de oportunidades detectadas
- Reducción de falsos negativos (oportunidades perdidas)
- Mayor stabilidad del pipeline

### Requisitos
- ✅ Proxy configurado en `.env`
- ✅ Credenciales del proxy verificadas
- ✅ Tests unitarios pasando
- ✅ Logs monitoreados en n8n

---

## Rollback (si algo falla)

### Opción 1: Deshabilitar proxy (sin cambiar código)

```bash
# En .env, comentar o eliminar:
# PROXY_URL=http://...

# Los scrapers automáticamente usan conexión directa
```

### Opción 2: Cambiar a otro proxy

```bash
# En .env
PROXY_URL=http://nuevo-proxy:8080

# Reiniciar scrapers
make scrape-all
```

---

## Recursos adicionales

- [httpx proxies documentation](https://www.python-httpx.org/advanced/#proxies)
- [LinkedIn scraping best practices](https://web.archive.org/web/20250101000000*/linkedin.com/robots.txt)
- [Google Search compliance](https://support.google.com/webmasters/answer/1061943)

---

**Última actualización:** 18 de junio de 2026  
**Versión:** 1.0.0
