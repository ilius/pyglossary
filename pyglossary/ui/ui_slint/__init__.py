# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# This file is part of PyGlossary project, https://github.com/ilius/pyglossary
#
# Slint-based graphical interface for PyGlossary, following the same ui
# module convention as ui_tk / ui_qt6 / ui_gtk4. Register and dispatch via
# `--ui=slint` (see pyglossary/ui/runner.py and pyglossary/ui/argparse_main.py).

from .ui import UI

__all__ = ["UI"]
