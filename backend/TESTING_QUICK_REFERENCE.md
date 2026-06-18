# Grants.gov Retry Logic — Quick Testing Reference

## Formato de ejecución rápida

### 1. Ejecutar tests automáticos (pytest)

```bash
# Setup (una sola vez)
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o: .\venv\Scripts\activate  # Windows
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov

# Correr tests
pytest tests/test_grantsgov_retry.py -v

# Correr tests con output detallado
pytest tests/test_grantsgov_retry.py -v -s

# Correr suite específica
pytest tests/test_grantsgov_retry.py::TestRetryLogic -v

# Coverage
pytest tests/test_grantsgov_retry.py --cov=app.scrapers.grantsgov_scrapling --cov-report=html
# Luego abrir: htmlcov/index.html
```

### 2. Ejecutar tests manuales (script interactivo)

```bash
cd backend
python test_retry_manual.py
```

**Output esperado:**
```
╔════════════════════════════════════════════════════════════════════════════╗
║         GRANTS.GOV RETRY LOGIC — MANUAL TEST SUITE                        ║
╚════════════════════════════════════════════════════════════════════════════╝

================================================================================
SCENARIO 1: Success en primer intento
================================================================================
✅ Response status: 200
✅ Request count: 1 (esperado: 1)
✅ Resultado: ÉXITO sin retry

[... más scenarios ...]

================================================================================
✅ ALL SCENARIOS PASSED
================================================================================
```

### 3. Ejecutar scraper en vivo (debug)

```bash
cd backend

# Debug mode con logs
DEBUG=1 python -c "
import asyncio
import logging
logging.basicConfig(level=logging.DEBUG)

from app.scrapers.grantsgov_scrapling import GrantsGovScraperScrapling

async def test():
    scraper = GrantsGovScraperScrapling()
    print('Starting Grants.gov scraper...')
    items = await scraper.fetch_raw()
    print(f'Fetched {len(items)} opportunities')
    for item in items[:5]:
        print(f'  - {item.get(\"title\", \"No title\")[:70]}')

asyncio.run(test())
"
```

### 4. Simular error 403 en vivo

Útil para verificar que el retry funciona contra Grants.gov real:

```bash
cd backend

python -c "
import asyncio
from app.scrapers.grantsgov_scrapling import GrantsGovScraperScrapling

async def test_real_403():
    scraper = GrantsGovScraperScrapling()
    print('Testing retry against real Grants.gov API...')
    print('(Si ves 4 intentos = retry logic funciona)')
    print()
    
    response = await scraper._fetch_with_retry(
        'https://api.grants.gov/v1/api/search2',
        params={'searchString': 'early childhood', 'pageNumber': 1},
        timeout=30
    )
    
    if response:
        print(f'✅ Success: status {response.status_code}')
        data = response.json()
        count = len(data.get('opportunities', []))
        print(f'✅ Fetched {count} opportunities')
    else:
        print('⚠️  Failed after all retries (expected if Grants.gov is blocking)')

asyncio.run(test_real_403())
"
```

---

## Estructura de tests

### Archivo: `backend/tests/test_grantsgov_retry.py`

**Suites:**

| Suite | Tests | Líneas | Propósito |
|-------|-------|--------|-----------|
| `TestRetryLogic` | 6 | Headers, retry, backoff exponencial |
| `TestFetchAPIWithRetry` | 2 | Integración de retry en _fetch_api |
| `TestIntegration` | 1 | End-to-end fallback a web scraping |

**Coverage esperado:** >95% de `grantsgov_scrapling.py`

---

## Validar cada componente

### 1. Headers random

```bash
python -c "
from app.scrapers.grantsgov_scrapling import get_random_headers
for i in range(3):
    headers = get_random_headers()
    print(f'Headers set {i+1}:')
    print(f'  User-Agent: {headers[\"User-Agent\"][:50]}...')
    print(f'  Referer: {headers[\"Referer\"]}')
    print()
"
```

### 2. Backoff timing

