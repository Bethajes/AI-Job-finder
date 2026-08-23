import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

RESEND_BASE_URL = "https://api.resend.com"
USER_AGENT = "ethiopian-job-platform/1.0"


class EmailService:
    def __init__(self) -> None:
        self.api_key = settings.RESEND_API_KEY
        self.from_email = settings.EMAIL_FROM
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=RESEND_BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "User-Agent": USER_AGENT,
                },
                timeout=30.0,
            )
        return self._client

    async def send_email(
        self,
        *,
        to: str,
        subject: str,
        html: str,
    ) -> bool:
        if not self.api_key or self.api_key.startswith("re_dev"):
            logger.info(
                "Email service (dev mode) - would send to=%s subject=%s",
                to,
                subject,
            )
            return True

        client = await self._get_client()
        payload = {
            "from": self.from_email,
            "to": [to],
            "subject": subject,
            "html": html,
        }

        try:
            response = await client.post("/emails", json=payload)
            response.raise_for_status()
            logger.info("Email sent successfully to=%s subject=%s", to, subject)
            return True
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Failed to send email to=%s status=%d body=%s",
                to,
                exc.response.status_code,
                exc.response.text,
            )
            return False
        except httpx.RequestError as exc:
            logger.error("Email request error to=%s error=%s", to, str(exc))
            return False

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
