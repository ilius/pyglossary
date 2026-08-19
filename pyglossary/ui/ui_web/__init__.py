"""
PyGlossary browser-based user interface package.

Exports the WebSocket-driven web UI used when ``--ui=web`` is selected.
"""

from .ui_controller import WebUI as UI

__all__ = ["UI"]
