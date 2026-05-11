"""Motor de scoring de 5 criterios de aeioTU.

Regla de oro: Go si score_total >= 6 (de 10 posibles).
Criterios 1-2: evaluados por LLM (Claude por defecto, Gemini como fallback).
Criterios 3-5: reglas deterministas.
"""

import json
import re
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone

import structlog
from anthropic import AsyncAnthropic
from google import genai
from google.genai import types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.funder import Funder
from app.models.opportunity import Opportunity
from app.models.score import ScoreLog

logger = structlog.get_logger()

GO_THRESHOLD = 6

STRATEGIC_FUNDERS = {
    "lego foundation", "grand challenges canada", "fundación hilton", "fundación cargill",
    "bid", "iadb", "fundación ford", "usaid", "giz", "onu mujeres", "unicef",
    "fundación gates", "luminate", "bill & melinda gates foundation",
}

# Rango viable aeioTU: COP $400M – $5.000M
TICKET_MIN_COP = 400_000_000
TICKET_MAX_COP = 5_000_000_000
TICKET_ADJACENT_FACTOR = 0.30

SCORING_PROMPT = """Eres el evaluador de oportunidades de financiamiento de aeioTU.

PERFIL DE aeioTU:
- Organización colombiana con 17 años de experiencia en educación inicial (ECD)
- 2.3 millones de niños alcanzados, 98.000 docentes formados
- Modelo escalable de transformación de política pública en educación inicial
- Estrategia 2025-2030: consultorías, transferencia de modelo y alianzas
- Financiadores históricos: LEGO Foundation, Grand Challenges Canada, Hilton, BID

OPORTUNIDAD A EVALUAR:
Título: {title}
Descripción: {description}
Financiador: {funder_name}
Tipo de organización: {funder_type}

EVALÚA Y CLASIFICA:

Criterio 1 - ALINEACIÓN ESTRATÉGICA (0-2):
2 = Apoya claramente educación inicial, primera infancia o ECD
1 = Alineación parcial (educación general, desarrollo social, infancia)
0 = Sin alineación con el mandato de aeioTU

Criterio 2 - AJUSTE DEL MODELO (0-2):
2 = Prioriza explícitamente modelos escalables, replicables o de transferencia
1 = Apertura implícita a modelos sistémicos o de impacto estructural
0 = Enfoque en proyectos puntuales sin escala

VENTANA DE MERCADO:
- funding_colombia: financia proyectos en Colombia
- funding_global: fundaciones/multilaterales internacionales
- strategic: redes/coaliciones ECD (posicionamiento, no dinero)
- latam: gobiernos/sistemas educativos de América Latina

Responde SOLO en JSON válido, sin markdown:
{{"criterion_1": <0|1|2>, "criterion_2": <0|1|2>, "reasoning_c1": "<max 40 palabras>", "reasoning_c2": "<max 40 palabras>", "window": "<funding_colombia|funding_global|strategic|latam>", "confidence": "<high|medium|low>"}}"""


@dataclass
class ScoreResult:
    c1: int
    c2: int
    c3: int
    c4: int
    c5: int
    total: int
    decision: str
    urgency: str
    llm_reasoning: str
    confidence: str
    market_window: str | None


def _extract_json(raw: str) -> dict:
    """Extrae JSON de respuesta LLM (Gemini a veces envuelve en markdown)."""
    raw = raw.strip()
    if raw.startswith("```"):
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if match:
            raw = match.group(1)
    return json.loads(raw)


