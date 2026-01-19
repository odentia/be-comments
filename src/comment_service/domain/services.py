from __future__ import annotations

import base64
import json
from typing import Optional


def encode_cursor(comment_id: int) -> str:
    """Закодировать курсор из ID комментария"""
    data = {"id": comment_id}
    return base64.b64encode(json.dumps(data).encode()).decode()


def decode_cursor(cursor: str) -> Optional[int]:
    """Декодировать курсор в ID комментария"""
    try:
        data = json.loads(base64.b64decode(cursor.encode()).decode())
        return data.get("id")
    except Exception:
        return None
