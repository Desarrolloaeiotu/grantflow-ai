#!/usr/bin/env python3
"""
Execute Alembic migrations
"""
import os
import sys
import subprocess

os.chdir("backend")

# Try to run alembic upgrade head
print("Ejecutando migraciones de Alembic...")
result = subprocess.run(
    [sys.executable, "-m", "alembic.command", "upgrade", "head"],
    capture_output=False
)

if result.returncode == 0:
    print("\nMigraciones ejecutadas correctamente!")
else:
    # Try alternate approach
    print(f"\nError con comando alembic. Intentando con subprocess...")
    result2 = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=False
    )

    if result2.returncode == 0:
        print("\nMigraciones ejecutadas!")
    else:
        print(f"\nError: {result2.returncode}")
        sys.exit(1)
