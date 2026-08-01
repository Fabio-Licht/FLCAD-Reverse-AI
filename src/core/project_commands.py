from __future__ import annotations

from copy import deepcopy
from typing import Any

import numpy as np
import vtk

from core.command_history import Command
from core.project_manager import ProjectManager
from core.project_model import (
    ProjectObjectMetadata,
    ProjectObjectSnapshot,
    ProjectObjectType,
)
from geometry.reference_manager import (
    ReferenceManager,
    ReferenceRecord,
)
from visualization.engine.scene import (
    SceneManager,
    SceneObjectSnapshot,
)


class ImportMeshCommand(Command):
    """Importa uma malha como operação reversível."""

    def __init__(
        self,
        scene: SceneManager,
        project_panel: Any,
        project_manager: ProjectManager,
        object_id: str,
        name: str,
        source_file: str,
        source_mesh: Any,
        display_mesh: Any,
        render_options: dict[str, Any],
    ) -> None:
        self.scene = scene
        self.project_panel = project_panel
        self.project_manager = project_manager

        self.object_id = object_id
        self.name = name
        self.source_file = source_file
        self.source_mesh = source_mesh
        self.display_mesh = display_mesh
        self.render_options = dict(render_options)

    @property
    def description(self) -> str:
        return f"Importar {self.name}"

    def execute(self) -> None:
        """Adiciona a malha ao projeto, cena e árvore."""

        if not self.project_manager.contains(self.object_id):
            self.project_manager.create_object(
                object_id=self.object_id,
                name=self.name,
                object_type=ProjectObjectType.MESH,
                data=self.source_mesh,
                metadata=ProjectObjectMetadata(
                    source_file=self.source_file,
                    created_by="ImportMeshCommand",
                    creation_method="import_stl",
                ),
            )

        self.scene.add_mesh(
            object_id=self.object_id,
            name=self.name,
            mesh=self.display_mesh,
            object_type="mesh",
            **self.render_options,
        )

        self.project_panel.add_object(
            object_id=self.object_id,
            name=self.name,
            object_type="mesh",
            data=self.source_mesh,
            visible=True,
        )

    def undo(self) -> None:
        """Remove a malha importada."""

        self.scene.remove_object(self.object_id)
        self.project_panel.remove_object(self.object_id)
        self.project_manager.remove_object(self.object_id)


class CreateReferenceCommand(Command):
    """Cria uma geometria de referência reversível."""

    def __init__(
        self,
        scene: SceneManager,
        project_panel: Any,
        project_manager: ProjectManager,
        reference_manager: ReferenceManager,
        record: ReferenceRecord,
        display_geometry: Any,
        render_options: dict[str, Any],
        metadata: ProjectObjectMetadata | None = None,
    ) -> None:
        self.scene = scene
        self.project_panel = project_panel
        self.project_manager = project_manager
        self.reference_manager = reference_manager

        self.record = record
        self.display_geometry = display_geometry
        self.render_options = dict(render_options)
        self.metadata = (
            deepcopy(metadata)
            if metadata is not None
            else ProjectObjectMetadata(
                created_by="CreateReferenceCommand",
                creation_method="manual_reference",
            )
        )

    @property
    def description(self) -> str:
        return f"Criar {self.record.name}"

    def execute(self) -> None:
        """Registra e exibe a referência."""

        if not self.reference_manager.contains(
            self.record.object_id
        ):
            self.reference_manager.register_existing(
                self.record
            )

        if not self.project_manager.contains(
            self.record.object_id
        ):
            self.project_manager.create_object(
                object_id=self.record.object_id,
                name=self.record.name,
                object_type=ProjectObjectType(
                    self.record.entity.object_type
                ),
                data=self.record.entity,
                metadata=deepcopy(self.metadata),
            )

        self.scene.add_mesh(
            object_id=self.record.object_id,
            name=self.record.name,
            mesh=self.display_geometry,
            object_type=self.record.entity.object_type,
            **self.render_options,
        )

        self.project_panel.add_object(
            object_id=self.record.object_id,
            name=self.record.name,
            object_type=self.record.entity.object_type,
            data=self.record.entity,
            visible=True,
        )

    def undo(self) -> None:
        """Remove a referência criada."""

        self.scene.remove_object(self.record.object_id)
        self.project_panel.remove_object(
            self.record.object_id
        )
        self.project_manager.remove_object(
            self.record.object_id
        )
        self.reference_manager.remove(
            self.record.object_id
        )


