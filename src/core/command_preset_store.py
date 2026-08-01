from __future__ import annotations
import json
from typing import Any
from PySide6.QtCore import QSettings

class CommandPresetStore:
    """Persistência dos últimos parâmetros usados em cada comando."""
    ORGANIZATION = "FLCAD"
    APPLICATION = "FLCAD Reverse AI"
    ROOT_KEY = "command_presets"

    def __init__(self) -> None:
        self._settings = QSettings(self.ORGANIZATION, self.APPLICATION)

    def load(self, command_name: str, defaults: dict[str, Any] | None = None) -> dict[str, Any]:
        result = dict(defaults or {})
        raw = self._settings.value(self._key(command_name), "")
        if not raw:
            return result
        try:
            stored = json.loads(str(raw))
        except (TypeError, ValueError, json.JSONDecodeError):
            return result
        if isinstance(stored, dict):
            result.update(stored)
        return result

    def save(self, command_name: str, values: dict[str, Any]) -> None:
        self._settings.setValue(
            self._key(command_name),
            json.dumps(self._json_safe(values), ensure_ascii=False, separators=(",", ":")),
        )
        self._settings.sync()

    def clear(self, command_name: str | None = None) -> None:
        self._settings.remove(self.ROOT_KEY if command_name is None else self._key(command_name))
        self._settings.sync()

    def _key(self, command_name: str) -> str:
        safe = command_name.strip().lower().replace(" ", "_")
        return f"{self.ROOT_KEY}/{safe}"

    def _json_safe(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {str(k): self._json_safe(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._json_safe(v) for v in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)
