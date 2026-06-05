"""Strategic analysis service for organizations using Claude API."""
import json
import structlog
from typing import Optional

from anthropic import Anthropic

from app.core.config import settings
from app.models.funder import Funder

logger = structlog.get_logger()


class AnalysisService:
    """Service for generating strategic analysis of organizations using Claude."""

    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-5"
        self.max_tokens = 2000

    def analyze_organization(self, org: Funder) -> dict:
        """
        Generate strategic analysis for an organization.

        Args:
            org: Funder object with organization data

        Returns:
            Dictionary with 5 analysis sections + primary_role + confidence
        """
        try:
            # Build context string
            org_data = self._build_org_context(org)
            aeiotu_profile = self._get_aeiotu_profile()

            # Build prompt
            prompt = self._build_analysis_prompt(org_data, aeiotu_profile)

            # Call Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract and parse response
            response_text = response.content[0].text

            # Try to extract JSON from response
            analysis = self._parse_response(response_text)

            logger.info(
                "Organization analyzed successfully",
                org_id=str(org.id),
                org_name=org.name,
                confidence=analysis.get("confidence", "unknown"),
            )

            return analysis

        except json.JSONDecodeError as e:
            logger.error("Failed to parse Claude response as JSON", error=str(e))
            raise ValueError("Claude response was not valid JSON")
        except Exception as e:
            logger.error(
                "Error analyzing organization",
                org_id=str(org.id),
                error=str(e),
            )
            raise

    def _build_org_context(self, org: Funder) -> str:
        """Build organization context string from Funder object."""
        lines = [
            f"Name: {org.name}",
            f"Country: {org.country or 'Unknown'}",
            f"Type: {org.org_type or 'Unknown'}",
            f"Website: {org.website or 'Not provided'}",
            f"LinkedIn: {org.linkedin_url or 'Not provided'}",
            f"General Objective: {org.general_objective or 'Not specified'}",
            f"Strategic Objective: {org.strategic_obj or 'Not specified'}",
            f"Access Type: {org.access_type or 'Not specified'}",
            f"Focus Sectors: {', '.join(org.focus_sectors or []) or 'Not specified'}",
            f"Invests in Colombia: {'Yes' if org.invests_colombia else 'No'}",
            f"Invests in Latin America: {'Yes' if org.invests_latam else 'No'}",
            f"Ticket Size (USD): ${org.ticket_min_usd or 0:,} - ${org.ticket_max_usd or 0:,}",
            f"Grant Range (COP): ${org.min_grant_cop or 0:,} - ${org.max_grant_cop or 0:,}",
            f"Has History with aeioTU: {'Yes' if org.has_history else 'No'}",
            f"aeioTU Role: {org.aeiotu_role or 'Not assigned'}",
            f"Data Verified: {'Yes' if org.verified_data else 'No'}",
        ]
        return "\n".join(lines)

    def _get_aeiotu_profile(self) -> str:
        """Get aeioTU profile for context."""
        return """
aeioTU is a Colombian organization with 17+ years of experience in early childhood education (ECD).

Key Profile Points:
- Founded in 2007, headquartered in Bogotá, Colombia
- Focus: Quality education for children 0-5 years, teacher training, policy influence
- Impact: 2.3 million children reached, 98,000 teachers trained
- Award: LEGO Foundation Prize 2022
- Strategic Focus: Model scaling, Latin American expansion, knowledge transfer
- Financing Mix: 41% philanthropic, 34% public, 25% own income
- Top Historical Funders: LEGO Foundation, Grand Challenges Canada, Fundación Hilton, Fundación Cargill, BID
- Strategy 2025-2030: Scale to 1.9M children via consulting, model transfer, and alliances
- Sectors: Education, child development, policy systems, capacity building, innovation

What aeioTU Seeks:
1. Capital: Funding for consulting projects, model transfer, capacity building
2. Model Export: Partners interested in scaling/replicating the aeioTU model in other regions
3. Network/Positioning: Strategic alliances that enhance regional influence and reputation
4. Colombia Operations: Financiers of projects in Colombia
5. Latin America Expansion: Partners for growth in neighboring countries
"""

    def _build_analysis_prompt(self, org_data: str, aeiotu_profile: str) -> str:
        """Build the analysis prompt for Claude."""
        return f"""You are a strategic analyst for aeioTU (early childhood education + innovation).

Your task is to analyze an organization for potential alliance, partnership, or funding opportunities with aeioTU.

=== ORGANIZATION DATA ===
{org_data}

=== aeioTU PROFILE ===
{aeiotu_profile}

=== YOUR ANALYSIS TASK ===

Evaluate this organization across 5 strategic dimensions for aeioTU:

1. **Capital** — Does this organization provide funding? What type (grants/loans/blended)? What amounts? At what stage (early/growth/scale)?
2. **Exportación del Modelo** — Is there interest in scaling or exporting educational models beyond their own country/context?
3. **Red (Posicionamiento)** — Does association with this organization position aeioTU well strategically? Articulation with other multilaterals/governments/NGOs/private sector?
4. **Inversión en Colombia** — Are there active projects in Colombia? If YES: specify project name, type, and location (city/department). If NO: state explicitly "No se evidencia presencia activa"
5. **Inversión en LatAm** — Does the organization operate in Latin America? Which countries? What is the program type and scale?

Additionally, identify the **primary role** of this organization for aeioTU (one of: "capital", "exportacion", "posicionamiento").

=== OUTPUT FORMAT ===

You MUST respond ONLY with valid JSON. No additional text. The JSON structure is:

{{
  "capital": {{
    "text": "[Max 150 characters. Analysis: does it finance? Type? Amounts? Stage?]",
    "conclusion": "Alto|Medio|Bajo"
  }},
  "model_export": {{
    "text": "[Max 150 characters. Analysis: interest in scaling/exporting models?]",
    "conclusion": "SÍ|NO"
  }},
  "network": {{
    "text": "[Max 150 characters. Positioning value? Articulation with multilaterals/govs/NGOs/private?]",
    "conclusion": "SÍ (Alto|Medio|Bajo)|NO"
  }},
  "colombia": {{
    "text": "[Max 150 characters. Active projects? If YES: name, type, location. If NO: 'No se evidencia presencia activa']",
    "conclusion": "Sí|No"
  }},
  "latam": {{
    "text": "[Max 150 characters. Which countries? Program type? Scale?]",
    "conclusion": "Prioridad|Secundaria|Marginal"
  }},
  "primary_role": "capital|exportacion|posicionamiento",
  "confidence": "high|medium|low"
}}

=== REQUIREMENTS ===
- Each "text" field must be concise (max 150 chars) and critical/analytical in tone
- Conclusions must be EXPLICIT and match exactly the format shown above
- If data is incomplete, note gaps explicitly in the text field
- Be honest about uncertainty — use "low" confidence if data is sparse
- Respond ONLY with JSON — no markdown formatting, no explanation text

Now analyze this organization."""

    def _parse_response(self, response_text: str) -> dict:
        """Parse Claude's JSON response and validate structure."""
        # Extract JSON from response (handle markdown code blocks if present)
        json_str = response_text.strip()
        if json_str.startswith("```"):
            # Remove markdown code block
            json_str = json_str.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
            json_str = json_str.strip()

        # Parse JSON
        analysis = json.loads(json_str)

        # Validate required fields
        required_keys = ["capital", "model_export", "network", "colombia", "latam", "primary_role", "confidence"]
        for key in required_keys:
            if key not in analysis:
                raise ValueError(f"Missing required field in analysis: {key}")

        # Validate section structure
        for section in ["capital", "model_export", "network", "colombia", "latam"]:
            if not isinstance(analysis[section], dict):
                raise ValueError(f"Section '{section}' must be a dictionary")
            if "text" not in analysis[section] or "conclusion" not in analysis[section]:
                raise ValueError(f"Section '{section}' missing 'text' or 'conclusion'")

        return analysis
