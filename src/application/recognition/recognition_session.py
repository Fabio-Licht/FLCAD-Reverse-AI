"""Lifecycle ownership for temporary recognition preview actors."""

from __future__ import annotations

from collections.abc import Callable


RemovePreview = Callable[[str], None]
RenderPreviews = Callable[[], None]


class RecognitionSession:
    """Own temporary preview names for one source-mesh recognition session."""

    def __init__(
        self,
        remove_preview: RemovePreview,
        render_previews: RenderPreviews,
    ) -> None:
        self._remove_preview = remove_preview
        self._render_previews = render_previews
        self._source_object_id: str | None = None
        self._multi_recognition = False
        self._generation = 0
        self._current: set[str] = set()
        self._accumulated: set[str] = set()

    @property
    def source_object_id(self) -> str | None:
        """Return the mesh identity owning the active session."""

        return self._source_object_id

    @property
    def temporary_actor_names(self) -> frozenset[str]:
        """Return every actor currently owned by the session."""

        return frozenset(self._current | self._accumulated)

    @property
    def current_actor_names(self) -> frozenset[str]:
        """Return actors belonging to the replaceable current preview."""

        return frozenset(self._current)

    def begin_preview(
        self,
        source_object_id: str | None,
        *,
        multi_recognition: bool,
    ) -> None:
        """Start a preview, replacing state according to session mode."""

        source_changed = (
            self._source_object_id is not None
            and source_object_id != self._source_object_id
        )

        if source_changed:
            self.clear(render=False)
        else:
            self.clear_current(render=False)

            if not multi_recognition:
                self._remove_names(self._accumulated)
                self._accumulated.clear()

        self._source_object_id = source_object_id
        self._multi_recognition = multi_recognition
        self._generation += 1

    def preview_name(self, base_name: str) -> str:
        """Create a deterministic actor name for the current generation."""

        return f"{base_name}:session:{self._generation:06d}"

    def register(self, actor_name: str) -> None:
        """Register one actor as part of the current temporary preview."""

        self._current.add(actor_name)

    def set_multi_recognition(self, enabled: bool) -> None:
        """Update accumulation mode and discard accumulated actors when disabled."""

        self._multi_recognition = enabled

        if enabled:
            return

        self._remove_names(self._accumulated)
        self._accumulated.clear()
        self._render_previews()

    def forget(self, actor_name: str) -> None:
        """Stop tracking an actor already removed by a specialized visualizer."""

        self._current.discard(actor_name)
        self._accumulated.discard(actor_name)

    def commit_current(self) -> None:
        """Preserve the current preview only in multi-recognition mode."""

        if self._multi_recognition:
            self._accumulated.update(self._current)
            self._current.clear()

    def clear_current(self, *, render: bool = True) -> None:
        """Remove the replaceable current preview only."""

        self._remove_names(self._current)
        self._current.clear()

        if render:
            self._render_previews()

    def clear(self, *, render: bool = True) -> None:
        """Remove every temporary actor while leaving scene objects untouched."""

        self._remove_names(self._current | self._accumulated)
        self._current.clear()
        self._accumulated.clear()
        self._source_object_id = None
        self._multi_recognition = False

        if render:
            self._render_previews()

    def _remove_names(self, actor_names: set[str]) -> None:
        """Remove a stable snapshot so callbacks cannot alter iteration."""

        for actor_name in tuple(sorted(actor_names)):
            self._remove_preview(actor_name)