class ScoringEngine:
    def __init__(self) -> None:
        self._anthropic: AsyncAnthropic | None = None
        self._gemini: genai.Client | None = None

        if settings.ANTHROPIC_API_KEY:
            self._anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            self._provider = "anthropic"
        elif settings.GOOGLE_API_KEY:
            # gemini-2.5-flash: ~250 RPD free tier.
            # Cuota PerModel separada de 2.0-flash y 2.5-flash-lite (ambos
            # ya consumidos hoy). Permite procesar otro batch grande.
            self._gemini = genai.Client(api_key=settings.GOOGLE_API_KEY)
            self._provider = "gemini"
        else:
            self._provider = "none"

    async def score(
        self,
        opp: Opportunity,
        funder: Funder | None,
    ) -> ScoreResult:
        # Una sola llamada LLM combina scoring + ventana de mercado
        c1, c2, llm_reasoning, confidence, market_window = await self._score_llm(opp, funder)
        c3 = self._score_ticket(opp.amount_min_cop, opp.amount_max_cop)
        c4 = self._score_viability(opp.deadline)
        c5 = self._score_relational(funder)

        total = c1 + c2 + c3 + c4 + c5
        decision = "go" if total >= GO_THRESHOLD else ("no_go" if total <= 3 else "pending")
        urgency = self._classify_urgency(opp.deadline)

        logger.info(
            "Opportunity scored",
            opportunity_id=str(opp.id),
            score=total,
            decision=decision,
            c1=c1, c2=c2, c3=c3, c4=c4, c5=c5,
        )
        return ScoreResult(
            c1=c1, c2=c2, c3=c3, c4=c4, c5=c5,
            total=total, decision=decision, urgency=urgency,
            llm_reasoning=llm_reasoning, confidence=confidence,
            market_window=market_window,
        )

    async def score_and_persist(self, opportunity_id: uuid.UUID, db: AsyncSession) -> None:
        opp = await db.get(Opportunity, opportunity_id)
        if not opp:
            logger.warning("Opportunity not found for scoring", id=str(opportunity_id))
            return

        funder: Funder | None = None
        if opp.funder_id:
            funder = await db.get(Funder, opp.funder_id)

        result = await self.score(opp, funder)

        opp.score_total = result.total
        opp.score_details = {
            "c1": result.c1, "c2": result.c2, "c3": result.c3,
            "c4": result.c4, "c5": result.c5,
            "llm_justification": result.llm_reasoning,
            "confidence": result.confidence,
        }
        opp.decision = result.decision
        opp.urgency = result.urgency
        if result.market_window:
            opp.market_window = result.market_window

        log_entry = ScoreLog(
            opportunity_id=opportunity_id,
            criterion_1=result.c1,
            criterion_2=result.c2,
            criterion_3=result.c3,
            criterion_4=result.c4,
            criterion_5=result.c5,
            llm_reasoning=result.llm_reasoning,
        )
        db.add(log_entry)
        await db.flush()

    # ── Criterios LLM ─────────────────────────────────────────────────────────

    async def _score_llm(
        self, opp: Opportunity, funder: Funder | None
    ) -> tuple[int, int, str, str, str | None]:
        """Devuelve (c1, c2, reasoning, confidence, market_window)."""
        if self._provider == "none":
            logger.warning("No LLM key set — LLM scoring skipped")
            return 1, 1, "LLM scoring not available (no API key)", "low", None

        prompt = SCORING_PROMPT.format(
            title=opp.title,
            description=(opp.description or "")[:1000],
            funder_name=funder.name if funder else "Desconocido",
            funder_type=funder.org_type if funder else "unknown",
        )

        try:
            raw = await self._llm_complete(prompt, max_tokens=600)
            data = _extract_json(raw)
            reasoning = (
                f"C1: {data.get('reasoning_c1', '')} | C2: {data.get('reasoning_c2', '')}"
            )
            window = data.get("window")
            if window not in {"funding_colombia", "funding_global", "strategic", "latam"}:
                window = None
            return (
                int(data.get("criterion_1", 0)),
                int(data.get("criterion_2", 0)),
                reasoning,
                data.get("confidence", "medium"),
                window,
            )
        except Exception as exc:
            msg = str(exc)
            logger.error("LLM scoring failed", error=msg[:200], opportunity_id=str(opp.id))
            # En errores de cuota (429) o conexión, propagamos para que el caller
            # decida abortar — NO persistimos scores fallback que ensucian datos.
            if "429" in msg or "quota" in msg.lower() or "rate" in msg.lower():
                raise
            return 0, 0, f"LLM error: {msg[:200]}", "low", None

    async def _llm_complete(self, prompt: str, max_tokens: int = 500) -> str:
        """Despacho a Anthropic o Gemini según el provider activo."""
        if self._provider == "anthropic" and self._anthropic:
            response = await self._anthropic.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()

        if self._provider == "gemini" and self._gemini:
            response = await self._gemini.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=max_tokens,
                    response_mime_type="application/json",
                ),
            )
            return response.text.strip()

        raise RuntimeError("No LLM provider configured")

    # ── Criterio 3 — Coherencia del ticket ────────────────────────────────────

    @staticmethod
    def _score_ticket(amount_min: int | None, amount_max: int | None) -> int:
        ref = amount_max or amount_min
        if ref is None:
            return 1  # Sin dato: puntaje neutro

        if TICKET_MIN_COP <= ref <= TICKET_MAX_COP:
            return 2

        lower = TICKET_MIN_COP * (1 - TICKET_ADJACENT_FACTOR)
        upper = TICKET_MAX_COP * (1 + TICKET_ADJACENT_FACTOR)
        if lower <= ref <= upper:
            return 1

        return 0

    # ── Criterio 4 — Viabilidad operativa ─────────────────────────────────────

    @staticmethod
    def _score_viability(deadline: date | None) -> int:
        if deadline is None:
            return 1  # Sin fecha: puntaje neutro

        days = (deadline - date.today()).days
        if days > 60:
            return 2
        if days >= 30:
            return 1
        return 0

    # ── Criterio 5 — Potencial relacional ─────────────────────────────────────

    @staticmethod
    def _score_relational(funder: Funder | None) -> int:
        if funder is None:
            return 0
        if funder.has_history:
            return 2
        if funder.name.lower() in STRATEGIC_FUNDERS:
            return 1
        return 0

    # ── Urgencia ──────────────────────────────────────────────────────────────

    @staticmethod
    def _classify_urgency(deadline: date | None) -> str:
        if deadline is None:
            return "medium"
        days = (deadline - date.today()).days
        if days <= 30:
            return "high"
        if days <= 60:
            return "medium"
        return "low"

