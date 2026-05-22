# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)

from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.ui.config import configDefDict

from .qt_imports import (
	QCheckBox,
	QComboBox,
	QDialog,
	QDialogButtonBox,
	QHBoxLayout,
	QLabel,
	QLineEdit,
	QVBoxLayout,
	QWidget,
)
from .sort_helpers import (
	SORT_KEY_DESC_BY_NAME,
	SORT_KEY_DESC_LIST,
	SORT_KEY_NAME_BY_DESC,
)

if TYPE_CHECKING:
	from .ui import UI


__all__ = ["GeneralOptionsQtDialog"]


class GeneralOptionsQtDialog(QDialog):
	def __init__(self, ui: UI, parent: QWidget | None) -> None:
		super().__init__(parent)
		self._ui = ui
		self.setWindowTitle("General Options")
		lay = QVBoxLayout(self)
		sort_row = QWidget()
		sr_lay = QHBoxLayout(sort_row)
		self._sort_check = QCheckBox("Sort entries by")
		self._sort_combo = QComboBox()
		self._sort_combo.addItems(SORT_KEY_DESC_LIST)
		sr_lay.addWidget(self._sort_check)
		sr_lay.addWidget(self._sort_combo)
		self._sort_check.toggled.connect(self._update_sort_controls)
		lay.addWidget(sort_row)

		enc_row = QWidget()
		er_lay = QHBoxLayout(enc_row)
		self._enc_check = QCheckBox("Sort Encoding")
		self._enc_edit = QLineEdit()
		self._enc_edit.setText("utf-8")
		self._enc_edit.setMaximumWidth(120)
		er_lay.addWidget(self._enc_check)
		er_lay.addWidget(self._enc_edit)
		lay.addWidget(enc_row)

		locale_row = QWidget()
		lr_lay = QHBoxLayout(locale_row)
		lr_lay.addWidget(QLabel("Sort Locale"))
		self._locale_e = QLineEdit()
		lr_lay.addWidget(self._locale_e)
		lay.addWidget(locale_row)

		self._sqlite_chk = QCheckBox("SQLite mode")
		lay.addWidget(self._sqlite_chk)

		self._cfg_checks: dict[str, QCheckBox] = {}
		self.config_params_defaults = {
			"save_info_json": False,
			"lower": False,
			"skip_resources": False,
			"rtl": False,
			"enable_alts": True,
			"cleanup": True,
			"remove_html_all": True,
		}
		for param in self.config_params_defaults:
			txt = configDefDict[param].comment.split("\n")[0]
			cb = QCheckBox(txt)
			self._cfg_checks[param] = cb
			lay.addWidget(cb)

		buttons = QDialogButtonBox(
			QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
		)
		buttons.accepted.connect(self._ok)
		buttons.rejected.connect(self.reject)
		lay.addWidget(buttons)
		self._load_from_ui()

	def _get_sqlite_allowed(self) -> bool:
		co = self._ui.convertOptions
		sqlite = co.get("sqlite")
		if sqlite is not None:
			return bool(sqlite)
		return bool(self._ui.config.get("auto_sqlite", True))

	def _update_sort_controls(self, on: bool) -> None:
		self._sort_combo.setEnabled(on)

	def _load_from_ui(self) -> None:
		co = self._ui.convertOptions
		sort = bool(co.get("sort", False))
		self._sort_check.setChecked(sort)
		self._sort_combo.setEnabled(sort)
		sort_key_name = co.get("sortKeyName", "")
		locale_txt = ""
		if sort_key_name and isinstance(sort_key_name, str):
			name_part, sep, locale_part = sort_key_name.partition(":")
			if sep:
				sort_key_name = name_part
				locale_txt = locale_part
		if sort_key_name and sort_key_name in SORT_KEY_DESC_BY_NAME:
			self._sort_combo.setCurrentText(SORT_KEY_DESC_BY_NAME[sort_key_name])
		self._locale_e.setText(locale_txt)
		self._sqlite_chk.setEnabled(self._get_sqlite_allowed())
		if "sortEncoding" in co:
			self._enc_check.setChecked(True)
			self._enc_edit.setText(co["sortEncoding"])
		else:
			self._enc_check.setChecked(False)
			self._enc_edit.setText("utf-8")
		cfg = self._ui.config
		for param, cb in self._cfg_checks.items():
			cb.setChecked(bool(cfg.get(param, self.config_params_defaults[param])))

	def _ok(self) -> None:
		co = self._ui.convertOptions
		cfg = self._ui.config
		co["sqlite"] = bool(self._sqlite_chk.isChecked())
		if self._sort_check.isChecked():
			desc = self._sort_combo.currentText()
			name = SORT_KEY_NAME_BY_DESC[desc]
			loc = self._locale_e.text().strip()
			if loc:
				name = f"{name}:{loc}"
			co["sort"] = True
			co["sortKeyName"] = name
			if self._enc_check.isChecked():
				co["sortEncoding"] = self._enc_edit.text().strip()
			elif "sortEncoding" in co:
				del co["sortEncoding"]
		else:
			for k in ("sort", "sortKeyName", "sortEncoding"):
				if k in co:
					del co[k]
		for param, cb in self._cfg_checks.items():
			cfg[param] = cb.isChecked()
		self.accept()
