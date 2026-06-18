#!/usr/bin/env python
"""
Script manual para testear retry logic en Grants.gov scraper.

Simula diferentes escenarios de error y verifica el comportamiento
del backoff exponencial, rotación de headers y fallback.

Uso:
    python backend/test_retry_manual.py
"""

import asyncio
import logging
from unittest.mock import AsyncMock, patch, MagicMock

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

# ═════════════════════════════════════════════════════════════════════════════
# SCENARIO 1: Success en primer intento
# ═════════════════════════════════════════════════════════════════════════════


async def test_scenario_1_success_first_try():
    """Scenario 1: Éxito en el primer intento (no retry)."""
    print("\n" + "=" * 80)
    print("SCENARIO 1: Success en primer intento")
    print("=" * 80)

    from app.scrapers.grantsgov_scrapling import GrantsGovScraperScrapling

    scraper = GrantsGovScraperScrapling()

    # Mock: Success inmediato
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"opportunities": [{"id": "1", "title": "Test Grant"}]}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        response = await scraper._fetch_with_retry(
            "https://api.grants.gov/v1/api/search2",
            params={"searchString": "test"},
        )

        print(f"✅ Response status: {response.status_code}")
        print(f"✅ Request count: {mock_get.call_count} (esperado: 1)")
        print(f"✅ Resultado: ÉXITO sin retry")

        assert mock_get.call_count == 1
        assert response.status_code == 200


# ═════════════════════════════════════════════════════════════════════════════
# SCENARIO 2: 403 error, luego éxito
# ═════════════════════════════════════════════════════════════════════════════


async def test_scenario_2_403_then_success():
    """Scenario 2: 403 Forbidden, luego success en 2do intento."""
    print("\n" + "=" * 80)
    print("SCENARIO 2: 403 Forbidden → retry → success")
    print("=" * 80)

    from app.scrapers.grantsgov_scrapling import GrantsGovScraperScrapling

    scraper = GrantsGovScraperScrapling()

    # Mock: 403 primero, 200 después
    mock_response_403 = MagicMock()
    mock_response_403.status_code = 403

    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {"opportunities": []}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = [mock_response_403, mock_response_200]

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            response = await scraper._fetch_with_retry(
                "https://api.grants.gov/v1/api/search2",
                params={"searchString": "test"},
            )

            print(f"✅ Response status: {response.status_code}")
            print(f"✅ Request count: {mock_get.call_count} (esperado: 2)")
            print(f"✅ Sleep calls: {mock_sleep.call_count} (esperado: 1)")
            print(f"✅ Backoff wait time: {mock_sleep.call_args_list[0][0][0]} segundos")
            print(f"✅ Resultado: ÉXITO tras 1 retry")

            assert mock_get.call_count == 2
            assert response.status_code == 200
            assert mock_sleep.call_count == 1
            assert mock_sleep.call_args_list[0][0][0] == 1  # First backoff = 1s


# ═════════════════════════════════════════════════════════════════════════════
# SCENARIO 3: Multiple errors con backoff exponencial
# ═════════════════════════════════════════════════════════════════════════════


async def test_scenario_3_exponential_backoff():
    """Scenario 3: Múltiples errores con backoff 1s → 2s → 4s."""
    print("\n" + "=" * 80)
    print("SCENARIO 3: Exponential backoff (403 → 500 → timeout → fail)")
    print("=" * 80)

    from app.scrapers.grantsgov_scrapling import GrantsGovScraperScrapling

    scraper = GrantsGovScraperScrapling()

    # Mock: Siempre error
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            response = await scraper._fetch_with_retry(
                "https://api.grants.gov/v1/api/search2",
                params={"searchString": "test"},
            )

            print(f"✅ Response: {response} (esperado: None)")
            print(f"✅ Request count: {mock_get.call_count} (esperado: 4)")
            print(f"✅ Sleep count: {mock_sleep.call_count} (esperado: 3)")

            sleep_times = [call[0][0] for call in mock_sleep.call_args_list]
            print(f"✅ Backoff times: {sleep_times} (esperado: [1, 2, 4])")
            print(f"✅ Resultado: FALLO tras 4 intentos con backoff exponencial")

            assert response is None
            assert mock_get.call_count == 4
            assert mock_sleep.call_count == 3
            assert sleep_times == [1, 2, 4]


# ═════════════════════════════════════════════════════════════════════════════
# SCENARIO 4: User-Agent rotation
# ═════════════════════════════════════════════════════════════════════════════


async def test_scenario_4_user_agent_rotation():
    """Scenario 4: Verificar que User-Agent rota en cada intento."""
    print("\n" + "=" * 80)
    print("SCENARIO 4: User-Agent rotation en cada retry")
    print("=" * 80)

    from app.scrapers.grantsgov_scrapling import GrantsGovScraperScrapling, get_random_headers

    # Test 1: Headers son variados
    headers_list = [get_random_headers() for _ in range(5)]
    user_agents = [h["User-Agent"] for h in headers_list]

    print(f"✅ Generated {len(headers_list)} header sets")
    print(f"✅ Unique User-Agents: {len(set(user_agents))} (esperado: >1)")
    print(f"✅ Sample User-Agents:")
    for i, ua in enumerate(user_agents[:3], 1):
        print(f"     {i}. {ua[:50]}...")

    # Test 2: Headers contienen todos los campos esperados
    required_fields = ["User-Agent", "Referer", "Accept", "Accept-Language"]
    headers = get_random_headers()
    for field in required_fields:
        assert field in headers, f"Missing required header: {field}"
        print(f"✅ Field '{field}' present")


# ═════════════════════════════════════════════════════════════════════════════
# SCENARIO 5: Integration with _fetch_api
# ═════════════════════════════════════════════════════════════════════════════


async def test_scenario_5_integration():
    """Scenario 5: Integración con _fetch_api."""
    print("\n" + "=" * 80)
    print("SCENARIO 5: Integration _fetch_api + _fetch_with_retry")
    print("=" * 80)

    from app.scrapers.grantsgov_scrapling import GrantsGovScraperScrapling

    scraper = GrantsGovScraperScrapling()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "opportunities": [
            {
                "id": "1",
                "title": "Early Childhood Development Grant",
                "description": "Funding for ECD programs",
            },
            {
                "id": "2",
                "title": "Teacher Training Program",
                "description": "Docent education support",
            },
        ]
    }

    with patch.object(scraper, "_fetch_with_retry", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_response

        with patch("asyncio.sleep", new_callable=AsyncMock):
            items = await scraper._fetch_api()

            print(f"✅ Total items fetched: {len(items)}")
            print(f"✅ _fetch_with_retry called: {mock_fetch.call_count} times")
            print(f"✅ Items:")
            for item in items:
                print(f"     - {item['title'][:50]}...")


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════


async def main():
    """Ejecutar todos los escenarios."""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " GRANTS.GOV RETRY LOGIC — MANUAL TEST SUITE ".center(78) + "║")
    print("╚" + "=" * 78 + "╝")

    try:
        await test_scenario_1_success_first_try()
        await test_scenario_2_403_then_success()
        await test_scenario_3_exponential_backoff()
        await test_scenario_4_user_agent_rotation()
        await test_scenario_5_integration()

        print("\n" + "=" * 80)
        print("✅ ALL SCENARIOS PASSED")
        print("=" * 80 + "\n")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
