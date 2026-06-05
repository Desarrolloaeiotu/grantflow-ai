#!/usr/bin/env python3
"""
Execute seed SQL for 60+ organizations
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import urllib.parse

# Load .env from backend directory
backend_path = Path(__file__).parent / "backend"
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv()

try:
    import psycopg
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg[binary]", "-q"])
    import psycopg

# Parse DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

print(f"DATABASE_URL: {DATABASE_URL[:50]}...")

parsed = urllib.parse.urlparse(DATABASE_URL)
db_config = {
    "host": parsed.hostname,
    "port": parsed.port or 5432,
    "user": parsed.username,
    "password": parsed.password,
    "dbname": parsed.path.lstrip("/"),
}

print(f"Conectando a: {db_config['host']} - {db_config['dbname']}")

# Read SQL file
sql_file = Path(__file__).parent / "seed_global_orgs.sql"
with open(sql_file, "r") as f:
    sql_content = f.read()

# Execute
try:
    conn = psycopg.connect(**db_config, autocommit=True)
    cursor = conn.cursor()

    print(f"\nEjecutando seed SQL...")
    cursor.execute(sql_content)

    # Count organizations
    cursor.execute("SELECT COUNT(*) FROM funders WHERE verified_data = true")
    count = cursor.fetchone()[0]

    print(f"\n[OK] Seed completado!")
    print(f"[OK] Total organizaciones en BD: {count}")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
