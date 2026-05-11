"""Configuración global de pytest para los tests del backend.

Resuelve el problema de "Event loop is closed" que ocurre porque:
- SQLAlchemy AsyncEngine se ata al primer event loop donde se usa
- pytest-asyncio por defecto crea un loop nuevo por test
- Cuando el segundo test corre, el engine intenta usar el loop viejo (cerrado)

Solución: compartir un solo event loop (session scope) entre todos los tests
async + scope session para el AsyncClient.
"""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def client():
    """AsyncClient compartido por toda la sesión de tests.

    Se importa `app` dentro del fixture para que se cree con el loop activo.
    """
    from main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c
