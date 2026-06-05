#!/usr/bin/env python3
"""
Check database directly
"""
import os
import sys
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

try:
    import psycopg
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg[binary]", "-q"])
    import psycopg

# Parse DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/grantflow")
parsed = urllib.parse.urlparse(DATABASE_URL)
db_config = {
    "host": parsed.hostname,
    "port": parsed.port or 5432,
    "user": parsed.username,
    "password": parsed.password,
    "dbname": parsed.path.lstrip("/"),
}

print(f"Conectando a: {db_config['host']}")

# Connect
conn = psycopg.connect(**db_config, autocommit=True)
cursor = conn.cursor()

# Get all tables
print("TABLAS EN LA BD:")
cursor.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name
""")
tables = cursor.fetchall()
for (table,) in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"  {table:30s} {count:,} registros")

# Get alembic version
print("\nVERSION EN ALEMBIC:")
cursor.execute("SELECT version_num FROM alembic_version")
version = cursor.fetchone()
if version:
    print(f"  {version[0]}")
else:
    print("  (no version)")

cursor.close()
conn.close()
