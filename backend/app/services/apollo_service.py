"""Apollo.io integration for email verification and contact enrichment."""

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

APOLLO_BASE_URL = "https://api.apollo.io/api/v1"
APOLLO_TIMEOUT = 10.0


class ApolloService:
    """Service for Apollo.io email verification and contact enrichment."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.APOLLO_API_KEY
        self.enabled = bool(self.api_key)

    async def verify_email(self, email: str, name: str | None = None) -> dict[str, Any]:
        """
        Verify email using Apollo.io.

        Returns:
            {
                "verified": bool,
                "confidence": "high" | "medium" | "low" | "unknown",
                "email": str,
                "first_name": str | None,
                "last_name": str | None,
                "title": str | None,
                "linkedin_url": str | None,
                "company": str | None,
                "raw_response": dict
            }
        """
        if not self.enabled:
            logger.warning("Apollo.io not configured (APOLLO_API_KEY missing)")
            return {
                "verified": False,
                "confidence": "unknown",
                "email": email,
                "error": "Apollo.io not configured",
            }

        try:
            async with httpx.AsyncClient(timeout=APOLLO_TIMEOUT) as client:
                payload = {
                    "email": email,
                    "reveal_personal_emails": False,
                }
                if name:
                    parts = name.split(maxsplit=1)
                    if len(parts) == 2:
                        payload["first_name"] = parts[0]
                        payload["last_name"] = parts[1]
                    else:
                        payload["first_name"] = parts[0]

                resp = await client.post(
                    f"{APOLLO_BASE_URL}/people/match",
                    json=payload,
                    headers={"x-api-key": self.api_key},
                )
                resp.raise_for_status()
                data = resp.json()

                person = data.get("person", {})
                email_status = person.get("email_status", "unknown")

                # email_status: "verified" | "likely" | "unknown" | "invalid"
                verified = email_status == "verified"

                return {
                    "verified": verified,
                    "confidence": email_status,
                    "email": email,
                    "first_name": person.get("first_name"),
                    "last_name": person.get("last_name"),
                    "title": person.get("title"),
                    "linkedin_url": person.get("linkedin_url"),
                    "company": person.get("company"),
                    "raw_response": data,
                }

        except httpx.TimeoutException:
            logger.error(f"Apollo.io timeout for email: {email}")
            return {
                "verified": False,
                "confidence": "unknown",
                "email": email,
                "error": "Apollo.io timeout",
            }
        except httpx.RequestError as e:
            logger.error(f"Apollo.io request error: {e}")
            return {
                "verified": False,
                "confidence": "unknown",
                "email": email,
                "error": f"Apollo.io error: {str(e)}",
            }
        except Exception as e:
            logger.exception(f"Unexpected error verifying email {email}: {e}")
            return {
                "verified": False,
                "confidence": "unknown",
                "email": email,
                "error": f"Unexpected error: {str(e)}",
            }

    async def search_people(
        self,
        company_name: str | None = None,
        title: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search for people using Apollo.io.

        Returns list of contacts matching criteria.
        """
        if not self.enabled:
            logger.warning("Apollo.io not configured (APOLLO_API_KEY missing)")
            return []

        try:
            async with httpx.AsyncClient(timeout=APOLLO_TIMEOUT) as client:
                payload: dict[str, Any] = {"per_page": limit}

                if company_name:
                    payload["q_organization_name"] = company_name
                if title:
                    payload["q_title"] = title
                if first_name:
                    payload["q_firstname"] = first_name
                if last_name:
                    payload["q_lastname"] = last_name

                resp = await client.post(
                    f"{APOLLO_BASE_URL}/people/search",
                    json=payload,
                    headers={"x-api-key": self.api_key},
                )
                resp.raise_for_status()
                data = resp.json()

                people = data.get("people", [])
                return [
                    {
                        "email": p.get("email"),
                        "first_name": p.get("first_name"),
                        "last_name": p.get("last_name"),
                        "title": p.get("title"),
                        "linkedin_url": p.get("linkedin_url"),
                        "company": p.get("organization", {}).get("name"),
                        "verified": p.get("email_status") == "verified",
                    }
                    for p in people
                ]

        except Exception as e:
            logger.exception(f"Error searching Apollo.io: {e}")
            return []


apollo = ApolloService()
