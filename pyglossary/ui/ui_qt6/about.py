# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)

from __future__ import annotations

from html import escape
from os.path import isabs, join

from pyglossary.core import appResDir, homePage
from pyglossary.ui.base import aboutText, authors, licenseText, logo
from pyglossary.ui.version import getVersion

from .qt_imports import (
	QDialog,
	QDialogButtonBox,
	QHBoxLayout,
	QIcon,
	QLabel,
	QPixmap,
	QPlainTextEdit,
	Qt,
	QTabWidget,
	QTextBrowser,
	QVBoxLayout,
	QWidget,
)

__all__ = ["exec_about_dialog"]


def _res_path(path: str) -> str:
	if not isabs(path):
		return join(appResDir, path)
	return path


def _set_tab_width(edit: QPlainTextEdit | QTextBrowser, width: int = 4) -> None:
	space = edit.fontMetrics().horizontalAdvance(" ")
	edit.setTabStopDistance(space * width)


def _new_readonly_text(text: str) -> QPlainTextEdit:
	edit = QPlainTextEdit()
	edit.setPlainText(text)
	edit.setReadOnly(True)
	_set_tab_width(edit)
	return edit


def _new_about_browser(text: str) -> QTextBrowser:
	browser = QTextBrowser()
	browser.setOpenExternalLinks(True)
	_set_tab_width(browser)
	html = escape(text).replace("\n", "<br>\n")
	html += f'<br><a href="{escape(homePage, quote=True)}">{escape(homePage)}</a>'
	browser.setHtml(html)
	return browser


class AboutQtDialog(QDialog):
	def __init__(self, parent: QWidget | None = None) -> None:
		super().__init__(parent)
		self.setWindowTitle("About PyGlossary")
		self.setMinimumSize(600, 550)

		layout = QVBoxLayout(self)
		layout.setSpacing(15)

		header = QHBoxLayout()
		header.setSpacing(20)
		logo_label = QLabel()
		logo_label.setPixmap(QPixmap(_res_path(logo)))
		header_label = QLabel(f"PyGlossary\nVersion {getVersion()}")
		header_label.setTextInteractionFlags(
			Qt.TextInteractionFlag.TextSelectableByMouse,
		)
		header.addWidget(logo_label)
		header.addWidget(header_label)
		header.addStretch()
		layout.addLayout(header)

		tabs = QTabWidget()
		tabs.addTab(
			_new_about_browser(aboutText),
			QIcon(_res_path("dialog-information-22.png")),
			"About",
		)
		tabs.addTab(
			_new_readonly_text("\n".join(authors)),
			QIcon(_res_path("author-22.png")),
			"Authors",
		)
		tabs.addTab(
			_new_readonly_text(licenseText),
			QIcon(_res_path("license-22.png")),
			"License",
		)
		layout.addWidget(tabs, 1)

		box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
		box.accepted.connect(self.accept)
		layout.addWidget(box)


def exec_about_dialog(parent: QWidget | None) -> None:
	AboutQtDialog(parent).exec()
