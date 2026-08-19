# mypy: ignore-errors
# do not sort these imports!
"""
GTK 3 helper widgets shared by the legacy GTK UI.

Re-exports small GTK 3 utilities (about dialog helpers, sizing controls) used
by :mod:`pyglossary.ui.ui_gtk3`.
"""

from gi.repository import Gtk as gtk  # noqa: I001
from gi.repository import Gdk as gdk  # noqa: I001

__all__ = ["gdk", "gtk"]
