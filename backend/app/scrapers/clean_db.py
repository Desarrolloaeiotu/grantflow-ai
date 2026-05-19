"""Script para limpiar la base de datos de oportunidades irrelevantes.

Uso: python -m app.scrapers.clean_db
"""

import asyncio
from sqlalchemy import text

from app.core.database import AsyncSessionLocal


async def clean_database():
    """Borra todas las oportunidades y score_log."""
    async with AsyncSessionLocal() as db:
        try:
            print("[CLEAN] Borrando datos anteriores...")

            # Borrar score_log primero (FK constraint)
            result = await db.execute(text("DELETE FROM score_log"))
            rows_deleted_log = result.rowcount
            print(f"[OK] Eliminados {rows_deleted_log} registros de score_log")

            # Borrar opportunities
            result = await db.execute(text("DELETE FROM opportunities"))
            rows_deleted_opp = result.rowcount
            print(f"[OK] Eliminadas {rows_deleted_opp} oportunidades")

            await db.commit()
            print("\n[SUCCESS] Base de datos limpia. Lista para nuevos datos.")

        except Exception as e:
            await db.rollback()
            print(f"\n[ERROR] Problema durante la limpieza: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(clean_database())
