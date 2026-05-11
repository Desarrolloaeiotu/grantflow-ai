"""Seed las 4 oportunidades nacionales estratégicas (CLAUDE.md §16) en la DB.

Estas son oportunidades curadas — NO vienen de scraping. Las insertamos
manualmente con source_name='manual_nacional' para que fluyan por el mismo
pipeline (alertas, pipeline GO, CSV export) que las scrapeadas.

Idempotente: usa UUID5 determinístico desde el slug, así re-correr no duplica.

Uso:
    python -m app.scrapers.seed_nacional
"""

import asyncio
import json
import uuid
from datetime import date, timedelta

import structlog
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.funder import Funder
from app.models.opportunity import Opportunity

logger = structlog.get_logger()

# Namespace arbitrario para UUID5 determinístico de opps nacionales
NACIONAL_NAMESPACE = uuid.UUID("12345678-1234-5678-1234-567812345678")


def deadline_from_quarter(quarter: int, year: int = 2026) -> date:
    """Las opps nacionales son objetivos estratégicos del año, no convocatorias
    con cierre exacto. Usamos 'fin del año target' como deadline para que el
    pipeline las trate como 'gestionar antes de fin de año' y NO disparen
    alertas falsas de urgencia.

    El startQuarter sigue mostrándose en el UI como 'Inicio Q2 2026' (info real).
    """
    return date(year, 12, 31)


def target_contact_from_quarter(quarter: int, year: int = 2026) -> date:
    """Fecha esperada del próximo contacto/acción estratégica.

    Lógica relativa a HOY (no a fechas absolutas) para que las alertas
    siempre tengan sentido sin depender de cuándo se corrió el seeder.

    - Q1 → ya pasó, contactar URGENTE (≤14 días)
    - Q2 → ventana abierta, contactar PRONTO (≤30 días)
    - Q3 → mediano plazo (~60 días)
    - Q4 → fin del año (~90+ días)
    """
    today = date.today()
    offsets = {1: 14, 2: 30, 3: 60, 4: 90}
    return today + timedelta(days=offsets[quarter])


# ── Las 4 oportunidades estratégicas ──────────────────────────────────────────


