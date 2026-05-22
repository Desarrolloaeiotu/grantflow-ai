#!/usr/bin/env python3
"""Ejecutar scrapers localmente en el host sin Docker."""

import asyncio
import os
import sys
from pathlib import Path

# Configurar variables de entorno
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/grantflow")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-dummy")
os.environ.setdefault("GOOGLE_API_KEY", "AIza-dummy")
os.environ.setdefault("USD_TO_COP_RATE", "4050")

# Agregar backend al path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.scrapers.runner import run_scraper, SCRAPERS

async def main():
    """Ejecutar todos los scrapers."""
    print(f"Scrapers disponibles: {list(SCRAPERS.keys())}")
    print()

    for scraper_name in ["nacional_colombia", "grantsgov", "bid", "unwomen", "developmentaid", "rss"]:
        if scraper_name not in SCRAPERS:
            print(f"[WARN] {scraper_name} no disponible")
            continue

        print(f"[RUN] Ejecutando {scraper_name}...")
        try:
            count = await run_scraper(scraper_name, do_score=True)
            print(f"[OK] {scraper_name}: {count} oportunidades")
        except Exception as e:
            print(f"[ERR] {scraper_name}: {str(e)[:100]}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
