from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")  # noqa: RUF067
gi.require_version("Gdk", "4.0")  # noqa: RUF067

from .ui import UI

__all__ = ["UI"]
