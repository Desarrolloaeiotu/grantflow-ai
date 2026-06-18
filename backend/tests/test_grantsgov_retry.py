"""Tests para retry con backoff exponencial en Grants.gov scraper.

Verifica:
1. Retry logic funciona con backoff 1s → 2s → 4s → 8s
2. User-Agent rotante en cada intento
3. 403 error es reintentado
4. Fallback a web scraping después de exhaustar reintentos
5. Rate limiting se respeta
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, Response

from app.scrapers.grantsgov_scrapling import (
    GrantsGovScraperScrapling,
    get_random_headers,
)


class TestRetryLogic:
    """Tests para la lógica de retry con backoff."""

    @pytest.mark.asyncio
    async def test_get_random_headers_returns_valid_headers(self):
        """Verifica que get_random_headers() retorna headers válidos."""
        headers = get_random_headers()

        assert "User-Agent" in headers
        assert "Referer" in headers
        assert "Accept" in headers
        assert "Accept-Language" in headers
        assert headers["Accept-Language"].startswith("en-US")

    @pytest.mark.asyncio
    async def test_get_random_headers_vary_on_calls(self):
        """Verifica que User-Agent varía entre llamadas."""
        headers1 = get_random_headers()
        headers2 = get_random_headers()
        headers3 = get_random_headers()

        # Al menos dos deben ser diferentes (probabilidad muy alta)
        user_agents = [headers1["User-Agent"], headers2["User-Agent"], headers3["User-Agent"]]
        assert len(set(user_agents)) > 1, "User-Agents should vary"

    @pytest.mark.asyncio
    async def test_fetch_with_retry_success_on_first_attempt(self):
        """Verifica que éxito en primer intento no hace retry."""
        scraper = GrantsGovScraperScrapling()

        # Mock response con status 200
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"opportunities": [{"id": "1", "title": "Test"}]}

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            response = await scraper._fetch_with_retry(
                "https://api.grants.gov/v1/api/search2",
                params={"searchString": "test"},
            )

            assert response is not None
            assert response.status_code == 200
            # Solo 1 llamada = éxito inmediato
            assert mock_get.call_count == 1

    @pytest.mark.asyncio
    async def test_fetch_with_retry_retries_on_403_then_succeeds(self):
        """Verifica retry tras 403, luego éxito en 2do intento."""
        scraper = GrantsGovScraperScrapling()

        mock_response_403 = MagicMock(spec=Response)
        mock_response_403.status_code = 403

        mock_response_200 = MagicMock(spec=Response)
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"opportunities": []}

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            # Primer intento: 403, segundo intento: 200
            mock_get.side_effect = [mock_response_403, mock_response_200]

            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                response = await scraper._fetch_with_retry(
                    "https://api.grants.gov/v1/api/search2",
                    params={"searchString": "test"},
                )

                assert response is not None
                assert response.status_code == 200
                # 2 llamadas (403 + retry success)
                assert mock_get.call_count == 2
                # 1 sleep (después del 403, antes del 2do intento)
                assert mock_sleep.call_count == 1
                # Verificar backoff = 1 segundo
                mock_sleep.assert_called_with(1)

    @pytest.mark.asyncio
    async def test_fetch_with_retry_backoff_exponential(self):
        """Verifica que backoff es exponencial: 1s, 2s, 4s, 8s."""
        scraper = GrantsGovScraperScrapling()

        # Simular 403 en todos los intentos
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 403

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                response = await scraper._fetch_with_retry(
                    "https://api.grants.gov/v1/api/search2",
                    params={"searchString": "test"},
                )

                assert response is None
                # 4 intentos = 4 llamadas get
                assert mock_get.call_count == 4
                # 3 sleeps (después de cada fallo excepto el último)
                assert mock_sleep.call_count == 3

                # Verificar backoff times: 1, 2, 4 segundos
                sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
                assert sleep_calls == [1, 2, 4], f"Expected [1, 2, 4], got {sleep_calls}"

    @pytest.mark.asyncio
    async def test_fetch_with_retry_exhausts_after_max_retries(self):
        """Verifica que retorna None después de max_retries intentos fallidos."""
        scraper = GrantsGovScraperScrapling()
        assert scraper.max_retries == 4

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 500  # Server error

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                response = await scraper._fetch_with_retry(
                    "https://api.grants.gov/v1/api/search2",
                    params={"searchString": "test"},
                )

                assert response is None
                assert mock_get.call_count == 4  # Max retries


class TestFetchAPIWithRetry:
    """Tests para _fetch_api() con retry integrado."""

    @pytest.mark.asyncio
    async def test_fetch_api_integrates_retry(self):
        """Verifica que _fetch_api() usa _fetch_with_retry()."""
        scraper = GrantsGovScraperScrapling()

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "opportunities": [
                {
                    "id": "1",
                    "title": "Early Childhood Grant",
                    "description": "ECD funding",
                    "deadline_date": "2026-12-31",
                }
            ]
        }

        with patch.object(scraper, "_fetch_with_retry", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_response

            with patch("asyncio.sleep", new_callable=AsyncMock):
                items = await scraper._fetch_api()

                # Verificar que _fetch_with_retry fue llamado (una vez por search term × 1 página)
                assert mock_fetch.call_count >= 1
                assert len(items) > 0

    @pytest.mark.asyncio
    async def test_fetch_api_rate_limiting(self):
        """Verifica que hay rate limiting entre pages y search terms."""
        scraper = GrantsGovScraperScrapling()

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"opportunities": []}

        with patch.object(scraper, "_fetch_with_retry", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_response

            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                await scraper._fetch_api()

                # Múltiples sleeps esperados (por page + por search term)
                assert mock_sleep.call_count > 0


class TestIntegration:
    """Tests de integración end-to-end."""

    @pytest.mark.asyncio
    async def test_scraper_fallback_to_web_on_api_exhaustion(self):
        """Verifica fallback a web scraping si API agota reintentos."""
        scraper = GrantsGovScraperScrapling()

        # Simular que API falla exhaustivamente
        with patch.object(scraper, "_fetch_api", new_callable=AsyncMock) as mock_api:
            with patch.object(scraper, "_fetch_web_scrapling", new_callable=AsyncMock) as mock_web:
                mock_api.side_effect = Exception("API failed after retries")
                mock_web.return_value = [
                    {
                        "title": "Web scraped grant",
                        "url": "https://example.com/grant",
                        "description": "Early childhood",
                        "source": "grantsgov_web",
                    }
                ]

                # fetch_raw debería usar fallback a web
                items = await scraper.fetch_raw()

                # API fue intenta
                assert mock_api.called
                # Web scraping fue usado como fallback
                assert mock_web.called


# ═════════════════════════════════════════════════════════════════════════════
# COMANDO PARA EJECUTAR ESTOS TESTS:
# ═════════════════════════════════════════════════════════════════════════════
# pytest backend/tests/test_grantsgov_retry.py -v
# pytest backend/tests/test_grantsgov_retry.py -v -s  # Con stdout
# pytest backend/tests/test_grantsgov_retry.py::TestRetryLogic -v
# ═════════════════════════════════════════════════════════════════════════════
