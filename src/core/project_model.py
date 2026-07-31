from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ProjectObjectType(StrEnum):
    """Tipos de objetos reconhecidos pelo projeto."""

    MESH = "mesh"

    REFERENCE_POINT = "reference_point"
    REFERENCE_AXIS = "reference_axis"
    REFERENCE_PLANE = "reference_plane"
    REFERENCE_CYLINDER = "reference_cylinder"

    SKETCH = "sketch"
    CURVE = "curve"
    SURFACE = "surface"
    SOLID = "solid"
    ANALYSIS = "analysis"


@dataclass
class ProjectObjectMetadata:
    """
    Informações auxiliares de um objeto do projeto.

    Esses dados poderão ser ampliados futuramente sem alterar
    a estrutura principal dos objetos.
    """

    source_file: str | None = None
    source_object_id: str | None = None

    created_by: str | None = None
    creation_method: str | None = None

    rms_error: float | None = None
    confidence: float | None = None

    notes: str = ""

    custom: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class ProjectObject:
    """
    Representa um objeto lógico do projeto.

    O objeto lógico é independente do ator gráfico usado
    para exibi-lo na viewport.
    """

    object_id: str
    name: str
    object_type: ProjectObjectType
    data: Any

    visible: bool = True
    locked: bool = False
    selected: bool = False

    parent_id: str | None = None

    metadata: ProjectObjectMetadata = field(
        default_factory=ProjectObjectMetadata
    )

    def rename(
        self,
        new_name: str,
    ) -> None:
        """Altera o nome do objeto."""

        cleaned_name = new_name.strip()

        if not cleaned_name:
            raise ValueError(
                "O nome do objeto não pode estar vazio."
            )

        self.name = cleaned_name

    def set_visibility(
        self,
        visible: bool,
    ) -> None:
        """Altera a visibilidade lógica do objeto."""

        self.visible = bool(visible)

    def set_locked(
        self,
        locked: bool,
    ) -> None:
        """Bloqueia ou desbloqueia o objeto."""

        self.locked = bool(locked)

    def set_selected(
        self,
        selected: bool,
    ) -> None:
        """Atualiza o estado lógico de seleção."""

        self.selected = bool(selected)


@dataclass(frozen=True)
class ProjectObjectSnapshot:
    """Estado restaurável de um objeto do projeto."""

    object_id: str
    name: str
    object_type: ProjectObjectType
    data: Any

    visible: bool
    locked: bool
    selected: bool

    parent_id: str | None

    metadata: ProjectObjectMetadata