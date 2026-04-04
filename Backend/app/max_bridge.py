import hashlib
import hmac
import json
from urllib.parse import parse_qs, unquote

from app.config import settings


def validate_init_data(init_data: str) -> dict | None:
    """
    Валидация initData от MAX Bridge.
    Возвращает распарсенные данные если валидны, иначе None.
    """
    # Парсим key=value пары
    params = parse_qs(init_data, keep_blank_values=True)
    # parse_qs возвращает списки, берём первый элемент
    flat = {k: v[0] for k, v in params.items()}

    # Извлекаем hash
    received_hash = flat.pop("hash", None)
    if not received_hash:
        return None

    # Сортируем по ключам, декодируем значения
    sorted_pairs = sorted(flat.items(), key=lambda x: x[0])
    launch_params = "\n".join(f"{k}={unquote(v)}" for k, v in sorted_pairs)

    # Генерируем secret_key: HMAC_SHA256("WebAppData", BOT_TOKEN)
    secret_key = hmac.new(
        b"WebAppData",
        settings.MAX_BOT_TOKEN.encode(),
        hashlib.sha256,
    ).digest()

    # Вычисляем подпись: HMAC_SHA256(secret_key, launch_params)
    computed_hash = hmac.new(
        secret_key,
        launch_params.encode(),
        hashlib.sha256,
    ).hexdigest()

    # Сравниваем (constant-time)
    if not hmac.compare_digest(computed_hash, received_hash):
        return None

    # Парсим user из JSON
    result = {}
    for k, v in sorted_pairs:
        decoded = unquote(v)
        if k in ("user", "chat"):
            try:
                result[k] = json.loads(decoded)
            except json.JSONDecodeError:
                result[k] = decoded
        else:
            result[k] = decoded

    result["hash"] = received_hash
    return result
