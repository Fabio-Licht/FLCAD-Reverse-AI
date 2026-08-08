from __future__ import annotations

from itertools import count
from types import SimpleNamespace
from math import isfinite, sqrt
from pathlib import Path
from typing import Any

from PySide6.QtCore import QEvent, QPoint, Qt
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
import vtk

from core.command_history import CommandManager
from core.command_preset_store import CommandPresetStore
from core.project_commands import (
    CompositeProjectCommand,
    CreateReferenceBatchCommand,
    CreateReferenceCommand,
    DeleteObjectsCommand,
    ImportMeshCommand,
    SetVisibilityCommand,
    TransformSceneObjectsCommand,
)
from core.project_manager import ProjectManager
from core.project_model import ProjectObjectMetadata
from geometry.reference_entities import (
    AxisReference,
    CylinderReference,
    PlaneReference,
    PointReference,
)
from geometry.alignment_engine import (
    pivot_rotation_transform,
    plane_to_global_transform,
    target_axis,
)
from geometry.cylinder_fit import fit_cylinder_to_points
from geometry.cylinder_quality import (
    CylinderQualityResult,
    evaluate_cylinder_quality,
)
from geometry.mesh_region import (
    grow_cylindrical_region,
    merge_cylindrical_seed_regions,
    refine_cylindrical_cells_multi_seed,
    grow_planar_region,
    refine_cylindrical_cells,
)
from geometry.pattern_engine import (
    PatternInstance,
    create_circular_pattern,
    create_linear_pattern,
)
from geometry.plane_fit import fit_plane_to_points
from geometry.plane_quality import evaluate_plane_quality
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
from visualization.engine.reference_display import (
    create_cylinder_reference_lines,
)
from visualization.engine.reference_factory import (
    ReferenceGeometryFactory,
)
from visualization.engine.scene import SceneManager
from visualization.engine.selection_manager import (
    SelectionManager,
)
from application.visualization.recognition.recognition_visualization_service import (
    RecognitionVisualizationService,
)
from application.interaction.context_menu_service import ContextMenuService
from application.interaction.inspection_service import InspectionService
from application.interaction.interaction_controller import InteractionController
from application.interaction.interaction_settings import InteractionSettings
from application.interaction.property_service import PropertyService
from application.interaction.selection_service import (
    SelectionService as EngineeringSelectionService,
)
from application.recognition.recognition_session import RecognitionSession
from domain.reference.managers.reference_manager import (
    ReferenceManager as EngineeringReferenceManager,
)