class DeleteObjectsCommand(Command):
    """Remove e restaura vários objetos do projeto."""

    def __init__(
        self,
        scene: SceneManager,
        project_panel: Any,
        project_manager: ProjectManager,
        reference_manager: ReferenceManager,
        object_ids: set[str],
    ) -> None:
        self.scene = scene
        self.project_panel = project_panel
        self.project_manager = project_manager
        self.reference_manager = reference_manager
        self.object_ids = tuple(sorted(object_ids))

        self._scene_snapshots: list[
            SceneObjectSnapshot
        ] = []

        self._project_snapshots: dict[
            str,
            ProjectObjectSnapshot,
        ] = {}

        self._reference_records: dict[
            str,
            ReferenceRecord,
        ] = {}

    @property
    def description(self) -> str:
        count = len(self.object_ids)

        if count == 1:
            snapshot = (
                self._scene_snapshots[0]
                if self._scene_snapshots
                else None
            )

            if snapshot is not None:
                return f"Excluir {snapshot.name}"

            return "Excluir objeto"

        return f"Excluir {count} objetos"

    def execute(self) -> None:
        """Remove os objetos preservando estados restauráveis."""

        if not self._scene_snapshots:
            for object_id in self.object_ids:
                scene_snapshot = (
                    self.scene.snapshot_object(
                        object_id
                    )
                )

                if scene_snapshot is not None:
                    self._scene_snapshots.append(
                        scene_snapshot
                    )

                project_snapshot = (
                    self.project_manager.snapshot_object(
                        object_id
                    )
                )

                if project_snapshot is not None:
                    self._project_snapshots[
                        object_id
                    ] = project_snapshot

                reference_record = (
                    self.reference_manager.get(
                        object_id
                    )
                )

                if reference_record is not None:
                    self._reference_records[
                        object_id
                    ] = reference_record

        for object_id in self.object_ids:
            self.scene.remove_object(object_id)
            self.project_panel.remove_object(object_id)
            self.project_manager.remove_object(object_id)
            self.reference_manager.remove(object_id)

    def undo(self) -> None:
        """Restaura os objetos removidos."""

        for scene_snapshot in self._scene_snapshots:
            object_id = scene_snapshot.object_id

            project_snapshot = (
                self._project_snapshots.get(
                    object_id
                )
            )

            if project_snapshot is not None:
                self.project_manager.restore_object(
                    project_snapshot
                )

            reference_record = (
                self._reference_records.get(
                    object_id
                )
            )

            if reference_record is not None:
                self.reference_manager.register_existing(
                    reference_record
                )

            self.scene.restore_object(
                scene_snapshot
            )

            project_object = (
                self.project_manager.get_object(
                    object_id
                )
            )

            logical_data = (
                project_object.data
                if project_object is not None
                else scene_snapshot.data
            )

            self.project_panel.add_object(
                object_id=object_id,
                name=scene_snapshot.name,
                object_type=scene_snapshot.object_type,
                data=logical_data,
                visible=scene_snapshot.visible,
            )


class SetVisibilityCommand(Command):
    """Altera reversivelmente a visibilidade."""

    def __init__(
        self,
        scene: SceneManager,
        project_panel: Any,
        project_manager: ProjectManager,
        object_id: str,
        new_visibility: bool,
    ) -> None:
        self.scene = scene
        self.project_panel = project_panel
        self.project_manager = project_manager
        self.object_id = object_id
        self.new_visibility = new_visibility

        scene_object = self.scene.get_object(object_id)

        self.old_visibility = (
            scene_object.visible
            if scene_object is not None
            else not new_visibility
        )

        self.object_name = (
            scene_object.name
            if scene_object is not None
            else object_id
        )

    @property
    def description(self) -> str:
        action = (
            "Mostrar"
            if self.new_visibility
            else "Ocultar"
        )

        return f"{action} {self.object_name}"

    def execute(self) -> None:
        self._apply(self.new_visibility)

    def undo(self) -> None:
        self._apply(self.old_visibility)

    def _apply(
        self,
        visible: bool,
    ) -> None:
        self.scene.set_visibility(
            self.object_id,
            visible,
        )

        self.project_panel.set_object_visibility(
            self.object_id,
            visible,
        )

        self.project_manager.set_visibility(
            self.object_id,
            visible,
        )



