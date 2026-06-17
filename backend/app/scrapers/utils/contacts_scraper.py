"""
Scraper de Contactos Clave para organizaciones
Estrategia: Web scraping + LLM para categorización de roles
"""
import asyncio
import re
from datetime import datetime, timezone
from typing import Optional
import uuid
import structlog
from httpx import AsyncClient, ConnectError, TimeoutException

from app.models.contact import Contact
from app.models.funder import Funder
from app.core.database import AsyncSessionLocal

logger = structlog.get_logger()

# Keywords para identificar contactos relevantes
ROLE_KEYWORDS = {
    "partnerships": ["partnerships", "strategic partnerships", "alliance", "external relations", "institutional relations"],
    "grants": ["grants", "grants manager", "funding", "philanthropy", "fundraising"],
    "cooperation": ["cooperation", "international cooperation", "development officer", "program officer"],
    "innovation": ["innovation", "innovation director", "innovation manager"],
    "development": ["development", "business development", "program director", "program manager"],
}

# Palabras clave para detectar contactos en páginas web
CONTACT_PATTERNS = [
    r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*(?:(?:—|,|/)\s*([^<\n]+?))?(?:\s+<([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})>)?',
    r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
    r'linkedin\.com/in/([a-zA-Z0-9-]+)',
]


class ContactsScraper:
    """Scraper de contactos clave desde páginas de organizaciones"""

    def __init__(self):
        self.client: Optional[AsyncClient] = None

    async def __aenter__(self):
        self.client = AsyncClient(timeout=10, follow_redirects=True)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def scrape_organization_contacts(self, org: Funder) -> list[dict]:
        """Scrape contactos desde página de organización"""
        if not org.website:
            logger.debug("No website for organization", org_id=str(org.id), org_name=org.name)
            return []

        contacts = []

        try:
            # Intentar páginas comunes
            pages_to_scrape = [
                org.website,
                f"{org.website}/about",
                f"{org.website}/team",
                f"{org.website}/leadership",
                f"{org.website}/contact",
                f"{org.website}/en/about",
                f"{org.website}/es/about",
            ]

            for page_url in pages_to_scrape:
                try:
                    html = await self._fetch_page(page_url)
                    if not html:
                        continue

                    page_contacts = await self._extract_contacts_from_html(html, org.id, org.name)
                    contacts.extend(page_contacts)

                except (ConnectError, TimeoutException) as e:
                    logger.debug(f"Failed to scrape {page_url}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error scraping contacts for {org.name}: {e}")

        # Deduplicar
        unique_contacts = {}
        for contact in contacts:
            key = (contact["full_name"], contact["email"])
            if key not in unique_contacts:
                unique_contacts[key] = contact

        return list(unique_contacts.values())

    async def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch página HTML"""
        if not self.client:
            return None

        try:
            response = await self.client.get(url)
            if response.status_code == 200:
                return response.text
        except Exception as e:
            logger.debug(f"Error fetching {url}: {e}")

        return None

    async def _extract_contacts_from_html(self, html: str, funder_id: uuid.UUID, funder_name: str) -> list[dict]:
        """Extraer contactos del HTML"""
        contacts = []

        # Buscar patrones simples
        # 1. Emails
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        emails = re.findall(email_pattern, html)

        # 2. LinkedIn URLs
        linkedin_pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/([a-zA-Z0-9-]+)'
        linkedin_urls = re.findall(linkedin_pattern, html)

        # 3. Nombres y títulos (búsqueda simple en <h3>, <h2>, <strong> tags)
        name_pattern = r'<(?:h[23]|strong|b|p)[^>]*>([A-Z][a-z]+\s+[A-Z][a-z]+)(?:<[^>]*>)?(?:\s*—\s*|\s*,\s*)([^<]*?)(?:</(?:h[23]|strong|b|p)>)?'
        names_and_titles = re.findall(name_pattern, html)

        # Crear contactos encontrados
        for full_name, title in names_and_titles[:10]:  # Limitar a 10 por página
            if not full_name or len(full_name.split()) < 2:
                continue

            contact = {
                "id": uuid.uuid4(),
                "full_name": full_name.strip(),
                "last_name": full_name.split()[-1] if len(full_name.split()) > 1 else "",
                "title": title.strip() if title else None,
                "email": None,
                "linkedin_url": None,
                "funder_id": funder_id,
                "source": "web_scrape",
                "role_category": None,
            }

            # Asignar email si encontramos
            if emails:
                contact["email"] = emails[0]
                emails.pop(0)

            # Asignar LinkedIn si encontramos
            if linkedin_urls:
                contact["linkedin_url"] = f"https://www.linkedin.com/in/{linkedin_urls[0]}"
                linkedin_urls.pop(0)

            # Categorizar rol
            if contact["title"]:
                contact["role_category"] = self._categorize_role(contact["title"])

            contacts.append(contact)

        return contacts

    def _categorize_role(self, title: str) -> Optional[str]:
        """Categorizar rol basado en palabras clave (sin LLM en versión MVP)"""
        title_lower = title.lower()

        for category, keywords in ROLE_KEYWORDS.items():
            if any(keyword in title_lower for keyword in keywords):
                return category

        return None

    async def categorize_role_with_llm(self, title: str) -> Optional[str]:
        """
        Categorizar rol con Claude LLM (para versión v2)
        Placeholder para futura integración con Claude API
        """
        # Implementar en v2 cuando tengamos Claude API key en producción
        return self._categorize_role(title)


async def scrape_all_contacts():
    """Scrape contactos para todas las organizaciones en BD"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select

        # Obtener todas las organizaciones
        stmt = select(Funder).where(Funder.verified_data == True)
        result = await session.execute(stmt)
        funders = result.scalars().all()

        logger.info(f"Scraping contacts for {len(funders)} organizations")

        async with ContactsScraper() as scraper:
            for funder in funders:
                try:
                    contacts_data = await scraper.scrape_organization_contacts(funder)

                    for contact_data in contacts_data[:5]:  # Limitar a 5 por org
                        # Verificar si existe
                        existing = await session.execute(
                            select(Contact).where(
                                Contact.full_name == contact_data["full_name"],
                                Contact.funder_id == contact_data["funder_id"],
                            )
                        )
                        if existing.scalar():
                            continue

                        # Crear nuevo contacto
                        contact = Contact(
                            id=contact_data["id"],
                            full_name=contact_data["full_name"],
                            last_name=contact_data["last_name"],
                            title=contact_data["title"],
                            email=contact_data["email"],
                            linkedin_url=contact_data["linkedin_url"],
                            funder_id=contact_data["funder_id"],
                            source=contact_data["source"],
                            role_category=contact_data["role_category"],
                            priority_score=2 if contact_data["role_category"] else 1,  # Priorizar por rol
                            fetched_at=datetime.now(timezone.utc),
                        )
                        session.add(contact)

                    await session.commit()
                    logger.info(f"Scraped {len(contacts_data)} contacts for {funder.name}")

                except Exception as e:
                    logger.error(f"Error scraping contacts for {funder.name}: {e}")
                    await session.rollback()


if __name__ == "__main__":
    asyncio.run(scrape_all_contacts())
