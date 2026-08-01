from __future__ import annotations

from uuid import UUID

from .engineering_feature import EngineeringFeature


class FeatureRepository:

    def __init__(self):

        self._features: dict[
            UUID,
            EngineeringFeature,
        ] = {}

    # ---------------------------------------------

    def add(
        self,
        feature: EngineeringFeature,
    ) -> None:

        self._features[
            feature.id
        ] = feature

    # ---------------------------------------------

    def remove(
        self,
        feature_id: UUID,
    ) -> None:

        self._features.pop(
            feature_id,
            None,
        )

    # ---------------------------------------------

    def find(
        self,
        feature_id: UUID,
    ) -> EngineeringFeature | None:

        return self._features.get(
            feature_id
        )

    # ---------------------------------------------

    def all(
        self,
    ) -> list[EngineeringFeature]:

        return list(
            self._features.values()
        )

    # ---------------------------------------------

    def clear(
        self,
    ) -> None:

        self._features.clear()

    # ---------------------------------------------

    def count(
        self,
    ) -> int:

        return len(
            self._features
        )