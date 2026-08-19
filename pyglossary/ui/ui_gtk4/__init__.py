"""
PyGlossary GTK 4 user interface package.

Exports the GTK 4 ``UI`` class and widgets for file selection, format options,
and conversion on Linux desktops with PyGObject/GTK 4.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")  # noqa: RUF067
gi.require_version("Gdk", "4.0")  # noqa: RUF067

from .ui import UI

__all__ = ["UI"]