NACIONAL_OPPS = [
    {
        "slug": "cdi-men",
        "title": "Fortalecimiento de CDI en contextos de vulnerabilidad",
        "description": (
            "Ministerio de Educación y Fondos de Compensación buscan mejorar calidad "
            "de CDI públicos en municipios vulnerables (post-conflicto, zonas rurales). "
            "Incluye: formación docente, acompañamiento pedagógico, transformación de "
            "ambientes y medición del desarrollo infantil."
        ),
        "amount_min_cop": 280_000_000,
        "amount_max_cop": 450_000_000,
        "start_quarter": 2,
        "capital_type": "consultoria",
        "score": 9,
        "decision": "go",
        "urgency": "medium",
        "funder_name": "Ministerio de Educación Nacional",
        "org_website": "https://www.mineducacion.gov.co",
        "org_email": "atencionalciudadano@mineducacion.gov.co",
        "org_email_verified": True,
        "ceo_name": "Por verificar",
        "ceo_title": "Viceministro(a) de Educación Preescolar, Básica y Media",
        "ceo_email": "viceministerio@mineducacion.gov.co",
        "ceo_email_verified": False,
        "ceo_linkedin_url": (
            "https://www.linkedin.com/search/results/people/?keywords="
            "Viceministra%20Educacion%20Preescolar%20Colombia"
        ),
        "url_rfp": "https://www.mineducacion.gov.co/",
        "criteria": {"c1": 2, "c2": 2, "c3": 2, "c4": 2, "c5": 1},
        "reasoning": (
            "Conecta directamente con expertise aeioTU en CDI públicos. Línea Innovación "
            "y Calidad + operación jardines como modelo. Potencial de sistematización nacional."
        ),
        "actions": [
            "Diagnóstico de 50-80 CDI en 3 regiones.",
            "Formación de 200+ docentes basada en modelo aeioTU.",
            "Acompañamiento pedagógico 6 meses + medición ConecTU.",
        ],
        "category": "gobierno",
    },
    {
        "slug": "cajas-comp",
        "title": "Diplomado de Primera Infancia Integral para Cajas de Compensación",
        "description": (
            "CAFAM, Caja Nariño y otras cajas de compensación necesitan fortalecer formación "
            "de docentes y cuidadores en educación inicial de calidad. Incluye: modalidades "
            "institucional y familiar, acompañamiento pedagógico modular, certificación aeioTU."
        ),
        "amount_min_cop": 180_000_000,
        "amount_max_cop": 320_000_000,
        "start_quarter": 2,
        "capital_type": "licensing",
        "score": 9,
        "decision": "go",
        "urgency": "medium",
        "funder_name": "CAFAM",
        "org_website": "https://www.cafam.com.co",
        "org_email": "servicioalcliente@cafam.com.co",
        "org_email_verified": True,
        "ceo_name": "Por verificar",
        "ceo_title": "Director(a) de Educación / Innovación CAFAM",
        "ceo_email": "innovacion@cafam.com.co",
        "ceo_email_verified": False,
        "ceo_linkedin_url": (
            "https://www.linkedin.com/search/results/people/?keywords="
            "Director%20Educacion%20CAFAM"
        ),
        "url_rfp": "https://www.cafam.com.co/",
        "criteria": {"c1": 2, "c2": 2, "c3": 2, "c4": 2, "c5": 1},
        "reasoning": (
            "CAFAM es socio operativo histórico de aeioTU. Combina Jardines en alianza + "
            "Economía del Cuidado. Sostenibilidad financiera clara (cuota anual / maestro / caja)."
        ),
        "actions": [
            "Diseñar diplomado modular (120 horas, 6 módulos).",
            "Negociar con CAFAM como piloto: 50 docentes/caja.",
            "Escalar a 6-8 cajas multinivel (ingresos recurrentes).",
        ],
        "category": "cajas",
    },
    {
        "slug": "jardines-privados",
        "title": "Acompañamiento Integrado de Calidad para Jardines Privados",
        "description": (
            "Jardines privados urbanos y rurales buscan mejorar calidad sin expansión de "
            "infraestructura. Necesitan: formación docente, acompañamiento pedagógico "
            "modular, acceso a Red aeioTU y medición continua con ConecTU. Modelo escalable "
            "por ciudad."
        ),
        "amount_min_cop": 120_000_000,
        "amount_max_cop": 200_000_000,
        "start_quarter": 2,
        "capital_type": "consultoria",
        "score": 7,
        "decision": "pending",
        "urgency": "medium",
        "funder_name": "Asociación Colombiana de Educación Preescolar (ACEP)",
        "org_website": "https://acepcolombia.org",
        "org_email": "info@acepcolombia.org",
        "org_email_verified": False,
        "ceo_name": "Por verificar",
        "ceo_title": "Presidente Ejecutivo ACEP",
        "ceo_email": "presidencia@acepcolombia.org",
        "ceo_email_verified": False,
        "ceo_linkedin_url": (
            "https://www.linkedin.com/search/results/people/?keywords="
            "Presidente%20ACEP%20Colombia"
        ),
        "url_rfp": "https://acepcolombia.org",
        "criteria": {"c1": 2, "c2": 2, "c3": 1, "c4": 1, "c5": 1},
        "reasoning": (
            "Segmento estable de ingresos. Bajo costo de entrada. Crea demanda de Red aeioTU "
            "+ ConecTU (sostenibilidad digital)."
        ),
        "actions": [
            "Diseñar propuesta comercial clara: grupos de 15-20 jardines.",
            "Piloto en Bogotá: diagnóstico + 3 meses formación.",
            "Replicar modelo en 5 ciudades (Medellín, Cali, Barranquilla).",
        ],
        "category": "privado",
    },
    {
        "slug": "icbf-men-politica",
        "title": "Estándares de Calidad en Primera Infancia: aeioTU + ICBF + MEN",
        "description": (
            "Gobierno actualiza marcos de calidad en primera infancia (CERO A SIEMPRE, "
            "estándares ICBF, orientaciones MEN 2026). Busca socio técnico para diseñar "
            "guías de formación docente, operación CDI, modalidades familiar e institucional, "
            "y medición con ConecTU."
        ),
        "amount_min_cop": 200_000_000,
        "amount_max_cop": 350_000_000,
        "start_quarter": 1,
        "capital_type": "advocacy",
        "score": 8,
        "decision": "go",
        "urgency": "high",
        "funder_name": "Instituto Colombiano de Bienestar Familiar (ICBF)",
        "org_website": "https://www.icbf.gov.co",
        "org_email": "atencionalciudadano@icbf.gov.co",
        "org_email_verified": True,
        "ceo_name": "Por verificar",
        "ceo_title": "Director(a) General del ICBF",
        "ceo_email": "direccion.general@icbf.gov.co",
        "ceo_email_verified": False,
        "ceo_linkedin_url": (
            "https://www.linkedin.com/search/results/people/?keywords="
            "Director%20General%20ICBF%20Colombia"
        ),
        "url_rfp": "https://www.icbf.gov.co/",
        "criteria": {"c1": 2, "c2": 2, "c3": 1, "c4": 2, "c5": 1},
        "reasoning": (
            "Posiciona a aeioTU como voz autorizada en política pública. Acceso a datos de "
            "impacto nacional. Base para relaciones internacionales (BID, GIZ)."
        ),
        "actions": [
            "Acercamiento directo a ICBF y DNP en Q1 2026.",
            "Propuesta de co-diseño: guías + seminarios en 10 regiones.",
            "Posicionamiento como voz autorizada en política pública.",
        ],
        "category": "politica",
    },
]