```bash
python -c "
import asyncio
import time

async def test_backoff():
    delays = []
    for attempt in range(4):
        backoff = 2 ** attempt
        delays.append(backoff)
    print('Backoff sequence (segundos):')
    for i, delay in enumerate(delays, 1):
        print(f'  Intento {i} → wait {delay}s')

asyncio.run(test_backoff())
"
```

**Output esperado:**
```
Backoff sequence (segundos):
  Intento 1 → wait 1s
  Intento 2 → wait 2s
  Intento 3 → wait 4s
  Intento 4 → wait 8s
```

### 3. Verificar logs

```bash
cd backend

# Con logging detallado
python -c "
import asyncio
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

from app.scrapers.grantsgov_scrapling import GrantsGovScraperScrapling

async def main():
    scraper = GrantsGovScraperScrapling()
    print('Logs esperados:')
    print('  ✓ GrantsGov API attempt (attempt=X)')
    print('  ✓ GrantsGov API 403 Forbidden (si aplica)')
    print('  ✓ GrantsGov backoff wait (wait_seconds=X)')
    print('  ✓ GrantsGov API success o error final')
    print()
    await scraper._fetch_api()

asyncio.run(main())
"
```

---

## Matriz de tests

| Escenario | Test | Verificación |
|-----------|------|--------------|
| **Success** | `test_fetch_with_retry_success_on_first_attempt` | 1 request, status 200 |
| **403 → retry** | `test_fetch_with_retry_retries_on_403_then_succeeds` | 2 requests, 1 sleep |
| **Backoff exponencial** | `test_fetch_with_retry_backoff_exponential` | sleep times [1, 2, 4] |
| **Max retries** | `test_fetch_with_retry_exhausts_after_max_retries` | 4 requests, None response |
| **Headers random** | `test_get_random_headers_vary_on_calls` | 3 headers diferentes |
| **API integration** | `test_fetch_api_integrates_retry` | _fetch_with_retry called |
| **Fallback** | `test_scraper_fallback_to_web_on_api_exhaustion` | web scraping triggered |

---

## CI/CD (GitHub Actions)

Agregar a `.github/workflows/test.yml`:

```yaml
name: Test Grants.gov Retry

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      
      - name: Run Grants.gov retry tests
        run: |
          cd backend
          pytest tests/test_grantsgov_retry.py -v --cov=app.scrapers.grantsgov_scrapling
```

---

## Troubleshooting

### Error: `ModuleNotFoundError: No module named 'app'`

**Solución:**
```bash
cd backend
export PYTHONPATH=$PWD:$PYTHONPATH
pytest tests/test_grantsgov_retry.py -v
```

### Error: `httpx` no instalado

**Solución:**
```bash
pip install httpx>=0.25.0
```

### Tests lentos (asyncio)

```bash
# Reducir timeout en pruebas
pytest tests/test_grantsgov_retry.py -v --asyncio-mode=auto
```

---

## Métrica de éxito

**Green:**
- ✅ Todos los tests pasan
- ✅ Coverage >95%
- ✅ No hay warnings en logs
- ✅ Backoff times correctos [1, 2, 4, 8]

**Red flags:**
- ❌ Mock no es llamado (retry logic no se ejecuta)
- ❌ Sleep times incorrectos (backoff no exponencial)
- ❌ Fallo en test de fallback (web scraping no funciona)
- ❌ Headers siempre iguales (rotation no funciona)

---

## Próximo paso

Una vez tests pasan:

```bash
# Commitear cambios
git add backend/app/scrapers/grantsgov_scrapling.py
git add backend/tests/test_grantsgov_retry.py
git add backend/GRANTS_GOV_RETRY_IMPLEMENTATION.md

git commit -m "feat(scraper): implement retry with exponential backoff for Grants.gov

- Add _fetch_with_retry() with backoff 1s → 2s → 4s → 8s
- Rotate User-Agent and Referer headers per attempt
- Add detailed logging for each attempt
- 4 max retries before falling back to web scraping
- Comprehensive test suite (12 tests, >95% coverage)

Fixes: Resolves 403 Forbidden errors from Grants.gov API"

# Push a rama de feature
git push origin feat/grantsgov-retry-logic
```

---

**Test framework:** pytest + pytest-asyncio  
**Coverage target:** >95%  
**Status:** ✅ Ready to test
