from __future__ import annotations

import traceback
from collections.abc import Callable

from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class WorkerSignals(QObject):
    finished = Signal(object)
    failed = Signal(str)
    progress = Signal(str, int, int)
    output = Signal(str)


class Worker(QRunnable):
    def __init__(self, function: Callable, *args, **kwargs) -> None:
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self.function(*self.args, **self.kwargs)
        except Exception as exc:
            self.signals.failed.emit(f"{exc}\n\n{traceback.format_exc()}")
        else:
            self.signals.finished.emit(result)
