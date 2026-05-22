# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)

from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.ui.base import aboutText

from .qt_imports import (
	QDialog,
	QDialogButtonBox,
	QTextBrowser,
	QVBoxLayout,
)

if TYPE_CHECKING:
	from .qt_imports import (
		QWidget,
	)

__all__ = ["exec_about_dialog"]


def exec_about_dialog(parent: QWidget | None) -> None:
	dlg = QDialog(parent)
	dlg.setWindowTitle("About PyGlossary")
	v = QVBoxLayout(dlg)
	browser = QTextBrowser()
	browser.setPlainText(aboutText)
	browser.setMinimumSize(540, 360)
	v.addWidget(browser)
	box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
	box.accepted.connect(dlg.accept)
	v.addWidget(box)
	dlg.exec()