async def get_or_create_funder(db, name: str) -> uuid.UUID:
    existing = (
        await db.execute(select(Funder).where(Funder.name == name))
    ).scalar_one_or_none()
    if existing:
        return existing.id

    funder = Funder(
        name=name,
        country="Colombia",
        org_type="government" if "Ministerio" in name or "ICBF" in name else "private",
        has_history=True,  # Las 4 son aliados estratégicos
    )
    db.add(funder)
    await db.flush()
    return funder.id


async def main() -> None:
    inserted = 0
    updated = 0
    async with AsyncSessionLocal() as db:
        for data in NACIONAL_OPPS:
            opp_id = uuid.uuid5(NACIONAL_NAMESPACE, f"nacional:{data['slug']}")

            # Check si ya existe
            existing = await db.get(Opportunity, opp_id)
            is_new = existing is None

            funder_id = await get_or_create_funder(db, data["funder_name"])
            score_details = {
                **data["criteria"],
                "llm_justification": data["reasoning"],
                "confidence": "high",
                "actions": data["actions"],
                "category": data["category"],
                "source_type": "curated_strategic",
            }

            fields = {
                "id": opp_id,
                "title": data["title"],
                "description": data["description"],
                "funder_id": funder_id,
                "amount_min_cop": data["amount_min_cop"],
                "amount_max_cop": data["amount_max_cop"],
                "deadline": deadline_from_quarter(data["start_quarter"]),
                "target_contact_date": target_contact_from_quarter(data["start_quarter"]),
                "url_rfp": data["url_rfp"],
                "url_source": f"manual_nacional:{data['slug']}",
                "source_name": "manual_nacional",
                "org_website": data["org_website"],
                "org_email": data["org_email"],
                "org_email_verified": data["org_email_verified"],
                "ceo_name": data["ceo_name"],
                "ceo_title": data["ceo_title"],
                "ceo_email": data["ceo_email"],
                "ceo_email_verified": data["ceo_email_verified"],
                "ceo_linkedin_url": data["ceo_linkedin_url"],
                "market_window": "funding_colombia",
                "capital_type": data["capital_type"],
                "score_total": data["score"],
                "score_details": score_details,
                "decision": data["decision"],
                "urgency": data["urgency"],
                "status": "detected",
                "raw_content": json.dumps(data, ensure_ascii=False),
            }

            if is_new:
                opp = Opportunity(**fields)
                db.add(opp)
                inserted += 1
                logger.info("Inserted nacional opp", slug=data["slug"], decision=data["decision"])
            else:
                for k, v in fields.items():
                    if k != "id":
                        setattr(existing, k, v)
                updated += 1
                logger.info("Updated nacional opp", slug=data["slug"])

        await db.commit()

    logger.info("Seed nacional complete", inserted=inserted, updated=updated, total=len(NACIONAL_OPPS))


if __name__ == "__main__":
    asyncio.run(main())
