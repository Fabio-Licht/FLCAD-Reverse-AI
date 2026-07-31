from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable


class Command(ABC):
    """Contrato básico de uma operação reversível."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Descrição exibida no histórico."""

    @abstractmethod
    def execute(self) -> None:
        """Executa ou refaz a operação."""

    @abstractmethod
    def undo(self) -> None:
        """Desfaz a operação."""


HistoryCallback = Callable[[], None]


class CommandManager:
    """Gerencia os históricos de desfazer e refazer."""

    def __init__(self) -> None:
        self._undo_stack: list[Command] = []
        self._redo_stack: list[Command] = []
        self._callbacks: list[HistoryCallback] = []

    def subscribe(
        self,
        callback: HistoryCallback,
    ) -> None:
        """Registra uma função para mudanças do histórico."""

        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def execute(
        self,
        command: Command,
    ) -> None:
        """Executa um comando e o adiciona ao histórico."""

        command.execute()

        self._undo_stack.append(command)
        self._redo_stack.clear()

        self._notify_changed()

    def undo(self) -> bool:
        """Desfaz o comando mais recente."""

        if not self._undo_stack:
            return False

        command = self._undo_stack.pop()
        command.undo()

        self._redo_stack.append(command)

        self._notify_changed()
        return True

    def redo(self) -> bool:
        """Refaz o último comando desfeito."""

        if not self._redo_stack:
            return False

        command = self._redo_stack.pop()
        command.execute()

        self._undo_stack.append(command)

        self._notify_changed()
        return True

    def clear(self) -> None:
        """Limpa os dois históricos."""

        self._undo_stack.clear()
        self._redo_stack.clear()

        self._notify_changed()

    def can_undo(self) -> bool:
        """Informa se existe algo para desfazer."""

        return bool(self._undo_stack)

    def can_redo(self) -> bool:
        """Informa se existe algo para refazer."""

        return bool(self._redo_stack)

    def undo_description(self) -> str | None:
        """Retorna a descrição da próxima operação de undo."""

        if not self._undo_stack:
            return None

        return self._undo_stack[-1].description

    def redo_description(self) -> str | None:
        """Retorna a descrição da próxima operação de redo."""

        if not self._redo_stack:
            return None

        return self._redo_stack[-1].description

    def _notify_changed(self) -> None:
        """Comunica que o histórico foi alterado."""

        for callback in tuple(self._callbacks):
            callback()