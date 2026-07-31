from __future__ import annotations

from itertools import count
from math import isfinite, sqrt
from pathlib import Path
from typing import Any

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QCloseEvent,
)
from PySide6.QtWidgets import (
    QDialog,
    QDockWidget,
    QFileDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QStatusBar,
    QToolBar,
    QToolButton,
)
from pyvistaqt import QtInteractor

from core.command_history import CommandManager
from core.project_commands import (
    CreateReferenceBatchCommand,
    CreateReferenceCommand,
    DeleteObjectsCommand,
    ImportMeshCommand,
    SetVisibilityCommand,
)
from core.project_manager import ProjectManager
from core.project_model import ProjectObjectMetadata
from geometry.reference_entities import (
    AxisReference,
    CylinderReference,
    PlaneReference,
    PointReference,
)
from geometry.cylinder_fit import fit_cylinder_to_points
from geometry.mesh_region import (
    grow_cylindrical_region,
    grow_planar_region,
    refine_cylindrical_cells,
)
from geometry.plane_fit import fit_plane_to_points
from geometry.reference_manager import ReferenceManager
from mesh_io.stl_loader import load_stl
from ui.delete_dialog import DeleteDialog
from ui.cylinder_preview_dialog import CylinderPreviewDialog
from ui.cylinder_region_dialog import CylinderRegionDialog
from ui.plane_preview_dialog import PlanePreviewDialog
from ui.plane_region_dialog import PlaneRegionDialog
from ui.point_dialog import PointDialog
from ui.project_panel import ProjectPanel
from visualization.engine.context_picker import ContextPicker
from visualization.engine.navigation_manager import (
    NavigationManager,
)
from visualization.engine.reference_factory import (
    ReferenceGeometryFactory,
)
from visualization.engine.scene import SceneManager
from visualization.engine.selection_manager import (
    SelectionManager,
)


