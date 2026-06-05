#!/usr/bin/env python3
"""
Execute seed for global organizations
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

os.chdir(backend_path)

# Import and run seed
try:
    from app.scrapers.seed_global_organizations import seed_global_organizations
    import asyncio

    print("Cargando 60+ organizaciones globales...")
    asyncio.run(seed_global_organizations())
    print("✓ Seed completado!")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
