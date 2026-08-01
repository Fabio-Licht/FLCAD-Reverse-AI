from __future__ import annotations

from .engineering_feature import EngineeringFeature


class FeatureFactory:

    @staticmethod
    def create(
        geometry,
        name: str | None = None,
    ) -> EngineeringFeature:

        if name is None:

            name = geometry.__class__.__name__

        return EngineeringFeature(

            geometry=geometry,

            name=name,

        )