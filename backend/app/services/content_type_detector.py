from enum import Enum
from dataclasses import dataclass
import re


class ContentType(str, Enum):
    CONVOCATORIA = "convocatoria"
    NEWS = "news"
    ARTICLE = "article"
    REPORT = "report"
    EVENT = "event"
    COURSE = "course"
    UNKNOWN = "unknown"


@dataclass
class ContentTypeResult:
    type: ContentType
    confidence: float  # 0-1
    reason: str | None = None


CONVOCATORIA_PATTERNS = (
    r"deadline|fecha límite|fecha cierre|call for|llamado|convocatoria|opportunity|grant.*apply|"
    r"apply.*now|submit.*proposal|proposal.*deadline|expression of interest|eoi|rfp|request for proposal|"
    r"oportunidad de financiamiento|financiamiento disponible|solicitud abierta"
)

NEWS_PATTERNS = (
    r"\bsays\b|\bannounces\b|\breports\b|\bstatement\b|\bnews\b|\bpress release\b|"
    r"comunicado de prensa|anunció|reporta|según|afirma"
)


def detect_content_type(content: dict) -> ContentTypeResult:
    """
    Classify content as CONVOCATORIA vs NEWS/ARTICLE/REPORT based on patterns.

    Args:
        content: Dictionary with 'title', 'description', and 'url' keys

    Returns:
        ContentTypeResult with type, confidence (0-1), and reason
    """
    title = (content.get("title") or "").lower()
    description = (content.get("description") or "").lower()
    url = (content.get("url") or "").lower()

    haystack = title + " " + description + " " + url

    # Check convocatoria patterns
    convocatoria_matches = len(re.findall(CONVOCATORIA_PATTERNS, haystack))
    if convocatoria_matches >= 2:
        return ContentTypeResult(
            type=ContentType.CONVOCATORIA,
            confidence=min(0.95, 0.7 + (convocatoria_matches * 0.1)),
            reason=f"Found {convocatoria_matches} convocatoria indicators"
        )

    # Check news patterns
    news_matches = len(re.findall(NEWS_PATTERNS, haystack))
    if news_matches >= 2:
        return ContentTypeResult(
            type=ContentType.NEWS,
            confidence=min(0.95, 0.7 + (news_matches * 0.1)),
            reason=f"Found {news_matches} news indicators"
        )

    # Check known portals
    if re.search(r"(grants\.gov|bid\.org|unwomen\.org.*grants|fordfoundation\.org.*grants)", url):
        return ContentTypeResult(
            type=ContentType.CONVOCATORIA,
            confidence=0.90,
            reason="Known convocation portal"
        )

    return ContentTypeResult(
        type=ContentType.UNKNOWN,
        confidence=0.5,
        reason="No strong indicators"
    )
