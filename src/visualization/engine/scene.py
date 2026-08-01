from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SceneObject:
    """Representa uma entidade existente na cena 3D."""

    object_id: str
    name: str
    object_type: str
    actor: Any
    data: Any
    base_color: str
    render_options: dict[str, Any]
    visible: bool = True
    selected: bool = False
    selection_state: dict[str, Any] | None = None


@dataclass
class SceneObjectSnapshot:
    """Estado necessário para restaurar um objeto."""

    object_id: str
    name: str
    object_type: str
    data: Any
    base_color: str
    render_options: dict[str, Any]
    visible: bool


class SceneManager:
    """Gerencia os objetos renderizados no Genesis."""

    SELECTION_COLORS = {
        "mesh": "#d9efff",
        "reference_plane": "#78ff9b",
        "reference_cylinder": "#ff9f43",
        "reference_axis": "#54d8ff",
        "reference_point": "#ff5b5b",
        "sketch": "#d6a7ff",
        "curve": "#ff77c8",
        "surface": "#7fffd4",
        "solid": "#fff176",
    }

    def __init__(
        self,
        viewer: Any,
    ) -> None:
        self.viewer = viewer
        self._objects: dict[str, SceneObject] = {}
        self._actor_ids: dict[int, str] = {}

    def add_mesh(
        self,
        object_id: str,
        name: str,
        mesh: Any,
        object_type: str = "mesh",
        **render_options: Any,
    ) -> SceneObject:
        """Adiciona uma entidade gráfica à cena."""

        if object_id in self._objects:
            self.remove_object(object_id)

        stored_options = dict(render_options)

        # Evita passar o argumento pickable duas vezes.
        pickable = bool(
            stored_options.pop("pickable", True)
        )

        base_color = str(
            stored_options.get(
                "color",
                "#8796a8",
            )
        )

        # Não envia "pickable" para add_mesh. Algumas versões do
        # PyVistaQt já encaminham esse argumento internamente e podem
        # gerar "multiple values for keyword argument 'pickable'".
        actor = self.viewer.add_mesh(
            mesh,
            name=object_id,
            **stored_options,
        )

        # Aplica a propriedade diretamente no ator depois da criação.
        try:
            actor.SetPickable(pickable)
        except AttributeError:
            try:
                actor.pickable = pickable
            except Exception:
                pass

        scene_object = SceneObject(
            object_id=object_id,
            name=name,
            object_type=object_type,
            actor=actor,
            data=mesh,
            base_color=base_color,
            render_options={
                **stored_options,
                "pickable": pickable,
            },
        )

        self._objects[object_id] = scene_object
        self._actor_ids[id(actor)] = object_id

        return scene_object

    def restore_object(
        self,
        snapshot: SceneObjectSnapshot,
    ) -> SceneObject:
        """Restaura um objeto a partir de um snapshot."""

        scene_object = self.add_mesh(
            object_id=snapshot.object_id,
            name=snapshot.name,
            mesh=snapshot.data,
            object_type=snapshot.object_type,
            **snapshot.render_options,
        )

        self.set_visibility(
            snapshot.object_id,
            snapshot.visible,
        )

        return scene_object

    def snapshot_object(
        self,
        object_id: str,
    ) -> SceneObjectSnapshot | None:
        """Cria uma cópia restaurável do objeto."""

        scene_object = self.get_object(object_id)

        if scene_object is None:
            return None

        return SceneObjectSnapshot(
            object_id=scene_object.object_id,
            name=scene_object.name,
            object_type=scene_object.object_type,
            data=scene_object.data,
            base_color=scene_object.base_color,
            render_options=dict(
                scene_object.render_options
            ),
            visible=scene_object.visible,
        )

    def get_object(
        self,
        object_id: str,
    ) -> SceneObject | None:
        return self._objects.get(object_id)

    def get_object_by_actor(
        self,
        actor: Any,
    ) -> SceneObject | None:
        if actor is None:
            return None

        object_id = self._actor_ids.get(id(actor))

        if object_id is not None:
            return self.get_object(object_id)

        for scene_object in self._objects.values():
            stored_actor = scene_object.actor

            if stored_actor is actor:
                return scene_object

            try:
                if (
                    stored_actor.GetAddressAsString("")
                    == actor.GetAddressAsString("")
                ):
                    return scene_object
            except (AttributeError, TypeError):
                continue

        return None

    def objects_by_type(
        self,
        object_type: str,
    ) -> tuple[SceneObject, ...]:
        return tuple(
            scene_object
            for scene_object in self._objects.values()
            if scene_object.object_type == object_type
        )

    def set_visibility(
        self,
        object_id: str,
        visible: bool,
    ) -> bool:
        scene_object = self.get_object(object_id)

        if scene_object is None:
            return False

        scene_object.visible = visible
        scene_object.actor.visibility = visible
        self.viewer.render()
        return True


    def _actor_property(
        self,
        scene_object: SceneObject,
    ) -> Any:
        """Obtém a propriedade VTK/PyVista do ator."""

        actor = scene_object.actor

        try:
            return actor.GetProperty()
        except Exception:
            return getattr(actor, "prop", None)

    def _capture_selection_state(
        self,
        scene_object: SceneObject,
    ) -> dict[str, Any]:
        """Guarda aparência para restauração fiel."""

        prop = self._actor_property(scene_object)
        state: dict[str, Any] = {}

        if prop is None:
            return state

        getters = {
            "color": ("GetColor",),
            "edge_color": ("GetEdgeColor",),
            "opacity": ("GetOpacity",),
            "line_width": ("GetLineWidth",),
            "edge_visibility": ("GetEdgeVisibility",),
        }

        for key, names in getters.items():
            for name in names:
                method = getattr(prop, name, None)

                if callable(method):
                    try:
                        state[key] = method()
                    except Exception:
                        pass
                    break

        return state

    def _apply_selection_appearance(
        self,
        scene_object: SceneObject,
    ) -> None:
        """Aplica destaque visual específico por tipo."""

        prop = self._actor_property(scene_object)

        if prop is None:
            return

        color = self.SELECTION_COLORS.get(
            scene_object.object_type,
            "#f2b134",
        )

        try:
            from pyvista import Color

            rgb = Color(color).float_rgb
        except Exception:
            rgb = (1.0, 0.70, 0.20)

        try:
            prop.SetColor(*rgb)
        except Exception:
            try:
                scene_object.actor.prop.color = color
            except Exception:
                pass

        object_type = scene_object.object_type

        if object_type == "mesh":
            try:
                prop.SetEdgeVisibility(True)
                prop.SetEdgeColor(0.35, 0.80, 1.0)
                prop.SetLineWidth(1.0)
            except Exception:
                pass

            # Mantém transparência existente, mas torna a seleção
            # suficientemente visível em qualquer modo de exibição.
            try:
                current_opacity = float(
                    scene_object.selection_state.get(
                        "opacity",
                        prop.GetOpacity(),
                    )
                )
                prop.SetOpacity(
                    max(current_opacity, 0.62)
                )
            except Exception:
                pass

        elif object_type == "reference_plane":
            try:
                prop.SetEdgeVisibility(True)
                prop.SetEdgeColor(0.55, 1.0, 0.65)
                prop.SetLineWidth(3.0)
                prop.SetOpacity(
                    max(
                        float(prop.GetOpacity()),
                        0.58,
                    )
                )
            except Exception:
                pass

        elif object_type in {
            "reference_cylinder",
            "reference_axis",
            "curve",
            "sketch",
        }:
            try:
                prop.SetLineWidth(
                    max(
                        float(prop.GetLineWidth()),
                        4.0,
                    )
                )
            except Exception:
                pass

        elif object_type == "reference_point":
            try:
                prop.SetOpacity(1.0)
            except Exception:
                pass

    def _restore_selection_appearance(
        self,
        scene_object: SceneObject,
    ) -> None:
        """Restaura exatamente a aparência anterior."""

        state = scene_object.selection_state or {}
        prop = self._actor_property(scene_object)

        if prop is None:
            scene_object.selection_state = None
            return

        try:
            color = state.get("color")

            if color is not None:
                prop.SetColor(*color)
            else:
                scene_object.actor.prop.color = (
                    scene_object.base_color
                )
        except Exception:
            try:
                scene_object.actor.prop.color = (
                    scene_object.base_color
                )
            except Exception:
                pass

        try:
            edge_color = state.get("edge_color")

            if edge_color is not None:
                prop.SetEdgeColor(*edge_color)
        except Exception:
            pass

        for key, setter_name in (
            ("opacity", "SetOpacity"),
            ("line_width", "SetLineWidth"),
            ("edge_visibility", "SetEdgeVisibility"),
        ):
            value = state.get(key)
            setter = getattr(
                prop,
                setter_name,
                None,
            )

            if (
                value is not None
                and callable(setter)
            ):
                try:
                    setter(value)
                except Exception:
                    pass

        scene_object.selection_state = None

    def set_selected(
        self,
        object_id: str,
        selected: bool,
        render: bool = True,
    ) -> bool:
        """Seleciona com destaque forte e restauração segura."""

        scene_object = self.get_object(object_id)

        if scene_object is None:
            return False

        if scene_object.selected == selected:
            return True

        scene_object.selected = selected

        if selected:
            scene_object.selection_state = (
                self._capture_selection_state(
                    scene_object
                )
            )
            self._apply_selection_appearance(
                scene_object
            )
        else:
            self._restore_selection_appearance(
                scene_object
            )

        if render:
            self.viewer.render()

        return True

    def set_selected_objects(
        self,
        selected_ids: set[str],
    ) -> None:
        for object_id, scene_object in self._objects.items():
            should_be_selected = (
                object_id in selected_ids
            )

            if (
                scene_object.selected
                == should_be_selected
            ):
                continue

            self.set_selected(
                object_id,
                should_be_selected,
                render=False,
            )

        self.viewer.render()


    def clear_selection(self) -> None:
        """Limpa seleção restaurando todos os estados visuais."""

        changed = False

        for scene_object in self._objects.values():
            if not scene_object.selected:
                continue

            scene_object.selected = False
            self._restore_selection_appearance(
                scene_object
            )
            changed = True

        if changed:
            self.viewer.render()

    def set_display_mode(
        self,
        object_id: str,
        mode: str,
        render: bool = True,
    ) -> bool:
        scene_object = self.get_object(object_id)

        if scene_object is None:
            return False

        prop = scene_object.actor.prop

        if mode == "solid":
            prop.style = "surface"
            prop.show_edges = False
            prop.opacity = 1.0
            prop.lighting = True

        elif mode == "edges":
            prop.style = "surface"
            prop.show_edges = True
            prop.edge_color = "#46515e"
            prop.edge_opacity = 0.65
            prop.line_width = 0.5
            prop.opacity = 1.0
            prop.lighting = True

        elif mode == "wireframe":
            prop.style = "wireframe"
            prop.show_edges = False
            prop.line_width = 0.6
            prop.opacity = 1.0
            prop.lighting = False

        elif mode == "transparent":
            prop.style = "surface"
            prop.show_edges = False
            prop.opacity = 0.35
            prop.lighting = True

        else:
            return False

        if render:
            self.viewer.render()

        return True

    def set_display_mode_by_type(
        self,
        object_type: str,
        mode: str,
    ) -> int:
        changed_count = 0

        for scene_object in self.objects_by_type(
            object_type
        ):
            if self.set_display_mode(
                scene_object.object_id,
                mode,
                render=False,
            ):
                changed_count += 1

        if changed_count:
            self.viewer.render()

        return changed_count

    def remove_object(
        self,
        object_id: str,
    ) -> bool:
        scene_object = self.get_object(object_id)

        if scene_object is None:
            return False

        actor = scene_object.actor

        try:
            self.viewer.remove_actor(
                actor,
                render=False,
            )
        finally:
            self._actor_ids.pop(id(actor), None)
            self._objects.pop(object_id, None)

        self.viewer.render()
        return True

    def clear(self) -> None:
        self.viewer.clear()
        self._objects.clear()
        self._actor_ids.clear()
        self.viewer.render()

    def object_count(self) -> int:
        return len(self._objects)

    def object_ids(self) -> tuple[str, ...]:
        return tuple(self._objects.keys())
