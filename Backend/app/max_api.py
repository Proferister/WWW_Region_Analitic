import httpx

BASE_URL = "https://platform-api.max.ru"


class MaxAPI:
    def __init__(self, token: str):
        self._token = token
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"Authorization": token},
        )

    async def get_chat(self, chat_id: int) -> dict:
        resp = await self._client.get(f"/chats/{chat_id}")
        resp.raise_for_status()
        return resp.json()

    async def send_message(
        self,
        text: str,
        chat_id: int | None = None,
        user_id: int | None = None,
        format: str = "markdown",
        attachments: list | None = None,
    ) -> dict:
        params = {}
        if chat_id:
            params["chat_id"] = chat_id
        if user_id:
            params["user_id"] = user_id
        body: dict = {"text": text, "format": format}
        if attachments:
            body["attachments"] = attachments
        resp = await self._client.post(
            "/messages",
            params=params,
            json=body,
        )
        resp.raise_for_status()
        return resp.json()

    async def answer_callback(self, callback_id: str, notification: str | None = None, message: dict | None = None) -> dict:
        params = {"callback_id": callback_id}
        body: dict = {}
        if notification:
            body["notification"] = notification
        if message:
            body["message"] = message
        resp = await self._client.post("/answers", params=params, json=body)
        resp.raise_for_status()
        return resp.json()

    async def leave_chat(self, chat_id: int) -> dict:
        resp = await self._client.delete(f"/chats/{chat_id}/members/me")
        resp.raise_for_status()
        return resp.json()

    async def subscribe_webhook(self, url: str) -> dict:
        resp = await self._client.post("/subscriptions", json={"url": url})
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self._client.aclose()
