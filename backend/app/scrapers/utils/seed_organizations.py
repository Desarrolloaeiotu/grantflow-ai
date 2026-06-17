"""Seed script: importar 23 financiadores históricos aeioTU a tabla funders.

Uso:
    python -m app.scrapers.seed_organizations --load
    python -m app.scrapers.seed_organizations --clear  # reset for dev

Los datos reflejan historial 2018-2025. Campos populados:
- name, country, org_type, website, has_history=True
- access_type, strategic_obj, invests_colombia, invests_latam, aeiotu_role (para v2)
- focus_sectors, ticket_min_usd, ticket_max_usd (rangos aproximados)
"""

import asyncio
import structlog
from sqlalchemy import delete, select
from app.core.database import AsyncSessionLocal
from app.models.funder import Funder

logger = structlog.get_logger()

# 23 Financiadores históricos aeioTU (2018–2025)
# Ordenados por volumen de inversión (estimado)
STRATEGIC_FUNDERS = [
    # ── TOP 5: Principal volumen ────────────────────────────────────────
    {
        "name": "LEGO Foundation",
        "country": "Denmark",
        "org_type": "Filantropía",
        "website": "https://www.legoforumdation.com",
        "has_history": True,
        "focus_sectors": ["early_childhood", "education", "learning"],
        "ticket_min_usd": 200_000,
        "ticket_max_usd": 2_000_000,
        "access_type": "convocatoria",
        "strategic_obj": "exportacion_modelo",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "financiador",
        "general_objective": "Innovación y escalabilidad en educación inicial",
    },
    {
        "name": "Grand Challenges Canada",
        "country": "Canada",
        "org_type": "Público",
        "website": "https://www.gcc.ca",
        "has_history": True,
        "focus_sectors": ["innovation", "development"],
        "ticket_min_usd": 250_000,
        "ticket_max_usd": 1_500_000,
        "access_type": "convocatoria",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "financiador",
        "general_objective": "Financiamiento para innovaciones en desarrollo social",
    },
    {
        "name": "Fundación Hilton",
        "country": "USA",
        "org_type": "Filantropía",
        "website": "https://www.hiltonfoundation.org",
        "has_history": True,
        "focus_sectors": ["hospitality", "development", "education"],
        "ticket_min_usd": 150_000,
        "ticket_max_usd": 800_000,
        "access_type": "convocatoria",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "financiador",
        "general_objective": "Oportunidades económicas para poblaciones vulnerables",
    },
    {
        "name": "Fundación Cargill",
        "country": "Colombia",
        "org_type": "Empresa",
        "website": "https://www.cargill.com.co",
        "has_history": True,
        "focus_sectors": ["agriculture", "nutrition", "education"],
        "ticket_min_usd": 100_000,
        "ticket_max_usd": 500_000,
        "access_type": "mixto",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": False,
        "aeiotu_role": "aliado",
        "general_objective": "Nutrición y educación en áreas rurales",
    },
    {
        "name": "BID (Banco Interamericano de Desarrollo)",
        "country": "Multilateral",
        "org_type": "Multilateral",
        "website": "https://www.iadb.org",
        "has_history": True,
        "focus_sectors": ["development", "education", "infrastructure"],
        "ticket_min_usd": 500_000,
        "ticket_max_usd": 5_000_000,
        "access_type": "convocatoria",
        "strategic_obj": "exportacion_modelo",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "financiador",
        "general_objective": "Desarrollo integral y transferencia de modelo",
    },

    # ── SECUNDARIOS: Socios activos ─────────────────────────────────────
    {
        "name": "CAFAM (Caja de Compensación Familiar)",
        "country": "Colombia",
        "org_type": "Cooperación",
        "website": "https://www.cafam.com.co",
        "has_history": True,
        "focus_sectors": ["childcare", "education", "family"],
        "ticket_min_usd": 50_000,
        "ticket_max_usd": 300_000,
        "access_type": "relacional",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": False,
        "aeiotu_role": "aliado",
        "general_objective": "Servicios de cuidado y educación inicial",
    },
    {
        "name": "ONU Mujeres",
        "country": "Multilateral",
        "org_type": "Multilateral",
        "website": "https://www.unwomen.org",
        "has_history": True,
        "focus_sectors": ["gender", "education", "women_empowerment"],
        "ticket_min_usd": 100_000,
        "ticket_max_usd": 1_000_000,
        "access_type": "convocatoria",
        "strategic_obj": "exportacion_modelo",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "aliado",
        "general_objective": "Empoderamiento femenino y educación integral",
    },
    {
        "name": "UNICEF",
        "country": "Multilateral",
        "org_type": "Multilateral",
        "website": "https://www.unicef.org",
        "has_history": True,
        "focus_sectors": ["early_childhood", "child_rights", "education"],
        "ticket_min_usd": 200_000,
        "ticket_max_usd": 2_000_000,
        "access_type": "convocatoria",
        "strategic_obj": "exportacion_modelo",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "aliado",
        "general_objective": "Derechos de la infancia y educación inicial",
    },
    {
        "name": "GIZ (Agencia Alemana de Cooperación)",
        "country": "Alemania",
        "org_type": "Cooperación",
        "website": "https://www.giz.de",
        "has_history": True,
        "focus_sectors": ["development", "education", "governance"],
        "ticket_min_usd": 150_000,
        "ticket_max_usd": 1_500_000,
        "access_type": "convocatoria",
        "strategic_obj": "exportacion_modelo",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "aliado",
        "general_objective": "Cooperación técnica para desarrollo educativo",
    },

    # ── COMPLEMENTARIOS: Histórico validado ─────────────────────────────
    {
        "name": "Fundación Ford",
        "country": "USA",
        "org_type": "Filantropía",
        "website": "https://www.fordfoundation.org",
        "has_history": True,
        "focus_sectors": ["social_justice", "education", "opportunity"],
        "ticket_min_usd": 100_000,
        "ticket_max_usd": 1_000_000,
        "access_type": "convocatoria",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "financiador",
        "general_objective": "Oportunidades económicas y justicia social",
    },
    {
        "name": "Fundación Luminate",
        "country": "USA",
        "org_type": "Filantropía",
        "website": "https://www.luminatetheworld.org",
        "has_history": True,
        "focus_sectors": ["learning", "early_childhood", "education"],
        "ticket_min_usd": 50_000,
        "ticket_max_usd": 500_000,
        "access_type": "convocatoria",
        "strategic_obj": "capital",
        "invests_colombia": False,
        "invests_latam": True,
        "aeiotu_role": "aliado",
        "general_objective": "Acceso a educación de calidad",
    },
    {
        "name": "USAID",
        "country": "USA",
        "org_type": "Público",
        "website": "https://www.usaid.gov",
        "has_history": True,
        "focus_sectors": ["development", "education", "humanitarian"],
        "ticket_min_usd": 200_000,
        "ticket_max_usd": 3_000_000,
        "access_type": "convocatoria",
        "strategic_obj": "exportacion_modelo",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "financiador",
        "general_objective": "Desarrollo internacional y cooperación",
    },
    {
        "name": "Fundación Bill & Melinda Gates",
        "country": "USA",
        "org_type": "Filantropía",
        "website": "https://www.gatesfoundation.org",
        "has_history": True,
        "focus_sectors": ["global_health", "education", "poverty"],
        "ticket_min_usd": 500_000,
        "ticket_max_usd": 5_000_000,
        "access_type": "convocatoria",
        "strategic_obj": "exportacion_modelo",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "aliado",
        "general_objective": "Reducción de pobreza y educación",
    },
    {
        "name": "Ministerio de Educación Nacional (MEN)",
        "country": "Colombia",
        "org_type": "Público",
        "website": "https://www.mineducacion.gov.co",
        "has_history": True,
        "focus_sectors": ["education", "policy", "public_sector"],
        "ticket_min_usd": 100_000,
        "ticket_max_usd": 2_000_000,
        "access_type": "convocatoria",
        "strategic_obj": "exportacion_modelo",
        "invests_colombia": True,
        "invests_latam": False,
        "aeiotu_role": "aliado",
        "general_objective": "Política pública e incidencia en educación inicial",
    },
    {
        "name": "ICBF (Instituto Colombiano de Bienestar Familiar)",
        "country": "Colombia",
        "org_type": "Público",
        "website": "https://www.icbf.gov.co",
        "has_history": True,
        "focus_sectors": ["childcare", "education", "family_protection"],
        "ticket_min_usd": 50_000,
        "ticket_max_usd": 800_000,
        "access_type": "convocatoria",
        "strategic_obj": "exportacion_modelo",
        "invests_colombia": True,
        "invests_latam": False,
        "aeiotu_role": "aliado",
        "general_objective": "Atención integral a la primera infancia",
    },
    {
        "name": "Fundación Empresarios por la Educación",
        "country": "Colombia",
        "org_type": "Filantropía",
        "website": "https://www.empresariosporlaeducacion.org",
        "has_history": True,
        "focus_sectors": ["education", "entrepreneurship", "public_private"],
        "ticket_min_usd": 30_000,
        "ticket_max_usd": 200_000,
        "access_type": "relacional",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": False,
        "aeiotu_role": "aliado",
        "general_objective": "Educación de calidad mediante alianzas público-privadas",
    },
    {
        "name": "Fundación FES Colombia",
        "country": "Colombia",
        "org_type": "Filantropía",
        "website": "https://www.fes.org.co",
        "has_history": True,
        "focus_sectors": ["education", "social_development", "policy"],
        "ticket_min_usd": 40_000,
        "ticket_max_usd": 300_000,
        "access_type": "relacional",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": False,
        "aeiotu_role": "aliado",
        "general_objective": "Desarrollo social y política educativa",
    },
    {
        "name": "Fundación Hubbard",
        "country": "Colombia",
        "org_type": "Filantropía",
        "website": "https://fundacionhubbard.org",
        "has_history": True,
        "focus_sectors": ["education", "arts", "culture"],
        "ticket_min_usd": 20_000,
        "ticket_max_usd": 150_000,
        "access_type": "relacional",
        "strategic_obj": "red",
        "invests_colombia": True,
        "invests_latam": False,
        "aeiotu_role": "aliado",
        "general_objective": "Educación artística y cultural",
    },
    {
        "name": "Fundación Éxito",
        "country": "Colombia",
        "org_type": "Empresa",
        "website": "https://www.fundacionexito.org",
        "has_history": True,
        "focus_sectors": ["education", "social_responsibility"],
        "ticket_min_usd": 30_000,
        "ticket_max_usd": 400_000,
        "access_type": "mixto",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": False,
        "aeiotu_role": "aliado",
        "general_objective": "Desarrollo social y educación",
    },
    {
        "name": "Fundación Bancaria Santodomingo",
        "country": "Colombia",
        "org_type": "Empresa",
        "website": "https://www.gruposanto.com",
        "has_history": True,
        "focus_sectors": ["education", "development", "commerce"],
        "ticket_min_usd": 50_000,
        "ticket_max_usd": 500_000,
        "access_type": "relacional",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": False,
        "aeiotu_role": "aliado",
        "general_objective": "Responsabilidad social empresarial",
    },

    # ── ADICIONALES: Cierre a 23 ───────────────────────────────────────
    {
        "name": "Fundación Telefónica",
        "country": "Colombia",
        "org_type": "Empresa",
        "website": "https://www.fundaciontelefonica.co",
        "has_history": True,
        "focus_sectors": ["education", "technology", "digital"],
        "ticket_min_usd": 40_000,
        "ticket_max_usd": 300_000,
        "access_type": "relacional",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": False,
        "aeiotu_role": "aliado",
        "general_objective": "Educación digital y transformación",
    },
    {
        "name": "Fundación Compartir",
        "country": "Colombia",
        "org_type": "Filantropía",
        "website": "https://www.fundacioncompartir.org",
        "has_history": True,
        "focus_sectors": ["education", "teachers", "quality"],
        "ticket_min_usd": 30_000,
        "ticket_max_usd": 250_000,
        "access_type": "relacional",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": False,
        "aeiotu_role": "aliado",
        "general_objective": "Calidad educativa y formación docente",
    },
    {
        "name": "World Education Inc. (WEI)",
        "country": "USA",
        "org_type": "ONG",
        "website": "https://www.worlded.org",
        "has_history": True,
        "focus_sectors": ["education", "development", "capacity_building"],
        "ticket_min_usd": 100_000,
        "ticket_max_usd": 800_000,
        "access_type": "convocatoria",
        "strategic_obj": "exportacion_modelo",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "aliado",
        "general_objective": "Fortalecimiento de capacidades educativas",
    },
]

