import httpx

from app.config import settings


async def send_otp_email(to: str, code: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            settings.MAIL_API_URL,
            headers={"x-api-key": settings.MAIL_API_KEY},
            json={
                "to": to,
                "subject": "Код подтверждения",
                "body": (
                    f"<div style='font-family:sans-serif;'>"
                    f"<h2>Ваш код подтверждения</h2>"
                    f"<p style='font-size:32px;font-weight:bold;letter-spacing:8px;'>{code}</p>"
                    f"<p>Код действителен 5 минут.</p>"
                    f"</div>"
                ),
                "html": True,
            },
        )
        resp.raise_for_status()
        return resp.json()
