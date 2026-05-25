# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# You can get a copy of GNU General Public License along this program
# But you can always get it from http://www.gnu.org/licenses/gpl.txt
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

from __future__ import annotations

__all__ = [
	"QAbstractItemView",
	"QApplication",
	"QCheckBox",
	"QComboBox",
	"QDialog",
	"QDialogButtonBox",
	"QFileDialog",
	"QFormLayout",
	"QGridLayout",
	"QHBoxLayout",
	"QIcon",
	"QKeySequence",
	"QLabel",
	"QLineEdit",
	"QListWidget",
	"QMainWindow",
	"QPixmap",
	"QPlainTextEdit",
	"QProgressBar",
	"QPushButton",
	"QScrollArea",
	"QShortcut",
	"QSizePolicy",
	"QSpinBox",
	"QStackedWidget",
	"QTabWidget",
	"QTextBrowser",
	"QVBoxLayout",
	"QWidget",
	"Qt",
]

try:
	from PySide6.QtCore import Qt
	from PySide6.QtGui import QIcon, QKeySequence, QPixmap, QShortcut
	from PySide6.QtWidgets import (
		QAbstractItemView,
		QApplication,
		QCheckBox,
		QComboBox,
		QDialog,
		QDialogButtonBox,
		QFileDialog,
		QFormLayout,
		QGridLayout,
		QHBoxLayout,
		QLabel,
		QLineEdit,
		QListWidget,
		QMainWindow,
		QPlainTextEdit,
		QProgressBar,
		QPushButton,
		QScrollArea,
		QSizePolicy,
		QSpinBox,
		QStackedWidget,
		QTabWidget,
		QTextBrowser,
		QVBoxLayout,
		QWidget,
	)

except ImportError:
	try:
		from PyQt6.QtCore import Qt
		from PyQt6.QtGui import QIcon, QKeySequence, QPixmap, QShortcut
		from PyQt6.QtWidgets import (
			QAbstractItemView,
			QApplication,
			QCheckBox,
			QComboBox,
			QDialog,
			QDialogButtonBox,
			QFileDialog,
			QFormLayout,
			QGridLayout,
			QHBoxLayout,
			QLabel,
			QLineEdit,
			QListWidget,
			QMainWindow,
			QPlainTextEdit,
			QProgressBar,
			QPushButton,
			QScrollArea,
			QSizePolicy,
			QSpinBox,
			QStackedWidget,
			QTabWidget,
			QTextBrowser,
			QVBoxLayout,
			QWidget,
		)

	except ImportError as err:  # pragma: no cover
		msg = "PyGlossary Qt 6 UI needs PySide6 or PyQt6 (install: pip install PySide6)."
		raise ImportError(msg) from err
