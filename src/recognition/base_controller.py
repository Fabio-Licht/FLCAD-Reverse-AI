from __future__ import annotations
from abc import ABC
class BaseRecognitionController(ABC):
    def __init__(self, main_window):
        self.main_window=main_window
