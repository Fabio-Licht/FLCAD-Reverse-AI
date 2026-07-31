from __future__ import annotations

from dataclasses import dataclass
from itertools import count
from typing import Any

from geometry.reference_entities import (
    AxisReference,
    CylinderReference,
    PlaneReference,
    PointReference,
)


ReferenceEntity = (
    PointReference
    | AxisReference
    | PlaneReference
    | CylinderReference
)


@dataclass(frozen=True)
class ReferenceRecord:
    """Registro de uma geometria de referência."""

    object_id: str
    name: str
    entity: ReferenceEntity


class ReferenceManager:
    """
    Gerencia identificadores, nomes e entidades de referência.

    O SceneManager continuará responsável pela representação
    gráfica. Este componente será responsável pelo significado
    geométrico das entidades.
    """

    TYPE_PREFIXES = {
        "reference_point": "point",
        "reference_axis": "axis",
        "reference_plane": "plane",
        "reference_cylinder": "cylinder",
    }

    DEFAULT_NAMES = {
        "reference_point": "Ponto",
        "reference_axis": "Eixo",
        "reference_plane": "Plano",
        "reference_cylinder": "Cilindro",
    }

    def __init__(self) -> None:
        self._records: dict[
            str,
            ReferenceRecord,
        ] = {}

        self._counters = {
            object_type: count(1)
            for object_type
            in self.TYPE_PREFIXES
        }

    def create_record(
        self,
        entity: ReferenceEntity,
        name: str | None = None,
    ) -> ReferenceRecord:
        """Cria e registra uma nova referência."""

        object_type = entity.object_type

        prefix = self.TYPE_PREFIXES.get(
            object_type
        )

        if prefix is None:
            raise ValueError(
                f"Tipo de referência desconhecido: {object_type}"
            )

        number = next(
            self._counters[object_type]
        )

        object_id = (
            f"{prefix}_{number:04d}"
        )

        default_name = (
            self.DEFAULT_NAMES[object_type]
        )

        record_name = (
            name.strip()
            if name is not None
            and name.strip()
            else f"{default_name} {number:02d}"
        )

        record = ReferenceRecord(
            object_id=object_id,
            name=record_name,
            entity=entity,
        )

        self._records[object_id] = record

        return record

    def register_existing(
        self,
        record: ReferenceRecord,
    ) -> None:
        """Registra novamente uma referência restaurada."""

        self._records[
            record.object_id
        ] = record

    def remove(
        self,
        object_id: str,
    ) -> ReferenceRecord | None:
        """Remove uma referência do registro."""

        return self._records.pop(
            object_id,
            None,
        )

    def get(
        self,
        object_id: str,
    ) -> ReferenceRecord | None:
        """Localiza uma referência pelo identificador."""

        return self._records.get(
            object_id
        )

    def records(
        self,
    ) -> tuple[ReferenceRecord, ...]:
        """Retorna todas as referências existentes."""

        return tuple(
            self._records.values()
        )

    def records_by_type(
        self,
        object_type: str,
    ) -> tuple[ReferenceRecord, ...]:
        """Retorna referências de uma determinada família."""

        return tuple(
            record
            for record in self._records.values()
            if record.entity.object_type
            == object_type
        )

    def clear(self) -> None:
        """Remove todas as referências registradas."""

        self._records.clear()

    def contains(
        self,
        object_id: str,
    ) -> bool:
        """Confirma se uma referência está registrada."""

        return object_id in self._records