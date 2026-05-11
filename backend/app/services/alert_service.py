"""Servicio de alertas: Slack + email vía Resend."""

import httpx
import resend
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class AlertService:
    def __init__(self) -> None:
        if settings.RESEND_API_KEY:
            resend.api_key = settings.RESEND_API_KEY

    async def send_slack(self, message: str, channel: str = "#alianzas") -> bool:
        if not settings.SLACK_WEBHOOK_URL:
            logger.warning("SLACK_WEBHOOK_URL not configured — Slack alert skipped")
            return False

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    settings.SLACK_WEBHOOK_URL,
                    json={"text": message, "channel": channel},
                )
                resp.raise_for_status()
                return True
        except Exception as exc:
            logger.error("Slack alert failed", error=str(exc))
            return False

    async def send_deadline_alert(self, opportunities: list[dict]) -> None:
        if not opportunities:
            return

        lines = ["*⏰ Oportunidades GO con vencimiento próximo:*\n"]
        for opp in opportunities:
            lines.append(
                f"• *{opp['title']}* — Score: {opp['score_total']} — "
                f"Cierra en {opp['days_left']} días — <{opp.get('url_rfp', '#')}|Ver convocatoria>"
            )

        await self.send_slack("\n".join(lines))

        if settings.RESEND_API_KEY:
            self._send_email_deadline(opportunities)

    def _send_email_deadline(self, opportunities: list[dict]) -> None:
        try:
            html = "<h2>Oportunidades GO con vencimiento próximo</h2><ul>"
            for opp in opportunities:
                html += (
                    f"<li><strong>{opp['title']}</strong> — Score: {opp['score_total']} — "
                    f"Cierra en {opp['days_left']} días</li>"
                )
            html += "</ul>"

            resend.Emails.send({
                "from": "GrantFlow AI <grantflow@aeiotu.org>",
                "to": ["alianzas@aeiotu.org"],
                "subject": f"⏰ {len(opportunities)} oportunidad(es) con vencimiento próximo",
                "html": html,
            })
        except Exception as exc:
            logger.error("Email alert failed", error=str(exc))
