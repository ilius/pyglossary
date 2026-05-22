# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .qt_imports import (
	QDialog,
	QDialogButtonBox,
	QFormLayout,
	QLineEdit,
)

if TYPE_CHECKING:
	from .qt_imports import (
		QWidget,
	)

__all__ = ["PreConvertInfoQtDialog"]


class PreConvertInfoQtDialog(QDialog):
	def __init__(self, info: dict[str, Any], parent: QWidget | None) -> None:
		super().__init__(parent)
		self._info = info
		self.setWindowTitle("Set Info / Metadata")
		form = QFormLayout(self)
		self._name_e = QLineEdit(info.get("name", ""))
		self._src_e = QLineEdit(info.get("sourceLang", ""))
		self._tgt_e = QLineEdit(info.get("targetLang", ""))
		form.addRow("Glossary Name", self._name_e)
		form.addRow("Source Language", self._src_e)
		form.addRow("Target Language", self._tgt_e)
		buttons = QDialogButtonBox(
			QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
		)
		buttons.accepted.connect(self._ok)
		buttons.rejected.connect(self.reject)
		form.addRow(buttons)

	def _ok(self) -> None:
		if self._name_e.text().strip():
			self._info["name"] = self._name_e.text().strip()
		if self._src_e.text().strip():
			self._info["sourceLang"] = self._src_e.text().strip()
		if self._tgt_e.text().strip():
			self._info["targetLang"] = self._tgt_e.text().strip()
		self.accept()
