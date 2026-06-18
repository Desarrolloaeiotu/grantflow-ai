"""Tests para validar soporte de proxy en scrapers LinkedIn y Twitter."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scrapers.linkedin_improved import LinkedInScraperImproved
from app.scrapers.twitter_improved import TwitterScraperImproved, _get_proxy_config


class TestProxyConfiguration:
    """Pruebas de configuración de proxy."""

    def test_proxy_url_from_env(self):
        """Verificar que PROXY_URL se lee correctamente del .env."""
        with patch.dict(os.environ, {"PROXY_URL": "http://user:pass@proxy.example.com:8080"}):
            config = _get_proxy_config()
            assert config.get("proxies") == "http://user:pass@proxy.example.com:8080"

    def test_no_proxy_url_configured(self):
        """Verificar fallback cuando PROXY_URL no está configurado."""
        with patch.dict(os.environ, {}, clear=False):
            # Asegurar que PROXY_URL no existe
            os.environ.pop("PROXY_URL", None)
            config = _get_proxy_config()
            assert config == {}

    def test_linkedin_proxy_config(self):
        """Verificar que LinkedInScraperImproved obtiene configuración de proxy."""
        scraper = LinkedInScraperImproved()

        with patch.dict(os.environ, {"PROXY_URL": "http://proxy.local:3128"}):
            config = scraper._get_proxy_config()
            assert config.get("proxies") == "http://proxy.local:3128"

    def test_linkedin_no_proxy_fallback(self):
        """Verificar fallback sin proxy en LinkedIn."""
        scraper = LinkedInScraperImproved()

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PROXY_URL", None)
            config = scraper._get_proxy_config()
            assert config == {}


class TestLinkedInProxyIntegration:
    """Pruebas de integración proxy con LinkedIn scraper."""

    @pytest.mark.asyncio
    async def test_fetch_raw_with_proxy(self):
        """Verificar que fetch_raw pasa proxy a AsyncClient."""
        scraper = LinkedInScraperImproved()

        with patch.dict(os.environ, {"PROXY_URL": "http://proxy.test:8080"}):
            with patch("app.scrapers.linkedin_improved.httpx.AsyncClient") as mock_client_class:
                # Configurar mock para AsyncClient
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_client_class.return_value = mock_client

                # Mock para los métodos de fetch
                with patch.object(scraper, "_fetch_jobs_api", new_callable=AsyncMock, return_value=[]):
                    with patch.object(scraper, "_fetch_company_pages", new_callable=AsyncMock, return_value=[]):
                        with patch.object(scraper, "_fetch_google_search", new_callable=AsyncMock, return_value=[]):
                            await scraper.fetch_raw()

                # Verificar que AsyncClient fue llamado con proxies
                call_kwargs = mock_client_class.call_args[1]
                assert "proxies" in call_kwargs
                assert call_kwargs["proxies"] == "http://proxy.test:8080"

    @pytest.mark.asyncio
    async def test_fetch_raw_without_proxy(self):
        """Verificar que fetch_raw funciona sin proxy (fallback)."""
        scraper = LinkedInScraperImproved()

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PROXY_URL", None)

            with patch("app.scrapers.linkedin_improved.httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_client_class.return_value = mock_client

                with patch.object(scraper, "_fetch_jobs_api", new_callable=AsyncMock, return_value=[]):
                    with patch.object(scraper, "_fetch_company_pages", new_callable=AsyncMock, return_value=[]):
                        with patch.object(scraper, "_fetch_google_search", new_callable=AsyncMock, return_value=[]):
                            await scraper.fetch_raw()

                # Verificar que AsyncClient fue llamado sin proxies
                call_kwargs = mock_client_class.call_args[1]
                assert "proxies" not in call_kwargs


class TestTwitterProxyIntegration:
    """Pruebas de integración proxy con Twitter scraper."""

    @pytest.mark.asyncio
    async def test_fetch_raw_with_proxy(self):
        """Verificar que fetch_raw de Twitter pasa proxy a AsyncClient."""
        scraper = TwitterScraperImproved()

        with patch.dict(os.environ, {"PROXY_URL": "http://proxy.twitter:8080"}):
            with patch("app.scrapers.twitter_improved.fetch_twitter_google_news", new_callable=AsyncMock, return_value=[]):
                with patch("app.scrapers.twitter_improved.httpx.AsyncClient") as mock_client_class:
                    mock_client = AsyncMock()
                    mock_client.__aenter__.return_value = mock_client
                    mock_client.__aexit__.return_value = None
                    mock_client_class.return_value = mock_client

                    await scraper.fetch_raw()

                    # Verificar que AsyncClient fue llamado
                    assert mock_client_class.called


class TestRandomDelayImplementation:
    """Pruebas para verificar delays aleatorios entre requests."""

    @pytest.mark.asyncio
    async def test_linkedin_random_delay(self):
        """Verificar que LinkedIn aplica delay entre requests."""
        scraper = LinkedInScraperImproved()

        with patch("app.scrapers.linkedin_improved.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            with patch("app.scrapers.linkedin_improved.httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_client_class.return_value = mock_client
                mock_client.get.return_value.status_code = 200
                mock_client.get.return_value.json.return_value = {"elements": []}

                with patch.object(scraper, "_fetch_company_pages", new_callable=AsyncMock, return_value=[]):
                    with patch.object(scraper, "_fetch_google_search", new_callable=AsyncMock, return_value=[]):
                        await scraper.fetch_raw()

                # Verificar que sleep fue llamado (al menos una vez)
                assert mock_sleep.called


class TestProxyUrlFormats:
    """Pruebas con diferentes formatos de URL de proxy."""

    def test_proxy_url_with_credentials(self):
        """Proxy con usuario y contraseña."""
        with patch.dict(os.environ, {"PROXY_URL": "http://admin:secret123@proxy.internal.com:3128"}):
            config = _get_proxy_config()
            assert config.get("proxies") == "http://admin:secret123@proxy.internal.com:3128"

    def test_proxy_url_simple(self):
        """Proxy sin credenciales."""
        with patch.dict(os.environ, {"PROXY_URL": "http://192.168.1.100:8080"}):
            config = _get_proxy_config()
            assert config.get("proxies") == "http://192.168.1.100:8080"

    def test_proxy_url_socks5(self):
        """Proxy SOCKS5."""
        with patch.dict(os.environ, {"PROXY_URL": "socks5://proxy.example.com:1080"}):
            config = _get_proxy_config()
            assert config.get("proxies") == "socks5://proxy.example.com:1080"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
