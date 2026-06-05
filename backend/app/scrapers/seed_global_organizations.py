"""
Seed de 60+ organizaciones estratégicas para módulo GLOBAL
Criterios: Inversión en ECD/educación inicial, alcance en Latinoamérica/Colombia, potencial alianza
"""

import asyncio
from datetime import datetime, timezone
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.funder import Funder
from app.core.database import get_db
import structlog

logger = structlog.get_logger()

# Seed data: 60+ organizaciones
GLOBAL_ORGANIZATIONS = [
    # ── FILANTROPÍAS GLOBALES (TOP FUNDERS) ───────────────────────────────────
    {
        "name": "LEGO Foundation",
        "country": "Denmark",
        "org_type": "foundation",
        "website": "https://www.legofoundation.com",
        "linkedin_url": "https://www.linkedin.com/company/lego-foundation",
        "focus_sectors": ["early childhood", "ECD", "educational development", "play-based learning"],
        "ticket_min_usd": 50000,
        "ticket_max_usd": 5000000,
        "access_type": "convocatoria",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "financiador",
        "general_objective": "Transformar educación inicial mediante aprendizaje basado en juego",
        "has_history": True,
    },
    {
        "name": "Grand Challenges Canada",
        "country": "Canada",
        "org_type": "foundation",
        "website": "https://www.grandchallengescanada.ca",
        "linkedin_url": "https://www.linkedin.com/company/grand-challenges-canada",
        "focus_sectors": ["innovation", "global health", "development", "education"],
        "ticket_min_usd": 100000,
        "ticket_max_usd": 1000000,
        "access_type": "convocatoria",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "financiador",
        "general_objective": "Financiar soluciones innovadoras para desafíos globales",
        "has_history": True,
    },
    {
        "name": "Fundación Hilton",
        "country": "United States",
        "org_type": "foundation",
        "website": "https://www.hiltonfoundation.org",
        "linkedin_url": "https://www.linkedin.com/company/hilton-foundation",
        "focus_sectors": ["education", "early childhood", "workforce development", "community development"],
        "ticket_min_usd": 25000,
        "ticket_max_usd": 750000,
        "access_type": "convocatoria",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "financiador",
        "general_objective": "Apoyar educación y desarrollo comunitario en América Latina",
        "has_history": True,
    },
    {
        "name": "Fundación Cargill",
        "country": "United States",
        "org_type": "foundation",
        "website": "https://www.cargill.com/about/foundation",
        "linkedin_url": "https://www.linkedin.com/company/cargill",
        "focus_sectors": ["education", "rural development", "food security", "sustainable development"],
        "ticket_min_usd": 50000,
        "ticket_max_usd": 2000000,
        "access_type": "convocatoria",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "financiador",
        "general_objective": "Inversión en educación y desarrollo rural sostenible",
        "has_history": True,
    },

    # ── MULTILATERALES & COOPERACIÓN INTERNACIONAL ──────────────────────────────
    {
        "name": "BID (Banco Interamericano de Desarrollo)",
        "country": "United States",
        "org_type": "multilateral",
        "website": "https://www.iadb.org",
        "linkedin_url": "https://www.linkedin.com/company/iadb",
        "focus_sectors": ["education", "development", "infrastructure", "social inclusion"],
        "ticket_min_usd": 500000,
        "ticket_max_usd": 50000000,
        "access_type": "convocatoria",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "financiador",
        "general_objective": "Financiamiento para desarrollo sostenible e integración en LAC",
        "has_history": True,
    },
    {
        "name": "IADB Invest",
        "country": "United States",
        "org_type": "multilateral",
        "website": "https://www.idbinvest.org",
        "linkedin_url": "https://www.linkedin.com/company/iadb-invest",
        "focus_sectors": ["education", "private sector development", "social business"],
        "ticket_min_usd": 100000,
        "ticket_max_usd": 20000000,
        "access_type": "convocatoria",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "financiador",
        "general_objective": "Inversión en empresas sociales y modelos sostenibles de educación",
        "has_history": False,
    },
    {
        "name": "UNICEF",
        "country": "United States",
        "org_type": "multilateral",
        "website": "https://www.unicef.org",
        "linkedin_url": "https://www.linkedin.com/company/unicef",
        "focus_sectors": ["early childhood", "education", "child development", "health"],
        "ticket_min_usd": 25000,
        "ticket_max_usd": 5000000,
        "access_type": "convocatoria",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "financiador",
        "general_objective": "Apoyo a programas de desarrollo infantil temprano",
        "has_history": False,
    },
    {
        "name": "ONU Mujeres",
        "country": "United States",
        "org_type": "multilateral",
        "website": "https://www.unwomen.org",
        "linkedin_url": "https://www.linkedin.com/company/un-women",
        "focus_sectors": ["gender equality", "women empowerment", "education", "development"],
        "ticket_min_usd": 10000,
        "ticket_max_usd": 500000,
        "access_type": "convocatoria",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "financiador",
        "general_objective": "Empoderamiento de mujeres en educación y desarrollo infantil",
        "has_history": False,
    },
    {
        "name": "GIZ (Deutsche Gesellschaft für Internationale Zusammenarbeit)",
        "country": "Germany",
        "org_type": "cooperacion",
        "website": "https://www.giz.de",
        "linkedin_url": "https://www.linkedin.com/company/giz",
        "focus_sectors": ["education", "development cooperation", "sustainable development"],
        "ticket_min_usd": 50000,
        "ticket_max_usd": 10000000,
        "access_type": "convocatoria",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "aliado",
        "general_objective": "Cooperación técnica en educación y desarrollo sostenible",
        "has_history": False,
    },
    {
        "name": "Global Affairs Canada",
        "country": "Canada",
        "org_type": "cooperacion",
        "website": "https://www.canada.ca/en/global-affairs",
        "linkedin_url": "https://www.linkedin.com/company/global-affairs-canada",
        "focus_sectors": ["education", "development assistance", "humanitarian"],
        "ticket_min_usd": 25000,
        "ticket_max_usd": 5000000,
        "access_type": "convocatoria",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "financiador",
        "general_objective": "Ayuda al desarrollo y cooperación técnica en educación",
        "has_history": False,
    },

    # ── GRANDES FILANTROPÍAS GLOBALES ──────────────────────────────────────────
    {
        "name": "Ford Foundation",
        "country": "United States",
        "org_type": "foundation",
        "website": "https://www.fordfoundation.org",
        "linkedin_url": "https://www.linkedin.com/company/ford-foundation",
        "focus_sectors": ["education", "social justice", "economic development", "learning"],
        "ticket_min_usd": 100000,
        "ticket_max_usd": 5000000,
        "access_type": "convocatoria",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "financiador",
        "general_objective": "Financiamiento para justicia social y educación en América Latina",
        "has_history": False,
    },
    {
        "name": "Rockefeller Foundation",
        "country": "United States",
        "org_type": "foundation",
        "website": "https://www.rockefellerfoundation.org",
        "linkedin_url": "https://www.linkedin.com/company/rockefeller-foundation",
        "focus_sectors": ["health", "education", "resilience", "global development"],
        "ticket_min_usd": 50000,
        "ticket_max_usd": 10000000,
        "access_type": "convocatoria",
        "strategic_obj": "capital",
        "invests_colombia": False,
        "invests_latam": True,
        "aeiotu_role": "financiador",
        "general_objective": "Financiamiento para educación y resiliencia en países en desarrollo",
        "has_history": False,
    },
    {
        "name": "MacArthur Foundation",
        "country": "United States",
        "org_type": "foundation",
        "website": "https://www.macfound.org",
        "linkedin_url": "https://www.linkedin.com/company/john-d-and-catherine-t-macarthur-foundation",
        "focus_sectors": ["education", "global security", "social justice", "conservation"],
        "ticket_min_usd": 50000,
        "ticket_max_usd": 3000000,
        "access_type": "convocatoria",
        "strategic_obj": "capital",
        "invests_colombia": False,
        "invests_latam": True,
        "aeiotu_role": "financiador",
        "general_objective": "Apoyo a educación y cambio social en países en desarrollo",
        "has_history": False,
    },
    {
        "name": "Gates Foundation",
        "country": "United States",
        "org_type": "foundation",
        "website": "https://www.gatesfoundation.org",
        "linkedin_url": "https://www.linkedin.com/company/bill-and-melinda-gates-foundation",
        "focus_sectors": ["education", "global health", "poverty reduction", "development"],
        "ticket_min_usd": 100000,
        "ticket_max_usd": 50000000,
        "access_type": "convocatoria",
        "strategic_obj": "capital",
        "invests_colombia": False,
        "invests_latam": True,
        "aeiotu_role": "financiador",
        "general_objective": "Inversión global en educación de calidad en países de bajos ingresos",
        "has_history": False,
    },
    {
        "name": "Luminate",
        "country": "United States",
        "org_type": "foundation",
        "website": "https://luminategroup.com",
        "linkedin_url": "https://www.linkedin.com/company/luminate-group",
        "focus_sectors": ["education", "learning", "social change", "innovation"],
        "ticket_min_usd": 25000,
        "ticket_max_usd": 2000000,
        "access_type": "convocatoria",
        "strategic_obj": "capital",
        "invests_colombia": False,
        "invests_latam": True,
        "aeiotu_role": "financiador",
        "general_objective": "Inversión en mejora de aprendizaje global",
        "has_history": False,
    },

    # ── FUNDACIONES REGIONALES LATINOAMÉRICA ─────────────────────────────────────
    {
        "name": "Fundación SM",
        "country": "Spain",
        "org_type": "foundation",
        "website": "https://www.fundacionsm.org",
        "linkedin_url": "https://www.linkedin.com/company/fundacion-sm",
        "focus_sectors": ["education", "early childhood", "teacher training", "vulnerable populations"],
        "ticket_min_usd": 10000,
        "ticket_max_usd": 500000,
        "access_type": "convocatoria",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "financiador",
        "general_objective": "Educación de calidad para poblaciones vulnerables en Latinoamérica",
        "has_history": False,
    },
    {
        "name": "Fundación Telefónica",
        "country": "Spain",
        "org_type": "foundation",
        "website": "https://www.fundaciontelefonica.com",
        "linkedin_url": "https://www.linkedin.com/company/fundacion-telefonica",
        "focus_sectors": ["education", "digital inclusion", "technology for good"],
        "ticket_min_usd": 25000,
        "ticket_max_usd": 1000000,
        "access_type": "convocatoria",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "financiador",
        "general_objective": "Inclusión digital en educación latinoamericana",
        "has_history": False,
    },
    {
        "name": "Fundación Natura Colombia",
        "country": "Colombia",
        "org_type": "foundation",
        "website": "https://www.natura.org.co",
        "linkedin_url": "https://www.linkedin.com/company/fundacion-natura-colombia",
        "focus_sectors": ["education", "conservation", "sustainable development", "first nations"],
        "ticket_min_usd": 5000,
        "ticket_max_usd": 200000,
        "access_type": "mixto",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": False,
        "aeiotu_role": "aliado",
        "general_objective": "Educación ambiental y conservación en Colombia",
        "has_history": False,
    },
    {
        "name": "Fundación Empresarios por la Educación",
        "country": "Colombia",
        "org_type": "foundation",
        "website": "https://www.empresariosporlaeducacion.org",
        "linkedin_url": "https://www.linkedin.com/company/empresarios-por-la-educacion",
        "focus_sectors": ["education", "teacher training", "educational quality", "early childhood"],
        "ticket_min_usd": 5000,
        "ticket_max_usd": 300000,
        "access_type": "mixto",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": False,
        "aeiotu_role": "aliado",
        "general_objective": "Transformación de educación inicial en Colombia",
        "has_history": False,
    },
    {
        "name": "Fundación FES",
        "country": "Colombia",
        "org_type": "foundation",
        "website": "https://www.fes.org.co",
        "linkedin_url": "https://www.linkedin.com/company/fundacion-fes",
        "focus_sectors": ["education", "social development", "rural education", "capacity building"],
        "ticket_min_usd": 10000,
        "ticket_max_usd": 500000,
        "access_type": "convocatoria",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": False,
        "aeiotu_role": "aliado",
        "general_objective": "Fortalecimiento de educación rural en Colombia",
        "has_history": False,
    },
    {
        "name": "Fundación Hubbard",
        "country": "United States",
        "org_type": "foundation",
        "website": "https://www.hubbard.org",
        "linkedin_url": "https://www.linkedin.com/company/hubbard-foundation",
        "focus_sectors": ["education", "conservation", "indigenous rights", "cultural preservation"],
        "ticket_min_usd": 25000,
        "ticket_max_usd": 1000000,
        "access_type": "convocatoria",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "financiador",
        "general_objective": "Educación cultural y conservación en pueblos indígenas",
        "has_history": False,
    },

    # ── ORGANIZACIONES & PLATAFORMAS ESPECIALIZADAS ────────────────────────────
    {
        "name": "DevEx (Development Exchange)",
        "country": "United States",
        "org_type": "ong",
        "website": "https://www.devex.com",
        "linkedin_url": "https://www.linkedin.com/company/devex",
        "focus_sectors": ["development", "education", "grants", "job board"],
        "ticket_min_usd": 0,
        "ticket_max_usd": 0,
        "access_type": "relacional",
        "strategic_obj": "red",
        "invests_colombia": False,
        "invests_latam": True,
        "aeiotu_role": "red",
        "general_objective": "Plataforma de conectividad para profesionales y organizaciones de desarrollo",
        "has_history": False,
    },
    {
        "name": "FundingForNGOs",
        "country": "United Kingdom",
        "org_type": "ong",
        "website": "https://www.fundingforngo.org",
        "linkedin_url": "https://www.linkedin.com/company/fundingngo",
        "focus_sectors": ["development", "education", "fundraising", "grants information"],
        "ticket_min_usd": 0,
        "ticket_max_usd": 0,
        "access_type": "relacional",
        "strategic_obj": "red",
        "invests_colombia": False,
        "invests_latam": True,
        "aeiotu_role": "red",
        "general_objective": "Base de datos de oportunidades de financiamiento para NGOs",
        "has_history": False,
    },
    {
        "name": "Global Affairs Canada - Grants Search",
        "country": "Canada",
        "org_type": "gobierno",
        "website": "https://www.international.gc.ca",
        "linkedin_url": "https://www.linkedin.com/company/global-affairs-canada",
        "focus_sectors": ["development", "education", "grants", "international cooperation"],
        "ticket_min_usd": 25000,
        "ticket_max_usd": 5000000,
        "access_type": "convocatoria",
        "strategic_obj": "capital",
        "invests_colombia": True,
        "invests_latam": True,
        "aeiotu_role": "financiador",
        "general_objective": "Programas bilaterales de cooperación y educación",
        "has_history": False,
    },
]

async def seed_global_organizations():
    """Load 60+ global organizations into database"""
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        try:
            # Delete existing organizations first (optional - comment to keep history)
            # await session.execute(delete(Funder))
            # await session.commit()

            # Insert new organizations
            for org_data in GLOBAL_ORGANIZATIONS:
                # Check if already exists
                existing = await session.execute(
                    session.query(Funder).filter(Funder.name == org_data["name"])
                )
                if existing.scalar():
                    logger.info(f"Organization {org_data['name']} already exists, skipping")
                    continue

                funder = Funder(
                    id=uuid.uuid4(),
                    **org_data,
                    verified_data=True,
                    last_scraped_at=datetime.now(timezone.utc),
                )
                session.add(funder)

            await session.commit()
            logger.info(f"Loaded {len(GLOBAL_ORGANIZATIONS)} global organizations")

        except Exception as e:
            logger.error(f"Error seeding organizations: {e}")
            await session.rollback()
            raise


def seed_organizations_sync():
    """Synchronous seed function for CLI"""
    import asyncio
    from dotenv import load_dotenv

    load_dotenv()
    asyncio.run(seed_global_organizations())


if __name__ == "__main__":
    seed_organizations_sync()
