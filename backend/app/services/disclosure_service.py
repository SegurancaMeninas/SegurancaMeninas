from __future__ import annotations

from typing import Any

UNKNOWN_TEXT = "Não divulgado oficialmente."


def disclosure_text(value: Any) -> str:
    if value is None:
        return UNKNOWN_TEXT
    if isinstance(value, bool):
        return "Sim" if value else "Não"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{value:,.0f}" if float(value).is_integer() else f"{value:,.2f}"
    text = str(value).strip()
    return text if text else UNKNOWN_TEXT
