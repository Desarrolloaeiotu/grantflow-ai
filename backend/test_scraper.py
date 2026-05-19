#!/usr/bin/env python
"""Test scraper nacional_colombia rápido."""

import asyncio
import sys

from app.scrapers.nacional_colombia import NacionalColombiaScraper
from app.core.database import AsyncSessionLocal


async def test_scraper():
    """Ejecuta el scraper y muestra resultados."""
    scraper = NacionalColombiaScraper()

    print("[TEST] Iniciando scraper Nacional Colombia...")
    print(f"[TEST] Fuente: {scraper.source_name}")

    try:
        # Fetch raw data
        raw_data = await scraper.fetch_raw()
        print(f"[FETCH] {len(raw_data)} items encontrados\n")

        if not raw_data:
            print("[RESULT] No se encontraron oportunidades.")
            return

        # Normalize y filter
        opportunities = []
        for raw in raw_data[:20]:  # Primeros 20 para prueba
            opp = scraper.normalize(raw)
            if opp:
                opportunities.append(opp)
                print(f"[ACCEPT] {opp.title[:60]}")
            else:
                title = raw.get("title", "Unknown")[:60]
                print(f"[REJECT] {title}")

        print(f"\n[SUMMARY] {len(opportunities)} de {len(raw_data[:20])} aceptadas")
        print(f"[RATE] {len(opportunities)/len(raw_data[:20])*100:.0f}% pass rate")

        if opportunities:
            print(f"\n[SAMPLE] Primera oportunidad:")
            opp = opportunities[0]
            print(f"  Title: {opp.title}")
            print(f"  Funder: {opp.funder_name}")
            print(f"  Source: {opp.source_name}")
            print(f"  URL: {opp.url_rfp}")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_scraper())
