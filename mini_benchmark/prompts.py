from __future__ import annotations

import json

from .config import PROMPTS_DIR


def render_prompt(template_name: str, **values: object) -> str:
    template = (PROMPTS_DIR / template_name).read_text(encoding="utf-8")
    safe_values = {
        key: json.dumps(value, indent=2, sort_keys=True) if isinstance(value, dict) else value
        for key, value in values.items()
    }
    return template.format(**safe_values)

