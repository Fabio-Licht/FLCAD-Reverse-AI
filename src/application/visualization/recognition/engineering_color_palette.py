"""Centralized deterministic colors for engineering visualization."""

from __future__ import annotations

from colorsys import hsv_to_rgb
from hashlib import sha256
from uuid import UUID


class EngineeringColorPalette:
    """Provide stable colors for recognition and reference categories."""

    MESH = "#8a939f"
    PLANE_CANDIDATE = "#4fc3f7"
    RECOGNIZED_PLANE = "#4caf70"
    REFERENCE_PLANE = "#f2c94c"
    SELECTION = "#ff9f1c"
    LOCKED = "#7f8c8d"
    WARNING = "#e85d5d"

    @classmethod
    def region(cls, region_id: UUID) -> str:
        """Return a deterministic engineering color for a region UUID."""

        digest = sha256(region_id.bytes).digest()
        hue = int.from_bytes(digest[:2], "big") / 65535.0
        saturation = 0.58 + digest[2] / 255.0 * 0.20
        value = 0.72 + digest[3] / 255.0 * 0.18
        red, green, blue = hsv_to_rgb(hue, saturation, value)
        return cls._hex(red, green, blue)

    @staticmethod
    def _hex(red: float, green: float, blue: float) -> str:
        """Convert normalized RGB components to a hexadecimal color."""

        return "#{:02x}{:02x}{:02x}".format(
            round(red * 255),
            round(green * 255),
            round(blue * 255),
        )