class CreateReferenceBatchCommand(Command):
    """Cria várias referências em uma única etapa de histórico."""

    def __init__(
        self,
        description: str,
        commands: list[CreateReferenceCommand],
    ) -> None:
        self._description = description
        self._commands = list(commands)

    @property
    def description(self) -> str:
        return self._description

    def execute(self) -> None:
        executed: list[CreateReferenceCommand] = []

        try:
            for command in self._commands:
                command.execute()
                executed.append(command)
        except Exception:
            for command in reversed(executed):
                command.undo()
            raise

    def undo(self) -> None:
        for command in reversed(
            self._commands
        ):
            command.undo()



class CompositeProjectCommand(Command):
    """Executa vários comandos como uma única etapa de Undo/Redo."""

    def __init__(
        self,
        description: str,
        commands: list[Command],
    ) -> None:
        self._description = description
        self._commands = list(commands)

    @property
    def description(self) -> str:
        return self._description

    def execute(self) -> None:
        executed: list[Command] = []

        try:
            for command in self._commands:
                command.execute()
                executed.append(command)
        except Exception:
            for command in reversed(executed):
                command.undo()
            raise

    def undo(self) -> None:
        for command in reversed(self._commands):
            command.undo()



class TransformSceneObjectsCommand(Command):
    """
    Aplica uma matriz 4 × 4 a vários atores com Undo/Redo.

    Esta primeira fundação de alinhamento transforma a representação
    da cena. A incorporação definitiva da matriz aos dados-fonte da
    malha será uma evolução posterior do Geometry Engine.
    """

    def __init__(
        self,
        *,
        scene: SceneManager,
        object_ids: set[str],
        transform: Any,
        description: str,
    ) -> None:
        self.scene = scene
        self.object_ids = tuple(
            sorted(object_ids)
        )
        self.transform = np.asarray(
            transform,
            dtype=float,
        )

        if self.transform.shape != (4, 4):
            raise ValueError(
                "A transformação deve ser uma matriz 4 × 4."
            )

        self._description = description
        self._old_matrices: dict[
            str,
            np.ndarray,
        ] = {}

    @property
    def description(self) -> str:
        return self._description

    def execute(self) -> None:
        if not self._old_matrices:
            for object_id in self.object_ids:
                scene_object = (
                    self.scene.get_object(
                        object_id
                    )
                )

                if scene_object is None:
                    continue

                self._old_matrices[
                    object_id
                ] = self._actor_matrix(
                    scene_object.actor
                )

        for object_id in self.object_ids:
            scene_object = self.scene.get_object(
                object_id
            )

            if scene_object is None:
                continue

            old_matrix = self._old_matrices.get(
                object_id,
                np.eye(4),
            )
            new_matrix = (
                self.transform @ old_matrix
            )

            self._set_actor_matrix(
                scene_object.actor,
                new_matrix,
            )

        self.scene.viewer.render()

    def undo(self) -> None:
        for object_id, matrix in (
            self._old_matrices.items()
        ):
            scene_object = self.scene.get_object(
                object_id
            )

            if scene_object is None:
                continue

            self._set_actor_matrix(
                scene_object.actor,
                matrix,
            )

        self.scene.viewer.render()

    def _actor_matrix(
        self,
        actor: Any,
    ) -> np.ndarray:
        vtk_matrix = actor.GetUserMatrix()

        if vtk_matrix is None:
            return np.eye(4)

        result = np.eye(4)

        for row in range(4):
            for column in range(4):
                result[row, column] = (
                    vtk_matrix.GetElement(
                        row,
                        column,
                    )
                )

        return result

    def _set_actor_matrix(
        self,
        actor: Any,
        matrix: np.ndarray,
    ) -> None:
        vtk_matrix = vtk.vtkMatrix4x4()

        for row in range(4):
            for column in range(4):
                vtk_matrix.SetElement(
                    row,
                    column,
                    float(
                        matrix[row, column]
                    ),
                )

        actor.SetUserMatrix(vtk_matrix)