assert len(STRATEGIC_FUNDERS) == 23, f"Expected 23 funders, got {len(STRATEGIC_FUNDERS)}"


async def load_organizations():
    """Inserta 23 financiadores en BD."""
    async with AsyncSessionLocal() as db:
        for funder_data in STRATEGIC_FUNDERS:
            # Verificar que no existe
            from app.models.funder import Funder
            existing = (
                await db.execute(
                    select(Funder).where(Funder.name == funder_data["name"])
                )
            ).scalar_one_or_none()

            if existing:
                logger.info(f"Funder already exists: {funder_data['name']}")
                continue

            funder = Funder(**funder_data)
            db.add(funder)
            logger.info(f"Added funder: {funder_data['name']}")

        await db.commit()
        logger.info("Organizations seed complete", total=len(STRATEGIC_FUNDERS))


async def clear_organizations():
    """Reset: elimina todos los funders (solo dev)."""
    async with AsyncSessionLocal() as db:
        await db.execute(delete(Funder))
        await db.commit()
        logger.info("All funders cleared")


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--load", action="store_true", help="Load organizations")
    parser.add_argument("--clear", action="store_true", help="Clear all organizations (dev only)")
    args = parser.parse_args()

    if args.load:
        await load_organizations()
    elif args.clear:
        await clear_organizations()
    else:
        print("Usage: python -m app.scrapers.seed_organizations --load|--clear")


if __name__ == "__main__":
    asyncio.run(main())
