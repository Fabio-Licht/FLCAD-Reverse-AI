from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import Any

from core.project_model import (
    ProjectObject,
    ProjectObjectMetadata,
    ProjectObjectSnapshot,
    ProjectObjectType,
)


ProjectChangedCallback = Callable[[], None]


class ProjectManager:
    """
    Gerencia todos os objetos lógicos do projeto.

    O ProjectManager não renderiza geometrias. Ele registra:
    - significado;
    - tipo;
    - dados geométricos;
    - relações;
    - visibilidade;
    - bloqueio;
    - metadados.
    """

    def __init__(self) -> None:
        self._objects: dict[
            str,
            ProjectObject,
        ] = {}

        self._callbacks: list[
            ProjectChangedCallback
        ] = []

    def subscribe(
        self,
        callback: ProjectChangedCallback,
    ) -> None:
        """Registra uma função para mudanças no projeto."""

        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unsubscribe(
        self,
        callback: ProjectChangedCallback,
    ) -> None:
        """Remove uma função registrada."""

        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def add_object(
        self,
        project_object: ProjectObject,
    ) -> ProjectObject:
        """Adiciona um objeto ao projeto."""

        object_id = project_object.object_id

        if object_id in self._objects:
            raise ValueError(
                f'Já existe um objeto com o ID "{object_id}".'
            )

        self._objects[object_id] = project_object

        self._notify_changed()

        return project_object

    def create_object(
        self,
        object_id: str,
        name: str,
        object_type: ProjectObjectType | str,
        data: Any,
        *,
        visible: bool = True,
        locked: bool = False,
        parent_id: str | None = None,
        metadata: ProjectObjectMetadata | None = None,
    ) -> ProjectObject:
        """Cria e registra um novo objeto."""

        resolved_type = ProjectObjectType(
            object_type
        )

        if parent_id is not None:
            self._validate_parent(parent_id)

        project_object = ProjectObject(
            object_id=object_id,
            name=name,
            object_type=resolved_type,
            data=data,
            visible=visible,
            locked=locked,
            parent_id=parent_id,
            metadata=(
                metadata
                if metadata is not None
                else ProjectObjectMetadata()
            ),
        )

        return self.add_object(project_object)

    def get_object(
        self,
        object_id: str,
    ) -> ProjectObject | None:
        """Retorna um objeto pelo identificador."""

        return self._objects.get(object_id)

    def require_object(
        self,
        object_id: str,
    ) -> ProjectObject:
        """Retorna um objeto ou gera um erro claro."""

        project_object = self.get_object(
            object_id
        )

        if project_object is None:
            raise KeyError(
                f'Objeto não encontrado: "{object_id}".'
            )

        return project_object

    def contains(
        self,
        object_id: str,
    ) -> bool:
        """Informa se o objeto está registrado."""

        return object_id in self._objects

    def remove_object(
        self,
        object_id: str,
    ) -> ProjectObject | None:
        """Remove um objeto do projeto."""

        project_object = self._objects.pop(
            object_id,
            None,
        )

        if project_object is None:
            return None

        # Objetos dependentes perdem apenas a relação.
        # Eles não são apagados automaticamente.
        for child in self._objects.values():
            if child.parent_id == object_id:
                child.parent_id = None

        self._notify_changed()

        return project_object

    def rename_object(
        self,
        object_id: str,
        new_name: str,
    ) -> bool:
        """Renomeia um objeto existente."""

        project_object = self.get_object(
            object_id
        )

        if project_object is None:
            return False

        project_object.rename(new_name)

        self._notify_changed()

        return True

    def set_visibility(
        self,
        object_id: str,
        visible: bool,
    ) -> bool:
        """Atualiza a visibilidade lógica."""

        project_object = self.get_object(
            object_id
        )

        if project_object is None:
            return False

        project_object.set_visibility(
            visible
        )

        self._notify_changed()

        return True

    def set_locked(
        self,
        object_id: str,
        locked: bool,
    ) -> bool:
        """Bloqueia ou desbloqueia um objeto."""

        project_object = self.get_object(
            object_id
        )

        if project_object is None:
            return False

        project_object.set_locked(
            locked
        )

        self._notify_changed()

        return True

    def set_selected(
        self,
        object_id: str,
        selected: bool,
    ) -> bool:
        """Atualiza a seleção lógica."""

        project_object = self.get_object(
            object_id
        )

        if project_object is None:
            return False

        project_object.set_selected(
            selected
        )

        self._notify_changed()

        return True

    def clear_selection(self) -> None:
        """Remove a seleção lógica de todos os objetos."""

        changed = False

        for project_object in self._objects.values():
            if not project_object.selected:
                continue

            project_object.selected = False
            changed = True

        if changed:
            self._notify_changed()

    def objects(
        self,
    ) -> tuple[ProjectObject, ...]:
        """Retorna todos os objetos do projeto."""

        return tuple(
            self._objects.values()
        )

    def object_ids(
        self,
    ) -> tuple[str, ...]:
        """Retorna todos os identificadores."""

        return tuple(
            self._objects.keys()
        )

    def objects_by_type(
        self,
        object_type: ProjectObjectType | str,
    ) -> tuple[ProjectObject, ...]:
        """Retorna objetos de uma determinada família."""

        resolved_type = ProjectObjectType(
            object_type
        )

        return tuple(
            project_object
            for project_object
            in self._objects.values()
            if project_object.object_type
            == resolved_type
        )

    def children_of(
        self,
        parent_id: str,
    ) -> tuple[ProjectObject, ...]:
        """Retorna objetos vinculados a um objeto-pai."""

        return tuple(
            project_object
            for project_object
            in self._objects.values()
            if project_object.parent_id
            == parent_id
        )

    def selected_objects(
        self,
    ) -> tuple[ProjectObject, ...]:
        """Retorna os objetos logicamente selecionados."""

        return tuple(
            project_object
            for project_object
            in self._objects.values()
            if project_object.selected
        )

    def visible_objects(
        self,
    ) -> tuple[ProjectObject, ...]:
        """Retorna os objetos logicamente visíveis."""

        return tuple(
            project_object
            for project_object
            in self._objects.values()
            if project_object.visible
        )

    def snapshot_object(
        self,
        object_id: str,
    ) -> ProjectObjectSnapshot | None:
        """Cria um estado restaurável."""

        project_object = self.get_object(
            object_id
        )

        if project_object is None:
            return None

        return ProjectObjectSnapshot(
            object_id=project_object.object_id,
            name=project_object.name,
            object_type=project_object.object_type,
            data=project_object.data,
            visible=project_object.visible,
            locked=project_object.locked,
            selected=project_object.selected,
            parent_id=project_object.parent_id,
            metadata=deepcopy(
                project_object.metadata
            ),
        )

    def restore_object(
        self,
        snapshot: ProjectObjectSnapshot,
    ) -> ProjectObject:
        """Restaura um objeto a partir de um snapshot."""

        if snapshot.object_id in self._objects:
            self.remove_object(
                snapshot.object_id
            )

        project_object = ProjectObject(
            object_id=snapshot.object_id,
            name=snapshot.name,
            object_type=snapshot.object_type,
            data=snapshot.data,
            visible=snapshot.visible,
            locked=snapshot.locked,
            selected=snapshot.selected,
            parent_id=snapshot.parent_id,
            metadata=deepcopy(
                snapshot.metadata
            ),
        )

        return self.add_object(
            project_object
        )

    def clear(self) -> None:
        """Remove todos os objetos do projeto."""

        if not self._objects:
            return

        self._objects.clear()

        self._notify_changed()

    def object_count(self) -> int:
        """Retorna a quantidade total de objetos."""

        return len(self._objects)

    def object_count_by_type(
        self,
        object_type: ProjectObjectType | str,
    ) -> int:
        """Retorna a quantidade de uma determinada família."""

        return len(
            self.objects_by_type(
                object_type
            )
        )

    def project_summary(
        self,
    ) -> dict[str, int]:
        """Retorna um resumo quantitativo do projeto."""

        summary: dict[str, int] = {
            object_type.value: 0
            for object_type
            in ProjectObjectType
        }

        for project_object in self._objects.values():
            summary[
                project_object.object_type.value
            ] += 1

        return summary

    def update_metadata(
        self,
        object_id: str,
        **metadata_values: Any,
    ) -> bool:
        """Atualiza campos personalizados dos metadados."""

        project_object = self.get_object(
            object_id
        )

        if project_object is None:
            return False

        project_object.metadata.custom.update(
            metadata_values
        )

        self._notify_changed()

        return True

    def _validate_parent(
        self,
        parent_id: str,
    ) -> None:
        """Confirma a existência de um objeto-pai."""

        if parent_id not in self._objects:
            raise ValueError(
                f'O objeto-pai "{parent_id}" não existe.'
            )

    def _notify_changed(self) -> None:
        """Comunica alterações aos observadores."""

        for callback in tuple(
            self._callbacks
        ):
            callback()