class MainWindow(QMainWindow):
    """Janela principal do FLCAD Reverse AI."""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(
            "FLCAD Reverse AI — v0.4.4 Genesis"
        )
        self.resize(1280, 800)

        self._mesh_id_counter = count(1)

        self.delete_mode_active = False
        self.delete_dialog: DeleteDialog | None = None

        self._context_point: tuple[
            float,
            float,
            float,
        ] | None = None

        self._context_object_id: str | None = None

        self._pending_plane_radius = 0.0
        self._pending_plane_minimum_points = 50
        self._pending_plane_scale = 2.0
        self._pending_plane_maximum_angle = 12.0

        self._plane_region_preview_name = (
            "__flcad_plane_region_preview__"
        )
        self._plane_preview_name = (
            "__flcad_plane_preview__"
        )

        self._pending_cylinder_radius = 0.0
        self._pending_cylinder_angle = 20.0
        self._pending_cylinder_minimum_points = 100

        self._cylinder_region_preview_name = (
            "__flcad_cylinder_region_preview__"
        )
        self._cylinder_preview_name = (
            "__flcad_cylinder_preview__"
        )
        self._cylinder_axis_preview_name = (
            "__flcad_cylinder_axis_preview__"
        )

        self._cylinder_preview_dialog = None
        self._pending_cylinder_creation = None

        self.viewer = QtInteractor(self)
        self.setCentralWidget(self.viewer)

        self.scene = SceneManager(self.viewer)
        self.project = ProjectManager()
        self.references = ReferenceManager()

        self.navigation = NavigationManager(
            self.viewer
        )

        self.context_picker = ContextPicker(
            viewer=self.viewer,
            scene=self.scene,
        )

        self.reference_factory = (
            ReferenceGeometryFactory()
        )

        self._create_project_dock()

        self.selection = SelectionManager(
            self.scene,
            self.project_panel,
        )

        self.selection.subscribe(
            self.on_selection_changed
        )

        self.project_panel.object_selection_toggled.connect(
            self.selection.toggle
        )

        self.history = CommandManager()
        self.history.subscribe(
            self.update_history_actions
        )

        self._create_toolbar()
        self._create_status_bar()
        self._configure_viewer()
        self._configure_viewport_context_menu()

        self.update_history_actions()

    def _create_toolbar(self) -> None:
        """Cria a barra principal."""

        toolbar = QToolBar(
            "Ferramentas principais"
        )
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        open_action = QAction(
            "Abrir STL",
            self,
        )
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(
            self.open_stl
        )

        self.undo_action = QAction(
            "Desfazer",
            self,
        )
        self.undo_action.setShortcut("Ctrl+Z")
        self.undo_action.triggered.connect(
            self.undo
        )

        self.redo_action = QAction(
            "Refazer",
            self,
        )
        self.redo_action.setShortcuts(
            ["Ctrl+Y", "Ctrl+Shift+Z"]
        )
        self.redo_action.triggered.connect(
            self.redo
        )

        fit_action = QAction(
            "Ajustar vista",
            self,
        )
        fit_action.setShortcut("F")
        fit_action.triggered.connect(
            self.fit_view
        )

        self.select_action = QAction(
            "Selecionar objetos",
            self,
        )
        self.select_action.setCheckable(True)
        self.select_action.setShortcut("S")
        self.select_action.toggled.connect(
            self.set_selection_mode
        )

        delete_action = QAction(
            "Deletar",
            self,
        )
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(
            self.start_delete_mode
        )

        toolbar.addAction(open_action)
        toolbar.addSeparator()

        toolbar.addAction(self.undo_action)
        toolbar.addAction(self.redo_action)
        toolbar.addSeparator()

        toolbar.addAction(fit_action)
        toolbar.addAction(self.select_action)
        toolbar.addAction(delete_action)
        toolbar.addSeparator()

        self._create_reference_menu(toolbar)
        self._create_recognition_menu(toolbar)
        self._create_visualization_menu(toolbar)

    def _create_reference_menu(
        self,
        toolbar: QToolBar,
    ) -> None:
        """Cria o menu para referências geométricas."""

        reference_menu = QMenu(
            "Criar referência",
            self,
        )

        point_action = QAction(
            "Ponto por coordenadas",
            self,
        )
        point_action.triggered.connect(
            self.create_point_by_coordinates
        )
        reference_menu.addAction(point_action)

        point_on_geometry_action = QAction(
            "Ponto sobre geometria",
            self,
        )
        point_on_geometry_action.triggered.connect(
            self.start_point_on_geometry_mode
        )
        reference_menu.addAction(
            point_on_geometry_action
        )

        reference_menu.addSeparator()

        axes_menu = reference_menu.addMenu(
            "Eixos globais"
        )

        for label, axis_name in (
            ("Eixo X", "x"),
            ("Eixo Y", "y"),
            ("Eixo Z", "z"),
        ):
            action = QAction(label, self)
            action.triggered.connect(
                lambda checked=False, value=axis_name:
                self.create_global_axis(value)
            )
            axes_menu.addAction(action)

        planes_menu = reference_menu.addMenu(
            "Planos globais"
        )

        for label, plane_name in (
            ("Plano XY", "xy"),
            ("Plano XZ", "xz"),
            ("Plano YZ", "yz"),
        ):
            action = QAction(label, self)
            action.triggered.connect(
                lambda checked=False, value=plane_name:
                self.create_global_plane(value)
            )
            planes_menu.addAction(action)

        reference_button = QToolButton(self)
        reference_button.setText(
            "Criar referência"
        )
        reference_button.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )
        reference_button.setMenu(reference_menu)

        toolbar.addWidget(reference_button)
        toolbar.addSeparator()

    def _create_recognition_menu(
        self,
        toolbar: QToolBar,
    ) -> None:
        """Cria o menu das ferramentas de reconhecimento."""

        recognition_menu = QMenu(
            "Reconhecer geometria",
            self,
        )

        plane_region_action = QAction(
            "Plano por região da malha",
            self,
        )
        plane_region_action.triggered.connect(
            self.start_plane_region_mode
        )
        recognition_menu.addAction(
            plane_region_action
        )

        cylinder_region_action = QAction(
            "Cilindro por região da malha",
            self,
        )
        cylinder_region_action.triggered.connect(
            self.start_cylinder_region_mode
        )
        recognition_menu.addAction(
            cylinder_region_action
        )

        recognition_button = QToolButton(self)
        recognition_button.setText(
            "Reconhecer geometria"
        )
        recognition_button.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )
        recognition_button.setMenu(
            recognition_menu
        )

        toolbar.addWidget(
            recognition_button
        )
        toolbar.addSeparator()

    def _create_visualization_menu(
        self,
        toolbar: QToolBar,
    ) -> None:
        """Cria o menu único de visualização."""

        visualization_menu = QMenu(
            "Visualização",
            self,
        )

        self.display_group = QActionGroup(self)
        self.display_group.setExclusive(True)

        self.solid_action = QAction(
            "Sólido",
            self,
        )
        self.solid_action.setCheckable(True)

        self.edges_action = QAction(
            "Sólido + Arestas",
            self,
        )
        self.edges_action.setCheckable(True)
        self.edges_action.setChecked(True)

        self.wireframe_action = QAction(
            "Wireframe",
            self,
        )
        self.wireframe_action.setCheckable(True)

        self.transparent_action = QAction(
            "Transparente",
            self,
        )
        self.transparent_action.setCheckable(True)

        display_actions = (
            (self.solid_action, "solid"),
            (self.edges_action, "edges"),
            (
                self.wireframe_action,
                "wireframe",
            ),
            (
                self.transparent_action,
                "transparent",
            ),
        )

        for action, mode in display_actions:
            self.display_group.addAction(action)
            action.triggered.connect(
                lambda checked=False, value=mode:
                self.set_display_mode(value)
            )
            visualization_menu.addAction(action)

        visualization_menu.addSeparator()

        views_menu = visualization_menu.addMenu(
            "Vistas técnicas"
        )

        view_definitions = (
            ("Isométrica", "isometric"),
            ("Frontal", "front"),
            ("Traseira", "back"),
            ("Superior (Z+)", "top"),
            ("Inferior (Z-)", "bottom"),
            ("Esquerda", "left"),
            ("Direita", "right"),
        )

        for label, view_name in view_definitions:
            action = QAction(label, self)
            action.triggered.connect(
                lambda checked=False, value=view_name:
                self.set_standard_view(value)
            )
            views_menu.addAction(action)

        views_menu.addSeparator()

        rotate_clockwise_action = QAction(
            "Rotacionar 90° horário",
            self,
        )
        rotate_clockwise_action.triggered.connect(
            lambda:
            self.rotate_view_90(clockwise=True)
        )

        rotate_counterclockwise_action = QAction(
            "Rotacionar 90° anti-horário",
            self,
        )
        rotate_counterclockwise_action.triggered.connect(
            lambda:
            self.rotate_view_90(clockwise=False)
        )

        views_menu.addAction(
            rotate_clockwise_action
        )
        views_menu.addAction(
            rotate_counterclockwise_action
        )

        visualization_menu.addSeparator()

        self.axes_action = QAction(
            "Mostrar eixos da viewport",
            self,
        )
        self.axes_action.setCheckable(True)
        self.axes_action.setChecked(True)
        self.axes_action.toggled.connect(
            self.navigation.set_axes_visible
        )
        visualization_menu.addAction(
            self.axes_action
        )

        visualization_menu.addSeparator()

        projection_group = QActionGroup(self)
        projection_group.setExclusive(True)

        self.perspective_action = QAction(
            "Perspectiva",
            self,
        )
        self.perspective_action.setCheckable(True)
        self.perspective_action.setChecked(True)

        self.orthographic_action = QAction(
            "Ortográfica",
            self,
        )
        self.orthographic_action.setCheckable(True)

        projection_group.addAction(
            self.perspective_action
        )
        projection_group.addAction(
            self.orthographic_action
        )

        self.perspective_action.triggered.connect(
            lambda:
            self.navigation.set_parallel_projection(
                False
            )
        )
        self.orthographic_action.triggered.connect(
            lambda:
            self.navigation.set_parallel_projection(
                True
            )
        )

        visualization_menu.addAction(
            self.perspective_action
        )
        visualization_menu.addAction(
            self.orthographic_action
        )

        visualization_menu.addSeparator()

        restore_center_action = QAction(
            "Restaurar centro global",
            self,
        )
        restore_center_action.triggered.connect(
            self.restore_global_rotation_center
        )
        visualization_menu.addAction(
            restore_center_action
        )

        visualization_button = QToolButton(self)
        visualization_button.setText(
            "Visualização"
        )
        visualization_button.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )
        visualization_button.setMenu(
            visualization_menu
        )

        toolbar.addWidget(
            visualization_button
        )

    def _create_project_dock(self) -> None:
        """Cria o painel lateral."""

        self.project_panel = ProjectPanel(self)
        self.project_panel.visibility_changed.connect(
            self.set_object_visibility
        )

        self.project_dock = QDockWidget(
            "Projeto",
            self,
        )
        self.project_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.project_dock.setMinimumWidth(310)
        self.project_dock.setWidget(
            self.project_panel
        )

        self.addDockWidget(
            Qt.DockWidgetArea.LeftDockWidgetArea,
            self.project_dock,
        )

    def _create_status_bar(self) -> None:
        """Cria a barra inferior."""

        status_bar = QStatusBar()
        status_bar.showMessage(
            "Pronto — abra uma malha STL"
        )
        self.setStatusBar(status_bar)

    def _configure_viewer(self) -> None:
        """Configura a viewport."""

        self.viewer.set_background(
            "#3a414b",
            top="#171b21",
        )
        self.viewer.show_axes()
        self.viewer.enable_anti_aliasing("ssaa")
        self.viewer.enable_lightkit()

    def _configure_viewport_context_menu(self) -> None:
        """Ativa o menu contextual da viewport."""

        context_widget = self.viewer.interactor
        context_widget.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        context_widget.customContextMenuRequested.connect(
            self.show_viewport_context_menu
        )

    def _next_mesh_id(self) -> str:
        """Cria identificador exclusivo de malha."""

        number = next(self._mesh_id_counter)
        return f"mesh_{number:04d}"

    def _reference_scale(self) -> float:
        """Calcula uma escala visual adequada."""

        mesh_objects = self.scene.objects_by_type(
            "mesh"
        )

        if not mesh_objects:
            return 100.0

        bounds_values: list[
            tuple[float, float, float, float, float, float]
        ] = []

        for scene_object in mesh_objects:
            try:
                bounds = tuple(
                    float(value)
                    for value in scene_object.data.bounds
                )
            except Exception:
                continue

            if (
                len(bounds) == 6
                and all(isfinite(value) for value in bounds)
            ):
                bounds_values.append(bounds)

        if not bounds_values:
            return 100.0

        combined = (
            min(bounds[0] for bounds in bounds_values),
            max(bounds[1] for bounds in bounds_values),
            min(bounds[2] for bounds in bounds_values),
            max(bounds[3] for bounds in bounds_values),
            min(bounds[4] for bounds in bounds_values),
            max(bounds[5] for bounds in bounds_values),
        )

        diagonal = sqrt(
            (combined[1] - combined[0]) ** 2
            + (combined[3] - combined[2]) ** 2
            + (combined[5] - combined[4]) ** 2
        )

        return max(diagonal, 100.0)

    def _execute_point_creation(
        self,
        position: tuple[float, float, float],
        name: str | None,
        creation_method: str,
    ) -> None:
        """Cria um ponto lógico, visual e reversível."""

        entity = PointReference(
            position=position
        )

        record = self.references.create_record(
            entity,
            name=name,
        )

        point_radius = max(
            self._reference_scale() * 0.008,
            0.5,
        )

        display_geometry = (
            self.reference_factory.create_point(
                entity,
                radius=point_radius,
            )
        )

        command = CreateReferenceCommand(
            scene=self.scene,
            project_panel=self.project_panel,
            project_manager=self.project,
            reference_manager=self.references,
            record=record,
            display_geometry=display_geometry,
            render_options={
                "color": "#ff7a45",
                "smooth_shading": True,
                "ambient": 0.55,
                "diffuse": 0.45,
                "specular": 0.25,
                "pickable": True,
            },
            metadata=ProjectObjectMetadata(
                created_by="user",
                creation_method=creation_method,
            ),
        )

        self.history.execute(command)
        self.viewer.render()

        self.statusBar().showMessage(
            f"Criado: {record.name}"
        )

    def start_point_on_geometry_mode(self) -> None:
        """
        Ativa a criação de um ponto clicando em uma geometria.

        Funciona sobre qualquer ator selecionável da cena:
        malha, curva, superfície, sólido ou referência.
        """

        if self.scene.object_count() == 0:
            QMessageBox.information(
                self,
                "Nenhuma geometria disponível",
                (
                    "Importe ou crie uma geometria antes "
                    "de definir um ponto sobre ela."
                ),
            )
            return

        if self.delete_mode_active:
            self.cancel_delete_mode()

        self.disable_selection_mode()

        try:
            self.viewer.disable_picking()
        except Exception:
            pass

        self.viewer.enable_surface_point_picking(
            callback=self.on_geometry_point_picked,
            show_message=False,
            show_point=True,
            point_size=12,
            color="#ff7a45",
            left_clicking=True,
            pickable_window=False,
            clear_on_no_selection=False,
            picker="cell",
        )

        self.statusBar().showMessage(
            "Clique sobre uma malha, curva, superfície "
            "ou sólido para criar o ponto"
        )

    def on_geometry_point_picked(
        self,
        point: Any,
    ) -> None:
        """Cria o ponto na posição capturada."""

        if point is None or len(point) < 3:
            self.statusBar().showMessage(
                "Nenhum ponto válido foi identificado"
            )
            return

        position = (
            float(point[0]),
            float(point[1]),
            float(point[2]),
        )

        try:
            self.viewer.disable_picking()
        except Exception:
            pass

        self._execute_point_creation(
            position=position,
            name=None,
            creation_method="point_on_geometry",
        )

    def create_point_by_coordinates(self) -> None:
        """Cria um ponto a partir de X, Y e Z."""

        dialog = PointDialog(self)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self._execute_point_creation(
            position=dialog.coordinates(),
            name=dialog.point_name(),
            creation_method="point_coordinates",
        )

    def create_global_axis(
        self,
        axis_name: str,
    ) -> None:
        """Cria um eixo global X, Y ou Z."""

        definitions = {
            "x": (
                "Eixo X",
                (1.0, 0.0, 0.0),
                "#ff5b5b",
            ),
            "y": (
                "Eixo Y",
                (0.0, 1.0, 0.0),
                "#56d364",
            ),
            "z": (
                "Eixo Z",
                (0.0, 0.0, 1.0),
                "#4ea1ff",
            ),
        }

        definition = definitions.get(axis_name)

        if definition is None:
            return

        name, direction, color = definition

        entity = AxisReference(
            origin=(0.0, 0.0, 0.0),
            direction=direction,
            display_length=self._reference_scale(),
        )

        record = self.references.create_record(
            entity,
            name=name,
        )

        display_geometry = (
            self.reference_factory.create_axis(
                entity
            )
        )

        command = CreateReferenceCommand(
            scene=self.scene,
            project_panel=self.project_panel,
            project_manager=self.project,
            reference_manager=self.references,
            record=record,
            display_geometry=display_geometry,
            render_options={
                "color": color,
                "lighting": False,
                "ambient": 1.0,
                "pickable": True,
            },
            metadata=ProjectObjectMetadata(
                created_by="system",
                creation_method=f"global_axis_{axis_name}",
            ),
        )

        self.history.execute(command)
        self.viewer.render()

        self.statusBar().showMessage(
            f"Criado: {record.name}"
        )

    def create_global_plane(
        self,
        plane_name: str,
    ) -> None:
        """Cria um plano global XY, XZ ou YZ."""

        definitions = {
            "xy": (
                "Plano XY",
                (0.0, 0.0, 1.0),
                "#4ea1ff",
            ),
            "xz": (
                "Plano XZ",
                (0.0, 1.0, 0.0),
                "#56d364",
            ),
            "yz": (
                "Plano YZ",
                (1.0, 0.0, 0.0),
                "#ff5b5b",
            ),
        }

        definition = definitions.get(plane_name)

        if definition is None:
            return

        name, normal, color = definition
        size = self._reference_scale() * 0.75

        entity = PlaneReference(
            origin=(0.0, 0.0, 0.0),
            normal=normal,
            size_x=size,
            size_y=size,
        )

        record = self.references.create_record(
            entity,
            name=name,
        )

        display_geometry = (
            self.reference_factory.create_plane(
                entity
            )
        )

        command = CreateReferenceCommand(
            scene=self.scene,
            project_panel=self.project_panel,
            project_manager=self.project,
            reference_manager=self.references,
            record=record,
            display_geometry=display_geometry,
            render_options={
                "color": color,
                "opacity": 0.22,
                "show_edges": True,
                "edge_color": color,
                "line_width": 1.5,
                "lighting": False,
                "ambient": 1.0,
                "pickable": True,
            },
            metadata=ProjectObjectMetadata(
                created_by="system",
                creation_method=f"global_plane_{plane_name}",
            ),
        )

        self.history.execute(command)
        self.viewer.render()

        self.statusBar().showMessage(
            f"Criado: {record.name}"
        )

    def start_plane_region_mode(self) -> None:
        """Solicita parâmetros e ativa a captura da região plana."""

        mesh_objects = self.scene.objects_by_type(
            "mesh"
        )

        if not mesh_objects:
            QMessageBox.information(
                self,
                "Nenhuma malha disponível",
                (
                    "Importe uma malha antes de reconhecer "
                    "uma região plana."
                ),
            )
            return

        default_radius = max(
            self._reference_scale() * 0.05,
            1.0,
        )

        dialog = PlaneRegionDialog(
            default_radius=default_radius,
            parent=self,
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self._pending_plane_radius = (
            dialog.region_radius()
        )
        self._pending_plane_minimum_points = (
            dialog.minimum_points()
        )
        self._pending_plane_maximum_angle = (
            dialog.maximum_angle()
        )
        self._pending_plane_scale = (
            dialog.plane_scale()
        )

        if self.delete_mode_active:
            self.cancel_delete_mode()

        self.disable_selection_mode()

        try:
            self.viewer.disable_picking()
        except Exception:
            pass

        self.viewer.enable_surface_point_picking(
            callback=self.on_plane_region_picked,
            show_message=False,
            show_point=True,
            point_size=14,
            color="#ffd166",
            left_clicking=True,
            pickable_window=False,
            clear_on_no_selection=False,
            picker="cell",
        )

        self.statusBar().showMessage(
            "Clique no centro aproximado da região plana"
        )


    def on_plane_region_picked(
        self,
        point: Any,
    ) -> None:
        """Expande, mostra e confirma uma região plana."""

        if point is None or len(point) < 3:
            self.statusBar().showMessage(
                "Nenhum ponto válido foi identificado"
            )
            return

        picked_point = (
            float(point[0]),
            float(point[1]),
            float(point[2]),
        )

        try:
            self.viewer.disable_picking()
        except Exception:
            pass

        source_object = self._nearest_mesh_object(
            picked_point
        )

        if source_object is None:
            QMessageBox.warning(
                self,
                "Região não encontrada",
                (
                    "Não foi possível localizar uma malha "
                    "próxima ao ponto clicado."
                ),
            )
            return

        try:
            region_result = grow_planar_region(
                mesh=source_object.data,
                seed_point=picked_point,
                radius=self._pending_plane_radius,
                maximum_angle_degrees=(
                    self._pending_plane_maximum_angle
                ),
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro na expansão da região",
                str(error),
            )
            return

        if (
            region_result.point_count
            < self._pending_plane_minimum_points
        ):
            QMessageBox.warning(
                self,
                "Poucos pontos na região",
                (
                    f"A expansão encontrou "
                    f"{region_result.point_count} pontos, "
                    "mas o mínimo configurado é "
                    f"{self._pending_plane_minimum_points}.\n\n"
                    "Aumente o raio ou o limite angular."
                ),
            )
            return

        try:
            fit_result = fit_plane_to_points(
                region_result.points
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro no ajuste do plano",
                str(error),
            )
            return

        normal = self._orient_normal_to_camera(
            fit_result.origin,
            fit_result.normal,
        )

        plane_size = max(
            self._pending_plane_radius
            * self._pending_plane_scale,
            1.0,
        )

        preview_entity = PlaneReference(
            origin=fit_result.origin,
            normal=normal,
            size_x=plane_size,
            size_y=plane_size,
        )

        region_geometry = (
            source_object.data.extract_cells(
                list(region_result.cell_ids)
            )
        )

        self._show_plane_region_preview(
            region_geometry=region_geometry,
            plane_entity=preview_entity,
        )

        preview_dialog = PlanePreviewDialog(
            triangle_count=(
                region_result.triangle_count
            ),
            point_count=region_result.point_count,
            rms_error=fit_result.rms_error,
            maximum_error=(
                fit_result.maximum_error
            ),
            normal=normal,
            parent=self,
        )

        accepted = (
            preview_dialog.exec()
            == QDialog.DialogCode.Accepted
        )

        self._clear_plane_region_preview()

        if not accepted:
            self.statusBar().showMessage(
                "Criação do plano cancelada"
            )
            return

        record = self.references.create_record(
            preview_entity
        )

        display_geometry = (
            self.reference_factory.create_plane(
                preview_entity
            )
        )

        command = CreateReferenceCommand(
            scene=self.scene,
            project_panel=self.project_panel,
            project_manager=self.project,
            reference_manager=self.references,
            record=record,
            display_geometry=display_geometry,
            render_options={
                "color": "#ffd166",
                "opacity": 0.28,
                "show_edges": True,
                "edge_color": "#ffe29a",
                "line_width": 1.5,
                "lighting": False,
                "ambient": 1.0,
                "pickable": True,
            },
            metadata=ProjectObjectMetadata(
                source_object_id=(
                    source_object.object_id
                ),
                created_by="user",
                creation_method=(
                    "plane_fit_connected_region"
                ),
                rms_error=fit_result.rms_error,
                custom={
                    "maximum_error": (
                        fit_result.maximum_error
                    ),
                    "point_count": (
                        fit_result.point_count
                    ),
                    "triangle_count": (
                        region_result.triangle_count
                    ),
                    "region_radius": (
                        self._pending_plane_radius
                    ),
                    "maximum_angle_degrees": (
                        self._pending_plane_maximum_angle
                    ),
                    "source_cell_ids": list(
                        region_result.cell_ids
                    ),
                },
            ),
        )

        self.history.execute(command)
        self.viewer.render()

        self.statusBar().showMessage(
            f"Criado: {record.name} | "
            f"{region_result.triangle_count} triângulos | "
            f"RMS {fit_result.rms_error:.4f} mm"
        )

    def _nearest_mesh_object(
        self,
        point: tuple[float, float, float],
    ) -> Any | None:
        """Localiza a malha visível mais próxima do clique."""

        import numpy as np

        target = np.asarray(
            point,
            dtype=float,
        )

        best_object = None
        best_distance = float("inf")

        for scene_object in self.scene.objects_by_type(
            "mesh"
        ):
            if not scene_object.visible:
                continue

            try:
                closest_point_id = int(
                    scene_object.data.find_closest_point(
                        target
                    )
                )

                closest_point = np.asarray(
                    scene_object.data.points[
                        closest_point_id
                    ],
                    dtype=float,
                )
            except Exception:
                continue

            distance = float(
                np.linalg.norm(
                    closest_point - target
                )
            )

            if distance < best_distance:
                best_distance = distance
                best_object = scene_object

        maximum_distance = max(
            self._pending_plane_radius * 0.25,
            0.5,
        )

        if best_distance > maximum_distance:
            return None

        return best_object

    def _show_plane_region_preview(
        self,
        region_geometry: Any,
        plane_entity: PlaneReference,
    ) -> None:
        """Mostra os triângulos usados e o plano provisório."""

        self._clear_plane_region_preview(
            render=False
        )

        region_actor = self.viewer.add_mesh(
            region_geometry,
            name=self._plane_region_preview_name,
            color="#ffd166",
            opacity=0.78,
            show_edges=True,
            edge_color="#fff0b3",
            line_width=1.0,
            lighting=False,
        )

        try:
            region_actor.SetPickable(False)
        except Exception:
            pass

        plane_geometry = (
            self.reference_factory.create_plane(
                plane_entity
            )
        )

        plane_actor = self.viewer.add_mesh(
            plane_geometry,
            name=self._plane_preview_name,
            color="#4ecdc4",
            opacity=0.32,
            show_edges=True,
            edge_color="#9ff3ed",
            line_width=2.0,
            lighting=False,
        )

        try:
            plane_actor.SetPickable(False)
        except Exception:
            pass

        self.viewer.render()

    def _clear_plane_region_preview(
        self,
        render: bool = True,
    ) -> None:
        """Remove todos os elementos temporários do reconhecimento."""

        for actor_name in (
            self._plane_region_preview_name,
            self._plane_preview_name,
        ):
            try:
                self.viewer.remove_actor(
                    actor_name,
                    render=False,
                )
            except Exception:
                pass

        if render:
            self.viewer.render()
    def _orient_normal_to_camera(
        self,
        origin: tuple[float, float, float],
        normal: tuple[float, float, float],
    ) -> tuple[float, float, float]:
        """Orienta a normal para o lado da câmera."""

        camera_position = (
            self.viewer.camera.position
        )

        to_camera = (
            float(camera_position[0]) - origin[0],
            float(camera_position[1]) - origin[1],
            float(camera_position[2]) - origin[2],
        )

        dot_product = (
            to_camera[0] * normal[0]
            + to_camera[1] * normal[1]
            + to_camera[2] * normal[2]
        )

        if dot_product >= 0.0:
            return normal

        return (
            -normal[0],
            -normal[1],
            -normal[2],
        )


    def start_cylinder_region_mode(self) -> None:
        """Ativa o reconhecimento de cilindro por região."""

        if not self.scene.objects_by_type("mesh"):
            QMessageBox.information(
                self,
                "Nenhuma malha disponível",
                (
                    "Importe uma malha antes de reconhecer "
                    "uma região cilíndrica."
                ),
            )
            return

        dialog = CylinderRegionDialog(
            default_radius=max(
                self._reference_scale() * 0.08,
                2.0,
            ),
            parent=self,
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self._pending_cylinder_radius = (
            dialog.region_radius()
        )
        self._pending_cylinder_angle = (
            dialog.maximum_neighbor_angle()
        )
        self._pending_cylinder_minimum_points = (
            dialog.minimum_points()
        )

        if self.delete_mode_active:
            self.cancel_delete_mode()

        self.disable_selection_mode()

        try:
            self.viewer.disable_picking()
        except Exception:
            pass

        self.viewer.enable_surface_point_picking(
            callback=self.on_cylinder_region_picked,
            show_message=False,
            show_point=True,
            point_size=14,
            color="#70e000",
            left_clicking=True,
            pickable_window=False,
            clear_on_no_selection=False,
            picker="cell",
        )

        self.statusBar().showMessage(
            "Clique no centro aproximado da região cilíndrica"
        )


    def _cylinder_confidence(
        self,
        *,
        radius: float,
        rms_error: float,
        coverage_angle: float,
        point_count: int,
    ) -> float:
        """Calcula uma confiança orientativa entre 0 e 100%."""

        relative_error = rms_error / max(radius, 1.0e-9)
        error_score = max(0.0, min(1.0, 1.0 - relative_error / 0.05))
        coverage_score = max(0.0, min(1.0, coverage_angle / 270.0))
        point_score = max(0.0, min(1.0, point_count / 500.0))

        return (
            error_score * 0.55
            + coverage_score * 0.30
            + point_score * 0.15
        ) * 100.0

    def on_cylinder_region_picked(
        self,
        point: Any,
    ) -> None:
        """Expande, refina e abre uma prévia navegável."""

        if point is None or len(point) < 3:
            return

        picked_point = (
            float(point[0]),
            float(point[1]),
            float(point[2]),
        )

        try:
            self.viewer.disable_picking()
        except Exception:
            pass

        source_object = self._nearest_mesh_object(
            picked_point
        )

        if source_object is None:
            QMessageBox.warning(
                self,
                "Região não encontrada",
                "Não foi possível localizar a malha clicada.",
            )
            return

        try:
            candidate_region, candidate_normals = (
                grow_cylindrical_region(
                    mesh=source_object.data,
                    seed_point=picked_point,
                    radius=self._pending_cylinder_radius,
                    maximum_neighbor_angle_degrees=(
                        self._pending_cylinder_angle
                    ),
                )
            )

            preliminary_fit = fit_cylinder_to_points(
                candidate_region.points,
                candidate_normals,
            )

            refined_region, refined_normals = (
                refine_cylindrical_cells(
                    mesh=source_object.data,
                    candidate_cell_ids=(
                        candidate_region.cell_ids
                    ),
                    seed_cell_id=(
                        candidate_region.seed_cell_id
                    ),
                    cylinder_center=(
                        preliminary_fit.center
                    ),
                    axis_direction=(
                        preliminary_fit.axis_direction
                    ),
                    radius=preliminary_fit.radius,
                    radial_tolerance=max(
                        preliminary_fit.radial_tolerance,
                        preliminary_fit.radius * 0.04,
                        0.05,
                    ),
                )
            )

            fit_result = fit_cylinder_to_points(
                refined_region.points,
                refined_normals,
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro no reconhecimento do cilindro",
                str(error),
            )
            return

        if (
            refined_region.point_count
            < self._pending_cylinder_minimum_points
        ):
            QMessageBox.warning(
                self,
                "Poucos pontos após o refinamento",
                (
                    f"A região final possui "
                    f"{refined_region.point_count} pontos, "
                    "mas o mínimo configurado é "
                    f"{self._pending_cylinder_minimum_points}.\n\n"
                    "Aumente o raio da expansão ou reduza "
                    "o mínimo de pontos."
                ),
            )
            return

        cylinder_entity = CylinderReference(
            center=fit_result.center,
            axis_direction=(
                fit_result.axis_direction
            ),
            radius=fit_result.radius,
            length=fit_result.length,
            rms_error=fit_result.rms_error,
            coverage_angle=(
                fit_result.coverage_angle
            ),
            source_object_id=(
                source_object.object_id
            ),
        )

        axis_entity = cylinder_entity.create_axis(
            display_extension=0.20
        )

        center_entity = (
            cylinder_entity.create_center_point()
        )

        region_geometry = (
            source_object.data.extract_cells(
                list(
                    refined_region.cell_ids
                )
            )
        )

        self._show_cylinder_preview(
            region_geometry=region_geometry,
            cylinder_entity=cylinder_entity,
            axis_entity=axis_entity,
        )

        confidence = self._cylinder_confidence(
            radius=cylinder_entity.radius,
            rms_error=fit_result.rms_error,
            coverage_angle=fit_result.coverage_angle,
            point_count=fit_result.point_count,
        )

        self._pending_cylinder_creation = {
            "source_object": source_object,
            "region_result": refined_region,
            "fit_result": fit_result,
            "cylinder_entity": cylinder_entity,
            "axis_entity": axis_entity,
            "center_entity": center_entity,
            "confidence": confidence,
        }

        dialog = CylinderPreviewDialog(
            triangle_count=(
                refined_region.triangle_count
            ),
            point_count=(
                fit_result.point_count
            ),
            diameter=cylinder_entity.diameter,
            length=cylinder_entity.length,
            rms_error=fit_result.rms_error,
            maximum_error=(
                fit_result.maximum_error
            ),
            coverage_angle=(
                fit_result.coverage_angle
            ),
            axis_direction=(
                fit_result.axis_direction
            ),
            confidence=confidence,
            parent=self,
        )

        self._cylinder_preview_dialog = dialog

        dialog.diameter_changed.connect(
            self.update_cylinder_diameter_preview
        )
        dialog.accepted.connect(
            self.confirm_cylinder_preview
        )
        dialog.rejected.connect(
            self.cancel_cylinder_preview
        )
        dialog.finished.connect(
            self._release_cylinder_preview_dialog
        )

        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

        self.statusBar().showMessage(
            "Prévia cilíndrica ativa — use a viewport "
            "para girar, mover e aplicar zoom"
        )


    def update_cylinder_diameter_preview(self, diameter: float) -> None:
        """Atualiza ao vivo o diâmetro nominal da prévia."""
        pending=self._pending_cylinder_creation
        if pending is None or diameter<=0.0:
            return
        original=pending["cylinder_entity"]
        preview_entity=CylinderReference(
            center=original.center,
            axis_direction=original.axis_direction,
            radius=diameter/2.0,
            length=original.length,
            rms_error=original.rms_error,
            coverage_angle=original.coverage_angle,
            source_object_id=original.source_object_id,
        )
        try:
            self.viewer.remove_actor(self._cylinder_preview_name, render=False)
        except Exception:
            pass
        actor=self.viewer.add_mesh(
            self.reference_factory.create_cylinder(preview_entity),
            name=self._cylinder_preview_name,
            color="#70e000", opacity=0.30,
            show_edges=True, edge_color="#b7ff8a",
            line_width=1.5, lighting=False,
        )
        try:
            actor.SetPickable(False)
        except Exception:
            pass
        self.viewer.render()

    def confirm_cylinder_preview(self) -> None:
        """Confirma a criação do cilindro e derivados."""

        pending = self._pending_cylinder_creation
        dialog = self._cylinder_preview_dialog

        if pending is None or dialog is None:
            self._clear_cylinder_preview()
            return

        source_object = pending[
            "source_object"
        ]
        region_result = pending[
            "region_result"
        ]
        fit_result = pending[
            "fit_result"
        ]
        cylinder_entity = pending[
            "cylinder_entity"
        ]
        axis_entity = pending[
            "axis_entity"
        ]
        center_entity = pending[
            "center_entity"
        ]

        create_axis = dialog.create_axis()
        create_center = (
            dialog.create_center_point()
        )
        final_diameter = dialog.final_diameter()
        detected_diameter = dialog.detected_diameter()
        length_mode = dialog.length_mode()
        extension_factor = dialog.extension_factor()

        self._clear_cylinder_preview()

        final_length = cylinder_entity.length
        if length_mode == CylinderPreviewDialog.LENGTH_EXTENDED:
            final_length = cylinder_entity.length * extension_factor

        final_cylinder_entity = CylinderReference(
            center=cylinder_entity.center,
            axis_direction=cylinder_entity.axis_direction,
            radius=final_diameter / 2.0,
            length=final_length,
            rms_error=cylinder_entity.rms_error,
            coverage_angle=cylinder_entity.coverage_angle,
            source_object_id=cylinder_entity.source_object_id,
        )

        final_axis_entity = final_cylinder_entity.create_axis(
            display_extension=0.20
        )

        cylinder_record = (
            self.references.create_record(
                final_cylinder_entity
            )
        )

        commands = [
            CreateReferenceCommand(
                scene=self.scene,
                project_panel=self.project_panel,
                project_manager=self.project,
                reference_manager=self.references,
                record=cylinder_record,
                display_geometry=(
                    self.reference_factory.create_cylinder(
                        final_cylinder_entity
                    )
                ),
                render_options={
                    "color": "#70e000",
                    "opacity": 0.30,
                    "show_edges": True,
                    "edge_color": "#b7ff8a",
                    "line_width": 1.0,
                    "lighting": False,
                    "ambient": 1.0,
                    "pickable": True,
                },
                metadata=ProjectObjectMetadata(
                    source_object_id=(
                        source_object.object_id
                    ),
                    created_by="user",
                    creation_method=(
                        "cylinder_fit_refined_region"
                    ),
                    rms_error=fit_result.rms_error,
                    custom={
                        "maximum_error": (
                            fit_result.maximum_error
                        ),
                        "point_count": (
                            fit_result.point_count
                        ),
                        "triangle_count": (
                            region_result.triangle_count
                        ),
                        "coverage_angle": (
                            fit_result.coverage_angle
                        ),
                        "confidence": pending[
                            "confidence"
                        ],
                        "detected_diameter": detected_diameter,
                        "nominal_diameter": final_diameter,
                        "diameter_adjustment": (
                            final_diameter - detected_diameter
                        ),
                        "length_mode": length_mode,
                        "extension_factor": (
                            extension_factor
                            if length_mode
                            == CylinderPreviewDialog.LENGTH_EXTENDED
                            else 1.0
                        ),
                        "radial_tolerance": (
                            fit_result.radial_tolerance
                        ),
                        "source_cell_ids": list(
                            region_result.cell_ids
                        ),
                    },
                ),
            )
        ]

        if create_axis:
            axis_record = (
                self.references.create_record(
                    final_axis_entity,
                    name=(
                        f"Eixo de "
                        f"{cylinder_record.name}"
                    ),
                )
            )

            commands.append(
                CreateReferenceCommand(
                    scene=self.scene,
                    project_panel=self.project_panel,
                    project_manager=self.project,
                    reference_manager=self.references,
                    record=axis_record,
                    display_geometry=(
                        self.reference_factory.create_axis(
                            final_axis_entity
                        )
                    ),
                    render_options={
                        "color": "#4ea1ff",
                        "lighting": False,
                        "ambient": 1.0,
                        "pickable": True,
                    },
                    metadata=ProjectObjectMetadata(
                        source_object_id=(
                            cylinder_record.object_id
                        ),
                        created_by="system",
                        creation_method=(
                            "axis_from_cylinder"
                        ),
                    ),
                )
            )

        if create_center:
            center_record = (
                self.references.create_record(
                    center_entity,
                    name=(
                        f"Centro de "
                        f"{cylinder_record.name}"
                    ),
                )
            )

            commands.append(
                CreateReferenceCommand(
                    scene=self.scene,
                    project_panel=self.project_panel,
                    project_manager=self.project,
                    reference_manager=self.references,
                    record=center_record,
                    display_geometry=(
                        self.reference_factory.create_point(
                            center_entity,
                            radius=max(
                                self._reference_scale()
                                * 0.006,
                                0.35,
                            ),
                        )
                    ),
                    render_options={
                        "color": "#ff7a45",
                        "smooth_shading": True,
                        "ambient": 0.7,
                        "diffuse": 0.3,
                        "pickable": True,
                    },
                    metadata=ProjectObjectMetadata(
                        source_object_id=(
                            cylinder_record.object_id
                        ),
                        created_by="system",
                        creation_method=(
                            "center_from_cylinder"
                        ),
                    ),
                )
            )

        batch = CreateReferenceBatchCommand(
            description=(
                f"Criar "
                f"{cylinder_record.name} "
                "e referências derivadas"
            ),
            commands=commands,
        )

        self.history.execute(batch)
        self.viewer.render()

        self._pending_cylinder_creation = None

        self.statusBar().showMessage(
            f"Criado: "
            f"{cylinder_record.name} | "
            f"Ø {final_cylinder_entity.diameter:.4f} mm | "
            f"RMS {fit_result.rms_error:.4f} mm"
        )

    def cancel_cylinder_preview(self) -> None:
        """Cancela a prévia sem criar referências."""

        self._clear_cylinder_preview()
        self._pending_cylinder_creation = None

        self.statusBar().showMessage(
            "Criação do cilindro cancelada"
        )

    def _release_cylinder_preview_dialog(
        self,
        _result: int,
    ) -> None:
        """Libera a referência da janela de prévia."""

        self._cylinder_preview_dialog = None

    def _show_cylinder_preview(
        self,
        region_geometry: Any,
        cylinder_entity: CylinderReference,
        axis_entity: AxisReference,
    ) -> None:
        """Mostra região, cilindro e eixo provisórios."""

        self._clear_cylinder_preview(
            render=False
        )

        actors = (
            self.viewer.add_mesh(
                region_geometry,
                name=self._cylinder_region_preview_name,
                color="#ffd166",
                opacity=0.80,
                show_edges=True,
                edge_color="#fff0b3",
                line_width=1.0,
                lighting=False,
            ),
            self.viewer.add_mesh(
                self.reference_factory.create_cylinder(
                    cylinder_entity
                ),
                name=self._cylinder_preview_name,
                color="#70e000",
                opacity=0.30,
                show_edges=True,
                edge_color="#b7ff8a",
                line_width=1.5,
                lighting=False,
            ),
            self.viewer.add_mesh(
                self.reference_factory.create_axis(
                    axis_entity
                ),
                name=self._cylinder_axis_preview_name,
                color="#4ea1ff",
                lighting=False,
                ambient=1.0,
            ),
        )

        for actor in actors:
            try:
                actor.SetPickable(False)
            except Exception:
                pass

        self.viewer.render()

    def _clear_cylinder_preview(
        self,
        render: bool = True,
    ) -> None:
        """Remove as geometrias provisórias."""

        for actor_name in (
            self._cylinder_region_preview_name,
            self._cylinder_preview_name,
            self._cylinder_axis_preview_name,
        ):
            try:
                self.viewer.remove_actor(
                    actor_name,
                    render=False,
                )
            except Exception:
                pass

        if render:
            self.viewer.render()

    def open_stl(self) -> None:
        """Importa um STL pelo histórico."""

        if self.delete_mode_active:
            self.cancel_delete_mode()

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir malha STL",
            "",
            "Arquivos STL (*.stl)",
        )

        if not file_path:
            return

        try:
            mesh = load_stl(file_path)

            display_mesh = mesh.compute_normals(
                point_normals=True,
                cell_normals=True,
                consistent_normals=True,
                auto_orient_normals=True,
                feature_angle=35.0,
                inplace=False,
            )

            object_id = self._next_mesh_id()
            file_name = Path(file_path).name

            render_options = {
                "color": "#8796a8",
                "smooth_shading": True,
                "split_sharp_edges": True,
                "show_edges": True,
                "edge_color": "#46515e",
                "edge_opacity": 0.65,
                "line_width": 0.5,
                "ambient": 0.12,
                "diffuse": 0.82,
                "specular": 0.35,
                "specular_power": 35.0,
            }

            command = ImportMeshCommand(
                scene=self.scene,
                project_panel=self.project_panel,
                project_manager=self.project,
                object_id=object_id,
                name=file_name,
                source_file=file_path,
                source_mesh=mesh,
                display_mesh=display_mesh,
                render_options=render_options,
            )

            self.history.execute(command)

            self.edges_action.setChecked(True)
            self.navigation.set_standard_view(
                "isometric"
            )

            self.statusBar().showMessage(
                f"Importado: {file_name}"
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao abrir STL",
                str(error),
            )

    def show_viewport_context_menu(
        self,
        position: QPoint,
    ) -> None:
        """Abre o menu referente ao ponto clicado."""

        pick_result = self.context_picker.pick(
            position
        )

        if pick_result is None:
            self._context_point = None
            self._context_object_id = None

            self.statusBar().showMessage(
                "Nenhuma superfície encontrada sob o cursor"
            )
            return

        scene_object = self.scene.get_object(
            pick_result.object_id
        )

        if scene_object is None:
            return

        self._context_point = pick_result.point
        self._context_object_id = (
            pick_result.object_id
        )

        context_menu = QMenu(self)

        if scene_object.object_type == "mesh":
            pivot_action = QAction(
                "Definir centro de rotação aqui",
                self,
            )
            pivot_action.triggered.connect(
                self.set_context_rotation_center
            )
            context_menu.addAction(pivot_action)

        fit_object_action = QAction(
            "Ajustar vista ao objeto",
            self,
        )
        fit_object_action.triggered.connect(
            self.fit_context_object
        )
        context_menu.addAction(
            fit_object_action
        )

        visibility_text = (
            "Ocultar objeto"
            if scene_object.visible
            else "Mostrar objeto"
        )

        visibility_action = QAction(
            visibility_text,
            self,
        )
        visibility_action.triggered.connect(
            lambda:
            self.set_object_visibility(
                scene_object.object_id,
                not scene_object.visible,
            )
        )

        context_menu.addSeparator()
        context_menu.addAction(
            visibility_action
        )

        context_menu.exec(
            self.viewer.interactor.mapToGlobal(
                position
            )
        )

    def set_context_rotation_center(self) -> None:
        """Usa o ponto clicado como pivô."""

        if self._context_point is None:
            return

        self.disable_selection_mode()
        self.navigation.set_rotation_center(
            self._context_point
        )

        point = self._context_point

        self.statusBar().showMessage(
            "Centro de rotação definido em "
            f"X={point[0]:.2f}, "
            f"Y={point[1]:.2f}, "
            f"Z={point[2]:.2f}"
        )

    def fit_context_object(self) -> None:
        """Enquadra apenas o objeto clicado."""

        if self._context_object_id is None:
            return

        scene_object = self.scene.get_object(
            self._context_object_id
        )

        if scene_object is None:
            return

        try:
            self.viewer.reset_camera(
                bounds=scene_object.data.bounds
            )
        except TypeError:
            self.viewer.reset_camera()

        self.viewer.render()

        self.statusBar().showMessage(
            f"Vista ajustada: {scene_object.name}"
        )

    def set_standard_view(
        self,
        view_name: str,
    ) -> None:
        """Aplica uma vista técnica."""

        if self.scene.object_count() == 0:
            self.statusBar().showMessage(
                "Nenhum objeto disponível"
            )
            return

        changed = (
            self.navigation.set_standard_view(
                view_name
            )
        )

        if not changed:
            return

        view_names = {
            "isometric": "Isométrica",
            "front": "Frontal",
            "back": "Traseira",
            "top": "Superior (Z+)",
            "bottom": "Inferior (Z-)",
            "left": "Esquerda",
            "right": "Direita",
        }

        self.statusBar().showMessage(
            f"Vista: {view_names.get(view_name, view_name)}"
        )

    def rotate_view_90(
        self,
        clockwise: bool,
    ) -> None:
        """Gira a câmera 90 graus."""

        if self.scene.object_count() == 0:
            self.statusBar().showMessage(
                "Nenhum objeto disponível"
            )
            return

        self.navigation.rotate_view_90(
            clockwise=clockwise
        )

        direction = (
            "horário"
            if clockwise
            else "anti-horário"
        )

        self.statusBar().showMessage(
            f"Vista rotacionada 90° {direction}"
        )

    def restore_global_rotation_center(self) -> None:
        """Restaura o centro global."""

        restored = (
            self.navigation.restore_global_center()
        )

        if not restored:
            self.statusBar().showMessage(
                "Nenhum objeto disponível"
            )
            return

        self.statusBar().showMessage(
            "Centro de rotação global restaurado"
        )

    def undo(self) -> None:
        """Desfaz a operação mais recente."""

        self._prepare_history_operation()

        description = (
            self.history.undo_description()
        )

        if not self.history.undo():
            self.statusBar().showMessage(
                "Não há operações para desfazer"
            )
            return

        self.viewer.show_axes()
        self.viewer.render()

        self.statusBar().showMessage(
            f"Desfeito: {description}"
        )

    def redo(self) -> None:
        """Refaz a operação mais recente."""

        self._prepare_history_operation()

        description = (
            self.history.redo_description()
        )

        if not self.history.redo():
            self.statusBar().showMessage(
                "Não há operações para refazer"
            )
            return

        self.viewer.show_axes()
        self.viewer.render()

        self.statusBar().showMessage(
            f"Refeito: {description}"
        )

    def _prepare_history_operation(self) -> None:
        """Prepara a interface para undo ou redo."""

        if self.delete_mode_active:
            self.cancel_delete_mode()

        self.selection.clear()

    def update_history_actions(self) -> None:
        """Atualiza os botões do histórico."""

        self.undo_action.setEnabled(
            self.history.can_undo()
        )
        self.redo_action.setEnabled(
            self.history.can_redo()
        )

        undo_description = (
            self.history.undo_description()
        )
        redo_description = (
            self.history.redo_description()
        )

        self.undo_action.setText(
            (
                f"Desfazer: {undo_description}"
                if undo_description
                else "Desfazer"
            )
        )

        self.redo_action.setText(
            (
                f"Refazer: {redo_description}"
                if redo_description
                else "Refazer"
            )
        )

    def set_selection_mode(
        self,
        active: bool,
    ) -> None:
        """Ativa ou desativa seleção."""

        if active:
            if self.scene.object_count() == 0:
                self.select_action.blockSignals(True)
                self.select_action.setChecked(False)
                self.select_action.blockSignals(False)

                self.statusBar().showMessage(
                    "Nenhum objeto disponível"
                )
                return

            self.selection.activate()
            self.enable_viewport_selection()

            self.statusBar().showMessage(
                "Seleção de objetos ativa"
            )
            return

        self.disable_viewport_selection()

        if not self.delete_mode_active:
            self.selection.deactivate(
                clear_selection=True
            )

    def disable_selection_mode(self) -> None:
        """Desativa seleção e limpa destaques."""

        self.disable_viewport_selection()
        self.selection.deactivate(
            clear_selection=True
        )

        self.select_action.blockSignals(True)
        self.select_action.setChecked(False)
        self.select_action.blockSignals(False)

    def enable_viewport_selection(self) -> None:
        """Ativa seleção pela viewport."""

        try:
            self.viewer.disable_picking()
        except Exception:
            pass

        self.viewer.enable_mesh_picking(
            callback=self.on_viewport_actor_picked,
            show=False,
            show_message=False,
            left_clicking=True,
            use_actor=True,
        )

    def disable_viewport_selection(self) -> None:
        """Desativa picking."""

        try:
            self.viewer.disable_picking()
        except Exception:
            pass

    def on_viewport_actor_picked(
        self,
        actor: Any,
    ) -> None:
        """Alterna seleção do objeto clicado."""

        if not self.selection.active:
            return

        self.selection.toggle_actor(actor)

    def on_selection_changed(
        self,
        selected_ids: set[str],
    ) -> None:
        """Recebe mudanças na seleção."""

        if self.delete_dialog is not None:
            self.delete_dialog.set_selected_objects(
                self.selection.selected_names()
            )

        count_selected = len(selected_ids)

        if count_selected == 0:
            message = "Nenhum objeto selecionado"
        elif count_selected == 1:
            message = "1 objeto selecionado"
        else:
            message = (
                f"{count_selected} objetos selecionados"
            )

        if self.delete_mode_active:
            message = f"Modo Deletar — {message}"

        self.statusBar().showMessage(message)

    def start_delete_mode(self) -> None:
        """Abre o modo de exclusão."""

        if self.scene.object_count() == 0:
            QMessageBox.information(
                self,
                "Nenhum objeto disponível",
                "Não existem objetos para excluir.",
            )
            return

        if self.delete_mode_active:
            if self.delete_dialog is not None:
                self.delete_dialog.raise_()
            return

        self.delete_mode_active = True

        self.selection.activate()
        self.enable_viewport_selection()

        self.select_action.blockSignals(True)
        self.select_action.setChecked(True)
        self.select_action.blockSignals(False)

        self.delete_dialog = DeleteDialog(self)

        self.delete_dialog.delete_requested.connect(
            self.confirm_delete_selected
        )
        self.delete_dialog.cancel_requested.connect(
            self.cancel_delete_mode
        )

        self.delete_dialog.set_selected_objects(
            self.selection.selected_names()
        )

        self.delete_dialog.show()
        self.delete_dialog.raise_()

    def confirm_delete_selected(self) -> None:
        """Confirma a exclusão."""

        selected_ids = self.selection.selected_ids()

        if not selected_ids:
            QMessageBox.information(
                self,
                "Nenhum objeto selecionado",
                "Selecione pelo menos um objeto.",
            )
            return

        names_text = "\n".join(
            f"• {name}"
            for name in self.selection.selected_names()
        )

        answer = QMessageBox.question(
            self,
            "Confirmar exclusão",
            (
                "Deseja realmente excluir os "
                "objetos selecionados?\n\n"
                f"{names_text}"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        command = DeleteObjectsCommand(
            scene=self.scene,
            project_panel=self.project_panel,
            project_manager=self.project,
            reference_manager=self.references,
            object_ids=selected_ids,
        )

        self.history.execute(command)

        dialog = self.delete_dialog
        self.delete_dialog = None

        if dialog is not None:
            dialog.complete_and_close()

        self.finish_delete_mode()

        self.statusBar().showMessage(
            f"{len(selected_ids)} objeto(s) excluído(s)"
        )

    def cancel_delete_mode(self) -> None:
        """Cancela o modo Deletar."""

        if not self.delete_mode_active:
            return

        dialog = self.delete_dialog
        self.delete_dialog = None

        if (
            dialog is not None
            and dialog.isVisible()
        ):
            dialog.complete_and_close()

        self.finish_delete_mode()

        self.statusBar().showMessage(
            "Exclusão cancelada"
        )

    def finish_delete_mode(self) -> None:
        """Finaliza o modo Deletar."""

        self.delete_mode_active = False

        self.disable_viewport_selection()
        self.selection.deactivate(
            clear_selection=True
        )

        self.select_action.blockSignals(True)
        self.select_action.setChecked(False)
        self.select_action.blockSignals(False)

        self.viewer.render()

    def set_object_visibility(
        self,
        object_id: str,
        visible: bool,
    ) -> None:
        """Altera visibilidade pelo histórico."""

        scene_object = self.scene.get_object(
            object_id
        )

        if scene_object is None:
            return

        if scene_object.visible == visible:
            return

        command = SetVisibilityCommand(
            scene=self.scene,
            project_panel=self.project_panel,
            project_manager=self.project,
            object_id=object_id,
            new_visibility=visible,
        )

        self.history.execute(command)

    def set_display_mode(
        self,
        mode: str,
    ) -> None:
        """Aplica um modo visual às malhas."""

        selected_mesh_ids = {
            object_id
            for object_id
            in self.selection.selected_ids()
            if (
                self.scene.get_object(object_id)
                is not None
                and self.scene.get_object(
                    object_id
                ).object_type == "mesh"
            )
        }

        if selected_mesh_ids:
            changed_count = 0

            for object_id in selected_mesh_ids:
                if self.scene.set_display_mode(
                    object_id,
                    mode,
                    render=False,
                ):
                    changed_count += 1

            if changed_count:
                self.viewer.render()
        else:
            changed_count = (
                self.scene.set_display_mode_by_type(
                    "mesh",
                    mode,
                )
            )

        if changed_count == 0:
            self.statusBar().showMessage(
                "Nenhuma malha disponível"
            )
            return

        mode_names = {
            "solid": "Sólido",
            "edges": "Sólido + Arestas",
            "wireframe": "Wireframe",
            "transparent": "Transparente",
        }

        self.statusBar().showMessage(
            f"Modo {mode_names.get(mode, mode)} "
            f"aplicado a {changed_count} malha(s)"
        )

    def fit_view(self) -> None:
        """Enquadra todos os objetos."""

        if self.scene.object_count() == 0:
            self.statusBar().showMessage(
                "Nenhum objeto carregado"
            )
            return

        self.navigation.remove_pivot_marker(
            render=False
        )

        self.viewer.reset_camera()
        self.viewer.render()

        self.statusBar().showMessage(
            "Todos os objetos foram enquadrados"
        )

    def closeEvent(
        self,
        event: QCloseEvent,
    ) -> None:
        """Finaliza o Genesis."""

        self.disable_viewport_selection()

        self.scene.clear()
        self.project.clear()
        self.references.clear()
        self.viewer.close()

        event.accept()