class MainWindow(QMainWindow):
    """Janela principal do FLCAD Reverse AI."""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(
            "FLCAD Reverse AI — v0.7.4 Genesis"
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
        self._plane_region_dialog = None
        self._pending_plane_seed_point: tuple[
            float,
            float,
            float,
        ] | None = None
        self._pending_plane_source_object_id: str | None = None
        self._pending_plane_creation = None

        self._plane_region_preview_name = (
            "__flcad_plane_region_preview__"
        )
        self._plane_preview_name = (
            "__flcad_plane_preview__"
        )
        self._plane_center_preview_name = (
            "__flcad_plane_center_preview__"
        )
        self._plane_normal_preview_name = (
            "__flcad_plane_normal_preview__"
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
        self._cylinder_center_preview_name = (
            "__flcad_cylinder_center_preview__"
        )
        self._cylinder_pattern_preview_names: list[str] = []
        self._active_cylinder_region_preview_name: str | None = None
        self._active_cylinder_preview_name: str | None = None
        self._active_cylinder_axis_preview_name: str | None = None
        self._active_cylinder_center_preview_name: str | None = None

        self._cylinder_preview_dialog = None
        self._cylinder_region_dialog = None
        self._pending_cylinder_creation = None
        self._editing_object_ids: set[str] = set()
        self._pending_cylinder_seed_count = 1
        self._pending_cylinder_seed_points: list[
            tuple[float, float, float]
        ] = []
        self._pending_cylinder_source_object_id: str | None = None
        self._cylinder_recognition_history: list[
            dict[str, Any]
        ] = []
        self._cylinder_production_mode = False
        self._cylinder_batch_queue: list[
            dict[str, Any]
        ] = []

        # Seleção protegida: Ctrl + clique curto.
        self._selection_press_position: tuple[int, int] | None = None
        self._selection_press_control = False
        self._selection_observer_ids: list[int] = []
        self._selection_drag_tolerance_px = 5
        self._selection_event_filter_installed = False

        self.viewer = QtInteractor(self)
        self.setCentralWidget(self.viewer)

        self.scene = SceneManager(self.viewer)
        self.recognition_session = RecognitionSession(
            remove_preview=self._remove_recognition_preview,
            render_previews=self.viewer.render,
        )
        self.recognition_visualization = RecognitionVisualizationService(
            self.scene
        )
        self.engineering_reference_manager = EngineeringReferenceManager()
        self.engineering_interaction_settings = InteractionSettings(
            enable_multi_selection=True,
            enable_context_menu=True,
            enable_hover_highlight=False,
            enable_inspector=True,
        )
        self.engineering_property_service = PropertyService()
        self.engineering_inspection_service = InspectionService(
            self.engineering_property_service
        )
        self.engineering_selection_service = EngineeringSelectionService(
            self.scene,
            self.engineering_interaction_settings,
        )
        self.engineering_context_menu_service = ContextMenuService(
            self.engineering_reference_manager,
            self.recognition_visualization,
        )
        self.engineering_interaction = InteractionController(
            self.engineering_selection_service,
            self.engineering_inspection_service,
            self.engineering_context_menu_service,
            self.engineering_interaction_settings,
        )
        self.recognition_visualization.attach_interaction_controller(
            self.engineering_interaction
        )
        self.engineering_inspection_service.subscribe(
            self._on_engineering_inspection
        )
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
        self.project_panel.object_double_clicked.connect(
            self.edit_project_object
        )

        self.command_presets = CommandPresetStore()

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
            "Selecionar objetos (Ctrl+clique)",
            self,
        )
        self.select_action.setCheckable(True)
        self.select_action.setShortcut("S")
        self.select_action.setToolTip(
            (
                "Ativa a seleção protegida. Use Ctrl + clique "
                "curto para selecionar; arrastar com o botão "
                "esquerdo continua reservado para rotacionar."
            )
        )
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
        self._create_alignment_menu(toolbar)
        self._create_visualization_menu(toolbar)

        settings_menu = QMenu("Configurações", self)
        clear_last_action = QAction(
            "Limpar dados dos últimos comandos",
            self,
        )
        clear_last_action.triggered.connect(
            self.clear_command_presets
        )
        settings_menu.addAction(clear_last_action)

        settings_button = QToolButton(self)
        settings_button.setText("Configurações")
        settings_button.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )
        settings_button.setMenu(settings_menu)
        toolbar.addWidget(settings_button)


    def clear_command_presets(self) -> None:
        """Apaga os parâmetros lembrados sem alterar o projeto."""
        answer = QMessageBox.question(
            self,
            "Limpar dados lembrados",
            "Deseja restaurar os valores padrão de todos os comandos?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.command_presets.clear()
        self.statusBar().showMessage("Dados dos últimos comandos restaurados")

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


    def _create_alignment_menu(
        self,
        toolbar: QToolBar,
    ) -> None:
        """Cria a primeira fundação do sistema de alinhamento."""

        alignment_menu = QMenu(
            "Alinhamento",
            self,
        )

        cylinder_menu = alignment_menu.addMenu(
            "Orientar eixo selecionado"
        )

        for label, axis_name in (
            ("Para X+", "x"),
            ("Para Y+", "y"),
            ("Para Z+", "z"),
            ("Para X−", "x-"),
            ("Para Y−", "y-"),
            ("Para Z−", "z-"),
        ):
            action = QAction(label, self)
            action.triggered.connect(
                lambda checked=False, value=axis_name:
                self.align_selected_axis_to_global(
                    value
                )
            )
            cylinder_menu.addAction(action)

        plane_menu = alignment_menu.addMenu(
            "Alinhar plano selecionado"
        )

        for label, axis_name in (
            ("Assentar em XY — normal Z+", "z"),
            ("Assentar em XY — normal Z−", "z-"),
            ("Assentar em XZ — normal Y+", "y"),
            ("Assentar em XZ — normal Y−", "y-"),
            ("Assentar em YZ — normal X+", "x"),
            ("Assentar em YZ — normal X−", "x-"),
        ):
            action = QAction(label, self)
            action.triggered.connect(
                lambda checked=False, value=axis_name:
                self.align_selected_plane_to_global(
                    value,
                    seat_on_global_plane=True,
                )
            )
            plane_menu.addAction(action)

        orient_only_menu = plane_menu.addMenu(
            "Somente orientar normal"
        )

        for label, axis_name in (
            ("Normal para X+", "x"),
            ("Normal para Y+", "y"),
            ("Normal para Z+", "z"),
            ("Normal para X−", "x-"),
            ("Normal para Y−", "y-"),
            ("Normal para Z−", "z-"),
        ):
            action = QAction(label, self)
            action.triggered.connect(
                lambda checked=False, value=axis_name:
                self.align_selected_plane_to_global(
                    value,
                    seat_on_global_plane=False,
                )
            )
            orient_only_menu.addAction(action)

        alignment_menu.addSeparator()

        help_action = QAction(
            "Como usar o alinhamento",
            self,
        )
        help_action.triggered.connect(
            self.show_alignment_help
        )
        alignment_menu.addAction(
            help_action
        )

        alignment_button = QToolButton(self)
        alignment_button.setText(
            "Alinhamento"
        )
        alignment_button.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )
        alignment_button.setMenu(
            alignment_menu
        )

        toolbar.addWidget(
            alignment_button
        )
        toolbar.addSeparator()

    def show_alignment_help(self) -> None:
        QMessageBox.information(
            self,
            "Alinhamento por eixo",
            (
                "ALINHAMENTO POR EIXO\n"
                "1. Ative Selecionar objetos.\n"
                "2. Selecione uma malha.\n"
                "3. Selecione um cilindro ou eixo.\n"
                "4. Escolha X, Y ou Z.\n\n"
                "ALINHAMENTO POR PLANO\n"
                "1. Selecione uma malha e um plano.\n"
                "2. Escolha XY, XZ ou YZ.\n"
                "3. Escolha o sentido positivo ou negativo da normal.\n\n"
                "Assentar orienta a normal e leva a origem do plano "
                "para o plano global correspondente. Tudo pode ser desfeito."
            ),
        )

    def _alignment_reference_data(
        self,
        object_id: str,
    ) -> tuple[
        tuple[float, float, float],
        tuple[float, float, float],
    ] | None:
        project_object = self.project.get_object(
            object_id
        )

        if project_object is None:
            return None

        data = getattr(
            project_object,
            "data",
            None,
        )

        if isinstance(data, CylinderReference):
            return (
                tuple(data.center),
                tuple(data.axis_direction),
            )

        if isinstance(data, AxisReference):
            return (
                tuple(data.origin),
                tuple(data.direction),
            )

        return None


    def _plane_alignment_reference_data(
        self,
        object_id: str,
    ) -> tuple[
        tuple[float, float, float],
        tuple[float, float, float],
    ] | None:
        """Obtém origem e normal de um plano de referência."""

        project_object = self.project.get_object(
            object_id
        )

        if project_object is None:
            return None

        data = getattr(
            project_object,
            "data",
            None,
        )

        if not isinstance(data, PlaneReference):
            return None

        return (
            tuple(data.origin),
            tuple(data.normal),
        )

    def _alignment_related_objects(
        self,
        mesh_id: str,
        reference_id: str,
    ) -> set[str]:
        """
        Inclui a malha e referências dependentes para que permaneçam
        visualmente coerentes após a rotação.
        """

        related = {
            mesh_id,
            reference_id,
        }
        changed = True

        while changed:
            changed = False

            for object_id in self.scene.object_ids():
                if object_id in related:
                    continue

                project_object = (
                    self.project.get_object(
                        object_id
                    )
                )

                if project_object is None:
                    continue

                metadata = getattr(
                    project_object,
                    "metadata",
                    None,
                )
                source_id = getattr(
                    metadata,
                    "source_object_id",
                    None,
                )

                if source_id in related:
                    related.add(object_id)
                    changed = True

        return related


    def align_selected_plane_to_global(
        self,
        axis_name: str,
        *,
        seat_on_global_plane: bool,
    ) -> None:
        """Alinha uma malha usando um plano reconhecido."""

        selected_ids = set(
            self.selection.selected_ids()
        )

        mesh_ids = [
            object_id
            for object_id in selected_ids
            if (
                self.scene.get_object(object_id)
                is not None
                and self.scene.get_object(
                    object_id
                ).object_type == "mesh"
            )
        ]

        plane_ids = [
            object_id
            for object_id in selected_ids
            if (
                self.scene.get_object(object_id)
                is not None
                and self.scene.get_object(
                    object_id
                ).object_type
                == "reference_plane"
            )
        ]

        if (
            len(mesh_ids) != 1
            or len(plane_ids) != 1
        ):
            QMessageBox.information(
                self,
                "Seleção para alinhamento por plano",
                (
                    "Selecione exatamente:\\n\\n"
                    "• uma malha;\\n"
                    "• um plano de referência.\\n\\n"
                    "Use Ctrl + clique curto na viewport "
                    "ou selecione pela árvore."
                ),
            )
            return

        mesh_id = mesh_ids[0]
        plane_id = plane_ids[0]

        reference_data = (
            self._plane_alignment_reference_data(
                plane_id
            )
        )

        if reference_data is None:
            QMessageBox.warning(
                self,
                "Plano incompatível",
                "O plano selecionado não possui origem e normal válidas.",
            )
            return

        plane_origin, plane_normal = (
            reference_data
        )

        try:
            transform = plane_to_global_transform(
                plane_origin=plane_origin,
                plane_normal=plane_normal,
                target_normal=target_axis(
                    axis_name
                ),
                seat_on_global_plane=(
                    seat_on_global_plane
                ),
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro no alinhamento por plano",
                str(error),
            )
            return

        plane_names = {
            "x": "YZ / X+",
            "x-": "YZ / X−",
            "y": "XZ / Y+",
            "y-": "XZ / Y−",
            "z": "XY / Z+",
            "z-": "XY / Z−",
        }
        target_label = plane_names.get(
            axis_name,
            axis_name.upper(),
        )

        operation_text = (
            "orientar e assentar"
            if seat_on_global_plane
            else "somente orientar"
        )

        answer = QMessageBox.question(
            self,
            "Confirmar alinhamento por plano",
            (
                f"Deseja {operation_text} o plano em {target_label}?\\n\\n"
                "A malha e suas referências dependentes serão "
                "transformadas juntas."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):
            return

        object_ids = (
            self._alignment_related_objects(
                mesh_id,
                plane_id,
            )
        )

        description = (
            f"Alinhar plano em {target_label}"
            if seat_on_global_plane
            else (
                f"Orientar normal do plano para "
                f"{axis_name.upper()}"
            )
        )

        command = TransformSceneObjectsCommand(
            scene=self.scene,
            object_ids=object_ids,
            transform=transform,
            description=description,
        )

        self.history.execute(command)
        self.selection.deactivate(
            clear_selection=True
        )
        self.select_action.blockSignals(True)
        self.select_action.setChecked(False)
        self.select_action.blockSignals(False)

        self.statusBar().showMessage(
            (
                f"Alinhamento por plano aplicado: {target_label} | "
                f"{len(object_ids)} objeto(s) transformado(s)"
            )
        )

    def align_selected_axis_to_global(
        self,
        axis_name: str,
    ) -> None:
        """Orienta uma malha por um cilindro ou eixo selecionado."""

        selected_ids = set(
            self.selection.selected_ids()
        )

        mesh_ids = [
            object_id
            for object_id in selected_ids
            if (
                self.scene.get_object(object_id)
                is not None
                and self.scene.get_object(
                    object_id
                ).object_type == "mesh"
            )
        ]

        reference_ids = [
            object_id
            for object_id in selected_ids
            if (
                self.scene.get_object(object_id)
                is not None
                and self.scene.get_object(
                    object_id
                ).object_type
                in {
                    "reference_cylinder",
                    "reference_axis",
                }
            )
        ]

        if (
            len(mesh_ids) != 1
            or len(reference_ids) != 1
        ):
            QMessageBox.information(
                self,
                "Seleção para alinhamento",
                (
                    "Selecione exatamente:\n\n"
                    "• uma malha;\n"
                    "• um cilindro ou eixo de referência."
                ),
            )
            return

        mesh_id = mesh_ids[0]
        reference_id = reference_ids[0]
        reference_data = (
            self._alignment_reference_data(
                reference_id
            )
        )

        if reference_data is None:
            QMessageBox.warning(
                self,
                "Referência incompatível",
                "A referência selecionada não possui eixo utilizável.",
            )
            return

        pivot, source_direction = (
            reference_data
        )

        try:
            transform = pivot_rotation_transform(
                source_direction=(
                    source_direction
                ),
                target_direction=target_axis(
                    axis_name
                ),
                pivot=pivot,
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro no alinhamento",
                str(error),
            )
            return

        target_label = axis_name.upper()

        answer = QMessageBox.question(
            self,
            "Confirmar alinhamento",
            (
                f"Orientar o eixo selecionado para {target_label}?\n\n"
                "A malha e as referências dependentes serão "
                "rotacionadas ao redor da referência."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):
            return

        object_ids = (
            self._alignment_related_objects(
                mesh_id,
                reference_id,
            )
        )

        command = TransformSceneObjectsCommand(
            scene=self.scene,
            object_ids=object_ids,
            transform=transform,
            description=(
                f"Alinhar eixo para {target_label}"
            ),
        )

        self.history.execute(command)
        self.selection.deactivate(
            clear_selection=True
        )
        self.select_action.blockSignals(True)
        self.select_action.setChecked(False)
        self.select_action.blockSignals(False)

        self.statusBar().showMessage(
            (
                f"Alinhamento aplicado: eixo → {target_label} | "
                f"{len(object_ids)} objeto(s) transformado(s)"
            )
        )

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
        """Abre o painel não modal de reconhecimento de planos."""

        if not self.scene.objects_by_type("mesh"):
            QMessageBox.information(
                self,
                "Nenhuma malha disponível",
                "Importe uma malha antes de reconhecer um plano.",
            )
            return

        if (
            self._plane_region_dialog is not None
            and self._plane_region_dialog.isVisible()
        ):
            self._plane_region_dialog.raise_()
            self._plane_region_dialog.activateWindow()
            return

        default_radius = max(
            self._reference_scale() * 0.05,
            1.0,
        )
        preset = self.command_presets.load(
            "recognize_plane_region",
            {
                "region_radius": default_radius,
                "maximum_angle": 12.0,
                "minimum_points": 50,
                "plane_scale": 2.0,
                "auto_recalculate": True,
            },
        )

        dialog = PlaneRegionDialog(
            default_radius=default_radius,
            preset=preset,
            parent=self,
        )
        self._plane_region_dialog = dialog

        dialog.selection_requested.connect(
            self.begin_plane_region_selection
        )
        dialog.recalculate_requested.connect(
            self.recalculate_plane_from_seed
        )
        dialog.create_requested.connect(
            self.create_pending_plane
        )
        dialog.clear_requested.connect(
            self.clear_plane_region_state
        )
        dialog.cancel_requested.connect(
            self.cancel_plane_region_mode
        )

        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

        self.statusBar().showMessage(
            "Painel de reconhecimento de plano aberto"
        )

    def begin_plane_region_selection(self) -> None:
        """Ativa um clique de região mantendo o painel aberto."""

        dialog = self._plane_region_dialog

        if dialog is None:
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
        self.command_presets.save(
            "recognize_plane_region",
            dialog.preset_values(),
        )

        self._pending_plane_seed_point = None
        self._pending_plane_source_object_id = None
        self._pending_plane_creation = None
        self._clear_plane_region_preview()

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

        dialog.set_selection_active(True)
        dialog.status_label.setText(
            "Clique no centro aproximado da região plana."
        )

    def on_plane_region_picked(
        self,
        point: Any,
    ) -> None:
        """Registra a semente e calcula o primeiro resultado."""

        if point is None or len(point) < 3:
            return

        picked_point = (
            float(point[0]),
            float(point[1]),
            float(point[2]),
        )
        source_object = self._nearest_mesh_object(
            picked_point
        )

        if source_object is None:
            dialog = self._plane_region_dialog
            if dialog is not None:
                dialog.set_error(
                    "Não foi possível localizar a malha clicada."
                )
            return

        self._pending_plane_seed_point = picked_point
        self._pending_plane_source_object_id = (
            source_object.object_id
        )

        try:
            self.viewer.disable_picking()
        except Exception:
            pass

        dialog = self._plane_region_dialog
        if dialog is not None:
            dialog.set_selection_active(False)
            dialog.set_seed_selected()

        self.recalculate_plane_from_seed()

    def recalculate_plane_from_seed(self) -> None:
        """Reutiliza a mesma semente com os parâmetros atuais."""

        dialog = self._plane_region_dialog

        if dialog is None:
            return

        if self._pending_plane_seed_point is None:
            dialog.set_error(
                "Selecione uma região antes de recalcular."
            )
            return

        source_object = self.scene.get_object(
            self._pending_plane_source_object_id
        )

        if source_object is None:
            dialog.set_error(
                "A malha selecionada não está mais disponível."
            )
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
        self.command_presets.save(
            "recognize_plane_region",
            dialog.preset_values(),
        )

        dialog.set_calculation_in_progress(True)

        try:
            region_result = grow_planar_region(
                mesh=source_object.data,
                seed_point=(
                    self._pending_plane_seed_point
                ),
                radius=self._pending_plane_radius,
                maximum_angle_degrees=(
                    self._pending_plane_maximum_angle
                ),
            )

            if (
                region_result.point_count
                < self._pending_plane_minimum_points
            ):
                raise ValueError(
                    (
                        f"A expansão encontrou "
                        f"{region_result.point_count} pontos; "
                        f"o mínimo é "
                        f"{self._pending_plane_minimum_points}."
                    )
                )

            fit_result = fit_plane_to_points(
                region_result.points
            )
            normal = self._orient_normal_to_camera(
                fit_result.origin,
                fit_result.normal,
            )
            plane_size = max(
                self._pending_plane_radius
                * self._pending_plane_scale,
                1.0,
            )
            entity = PlaneReference(
                origin=fit_result.origin,
                normal=normal,
                size_x=plane_size,
                size_y=plane_size,
            )

            quality = evaluate_plane_quality(
                points=region_result.points,
                origin=fit_result.origin,
                normal=normal,
                rms_error=fit_result.rms_error,
                maximum_error=fit_result.maximum_error,
                region_radius=self._pending_plane_radius,
            )

            region_geometry = (
                source_object.data.extract_cells(
                    list(region_result.cell_ids)
                )
            )

            self._show_plane_region_preview(
                region_geometry=region_geometry,
                plane_entity=entity,
            )

        except Exception as error:
            self._pending_plane_creation = None
            self._clear_plane_region_preview()
            dialog.set_error(str(error))
            return

        self._pending_plane_creation = {
            "source_object": source_object,
            "region_result": region_result,
            "fit_result": fit_result,
            "entity": entity,
            "seed_point": (
                self._pending_plane_seed_point
            ),
            "quality": quality,
        }

        dialog.set_result(
            rms_error=fit_result.rms_error,
            maximum_error=fit_result.maximum_error,
            point_count=fit_result.point_count,
            triangle_count=(
                region_result.triangle_count
            ),
            normal=normal,
            quality_score=quality.score,
            quality_grade=quality.grade,
            quality_stars=quality.stars,
            mean_absolute_error=(
                quality.mean_absolute_error
            ),
            standard_deviation=(
                quality.standard_deviation
            ),
            inlier_ratio=quality.inlier_ratio,
            quality_reasons=quality.reasons,
        )

        self.statusBar().showMessage(
            (
                f"Plano recalculado | "
                f"RMS {fit_result.rms_error:.4f} mm | "
                f"{region_result.triangle_count} triângulos | "
                f"{quality.grade} {quality.score:.1f}%"
            )
        )

    def create_pending_plane(self) -> None:
        """Cria o plano atualmente exibido no painel."""

        pending = self._pending_plane_creation

        if pending is None:
            QMessageBox.information(
                self,
                "Resultado inexistente",
                "Calcule um plano válido antes de criar.",
            )
            return

        entity = pending["entity"]
        source_object = pending["source_object"]
        region_result = pending["region_result"]
        fit_result = pending["fit_result"]

        record = self.references.create_record(
            entity
        )
        command = CreateReferenceCommand(
            scene=self.scene,
            project_panel=self.project_panel,
            project_manager=self.project,
            reference_manager=self.references,
            record=record,
            display_geometry=(
                self.reference_factory.create_plane(
                    entity
                )
            ),
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
                    "plane_scale": (
                        self._pending_plane_scale
                    ),
                    "quality_score": (
                        pending["quality"].score
                    ),
                    "quality_grade": (
                        pending["quality"].grade
                    ),
                    "quality_stars": (
                        pending["quality"].stars
                    ),
                    "mean_absolute_error": (
                        pending["quality"].mean_absolute_error
                    ),
                    "standard_deviation": (
                        pending["quality"].standard_deviation
                    ),
                    "inlier_ratio": (
                        pending["quality"].inlier_ratio
                    ),
                    "quality_reasons": list(
                        pending["quality"].reasons
                    ),
                    "seed_point": tuple(
                        pending["seed_point"]
                    ),
                    "source_cell_ids": list(
                        region_result.cell_ids
                    ),
                },
            ),
        )

        self.history.execute(command)
        self.viewer.render()
        self.clear_plane_region_state()

        dialog = self._plane_region_dialog
        if dialog is not None:
            dialog.status_label.setText(
                (
                    f"Criado: {record.name}. "
                    "Você pode selecionar outra região."
                )
            )

        self.statusBar().showMessage(
            f"Criado: {record.name}"
        )

    def clear_plane_region_state(self) -> None:
        """Limpa semente e prévia sem fechar o painel."""

        self._pending_plane_seed_point = None
        self._pending_plane_source_object_id = None
        self._pending_plane_creation = None
        self._clear_plane_region_preview()

        try:
            self.viewer.disable_picking()
        except Exception:
            pass

        dialog = self._plane_region_dialog
        if dialog is not None:
            dialog.clear_state()

    def _remove_recognition_preview(self, actor_name: str) -> None:
        """Remove one session-owned preview without affecting scene objects."""

        try:
            self.viewer.remove_actor(actor_name, render=False)
        except Exception:
            pass

    def cancel_plane_region_mode(self) -> None:
        """Encerra o painel interativo de planos."""

        self.clear_plane_region_state()

        dialog = self._plane_region_dialog
        self._plane_region_dialog = None

        if dialog is not None:
            dialog.blockSignals(True)
            dialog.close()
            dialog.deleteLater()

        self.statusBar().showMessage(
            "Reconhecimento de plano cancelado"
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
        """Mostra região, plano, centro e normal provisórios."""

        self.recognition_session.begin_preview(
            getattr(plane_entity, "source_object_id", None),
            multi_recognition=False,
        )

        region_name = self.recognition_session.preview_name(
            self._plane_region_preview_name
        )
        plane_name = self.recognition_session.preview_name(
            self._plane_preview_name
        )
        center_name = self.recognition_session.preview_name(
            self._plane_center_preview_name
        )
        normal_name = self.recognition_session.preview_name(
            self._plane_normal_preview_name
        )

        for actor_name in (
            region_name,
            plane_name,
            center_name,
            normal_name,
        ):
            self.recognition_session.register(actor_name)

        region_actor = self.viewer.add_mesh(
            region_geometry,
            name=region_name,
            color="#ffd166",
            opacity=0.78,
            show_edges=True,
            edge_color="#fff0b3",
            line_width=1.0,
            lighting=False,
        )

        plane_actor = self.viewer.add_mesh(
            self.reference_factory.create_plane(
                plane_entity
            ),
            name=plane_name,
            color="#4ecdc4",
            opacity=0.32,
            show_edges=True,
            edge_color="#9ff3ed",
            line_width=2.0,
            lighting=False,
        )

        center_entity = PointReference(
            position=tuple(
                plane_entity.origin
            )
        )
        center_actor = self.viewer.add_mesh(
            self.reference_factory.create_point(
                center_entity,
                radius=max(
                    self._reference_scale() * 0.004,
                    0.30,
                ),
            ),
            name=center_name,
            color="#ff7a45",
            smooth_shading=True,
            ambient=0.8,
            diffuse=0.2,
        )

        normal_entity = AxisReference(
            origin=tuple(
                plane_entity.origin
            ),
            direction=tuple(
                plane_entity.normal
            ),
            display_length=max(
                plane_entity.size_x * 0.75,
                1.0,
            ),
        )
        normal_actor = self.viewer.add_mesh(
            self.reference_factory.create_axis(
                normal_entity
            ),
            name=normal_name,
            color="#4ea1ff",
            lighting=False,
            ambient=1.0,
        )

        for actor in (
            region_actor,
            plane_actor,
            center_actor,
            normal_actor,
        ):
            try:
                actor.SetPickable(False)
            except Exception:
                pass

        self.viewer.render()
    def _clear_plane_region_preview(
        self,
        render: bool = True,
    ) -> None:
        """Remove todos os elementos temporários do reconhecimento."""

        self.recognition_session.clear(render=render)
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



    def _metadata_custom(
        self,
        project_object: Any,
    ) -> dict[str, Any]:
        """Obtém metadados personalizados com tolerância a versões."""

        metadata = getattr(
            project_object,
            "metadata",
            None,
        )

        custom = getattr(
            metadata,
            "custom",
            None,
        )

        return (
            dict(custom)
            if isinstance(custom, dict)
            else {}
        )

    def _objects_in_pattern(
        self,
        pattern_id: str | None,
        master_id: str,
    ) -> set[str]:
        """Localiza o mestre, instâncias e referências derivadas."""

        result = {master_id}

        if not pattern_id:
            for object_id in self.scene.object_ids():
                project_object = (
                    self.project.get_object(
                        object_id
                    )
                )

                if project_object is None:
                    continue

                metadata = getattr(
                    project_object,
                    "metadata",
                    None,
                )
                source_object_id = getattr(
                    metadata,
                    "source_object_id",
                    None,
                )

                if source_object_id == master_id:
                    result.add(object_id)

            return result

        for object_id in self.scene.object_ids():
            project_object = self.project.get_object(
                object_id
            )

            if project_object is None:
                continue

            custom = self._metadata_custom(
                project_object
            )

            if custom.get("pattern_id") == pattern_id:
                result.add(object_id)

        return result

    def edit_project_object(
        self,
        object_id: str,
    ) -> None:
        """Reabre propriedades ao dar duplo clique na árvore."""

        scene_object = self.scene.get_object(
            object_id
        )

        if (
            scene_object is None
            or scene_object.object_type
            != "reference_cylinder"
        ):
            self.statusBar().showMessage(
                "A edição por duplo clique está disponível "
                "nesta versão para cilindros"
            )
            return

        project_object = self.project.get_object(
            object_id
        )

        if project_object is None:
            QMessageBox.warning(
                self,
                "Referência indisponível",
                "Não foi possível recuperar os dados do cilindro.",
            )
            return

        custom = self._metadata_custom(
            project_object
        )

        master_id = str(
            custom.get(
                "pattern_master_id",
                object_id,
            )
            or object_id
        )

        master_project_object = (
            self.project.get_object(
                master_id
            )
        )

        if master_project_object is None:
            master_project_object = project_object
            master_id = object_id

        entity = getattr(
            master_project_object,
            "data",
            None,
        )

        if not isinstance(
            entity,
            CylinderReference,
        ):
            QMessageBox.warning(
                self,
                "Tipo incompatível",
                "O objeto selecionado não contém um cilindro editável.",
            )
            return

        master_custom = self._metadata_custom(
            master_project_object
        )
        master_metadata = getattr(
            master_project_object,
            "metadata",
            None,
        )

        detected_diameter = float(
            master_custom.get(
                "detected_diameter",
                entity.diameter,
            )
            or entity.diameter
        )
        detected_center = tuple(
            master_custom.get(
                "detected_center",
                entity.center,
            )
            or entity.center
        )
        detected_direction = tuple(
            master_custom.get(
                "detected_direction",
                entity.axis_direction,
            )
            or entity.axis_direction
        )

        stored_extension_factor = float(
            master_custom.get(
                "extension_factor",
                1.0,
            )
            or 1.0
        )
        stored_length_mode = str(
            master_custom.get(
                "length_mode",
                CylinderPreviewDialog.LENGTH_REGION,
            )
        )

        recognized_length = master_custom.get(
            "recognized_length",
            None,
        )

        if recognized_length is None:
            if (
                stored_length_mode
                == CylinderPreviewDialog.LENGTH_EXTENDED
                and stored_extension_factor > 1.0e-12
            ):
                recognized_length = (
                    float(entity.length)
                    / stored_extension_factor
                )
            else:
                recognized_length = float(
                    entity.length
                )

        recognized_length = max(
            float(recognized_length),
            1.0e-9,
        )

        source_object_id = getattr(
            master_metadata,
            "source_object_id",
            None,
        )
        source_object = (
            self.scene.get_object(
                source_object_id
            )
            if source_object_id
            else None
        )

        if source_object is None:
            source_object = SimpleNamespace(
                object_id=(
                    source_object_id
                    or master_id
                )
            )

        region_dialog = self._cylinder_region_dialog
        self._cylinder_region_dialog = None
        self._cylinder_recognition_history = []

        if region_dialog is not None:
            region_dialog.blockSignals(True)
            region_dialog.close()
            region_dialog.deleteLater()

        dialog = CylinderPreviewDialog(
            triangle_count=int(
                master_custom.get(
                    "triangle_count",
                    0,
                )
                or 0
            ),
            point_count=int(
                master_custom.get(
                    "point_count",
                    0,
                )
                or 0
            ),
            diameter=detected_diameter,
            length=recognized_length,
            rms_error=float(
                getattr(
                    master_metadata,
                    "rms_error",
                    0.0,
                )
                or 0.0
            ),
            maximum_error=float(
                master_custom.get(
                    "maximum_error",
                    0.0,
                )
                or 0.0
            ),
            coverage_angle=float(
                master_custom.get(
                    "coverage_angle",
                    getattr(
                        entity,
                        "coverage_angle",
                        0.0,
                    ),
                )
                or 0.0
            ),
            center=tuple(
                float(value)
                for value in detected_center
            ),
            axis_direction=tuple(
                float(value)
                for value in detected_direction
            ),
            confidence=float(
                master_custom.get(
                    "confidence",
                    0.0,
                )
                or 0.0
            ),
            quality_score=float(
                master_custom.get(
                    "quality_score",
                    0.0,
                )
                or 0.0
            ),
            quality_grade=str(
                master_custom.get(
                    "quality_grade",
                    "Não avaliada",
                )
            ),
            quality_stars=int(
                master_custom.get(
                    "quality_stars",
                    0,
                )
                or 0
            ),
            circularity=float(
                master_custom.get(
                    "circularity",
                    0.0,
                )
                or 0.0
            ),
            mean_absolute_error=float(
                master_custom.get(
                    "mean_absolute_error",
                    0.0,
                )
                or 0.0
            ),
            standard_deviation=float(
                master_custom.get(
                    "standard_deviation",
                    0.0,
                )
                or 0.0
            ),
            relative_rms_percent=float(
                master_custom.get(
                    "relative_rms_percent",
                    0.0,
                )
                or 0.0
            ),
            inlier_ratio=float(
                master_custom.get(
                    "inlier_ratio",
                    0.0,
                )
                or 0.0
            ),
            quality_reasons=tuple(
                master_custom.get(
                    "quality_reasons",
                    (),
                )
                or ()
            ),
            parent=self,
        )

        pattern_settings = (
            master_custom.get(
                "pattern_settings",
                None,
            )
        )

        dialog.load_existing_values(
            nominal_diameter=float(
                entity.diameter
            ),
            nominal_center=tuple(
                entity.center
            ),
            nominal_direction=tuple(
                entity.axis_direction
            ),
            length_mode=stored_length_mode,
            extension_factor=stored_extension_factor,
            property_state=str(
                master_custom.get(
                    "property_state",
                    CylinderPreviewDialog.STATE_RECOGNIZED,
                )
            ),
            properties_locked=bool(
                master_custom.get(
                    "properties_locked",
                    False,
                )
            ),
            pattern_settings=(
                dict(pattern_settings)
                if isinstance(
                    pattern_settings,
                    dict,
                )
                else None
            ),
        )

        pattern_id = master_custom.get(
            "pattern_id",
            None,
        )

        self._editing_object_ids = (
            self._objects_in_pattern(
                str(pattern_id)
                if pattern_id
                else None,
                master_id,
            )
        )

        fit_result = SimpleNamespace(
            rms_error=float(
                getattr(
                    master_metadata,
                    "rms_error",
                    0.0,
                )
                or 0.0
            ),
            maximum_error=float(
                master_custom.get(
                    "maximum_error",
                    0.0,
                )
                or 0.0
            ),
            point_count=int(
                master_custom.get(
                    "point_count",
                    0,
                )
                or 0
            ),
            coverage_angle=float(
                master_custom.get(
                    "coverage_angle",
                    0.0,
                )
                or 0.0
            ),
            radial_tolerance=float(
                master_custom.get(
                    "radial_tolerance",
                    0.0,
                )
                or 0.0
            ),
        )

        region_result = SimpleNamespace(
            triangle_count=int(
                master_custom.get(
                    "triangle_count",
                    0,
                )
                or 0
            ),
            cell_ids=tuple(
                master_custom.get(
                    "source_cell_ids",
                    (),
                )
                or ()
            ),
        )

        base_cylinder_entity = CylinderReference(
            center=tuple(entity.center),
            axis_direction=tuple(
                entity.axis_direction
            ),
            radius=float(entity.radius),
            length=recognized_length,
            rms_error=float(entity.rms_error),
            coverage_angle=float(
                entity.coverage_angle
            ),
            source_object_id=(
                entity.source_object_id
            ),
        )

        self._pending_cylinder_creation = {
            "source_object": source_object,
            "region_result": region_result,
            "fit_result": fit_result,
            "cylinder_entity": base_cylinder_entity,
            "axis_entity": base_cylinder_entity.create_axis(
                display_extension=0.65
            ),
            "center_entity": (
                base_cylinder_entity.create_center_point()
            ),
            "confidence": float(
                master_custom.get(
                    "confidence",
                    0.0,
                )
                or 0.0
            ),
            "quality": CylinderQualityResult(
                score=float(
                    master_custom.get(
                        "quality_score",
                        0.0,
                    )
                    or 0.0
                ),
                grade=str(
                    master_custom.get(
                        "quality_grade",
                        "Não avaliada",
                    )
                ),
                stars=int(
                    master_custom.get(
                        "quality_stars",
                        0,
                    )
                    or 0
                ),
                circularity=float(
                    master_custom.get(
                        "circularity",
                        0.0,
                    )
                    or 0.0
                ),
                mean_absolute_error=float(
                    master_custom.get(
                        "mean_absolute_error",
                        0.0,
                    )
                    or 0.0
                ),
                standard_deviation=float(
                    master_custom.get(
                        "standard_deviation",
                        0.0,
                    )
                    or 0.0
                ),
                relative_rms_percent=float(
                    master_custom.get(
                        "relative_rms_percent",
                        0.0,
                    )
                    or 0.0
                ),
                inlier_ratio=float(
                    master_custom.get(
                        "inlier_ratio",
                        0.0,
                    )
                    or 0.0
                ),
                evaluated_point_count=int(
                    master_custom.get(
                        "evaluated_point_count",
                        0,
                    )
                    or 0
                ),
                reasons=tuple(
                    master_custom.get(
                        "quality_reasons",
                        (),
                    )
                    or ()
                ),
            ),
        }

        preview_length = recognized_length

        if (
            stored_length_mode
            == CylinderPreviewDialog.LENGTH_EXTENDED
        ):
            preview_length *= stored_extension_factor

        preview_entity = CylinderReference(
            center=tuple(entity.center),
            axis_direction=tuple(
                entity.axis_direction
            ),
            radius=float(entity.radius),
            length=preview_length,
            rms_error=float(entity.rms_error),
            coverage_angle=float(
                entity.coverage_angle
            ),
            source_object_id=(
                entity.source_object_id
            ),
        )

        self._show_cylinder_preview(
            region_geometry=None,
            cylinder_entity=preview_entity,
            axis_entity=preview_entity.create_axis(
                display_extension=0.65
            ),
        )

        self._cylinder_preview_dialog = dialog

        dialog.geometry_changed.connect(
            self.update_cylinder_geometry_preview
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

        dialog.setWindowTitle(
            f"Editar {getattr(master_project_object, 'name', 'Cilindro')}"
        )
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

        self.statusBar().showMessage(
            "Editando cilindro existente — confirme para atualizar"
        )


    def start_cylinder_region_mode(self) -> None:
        """Abre o painel interativo sem bloquear a viewport."""

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

        if (
            self._cylinder_region_dialog is not None
            and self._cylinder_region_dialog.isVisible()
        ):
            self._cylinder_region_dialog.raise_()
            self._cylinder_region_dialog.activateWindow()
            return

        default_radius = max(
            self._reference_scale() * 0.08,
            2.0,
        )
        cylinder_preset = self.command_presets.load(
            "recognize_cylinder_region",
            {
                "region_radius": default_radius,
                "maximum_neighbor_angle": 20.0,
                "minimum_points": 100,
                "seed_count": 2,
                "auto_recalculate": True,
                "production_mode": False,
                "multi_recognition": False,
            },
        )

        dialog = CylinderRegionDialog(
            default_radius=default_radius,
            preset=cylinder_preset,
            parent=self,
        )
        self._cylinder_region_dialog = dialog

        dialog.selection_requested.connect(
            self.begin_cylinder_seed_selection
        )
        dialog.clear_requested.connect(
            self.clear_cylinder_seeds
        )
        dialog.recalculate_requested.connect(
            self.recalculate_cylinder_from_seeds
        )
        dialog.automatic_recalculate_requested.connect(
            self.recalculate_cylinder_from_seeds
        )
        dialog.history_result_requested.connect(
            self.use_cylinder_recognition_history
        )
        dialog.add_to_batch_requested.connect(
            self.add_pending_cylinder_to_batch
        )
        dialog.multi_recognition_checkbox.toggled.connect(
            self.recognition_session.set_multi_recognition
        )
        dialog.create_batch_requested.connect(
            self.create_cylinder_batch
        )
        dialog.continue_requested.connect(
            self.open_pending_cylinder_properties
        )
        dialog.cancel_requested.connect(
            self.cancel_cylinder_region_mode
        )

        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

        self.statusBar().showMessage(
            "Painel de reconhecimento aberto"
        )

    def begin_cylinder_seed_selection(
        self,
    ) -> None:
        """Lê os parâmetros atuais e habilita cliques na malha."""

        dialog = self._cylinder_region_dialog

        if dialog is None:
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
        self._pending_cylinder_seed_count = (
            dialog.seed_count()
        )
        self._cylinder_production_mode = (
            dialog.production_mode_enabled()
        )

        self.command_presets.save(
            "recognize_cylinder_region",
            dialog.preset_values(),
        )

        self._pending_cylinder_seed_points = []
        self._pending_cylinder_source_object_id = None
        self._cylinder_recognition_history = []
        dialog.clear_history_results()

        if not dialog.multi_recognition_enabled():
            self._cylinder_batch_queue = []
            dialog.clear_batch_results()

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

        dialog.set_selection_active(True)
        dialog.set_seed_progress(
            0,
            self._pending_cylinder_seed_count,
        )

        self.statusBar().showMessage(
            "Seleção de sementes ativa"
        )

    def clear_cylinder_seeds(self) -> None:
        """Limpa cliques atuais sem fechar o painel."""

        self._pending_cylinder_seed_points = []
        self._pending_cylinder_source_object_id = None
        self._pending_cylinder_creation = None
        self._cylinder_recognition_history = []
        self._clear_cylinder_preview()

        dialog = self._cylinder_region_dialog

        if dialog is not None:
            dialog.set_selection_active(False)
            dialog.set_seed_progress(
                0,
                dialog.seed_count(),
                "Sementes removidas. Clique em Selecionar sementes.",
            )
            dialog.clear_result()
            dialog.clear_history_results()

        try:
            self.viewer.disable_picking()
        except Exception:
            pass

        self.statusBar().showMessage(
            "Sementes do cilindro removidas"
        )

    def cancel_cylinder_region_mode(self) -> None:
        """Cancela a seleção interativa e fecha o painel."""

        try:
            self.viewer.disable_picking()
        except Exception:
            pass

        self._pending_cylinder_seed_points = []
        self._pending_cylinder_source_object_id = None
        self._pending_cylinder_creation = None
        self._cylinder_recognition_history = []
        self._cylinder_production_mode = False
        self._cylinder_batch_queue = []
        self._clear_cylinder_preview()

        dialog = self._cylinder_region_dialog
        self._cylinder_region_dialog = None

        if dialog is not None:
            dialog.blockSignals(True)
            dialog.close()
            dialog.deleteLater()

        self.statusBar().showMessage(
            "Reconhecimento cilíndrico cancelado"
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
        """Coleta sementes sem fechar o painel."""

        if point is None or len(point) < 3:
            return

        picked_point = (
            float(point[0]),
            float(point[1]),
            float(point[2]),
        )
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

        if (
            self._pending_cylinder_source_object_id
            is not None
            and source_object.object_id
            != self._pending_cylinder_source_object_id
        ):
            QMessageBox.warning(
                self,
                "Malhas diferentes",
                (
                    "As sementes devem pertencer à mesma malha. "
                    "Clique na malha da primeira semente."
                ),
            )
            return

        self._pending_cylinder_source_object_id = (
            source_object.object_id
        )
        self._pending_cylinder_seed_points.append(
            picked_point
        )

        dialog = self._cylinder_region_dialog
        collected = len(
            self._pending_cylinder_seed_points
        )
        required = int(
            self._pending_cylinder_seed_count
        )

        if dialog is not None:
            dialog.set_seed_progress(
                collected,
                required,
            )

        if collected < required:
            self.statusBar().showMessage(
                (
                    f"Semente {collected}/{required} registrada. "
                    "Clique novamente na parede cilíndrica."
                )
            )
            return

        try:
            self.viewer.disable_picking()
        except Exception:
            pass

        self.recalculate_cylinder_from_seeds()

    def recalculate_cylinder_from_seeds(
        self,
    ) -> None:
        """Reutiliza as mesmas sementes com os parâmetros atuais."""

        dialog = self._cylinder_region_dialog

        if dialog is None:
            return

        required = int(
            dialog.seed_count()
        )

        if (
            len(self._pending_cylinder_seed_points)
            < required
        ):
            dialog.set_error(
                "Selecione todas as sementes antes de recalcular."
            )
            return

        source_object = self.scene.get_object(
            self._pending_cylinder_source_object_id
        )

        if source_object is None:
            dialog.set_error(
                "A malha das sementes não está mais disponível."
            )
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
        self._pending_cylinder_seed_count = required

        self.command_presets.save(
            "recognize_cylinder_region",
            dialog.preset_values(),
        )

        dialog.set_calculation_in_progress(
            True
        )
        dialog.set_seed_progress(
            required,
            required,
            "Recalculando com as sementes atuais...",
        )

        try:
            seed_regions = []

            for seed_point in (
                self._pending_cylinder_seed_points[:required]
            ):
                seed_regions.append(
                    grow_cylindrical_region(
                        mesh=source_object.data,
                        seed_point=seed_point,
                        radius=(
                            self._pending_cylinder_radius
                        ),
                        maximum_neighbor_angle_degrees=(
                            self._pending_cylinder_angle
                        ),
                    )
                )

            (
                candidate_cell_ids,
                candidate_points,
                candidate_normals,
                seed_cell_ids,
            ) = merge_cylindrical_seed_regions(
                seed_regions
            )

            preliminary_fit = fit_cylinder_to_points(
                candidate_points,
                candidate_normals,
            )

            refined_region, refined_normals = (
                refine_cylindrical_cells_multi_seed(
                    mesh=source_object.data,
                    candidate_cell_ids=(
                        candidate_cell_ids
                    ),
                    seed_cell_ids=seed_cell_ids,
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

            if (
                refined_region.point_count
                < self._pending_cylinder_minimum_points
            ):
                raise ValueError(
                    (
                        f"A região possui "
                        f"{refined_region.point_count} pontos; "
                        f"o mínimo é "
                        f"{self._pending_cylinder_minimum_points}."
                    )
                )

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
                display_extension=0.65
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
                coverage_angle=(
                    fit_result.coverage_angle
                ),
                point_count=fit_result.point_count,
            )

            quality = evaluate_cylinder_quality(
                points=refined_region.points,
                center=fit_result.center,
                axis_direction=(
                    fit_result.axis_direction
                ),
                radius=fit_result.radius,
                rms_error=fit_result.rms_error,
                maximum_error=(
                    fit_result.maximum_error
                ),
                coverage_angle=(
                    fit_result.coverage_angle
                ),
                radial_tolerance=(
                    fit_result.radial_tolerance
                ),
            )

        except Exception as error:
            self._pending_cylinder_creation = None
            self._clear_cylinder_preview()
            dialog.set_calculation_in_progress(
                False
            )
            dialog.set_error(
                str(error)
            )
            self.statusBar().showMessage(
                "O reconhecimento precisa ser ajustado"
            )
            return

        snapshot = {
            "source_object": source_object,
            "region_result": refined_region,
            "fit_result": fit_result,
            "cylinder_entity": cylinder_entity,
            "axis_entity": axis_entity,
            "center_entity": center_entity,
            "confidence": confidence,
            "quality": quality,
            "seed_points": tuple(
                self._pending_cylinder_seed_points[:required]
            ),
            "seed_count": required,
            "region_geometry": region_geometry,
            "region_radius": float(
                self._pending_cylinder_radius
            ),
            "neighbor_angle": float(
                self._pending_cylinder_angle
            ),
            "minimum_points": int(
                self._pending_cylinder_minimum_points
            ),
            "production_mode": bool(
                self._cylinder_production_mode
            ),
        }

        self._cylinder_recognition_history.append(
            snapshot
        )

        best_index = max(
            range(
                len(
                    self._cylinder_recognition_history
                )
            ),
            key=lambda index: (
                self._cylinder_recognition_history[
                    index
                ]["quality"].score,
                -self._cylinder_recognition_history[
                    index
                ]["fit_result"].rms_error,
                self._cylinder_recognition_history[
                    index
                ]["fit_result"].coverage_angle,
            ),
        )

        current_index = (
            len(
                self._cylinder_recognition_history
            )
            - 1
        )
        self._pending_cylinder_creation = snapshot

        dialog.set_calculation_in_progress(
            False
        )
        dialog.set_result(
            diameter=cylinder_entity.diameter,
            rms_error=fit_result.rms_error,
            coverage_angle=(
                fit_result.coverage_angle
            ),
            quality_grade=quality.grade,
            quality_score=quality.score,
            point_count=fit_result.point_count,
        )
        dialog.add_history_result(
            attempt_number=current_index + 1,
            diameter=cylinder_entity.diameter,
            rms_error=fit_result.rms_error,
            coverage_angle=(
                fit_result.coverage_angle
            ),
            quality_grade=quality.grade,
            quality_score=quality.score,
            region_radius=float(
                self._pending_cylinder_radius
            ),
            neighbor_angle=float(
                self._pending_cylinder_angle
            ),
            is_best=current_index == best_index,
        )
        dialog.mark_best_history_result(
            best_index
        )

        self.statusBar().showMessage(
            (
                f"Resultado recalculado | "
                f"Ø {cylinder_entity.diameter:.4f} mm | "
                f"{quality.grade} {quality.score:.1f}%"
            )
        )


    def use_cylinder_recognition_history(
        self,
        index: int,
    ) -> None:
        """Recupera uma tentativa anterior da sessão."""

        if (
            index < 0
            or index
            >= len(
                self._cylinder_recognition_history
            )
        ):
            return

        snapshot = (
            self._cylinder_recognition_history[
                index
            ]
        )
        self._pending_cylinder_creation = snapshot

        self._show_cylinder_preview(
            region_geometry=(
                snapshot["region_geometry"]
            ),
            cylinder_entity=(
                snapshot["cylinder_entity"]
            ),
            axis_entity=snapshot["axis_entity"],
        )

        dialog = self._cylinder_region_dialog

        if dialog is not None:
            fit_result = snapshot["fit_result"]
            quality = snapshot["quality"]
            cylinder = snapshot[
                "cylinder_entity"
            ]

            dialog.set_result(
                diameter=cylinder.diameter,
                rms_error=fit_result.rms_error,
                coverage_angle=(
                    fit_result.coverage_angle
                ),
                quality_grade=quality.grade,
                quality_score=quality.score,
                point_count=fit_result.point_count,
            )
            dialog.select_history_result(index)
            dialog.progress_label.setText(
                (
                    f"Resultado {index + 1} recuperado.\\n"
                    "Você pode abrir as propriedades ou "
                    "continuar comparando."
                )
            )

        self.statusBar().showMessage(
            (
                f"Resultado {index + 1} recuperado | "
                f"Ø "
                f"{snapshot['cylinder_entity'].diameter:.4f} mm | "
                f"{snapshot['quality'].grade} "
                f"{snapshot['quality'].score:.1f}%"
            )
        )


    def add_pending_cylinder_to_batch(
        self,
    ) -> None:
        """Adiciona o resultado ativo ao lote e prepara nova seleção."""

        pending = self._pending_cylinder_creation
        dialog = self._cylinder_region_dialog

        if pending is None or dialog is None:
            QMessageBox.information(
                self,
                "Resultado inexistente",
                "Reconheça um cilindro válido antes de adicionar ao lote.",
            )
            return

        snapshot = dict(pending)
        self._cylinder_batch_queue.append(
            snapshot
        )

        cylinder = snapshot["cylinder_entity"]
        quality = snapshot["quality"]

        dialog.add_batch_result(
            index=len(self._cylinder_batch_queue),
            diameter=cylinder.diameter,
            quality_grade=quality.grade,
            quality_score=quality.score,
        )

        self._pending_cylinder_creation = None
        self._pending_cylinder_seed_points = []
        self._pending_cylinder_source_object_id = None
        self._cylinder_recognition_history = []
        dialog.clear_history_results()
        self.recognition_session.commit_current()
        self.viewer.render()

        try:
            self.viewer.disable_picking()
        except Exception:
            pass

        dialog.set_selection_active(False)
        dialog.set_seed_progress(
            0,
            dialog.seed_count(),
            (
                f"{len(self._cylinder_batch_queue)} cilindro(s) no lote. "
                "Clique em Selecionar sementes para o próximo."
            ),
        )

        self.statusBar().showMessage(
            (
                f"Cilindro adicionado ao lote | "
                f"Total: {len(self._cylinder_batch_queue)}"
            )
        )

    def create_cylinder_batch(
        self,
    ) -> None:
        """Cria todos os cilindros acumulados em uma única operação."""

        dialog = self._cylinder_region_dialog

        if not self._cylinder_batch_queue:
            QMessageBox.information(
                self,
                "Lote vazio",
                "Adicione ao menos um cilindro ao lote.",
            )
            return

        creation_preset = self.command_presets.load(
            "create_cylinder_reference",
            {},
        )

        length_mode = str(
            creation_preset.get(
                "length_mode",
                CylinderPreviewDialog.LENGTH_REGION,
            )
        )
        extension_factor = max(
            1.0,
            float(
                creation_preset.get(
                    "extension_factor",
                    3.0,
                )
            ),
        )
        create_axis = bool(
            creation_preset.get(
                "create_axis",
                True,
            )
        )
        create_center = bool(
            creation_preset.get(
                "create_center",
                True,
            )
        )

        commands = []

        for batch_index, snapshot in enumerate(
            self._cylinder_batch_queue,
            start=1,
        ):
            source_object = snapshot[
                "source_object"
            ]
            region_result = snapshot[
                "region_result"
            ]
            fit_result = snapshot[
                "fit_result"
            ]
            base_entity = snapshot[
                "cylinder_entity"
            ]
            quality = snapshot["quality"]

            final_length = float(
                base_entity.length
            )

            if (
                length_mode
                == CylinderPreviewDialog.LENGTH_EXTENDED
            ):
                final_length *= extension_factor

            entity = CylinderReference(
                center=tuple(base_entity.center),
                axis_direction=tuple(
                    base_entity.axis_direction
                ),
                radius=float(base_entity.radius),
                length=final_length,
                rms_error=float(
                    base_entity.rms_error
                ),
                coverage_angle=float(
                    base_entity.coverage_angle
                ),
                source_object_id=(
                    base_entity.source_object_id
                ),
            )

            record = self.references.create_record(
                entity,
                name=f"Cilindro Lote {batch_index:02d}",
            )

            commands.append(
                CreateReferenceCommand(
                    scene=self.scene,
                    project_panel=self.project_panel,
                    project_manager=self.project,
                    reference_manager=self.references,
                    record=record,
                    display_geometry=(
                        create_cylinder_reference_lines(
                            entity
                        )
                    ),
                    render_options={
                        "color": "#70e000",
                        "opacity": 0.82,
                        "line_width": 2.0,
                        "lighting": False,
                        "ambient": 1.0,
                        "pickable": True,
                    },
                    metadata=ProjectObjectMetadata(
                        source_object_id=(
                            source_object.object_id
                        ),
                        created_by="multi_recognition",
                        creation_method=(
                            "cylinder_multi_recognition"
                        ),
                        rms_error=(
                            fit_result.rms_error
                        ),
                        custom={
                            "batch_index": batch_index,
                            "batch_size": len(
                                self._cylinder_batch_queue
                            ),
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
                            "quality_score": (
                                quality.score
                            ),
                            "quality_grade": (
                                quality.grade
                            ),
                            "quality_stars": (
                                quality.stars
                            ),
                            "circularity": (
                                quality.circularity
                            ),
                            "recognized_length": (
                                float(
                                    base_entity.length
                                )
                            ),
                            "display_length": (
                                float(final_length)
                            ),
                            "length_mode": length_mode,
                            "extension_factor": (
                                extension_factor
                                if length_mode
                                == CylinderPreviewDialog.LENGTH_EXTENDED
                                else 1.0
                            ),
                            "recognition_seed_count": (
                                int(
                                    snapshot.get(
                                        "seed_count",
                                        1,
                                    )
                                )
                            ),
                            "recognition_seed_points": [
                                tuple(point)
                                for point in snapshot.get(
                                    "seed_points",
                                    (),
                                )
                            ],
                            "source_cell_ids": list(
                                region_result.cell_ids
                            ),
                        },
                    ),
                )
            )

            if create_axis:
                axis_entity = entity.create_axis(
                    display_extension=0.65
                )
                axis_record = self.references.create_record(
                    axis_entity,
                    name=f"Eixo de {record.name}",
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
                                axis_entity
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
                                record.object_id
                            ),
                            created_by="multi_recognition",
                            creation_method=(
                                "axis_from_batch_cylinder"
                            ),
                        ),
                    )
                )

            if create_center:
                center_entity = (
                    entity.create_center_point()
                )
                center_record = (
                    self.references.create_record(
                        center_entity,
                        name=f"Centro de {record.name}",
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
                                    * 0.0035,
                                    0.25,
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
                                record.object_id
                            ),
                            created_by="multi_recognition",
                            creation_method=(
                                "center_from_batch_cylinder"
                            ),
                        ),
                    )
                )

        batch_command = CreateReferenceBatchCommand(
            description=(
                f"Criar lote com "
                f"{len(self._cylinder_batch_queue)} cilindros"
            ),
            commands=commands,
        )

        self.history.execute(
            batch_command
        )
        created_count = len(
            self._cylinder_batch_queue
        )
        self._cylinder_batch_queue = []
        self.recognition_session.clear(render=False)
        self.viewer.render()

        if dialog is not None:
            dialog.clear_batch_results()
            dialog.set_seed_progress(
                0,
                dialog.seed_count(),
                (
                    f"Lote com {created_count} cilindros criado. "
                    "Você pode iniciar outro lote ou cancelar."
                ),
            )

        self.statusBar().showMessage(
            (
                f"Lote criado: {created_count} cilindros | "
                "Ctrl+Z desfaz todo o lote"
            )
        )

    def open_pending_cylinder_properties(
        self,
    ) -> None:
        """Aceita o resultado atual e abre as propriedades nominais."""

        pending = self._pending_cylinder_creation

        if pending is None:
            QMessageBox.information(
                self,
                "Resultado inexistente",
                "Calcule um cilindro válido antes de continuar.",
            )
            return

        source_object = pending["source_object"]
        refined_region = pending["region_result"]
        fit_result = pending["fit_result"]
        cylinder_entity = pending["cylinder_entity"]
        confidence = pending["confidence"]
        quality = pending["quality"]
        self._cylinder_production_mode = bool(
            pending.get(
                "production_mode",
                self._cylinder_production_mode,
            )
        )

        try:
            self.viewer.disable_picking()
        except Exception:
            pass

        region_dialog = self._cylinder_region_dialog
        self._cylinder_region_dialog = None

        if region_dialog is not None:
            region_dialog.blockSignals(True)
            region_dialog.close()
            region_dialog.deleteLater()

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
            center=cylinder_entity.center,
            axis_direction=(
                fit_result.axis_direction
            ),
            confidence=confidence,
            quality_score=quality.score,
            quality_grade=quality.grade,
            quality_stars=quality.stars,
            circularity=quality.circularity,
            mean_absolute_error=(
                quality.mean_absolute_error
            ),
            standard_deviation=(
                quality.standard_deviation
            ),
            relative_rms_percent=(
                quality.relative_rms_percent
            ),
            inlier_ratio=quality.inlier_ratio,
            quality_reasons=quality.reasons,
            parent=self,
        )

        dialog.apply_creation_preset(
            self.command_presets.load(
                "create_cylinder_reference",
                {},
            )
        )

        self._cylinder_preview_dialog = dialog
        dialog.geometry_changed.connect(
            self.update_cylinder_geometry_preview
        )

        self.update_cylinder_geometry_preview(
            {
                "diameter": dialog.final_diameter(),
                "center": dialog.final_center(),
                "direction": dialog.final_direction(),
                "length_mode": dialog.length_mode(),
                "extension_factor": (
                    dialog.extension_factor()
                ),
                "create_axis": dialog.create_axis(),
                "create_center": (
                    dialog.create_center_point()
                ),
                "pattern_settings": (
                    dialog.pattern_settings()
                ),
            }
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
            "Resultado aceito — ajuste as propriedades nominais"
        )

    def update_cylinder_geometry_preview(
        self,
        values: object,
    ) -> None:
        """Atualiza ao vivo o cilindro mestre e o padrão completo."""

        pending = self._pending_cylinder_creation

        if pending is None or not isinstance(values, dict):
            return

        original = pending["cylinder_entity"]

        diameter = float(
            values.get("diameter", original.diameter)
        )
        center = tuple(
            float(value)
            for value in values.get(
                "center",
                original.center,
            )
        )
        direction = tuple(
            float(value)
            for value in values.get(
                "direction",
                original.axis_direction,
            )
        )

        if diameter <= 0.0:
            return

        length = float(original.length)
        length_mode = str(
            values.get(
                "length_mode",
                CylinderPreviewDialog.LENGTH_REGION,
            )
        )
        extension_factor = max(
            1.0,
            float(
                values.get(
                    "extension_factor",
                    1.0,
                )
            ),
        )

        if (
            length_mode
            == CylinderPreviewDialog.LENGTH_EXTENDED
        ):
            length *= extension_factor

        create_axis = bool(
            values.get("create_axis", True)
        )
        create_center = bool(
            values.get("create_center", True)
        )

        settings = values.get(
            "pattern_settings",
            {},
        )
        if not isinstance(settings, dict):
            settings = {}

        pattern_type = str(
            settings.get(
                "type",
                CylinderPreviewDialog.PATTERN_NONE,
            )
        )
        quantity = max(
            1,
            int(settings.get("quantity", 1)),
        )

        try:
            if (
                pattern_type
                == CylinderPreviewDialog.PATTERN_LINEAR
            ):
                instances = create_linear_pattern(
                    master_center=center,
                    master_direction=direction,
                    translation_direction=tuple(
                        settings.get(
                            "axis_direction",
                            (1.0, 0.0, 0.0),
                        )
                    ),
                    spacing=float(
                        settings.get(
                            "spacing",
                            100.0,
                        )
                    ),
                    quantity=quantity,
                )
            elif (
                pattern_type
                == CylinderPreviewDialog.PATTERN_CIRCULAR
            ):
                instances = create_circular_pattern(
                    master_center=center,
                    master_direction=direction,
                    axis_origin=tuple(
                        settings.get(
                            "axis_origin",
                            (0.0, 0.0, 0.0),
                        )
                    ),
                    axis_direction=tuple(
                        settings.get(
                            "axis_direction",
                            (0.0, 0.0, 1.0),
                        )
                    ),
                    angle_step_degrees=float(
                        settings.get(
                            "angle_step",
                            30.0,
                        )
                    ),
                    quantity=quantity,
                    rotate_orientation=bool(
                        settings.get(
                            "rotate_orientation",
                            False,
                        )
                    ),
                )
            else:
                instances = [
                    PatternInstance(
                        index=0,
                        center=center,
                        direction=direction,
                        parameter=0.0,
                        is_master=True,
                    )
                ]
        except Exception as error:
            self.statusBar().showMessage(
                f"Prévia inválida: {error}"
            )
            return

        for actor_name in [
            self._active_cylinder_preview_name,
            self._active_cylinder_axis_preview_name,
            self._active_cylinder_center_preview_name,
            *self._cylinder_pattern_preview_names,
        ]:
            if actor_name is None:
                continue

            try:
                self.viewer.remove_actor(
                    actor_name,
                    render=False,
                )
            except Exception:
                pass

            self.recognition_session.forget(actor_name)

        self._cylinder_pattern_preview_names = []
        self._active_cylinder_preview_name = None
        self._active_cylinder_axis_preview_name = None
        self._active_cylinder_center_preview_name = None
        actors = []

        for instance in instances:
            entity = CylinderReference(
                center=instance.center,
                axis_direction=instance.direction,
                radius=diameter / 2.0,
                length=length,
                rms_error=original.rms_error,
                coverage_angle=(
                    original.coverage_angle
                ),
                source_object_id=(
                    original.source_object_id
                ),
            )

            prefix = (
                "__flcad_pattern_preview_"
                f"{instance.index:03d}"
            )

            cylinder_name = self.recognition_session.preview_name(
                f"{prefix}_cylinder"
            )
            self._cylinder_pattern_preview_names.append(
                cylinder_name
            )
            self.recognition_session.register(cylinder_name)
            actors.append(
                self.viewer.add_mesh(
                    create_cylinder_reference_lines(
                        entity
                    ),
                    name=cylinder_name,
                    color=(
                        "#70e000"
                        if instance.is_master
                        else "#9be564"
                    ),
                    opacity=(
                        0.95
                        if instance.is_master
                        else 0.68
                    ),
                    line_width=(
                        2.4
                        if instance.is_master
                        else 1.6
                    ),
                    lighting=False,
                    ambient=1.0,
                )
            )

            if create_axis:
                axis_name = self.recognition_session.preview_name(
                    f"{prefix}_axis"
                )
                self._cylinder_pattern_preview_names.append(
                    axis_name
                )
                self.recognition_session.register(axis_name)
                actors.append(
                    self.viewer.add_mesh(
                        self.reference_factory.create_axis(
                            entity.create_axis(
                                display_extension=0.65
                            )
                        ),
                        name=axis_name,
                        color="#4ea1ff",
                        opacity=(
                            1.0
                            if instance.is_master
                            else 0.58
                        ),
                        lighting=False,
                        ambient=1.0,
                    )
                )

            if create_center:
                center_name = self.recognition_session.preview_name(
                    f"{prefix}_center"
                )
                self._cylinder_pattern_preview_names.append(
                    center_name
                )
                self.recognition_session.register(center_name)
                actors.append(
                    self.viewer.add_mesh(
                        self.reference_factory.create_point(
                            entity.create_center_point(),
                            radius=max(
                                self._reference_scale()
                                * 0.0035,
                                0.25,
                            ),
                        ),
                        name=center_name,
                        color="#ff7a45",
                        opacity=(
                            1.0
                            if instance.is_master
                            else 0.65
                        ),
                        smooth_shading=True,
                        ambient=0.8,
                        diffuse=0.2,
                    )
                )

        for actor in actors:
            try:
                actor.SetPickable(False)
            except Exception:
                pass

        self.viewer.render()
        self.statusBar().showMessage(
            (
                f"Prévia dinâmica: {len(instances)} cilindro(s) | "
                f"Ø {diameter:.4f} mm"
            )
        )

    def confirm_cylinder_preview(self) -> None:
        """Cria o cilindro mestre e suas instâncias opcionais."""

        pending = self._pending_cylinder_creation
        dialog = self._cylinder_preview_dialog

        if pending is None or dialog is None:
            self._clear_cylinder_preview()
            return

        source_object = pending["source_object"]
        region_result = pending["region_result"]
        fit_result = pending["fit_result"]
        cylinder_entity = pending["cylinder_entity"]

        create_axis = dialog.create_axis()
        create_center = dialog.create_center_point()
        final_diameter = dialog.final_diameter()
        detected_diameter = dialog.detected_diameter()
        final_center = dialog.final_center()
        detected_center = dialog.detected_center()
        final_direction = dialog.final_direction()
        detected_direction = dialog.detected_direction()
        property_state = dialog.property_state()
        properties_locked = dialog.properties_locked()
        length_mode = dialog.length_mode()
        extension_factor = dialog.extension_factor()
        pattern_settings = dialog.pattern_settings()

        self.command_presets.save(
            "create_cylinder_reference",
            dialog.creation_preset_values(),
        )

        self._clear_cylinder_preview()

        final_length = cylinder_entity.length

        if (
            length_mode
            == CylinderPreviewDialog.LENGTH_EXTENDED
        ):
            final_length = (
                cylinder_entity.length
                * extension_factor
            )

        pattern_type = str(
            pattern_settings["type"]
        )
        quantity = int(
            pattern_settings["quantity"]
        )

        if (
            pattern_type
            == CylinderPreviewDialog.PATTERN_LINEAR
        ):
            instances = create_linear_pattern(
                master_center=final_center,
                master_direction=final_direction,
                translation_direction=(
                    pattern_settings[
                        "axis_direction"
                    ]
                ),
                spacing=float(
                    pattern_settings["spacing"]
                ),
                quantity=quantity,
            )
        elif (
            pattern_type
            == CylinderPreviewDialog.PATTERN_CIRCULAR
        ):
            instances = create_circular_pattern(
                master_center=final_center,
                master_direction=final_direction,
                axis_origin=(
                    pattern_settings[
                        "axis_origin"
                    ]
                ),
                axis_direction=(
                    pattern_settings[
                        "axis_direction"
                    ]
                ),
                angle_step_degrees=float(
                    pattern_settings[
                        "angle_step"
                    ]
                ),
                quantity=quantity,
                rotate_orientation=bool(
                    pattern_settings[
                        "rotate_orientation"
                    ]
                ),
            )
        else:
            instances = [
                PatternInstance(
                    index=0,
                    center=tuple(final_center),
                    direction=tuple(
                        final_direction
                    ),
                    parameter=0.0,
                    is_master=True,
                )
            ]

        commands = []
        created_cylinder_names: list[str] = []
        master_record_id: str | None = None
        pattern_id = (
            None
            if pattern_type
            == CylinderPreviewDialog.PATTERN_NONE
            else f"pattern-{source_object.object_id}-{id(instances)}"
        )

        for instance in instances:
            instance_entity = CylinderReference(
                center=instance.center,
                axis_direction=instance.direction,
                radius=final_diameter / 2.0,
                length=final_length,
                rms_error=(
                    cylinder_entity.rms_error
                ),
                coverage_angle=(
                    cylinder_entity.coverage_angle
                ),
                source_object_id=(
                    cylinder_entity.source_object_id
                ),
            )

            if instance.is_master:
                record_name = None
            else:
                record_name = (
                    f"Instância {instance.index + 1:02d}"
                )

            cylinder_record = (
                self.references.create_record(
                    instance_entity,
                    name=record_name,
                )
            )

            if instance.is_master:
                master_record_id = (
                    cylinder_record.object_id
                )

            created_cylinder_names.append(
                cylinder_record.name
            )

            instance_role = (
                "master_recognized"
                if instance.is_master
                else "nominal_instance"
            )

            commands.append(
                CreateReferenceCommand(
                    scene=self.scene,
                    project_panel=self.project_panel,
                    project_manager=self.project,
                    reference_manager=self.references,
                    record=cylinder_record,
                    display_geometry=(
                        create_cylinder_reference_lines(
                            instance_entity
                        )
                    ),
                    render_options={
                        "color": "#70e000",
                        "opacity": 0.82,
                        "line_width": 2.0,
                        "lighting": False,
                        "ambient": 1.0,
                        "pickable": True,
                    },
                    metadata=ProjectObjectMetadata(
                        source_object_id=(
                            source_object.object_id
                        ),
                        created_by=(
                            "user"
                            if instance.is_master
                            else "pattern_engine"
                        ),
                        creation_method=(
                            "cylinder_fit_refined_region"
                            if instance.is_master
                            else (
                                f"cylinder_pattern_"
                                f"{pattern_type}"
                            )
                        ),
                        rms_error=(
                            fit_result.rms_error
                            if instance.is_master
                            else None
                        ),
                        custom={
                            "maximum_error": (
                                fit_result.maximum_error
                                if instance.is_master
                                else None
                            ),
                            "point_count": (
                                fit_result.point_count
                                if instance.is_master
                                else 0
                            ),
                            "triangle_count": (
                                region_result.triangle_count
                                if instance.is_master
                                else 0
                            ),
                            "coverage_angle": (
                                fit_result.coverage_angle
                            ),
                            "confidence": (
                                pending["confidence"]
                                if instance.is_master
                                else None
                            ),
                            "quality_score": (
                                pending["quality"].score
                                if instance.is_master
                                else None
                            ),
                            "quality_grade": (
                                pending["quality"].grade
                                if instance.is_master
                                else None
                            ),
                            "quality_stars": (
                                pending["quality"].stars
                                if instance.is_master
                                else None
                            ),
                            "circularity": (
                                pending["quality"].circularity
                                if instance.is_master
                                else None
                            ),
                            "mean_absolute_error": (
                                pending[
                                    "quality"
                                ].mean_absolute_error
                                if instance.is_master
                                else None
                            ),
                            "standard_deviation": (
                                pending[
                                    "quality"
                                ].standard_deviation
                                if instance.is_master
                                else None
                            ),
                            "relative_rms_percent": (
                                pending[
                                    "quality"
                                ].relative_rms_percent
                                if instance.is_master
                                else None
                            ),
                            "inlier_ratio": (
                                pending[
                                    "quality"
                                ].inlier_ratio
                                if instance.is_master
                                else None
                            ),
                            "evaluated_point_count": (
                                pending[
                                    "quality"
                                ].evaluated_point_count
                                if instance.is_master
                                else 0
                            ),
                            "quality_reasons": (
                                list(
                                    pending[
                                        "quality"
                                    ].reasons
                                )
                                if instance.is_master
                                else []
                            ),
                            "detected_diameter": (
                                detected_diameter
                                if instance.is_master
                                else None
                            ),
                            "nominal_diameter": (
                                final_diameter
                            ),
                            "detected_center": (
                                tuple(detected_center)
                                if instance.is_master
                                else None
                            ),
                            "nominal_center": tuple(
                                instance.center
                            ),
                            "detected_direction": (
                                tuple(
                                    detected_direction
                                )
                                if instance.is_master
                                else None
                            ),
                            "nominal_direction": tuple(
                                instance.direction
                            ),
                            "property_state": (
                                property_state
                                if instance.is_master
                                else "Instância nominal"
                            ),
                            "properties_locked": (
                                properties_locked
                            ),
                            "recognized_length": (
                                float(
                                    cylinder_entity.length
                                )
                            ),
                            "display_length": (
                                float(final_length)
                            ),
                            "length_mode": length_mode,
                            "extension_factor": (
                                extension_factor
                                if length_mode
                                == CylinderPreviewDialog.LENGTH_EXTENDED
                                else 1.0
                            ),
                            "pattern_id": pattern_id,
                            "pattern_type": pattern_type,
                            "pattern_role": instance_role,
                            "pattern_index": (
                                instance.index
                            ),
                            "pattern_parameter": (
                                instance.parameter
                            ),
                            "pattern_quantity": (
                                len(instances)
                            ),
                            "pattern_master_id": (
                                master_record_id
                            ),
                            "pattern_settings": dict(
                                pattern_settings
                            ),
                            "radial_tolerance": (
                                fit_result.radial_tolerance
                                if instance.is_master
                                else None
                            ),
                            "source_cell_ids": (
                                list(
                                    region_result.cell_ids
                                )
                                if instance.is_master
                                else []
                            ),
                            "recognition_seed_count": (
                                int(
                                    pending.get(
                                        "seed_count",
                                        1,
                                    )
                                )
                                if instance.is_master
                                else 0
                            ),
                            "recognition_seed_points": (
                                [
                                    tuple(point)
                                    for point in pending.get(
                                        "seed_points",
                                        (),
                                    )
                                ]
                                if instance.is_master
                                else []
                            ),
                        },
                    ),
                )
            )

            if create_axis:
                axis_entity = (
                    instance_entity.create_axis(
                        display_extension=0.65
                    )
                )
                axis_record = (
                    self.references.create_record(
                        axis_entity,
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
                                axis_entity
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
                            created_by="pattern_engine",
                            creation_method=(
                                "axis_from_cylinder"
                            ),
                            custom={
                                "pattern_id": pattern_id,
                                "pattern_index": (
                                    instance.index
                                ),
                                "derived_from": (
                                    cylinder_record.object_id
                                ),
                                "cylinder_display_length": (
                                    float(final_length)
                                ),
                                "axis_display_extension": 0.65,
                            },
                        ),
                    )
                )

            if create_center:
                center_entity = (
                    instance_entity.create_center_point()
                )
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
                                    * 0.0035,
                                    0.25,
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
                            created_by="pattern_engine",
                            creation_method=(
                                "center_from_cylinder"
                            ),
                            custom={
                                "pattern_id": pattern_id,
                                "pattern_index": (
                                    instance.index
                                ),
                                "derived_from": (
                                    cylinder_record.object_id
                                ),
                            },
                        ),
                    )
                )

        if len(instances) == 1:
            description = (
                f"Criar {created_cylinder_names[0]} "
                "e referências derivadas"
            )
        else:
            description = (
                f"Criar padrão {pattern_type} "
                f"com {len(instances)} cilindros"
            )

        batch = CreateReferenceBatchCommand(
            description=description,
            commands=commands,
        )

        was_editing_existing = bool(
            self._editing_object_ids
        )

        if self._editing_object_ids:
            delete_command = DeleteObjectsCommand(
                scene=self.scene,
                project_panel=self.project_panel,
                project_manager=self.project,
                reference_manager=self.references,
                object_ids=set(
                    self._editing_object_ids
                ),
            )

            history_command = CompositeProjectCommand(
                description=(
                    "Editar cilindro e atualizar padrão"
                ),
                commands=[
                    delete_command,
                    batch,
                ],
            )
        else:
            history_command = batch

        self.history.execute(
            history_command
        )
        self._editing_object_ids.clear()
        self.viewer.render()

        self._pending_cylinder_creation = None

        restart_production_mode = (
            bool(self._cylinder_production_mode)
            and not was_editing_existing
        )

        self.statusBar().showMessage(
            (
                f"Criados {len(instances)} cilindro(s) | "
                f"Ø {final_diameter:.4f} mm | "
                f"Padrão: {pattern_type} | "
                f"Qualidade: "
                f"{pending['quality'].grade} "
                f"({pending['quality'].score:.1f}%)"
            )
        )

        if restart_production_mode:
            self.statusBar().showMessage(
                (
                    "Cilindro criado. "
                    "Modo produção ativo: aguardando próximo reconhecimento."
                )
            )
            self.start_cylinder_region_mode()

    def cancel_cylinder_preview(self) -> None:
        """Cancela a prévia sem criar referências."""

        self._clear_cylinder_preview()
        self._pending_cylinder_creation = None
        self._editing_object_ids.clear()
        self._pending_cylinder_seed_points = []
        self._pending_cylinder_source_object_id = None

        self.statusBar().showMessage(
            "Criação ou edição do cilindro cancelada"
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
        """Mostra região, cilindro, eixo e centro provisórios."""

        dialog = self._cylinder_region_dialog
        multi_recognition = bool(
            dialog is not None
            and dialog.multi_recognition_enabled()
        )
        self.recognition_session.begin_preview(
            cylinder_entity.source_object_id,
            multi_recognition=multi_recognition,
        )

        self._active_cylinder_region_preview_name = (
            self.recognition_session.preview_name(
                self._cylinder_region_preview_name
            )
        )
        self._active_cylinder_preview_name = (
            self.recognition_session.preview_name(
                self._cylinder_preview_name
            )
        )
        self._active_cylinder_axis_preview_name = (
            self.recognition_session.preview_name(
                self._cylinder_axis_preview_name
            )
        )
        self._active_cylinder_center_preview_name = (
            self.recognition_session.preview_name(
                self._cylinder_center_preview_name
            )
        )

        for actor_name in (
            self._active_cylinder_preview_name,
            self._active_cylinder_axis_preview_name,
            self._active_cylinder_center_preview_name,
        ):
            if actor_name is not None:
                self.recognition_session.register(actor_name)

        if (
            region_geometry is not None
            and self._active_cylinder_region_preview_name is not None
        ):
            self.recognition_session.register(
                self._active_cylinder_region_preview_name
            )

        actors = []

        if region_geometry is not None:
            actors.append(
                self.viewer.add_mesh(
                    region_geometry,
                    name=self._active_cylinder_region_preview_name,
                    color="#ffd166",
                    opacity=0.80,
                    show_edges=True,
                    edge_color="#fff0b3",
                    line_width=1.0,
                    lighting=False,
                )
            )

        actors.append(
            self.viewer.add_mesh(
                create_cylinder_reference_lines(
                    cylinder_entity
                ),
                name=self._active_cylinder_preview_name,
                color="#70e000",
                opacity=0.88,
                line_width=2.0,
                lighting=False,
                ambient=1.0,
            )
        )

        actors.append(
            self.viewer.add_mesh(
                self.reference_factory.create_axis(
                    axis_entity
                ),
                name=self._active_cylinder_axis_preview_name,
                color="#4ea1ff",
                lighting=False,
                ambient=1.0,
            )
        )

        actors.append(
            self.viewer.add_mesh(
                self.reference_factory.create_point(
                    cylinder_entity.create_center_point(),
                    radius=max(
                        self._reference_scale() * 0.0035,
                        0.25,
                    ),
                ),
                name=self._active_cylinder_center_preview_name,
                color="#ff7a45",
                smooth_shading=True,
                ambient=0.8,
                diffuse=0.2,
            )
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
        """Remove todas as geometrias provisórias."""

        self.recognition_session.clear(render=render)
        self._cylinder_pattern_preview_names = []
        self._active_cylinder_region_preview_name = None
        self._active_cylinder_preview_name = None
        self._active_cylinder_axis_preview_name = None
        self._active_cylinder_center_preview_name = None

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

            self.recognition_session.clear()

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

        engineering_menu = self.engineering_interaction.context_menu(
            pick_result.object_id,
            self,
        )

        if engineering_menu is not None:
            engineering_menu.exec(
                self.viewer.interactor.mapToGlobal(position)
            )
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
                (
                    "Seleção ativa — use Ctrl + clique curto. "
                    "Arraste normalmente para rotacionar."
                )
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


    def _vtk_interactor(
        self,
    ) -> Any:
        """Retorna o interactor VTK real usado pelo QtInteractor."""

        interactor = getattr(
            self.viewer,
            "iren",
            None,
        )

        if interactor is None:
            return None

        return getattr(
            interactor,
            "interactor",
            interactor,
        )


    def enable_viewport_selection(self) -> None:
        """
        Ativa seleção pela viewport usando o filtro de eventos do Qt.

        Esse caminho é mais confiável no QtInteractor do que depender
        apenas de observadores VTK, que podem não receber o clique em
        algumas versões do PyVistaQt/VTK.
        """

        self.disable_viewport_selection()

        viewport_widget = self.viewer.interactor

        if viewport_widget is None:
            self.statusBar().showMessage(
                "Não foi possível ativar a seleção da viewport"
            )
            return

        viewport_widget.installEventFilter(self)
        self._selection_event_filter_installed = True

    def disable_viewport_selection(self) -> None:
        """Desativa o filtro Qt e remove observadores antigos."""

        viewport_widget = getattr(
            self.viewer,
            "interactor",
            None,
        )

        if (
            viewport_widget is not None
            and self._selection_event_filter_installed
        ):
            try:
                viewport_widget.removeEventFilter(self)
            except Exception:
                pass

        self._selection_event_filter_installed = False

        vtk_interactor = self._vtk_interactor()

        if vtk_interactor is not None:
            for observer_id in self._selection_observer_ids:
                try:
                    vtk_interactor.RemoveObserver(
                        observer_id
                    )
                except Exception:
                    pass

        self._selection_observer_ids = []
        self._selection_press_position = None
        self._selection_press_control = False

        try:
            self.viewer.disable_picking()
        except Exception:
            pass

    def eventFilter(
        self,
        watched: Any,
        event: Any,
    ) -> bool:
        """
        Captura Ctrl + clique curto diretamente no widget da viewport.

        Retorna False para que a navegação continue recebendo os eventos.
        """

        if (
            watched is getattr(
                self.viewer,
                "interactor",
                None,
            )
            and self._selection_event_filter_installed
            and self.selection.active
        ):
            event_type = event.type()

            if (
                event_type
                == QEvent.Type.MouseButtonPress
                and event.button()
                == Qt.MouseButton.LeftButton
            ):
                position = event.position()
                self._selection_press_position = (
                    int(position.x()),
                    int(position.y()),
                )
                self._selection_press_control = bool(
                    event.modifiers()
                    & Qt.KeyboardModifier.ControlModifier
                )

            elif (
                event_type
                == QEvent.Type.MouseButtonRelease
                and event.button()
                == Qt.MouseButton.LeftButton
            ):
                press_position = (
                    self._selection_press_position
                )
                control_pressed = (
                    self._selection_press_control
                    and bool(
                        event.modifiers()
                        & Qt.KeyboardModifier.ControlModifier
                    )
                )

                self._selection_press_position = None
                self._selection_press_control = False

                if (
                    press_position is not None
                    and control_pressed
                ):
                    position = event.position()
                    release_position = (
                        int(position.x()),
                        int(position.y()),
                    )

                    distance_squared = (
                        (
                            release_position[0]
                            - press_position[0]
                        ) ** 2
                        + (
                            release_position[1]
                            - press_position[1]
                        ) ** 2
                    )

                    if distance_squared <= (
                        self._selection_drag_tolerance_px
                        ** 2
                    ):
                        self._pick_viewport_at_qt_position(
                            release_position
                        )
                    else:
                        self.statusBar().showMessage(
                            (
                                "Movimento interpretado como rotação; "
                                "nenhum objeto foi selecionado."
                            )
                        )

        return super().eventFilter(
            watched,
            event,
        )

    def _pick_viewport_at_qt_position(
        self,
        position: tuple[int, int],
    ) -> None:
        """Converte coordenadas Qt e executa o picking VTK."""

        viewport_widget = self.viewer.interactor
        viewport_height = max(
            int(viewport_widget.height()),
            1,
        )

        vtk_x = int(position[0])
        vtk_y = int(
            viewport_height - position[1] - 1
        )

        actor = None

        cell_picker = vtk.vtkCellPicker()
        cell_picker.SetTolerance(0.01)

        picked = cell_picker.Pick(
            vtk_x,
            vtk_y,
            0.0,
            self.viewer.renderer,
        )

        if picked:
            actor = cell_picker.GetActor()

            if actor is None:
                actor = cell_picker.GetViewProp()

        if actor is None:
            prop_picker = vtk.vtkPropPicker()
            picked = prop_picker.Pick(
                vtk_x,
                vtk_y,
                0.0,
                self.viewer.renderer,
            )

            if picked:
                actor = prop_picker.GetActor()

                if actor is None:
                    actor = prop_picker.GetViewProp()

        if actor is None:
            self.statusBar().showMessage(
                "Nenhum objeto encontrado sob o cursor"
            )
            return

        self.on_viewport_actor_picked(actor)

    def _on_selection_left_press(
        self,
        interactor: Any,
        event_name: str,
    ) -> None:
        """Registra a posição inicial sem interromper a navegação."""

        if not self.selection.active:
            return

        position = interactor.GetEventPosition()
        self._selection_press_position = (
            int(position[0]),
            int(position[1]),
        )
        self._selection_press_control = bool(
            interactor.GetControlKey()
        )


    def _on_selection_left_release(
        self,
        interactor: Any,
        event_name: str,
    ) -> None:
        """Seleciona com Ctrl + clique curto sem bloquear a rotação."""

        if (
            not self.selection.active
            or self._selection_press_position is None
        ):
            return

        release = interactor.GetEventPosition()
        release_position = (
            int(release[0]),
            int(release[1]),
        )
        press_position = self._selection_press_position
        control_pressed = (
            self._selection_press_control
            and bool(interactor.GetControlKey())
        )

        self._selection_press_position = None
        self._selection_press_control = False

        distance_squared = (
            (
                release_position[0]
                - press_position[0]
            ) ** 2
            + (
                release_position[1]
                - press_position[1]
            ) ** 2
        )

        if not control_pressed:
            return

        if distance_squared > (
            self._selection_drag_tolerance_px ** 2
        ):
            self.statusBar().showMessage(
                (
                    "Movimento interpretado como rotação; "
                    "nenhum objeto foi selecionado."
                )
            )
            return

        actor = None

        # vtkCellPicker é mais confiável para malhas, planos,
        # cilindros em linhas e pequenas referências.
        cell_picker = vtk.vtkCellPicker()
        cell_picker.SetTolerance(0.006)
        picked = cell_picker.Pick(
            release_position[0],
            release_position[1],
            0.0,
            self.viewer.renderer,
        )

        if picked:
            actor = cell_picker.GetActor()

            if actor is None:
                actor = cell_picker.GetViewProp()

        # Fallback para atores sem células selecionáveis.
        if actor is None:
            prop_picker = vtk.vtkPropPicker()
            picked = prop_picker.Pick(
                release_position[0],
                release_position[1],
                0.0,
                self.viewer.renderer,
            )

            if picked:
                actor = prop_picker.GetActor()

                if actor is None:
                    actor = prop_picker.GetViewProp()

        if actor is None:
            self.statusBar().showMessage(
                "Nenhum objeto encontrado sob o cursor"
            )
            return

        self.on_viewport_actor_picked(actor)


    def on_viewport_actor_picked(
        self,
        actor: Any,
    ) -> None:
        """Resolve o ator para o objeto lógico e alterna sua seleção."""

        if not self.selection.active:
            return

        scene_object = self.scene.get_object_by_actor(
            actor
        )

        if scene_object is None:
            # Alguns pickers retornam o vtkProp interno do wrapper
            # PyVista. Comparamos endereços VTK como fallback.
            try:
                picked_address = actor.GetAddressAsString(
                    ""
                )
            except Exception:
                picked_address = None

            if picked_address is not None:
                for object_id in self.scene.object_ids():
                    candidate = self.scene.get_object(
                        object_id
                    )

                    if candidate is None:
                        continue

                    try:
                        candidate_address = (
                            candidate.actor.GetAddressAsString(
                                ""
                            )
                        )
                    except Exception:
                        continue

                    if candidate_address == picked_address:
                        scene_object = candidate
                        break

        if scene_object is None:
            self.statusBar().showMessage(
                (
                    "O elemento foi localizado na viewport, "
                    "mas não está vinculado à árvore do projeto."
                )
            )
            return

        # Usa o mesmo caminho da seleção pela árvore, garantindo
        # sincronização visual e lógica.
        self.selection.toggle(
            scene_object.object_id
        )

    def on_selection_changed(
        self,
        selected_ids: set[str],
    ) -> None:
        """Recebe mudanças e informa operações disponíveis."""

        if self.delete_dialog is not None:
            self.delete_dialog.set_selected_objects(
                self.selection.selected_names()
            )

        type_counts: dict[str, int] = {}

        for object_id in selected_ids:
            scene_object = self.scene.get_object(
                object_id
            )

            if scene_object is None:
                continue

            object_type = scene_object.object_type
            type_counts[object_type] = (
                type_counts.get(object_type, 0)
                + 1
            )

        mesh_count = type_counts.get("mesh", 0)
        plane_count = type_counts.get(
            "reference_plane",
            0,
        )
        cylinder_count = type_counts.get(
            "reference_cylinder",
            0,
        )
        axis_count = type_counts.get(
            "reference_axis",
            0,
        )

        parts: list[str] = []

        if mesh_count:
            parts.append(
                f"{mesh_count} malha"
                f"{'s' if mesh_count != 1 else ''}"
            )

        if plane_count:
            parts.append(
                f"{plane_count} plano"
                f"{'s' if plane_count != 1 else ''}"
            )

        if cylinder_count:
            parts.append(
                f"{cylinder_count} cilindro"
                f"{'s' if cylinder_count != 1 else ''}"
            )

        if axis_count:
            parts.append(
                f"{axis_count} eixo"
                f"{'s' if axis_count != 1 else ''}"
            )

        other_count = (
            len(selected_ids)
            - mesh_count
            - plane_count
            - cylinder_count
            - axis_count
        )

        if other_count > 0:
            parts.append(
                f"{other_count} outro"
                f"{'s' if other_count != 1 else ''}"
            )

        if not selected_ids:
            message = (
                "Nenhum objeto selecionado — "
                "Ctrl + clique curto para selecionar"
            )
        else:
            message = "Selecionado: " + ", ".join(
                parts
            )

            if (
                mesh_count == 1
                and plane_count == 1
                and len(selected_ids) == 2
            ):
                message += (
                    " | ✓ Pronto para alinhamento por plano"
                )
            elif (
                mesh_count == 1
                and (
                    cylinder_count + axis_count
                ) == 1
                and len(selected_ids) == 2
            ):
                message += (
                    " | ✓ Pronto para alinhamento por eixo"
                )
            elif mesh_count == 1:
                message += (
                    " | Selecione um plano, cilindro ou eixo"
                )

        if self.delete_mode_active:
            message = f"Modo Deletar — {message}"

        self.statusBar().showMessage(message)
        self.engineering_interaction.synchronize_selection(selected_ids)

    def _on_engineering_inspection(self, snapshot: Any) -> None:
        """Present the current read-only engineering inspection summary."""

        if snapshot is None:
            return

        summary = " | ".join(
            f"{name}: {value}"
            for name, value in snapshot.properties
        )
        self.statusBar().showMessage(summary)

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

        self.statusBar().showMessage(
            (
                "Modo Deletar — selecione com Ctrl + clique curto; "
                "arraste para rotacionar normalmente."
            )
        )

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
