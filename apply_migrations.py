#!/usr/bin/env python3
"""
Apply Alembic migrations directly
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

# Set environment
os.chdir("backend")
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/grantflow"

try:
    from alembic.config import Config
    from alembic import command

    print("Aplicando migraciones...")
    config = Config("alembic.ini")

    # Run upgrade
    command.upgrade(config, "head")
    print("\n[OK] Migraciones aplicadas correctamente!")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
