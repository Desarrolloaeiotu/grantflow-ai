#!/usr/bin/env python3
"""
Auditoría de BD y reset para GrantFlow AI
Ejecutar: python audit_and_reset.py
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Force UTF-8 encoding
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Instalar psycopg3 si no está disponible
try:
    import psycopg
except ImportError:
    print("Instalando psycopg3...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg[binary]", "-q"])
    import psycopg

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/grantflow")

# Parse connection string
import urllib.parse
parsed = urllib.parse.urlparse(DATABASE_URL)
db_config = {
    "host": parsed.hostname or "localhost",
    "port": parsed.port or 5432,
    "user": parsed.username or "postgres",
    "password": parsed.password or "postgres",
    "dbname": parsed.path.lstrip("/") or "grantflow",
}

def connect_db():
    """Conectar a la BD."""
    try:
        conn = psycopg.connect(**db_config)
        return conn
    except Exception as e:
        print(f"\nERROR: No se pudo conectar a la BD: {e}")
        print(f"   Configuracion: host={db_config['host']}, port={db_config['port']}, user={db_config['user']}")
        print(f"\n   Asegurate de que Docker este corriendo:")
        print(f"   docker-compose up -d")
        return None

def audit_database():
    """Ejecutar auditoría de BD."""
    conn = connect_db()
    if not conn:
        return False

    cursor = conn.cursor()
    # Set autocommit to handle errors better
    conn.autocommit = True

    queries = {
        "RESUMEN GENERAL": """
            SELECT
              COUNT(*) as total_oportunidades,
              COUNT(CASE WHEN title IS NULL THEN 1 END) as null_title,
              COUNT(CASE WHEN deadline IS NULL THEN 1 END) as null_deadline,
              COUNT(CASE WHEN score_total IS NULL THEN 1 END) as null_score,
              COUNT(CASE WHEN decision IS NULL THEN 1 END) as null_decision
            FROM opportunities
        """,
        "DISTRIBUCIÓN DE VENTANAS": """
            SELECT market_window, COUNT(*) as count
            FROM opportunities
            GROUP BY market_window
            ORDER BY count DESC
        """,
        "DISTRIBUCIÓN DE DECISIONES": """
            SELECT decision, COUNT(*) as count
            FROM opportunities
            GROUP BY decision
            ORDER BY count DESC
        """,
        "DISTRIBUCIÓN DE FUENTES": """
            SELECT source_name, COUNT(*) as count
            FROM opportunities
            GROUP BY source_name
            ORDER BY count DESC
        """,
        "OPORTUNIDADES SIN MONTO": """
            SELECT source_name, COUNT(*) as without_amount
            FROM opportunities
            WHERE amount_max_cop IS NULL
            GROUP BY source_name
            ORDER BY without_amount DESC
        """,
        "DUPLICADOS": """
            SELECT title, COUNT(*) as cnt
            FROM opportunities
            GROUP BY title
            HAVING COUNT(*) > 1
            ORDER BY cnt DESC
            LIMIT 10
        """,
        "NACIONAL vs GLOBAL": """
            SELECT
              COUNT(CASE WHEN source_name IN ('nacional_colombia', 'secop') THEN 1 END) as nacional_count,
              COUNT(CASE WHEN source_name NOT IN ('nacional_colombia', 'secop') THEN 1 END) as global_count
            FROM opportunities
        """,
    }

    print("\n" + "="*80)
    print("AUDITORIA DE BASE DE DATOS - GrantFlow AI")
    print("="*80 + "\n")
    print(f"Base de datos: {db_config['dbname']}")
    print(f"Host: {db_config['host']}:{db_config['port']}")
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    for title, query in queries.items():
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            print(f"[{title}]")
            if result:
                # Get column names
                col_names = [desc[0] for desc in cursor.description]
                for row in result:
                    row_dict = dict(zip(col_names, row))
                    print(f"  {row_dict}")
            else:
                print(f"  (sin resultados)")
            print()
        except Exception as e:
            print(f"ERROR en {title}")
            print(f"  {e}\n")

    # Get table info
    print("TABLAS Y REGISTROS:")
    print("-" * 40)
    try:
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        for (table,) in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table:30s} {count:,} registros")
            except Exception as e:
                print(f"  {table:30s} ERROR: {e}")
    except Exception as e:
        print(f"Error obteniendo tablas: {e}")

    print("-" * 40)
    cursor.close()
    conn.close()
    print("\n" + "="*80)
    return True

def reset_database():
    """DROP de todas las tablas."""
    conn = connect_db()
    if not conn:
        return False

    cursor = conn.cursor()

    print("\n" + "="*80)
    print("RESET DE BASE DE DATOS")
    print("="*80)

    try:
        # Obtener todas las tablas
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]

        if not tables:
            print("\nNo hay tablas para eliminar.")
            cursor.close()
            conn.close()
            return True

        print(f"\nTablas a ELIMINAR: {len(tables)}")
        for table in sorted(tables):
            print(f"  - {table}")

        confirm = input("\nADVERTENCIA: Confirmar DROP de TODAS las tablas? (si/no): ").strip().lower()
        if confirm not in ["si", "yes", "y"]:
            print("Operacion CANCELADA.")
            cursor.close()
            conn.close()
            return False

        print("\nEliminando tablas...")

        # Usar DROP CASCADE
        for table in tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                print(f"  [OK] {table} eliminada")
            except Exception as e:
                print(f"  [ERROR] {table}: {e}")

        conn.commit()
        print("\n[OK] Todas las tablas eliminadas correctamente")
        print("\nPROXIMO PASO:")
        print("   cd backend")
        print("   alembic upgrade head")

    except Exception as e:
        print(f"\nERROR durante reset: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        return False

    cursor.close()
    conn.close()
    return True

if __name__ == "__main__":
    try:
        # Ejecutar auditoria
        if audit_database():
            # Preguntar si hacer reset
            reset_confirm = input("\nQUIERES HACER UN RESET (DROP) DE LA BD? (si/no): ").strip().lower()
            if reset_confirm in ["si", "yes", "y"]:
                reset_database()
            else:
                print("Reset NO ejecutado.")
        else:
            print("\nNo se pudo ejecutar la auditoria.")
            sys.exit(1)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
