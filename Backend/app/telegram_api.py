import httpx

BASE_URL = "https://api.telegram.org"


class TelegramAPI:
    def __init__(self, token: str):
        self._token = token
        self._client = httpx.AsyncClient(
            base_url=f"{BASE_URL}/bot{token}",
        )

    async def get_chat(self, chat_id: int) -> dict:
        resp = await self._client.post("/getChat", json={"chat_id": chat_id})
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise Exception(data.get("description", "Unknown error"))
        return data["result"]

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "Markdown",
    ) -> dict:
        resp = await self._client.post(
            "/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
        )
        resp.raise_for_status()
        return resp.json()

    async def leave_chat(self, chat_id: int) -> dict:
        resp = await self._client.post("/leaveChat", json={"chat_id": chat_id})
        resp.raise_for_status()
        return resp.json()

    async def set_webhook(self, url: str) -> dict:
        resp = await self._client.post("/setWebhook", json={"url": url})
        resp.raise_for_status()
        return resp.json()

    async def get_chat_avatar_url(self, chat_id: int) -> str | None:
        """Получить URL аватарки чата."""
        try:
            chat = await self.get_chat(chat_id)
            photo = chat.get("photo")
            if not photo:
                return None
            file_id = photo.get("big_file_id") or photo.get("small_file_id")
            if not file_id:
                return None
            resp = await self._client.post("/getFile", json={"file_id": file_id})
            resp.raise_for_status()
            data = resp.json()
            if not data.get("ok"):
                return None
            file_path = data["result"].get("file_path")
            if file_path:
                return f"{BASE_URL}/file/bot{self._token}/{file_path}"
        except Exception:
            pass
        return None

    async def get_me(self) -> dict:
        resp = await self._client.post("/getMe")
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self._client.aclose()
