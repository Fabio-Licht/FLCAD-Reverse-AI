from __future__ import annotations

from collections.abc import Callable
from typing import Any


SelectionCallback = Callable[[set[str]], None]


class SelectionManager:
    """
    Gerencia a seleção de objetos do Genesis.

    A seleção pode ser alterada pela árvore do projeto,
    pela viewport ou futuramente por janela, laço e pincel.
    """

    def __init__(
        self,
        scene: Any,
        project_panel: Any,
    ) -> None:
        self.scene = scene
        self.project_panel = project_panel

        self._selected_ids: set[str] = set()
        self._active = False
        self._callbacks: list[SelectionCallback] = []

    @property
    def active(self) -> bool:
        """Informa se o modo de seleção está ativo."""

        return self._active

    def selected_ids(self) -> set[str]:
        """Retorna uma cópia da seleção atual."""

        return set(self._selected_ids)

    def selected_count(self) -> int:
        """Retorna a quantidade de objetos selecionados."""

        return len(self._selected_ids)

    def activate(self) -> None:
        """Ativa a seleção de objetos."""

        self._active = True

        self.project_panel.set_selection_mode_active(
            True
        )

        self._synchronize_visuals()

    def deactivate(
        self,
        clear_selection: bool = True,
    ) -> None:
        """Desativa o modo de seleção."""

        self._active = False

        self.project_panel.set_selection_mode_active(
            False
        )

        if clear_selection:
            self.clear()
        else:
            self._synchronize_visuals()

    def subscribe(
        self,
        callback: SelectionCallback,
    ) -> None:
        """Registra uma função para receber mudanças."""

        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unsubscribe(
        self,
        callback: SelectionCallback,
    ) -> None:
        """Remove uma função registrada."""

        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def replace(
        self,
        object_ids: set[str],
    ) -> None:
        """Substitui completamente a seleção atual."""

        valid_ids = {
            object_id
            for object_id in object_ids
            if self.scene.get_object(object_id)
            is not None
        }

        self._selected_ids = valid_ids
        self._selection_changed()

    def add(
        self,
        object_id: str,
    ) -> bool:
        """Adiciona um objeto à seleção."""

        if self.scene.get_object(object_id) is None:
            return False

        if object_id in self._selected_ids:
            return False

        self._selected_ids.add(object_id)
        self._selection_changed()

        return True

    def remove(
        self,
        object_id: str,
    ) -> bool:
        """Remove um objeto da seleção."""

        if object_id not in self._selected_ids:
            return False

        self._selected_ids.remove(object_id)
        self._selection_changed()

        return True

    def toggle(
        self,
        object_id: str,
    ) -> bool:
        """Alterna a seleção de um objeto."""

        if self.scene.get_object(object_id) is None:
            return False

        if object_id in self._selected_ids:
            self._selected_ids.remove(object_id)
            selected = False
        else:
            self._selected_ids.add(object_id)
            selected = True

        self._selection_changed()

        return selected

    def toggle_actor(
        self,
        actor: Any,
    ) -> str | None:
        """Alterna o objeto correspondente ao ator clicado."""

        scene_object = self.scene.get_object_by_actor(
            actor
        )

        if scene_object is None:
            return None

        self.toggle(scene_object.object_id)

        return scene_object.object_id

    def clear(self) -> None:
        """Remove todos os objetos da seleção."""

        if not self._selected_ids:
            self._synchronize_visuals()
            return

        self._selected_ids.clear()
        self._selection_changed()

    def remove_deleted_object(
        self,
        object_id: str,
    ) -> None:
        """Retira da seleção um objeto já excluído."""

        if object_id not in self._selected_ids:
            return

        self._selected_ids.discard(object_id)
        self._selection_changed()

    def selected_names(self) -> list[str]:
        """Retorna os nomes dos objetos selecionados."""

        names: list[str] = []

        for object_id in sorted(self._selected_ids):
            scene_object = self.scene.get_object(
                object_id
            )

            if scene_object is not None:
                names.append(scene_object.name)

        return names

    def _selection_changed(self) -> None:
        """Sincroniza e comunica uma alteração."""

        self._synchronize_visuals()

        selected_copy = set(self._selected_ids)

        for callback in tuple(self._callbacks):
            callback(selected_copy)

    def _synchronize_visuals(self) -> None:
        """Atualiza árvore e viewport."""

        self.scene.set_selected_objects(
            self._selected_ids
        )

        self.project_panel.set_selected_objects(
            self._selected_ids
        )