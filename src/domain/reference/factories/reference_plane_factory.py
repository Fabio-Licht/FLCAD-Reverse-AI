"""Factory for traceable engineering reference planes."""

from __future__ import annotations

from core.entity.entity_source import EntitySource
from core.entity.entity_state import EntityState
from core.entity.entity_type import EntityType
from domain.recognition.plane.entities.recognized_plane import RecognizedPlane
from domain.reference.entities.reference_plane import ReferencePlane
from domain.reference.value_objects.reference_plane_settings import (
    ReferencePlaneSettings,
)


class ReferencePlaneFactory:
    """Create reference planes without modifying mathematical geometry."""

    def create(
        self,
        recognized_plane: RecognizedPlane,
        settings: ReferencePlaneSettings,
    ) -> ReferencePlane:
        """Create a reference preserving the complete recognition chain."""

        name = (
            f"{settings.default_name_prefix}-"
            f"{recognized_plane.plane.id.hex[:8]}"
        )

        return ReferencePlane(
            name=name,
            display_name=name,
            entity_type=EntityType.PLANE,
            state=EntityState.REFERENCED,
            source=EntitySource.CALCULATED,
            confidence=recognized_plane.recognition_confidence,
            visible=settings.default_visibility,
            color=settings.default_color,
            opacity=settings.default_opacity,
            layer=settings.default_layer,
            recognized_plane=recognized_plane,
        )
