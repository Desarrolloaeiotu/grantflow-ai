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
            print("[CLEAN] Borrando score_log...")
            result = await db.execute(text("DELETE FROM score_log"))
            rows_log = result.rowcount
            await db.commit()
            print(f"[OK] {rows_log} score_log eliminados y COMMITTED")

            print("[CLEAN] Borrando opportunities...")
            result = await db.execute(text("DELETE FROM opportunities"))
            rows_opp = result.rowcount
            await db.commit()
            print(f"[OK] {rows_opp} opportunities eliminadas y COMMITTED")

            print(f"\n[SUCCESS] Total eliminado: {rows_log + rows_opp} registros")
            print("[SUCCESS] Base de datos limpia. Lista para nuevos datos.")

        except Exception as e:
            await db.rollback()
            print(f"\n[ERROR] {e}")
            raise


if __name__ == "__main__":
    asyncio.run(clean_database())
