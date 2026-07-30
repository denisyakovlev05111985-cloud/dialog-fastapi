import httpx
from app.config import settings
from typing import Any, List, Dict

class PolzaError(Exception):
    pass

class PolzaClient:
    def __init__(self) -> None:
        self.client = httpx.AsyncClient(
            base_url=settings.polza_api_base_url,
            timeout=settings.polza_timeout_seconds,
        )

    async def close(self) -> None:
        await self.client.aclose()

    def headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {settings.polza_api_key}"}

    async def list_models(self) -> List[Dict[str, str]]:
        response = await self._request("GET", "/models")
        payload = self._json(response)
        raw_data = payload.get("data") or []

        if not isinstance(raw_data, list):
            raise PolzaError("Polza.ai вернул неверный формат поля data")

        models = []
        for item in raw_data:
            if not isinstance(item, dict):
                continue
            if not self._is_chat_model(item):
                continue

            model_id = item.get("id")
            if isinstance(model_id, str) and model_id:
                name = item.get("name") or ""
                models.append({"id": model_id, "name": name})

        return sorted(models, key=lambda m: m["name"].lower())

    async def complete(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
    ) -> str:
        if not settings.polza_api_key:
            raise PolzaError("На сервере не настроен POLZA_API_KEY")

        response = await self._request(
            "POST",
            "/chat/completions",
            json={"model": model_id, "messages": messages},
        )

        payload = self._json(response)

        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise PolzaError("Polza.ai вернул ответ неизвестного формата") from exc

        if not isinstance(content, str) or not content.strip():
            raise PolzaError("Модель вернула пустой ответ")

        return content

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            response = await self.client.request(
                method,
                path,
                headers=self.headers(),
                **kwargs,
            )
        except httpx.TimeoutException as exc:
            raise PolzaError("Polza.ai не ответил за отведённое время") from exc
        except httpx.HTTPError as exc:
            raise PolzaError("Не удалось подключиться к Polza.ai") from exc

        if response.is_success:
            return response

        # Обработка ошибки от API
        message = None
        try:
            error_payload = response.json()
            if isinstance(error_payload, dict):
                message = error_payload.get("error", {}).get("message")
        except (AttributeError, ValueError):
            pass

        raise PolzaError(message or "Polza.ai вернул ошибку")

    @staticmethod
    def _json(response: httpx.Response) -> Dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise PolzaError("Polza.ai вернул некорректный JSON") from exc

        if not isinstance(payload, dict):
            raise PolzaError("Polza.ai вернул ответ неизвестного формата")
        return payload

    @staticmethod
    def _is_chat_model(model: Dict[str, Any]) -> bool:
        endpoints = model.get("endpoints") or []
        return model.get("type") == "chat" or "/v1/chat/completions" in endpoints


polza = PolzaClient()