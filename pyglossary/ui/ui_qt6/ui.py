# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)

from __future__ import annotations

import logging
import os
import subprocess
import sys
from os.path import isfile, join, splitext
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from pyglossary.core import confDir, homeDir, sysName
from pyglossary.glossary_utils import Error
from pyglossary.glossary_v2 import ConvertArgs, Glossary
from pyglossary.os_utils import abspath2
from pyglossary.text_utils import urlToPath
from pyglossary.ui.base import UIBase, logo

from .about import exec_about_dialog
from .constants import (
	INPUT_FILE_DIALOG_USE_NON_NATIVE_QT,
	OUTPUT_DIR_CUSTOM,
	PATH_BTN_EMPTY,
	PLUGIN_BY_DESC,
	READ_DESC,
	WRITE_DESC,
)
from .format_widgets import FormatOptionsQtDialog, format_pick_dialog
from .general_options import GeneralOptionsQtDialog
from .info import PreConvertInfoQtDialog
from .log_handler import QtLogHandler
from .macos_icons import configure_macos_dock_icon
from .qt_imports import (
	QApplication,
	QComboBox,
	QDragEnterEvent,
	QDragMoveEvent,
	QDropEvent,
	QEvent,
	QFileDialog,
	QGridLayout,
	QHBoxLayout,
	QIcon,
	QKeySequence,
	QLabel,
	QLineEdit,
	QMainWindow,
	QObject,
	QPlainTextEdit,
	QProgressBar,
	QPushButton,
	QShortcut,
	QSizePolicy,
	QStackedWidget,
	Qt,
	QVBoxLayout,
	QWidget,
)

if TYPE_CHECKING:
	from collections.abc import Callable

	from pyglossary.config_type import ConfigType

__all__ = ["UI"]

log = logging.getLogger("pyglossary")


class _IoStepDropSurface(QWidget):
	"""Centers ``inner`` and accepts file URL drops on the full step area."""

	def __init__(self, inner: QWidget, on_path: Callable[[str], None]) -> None:
		super().__init__()
		self._on_path = on_path
		self.setAcceptDrops(True)
		outer = QVBoxLayout(self)
		outer.setContentsMargins(8, 4, 8, 4)
		outer.addStretch(1)
		mid = QHBoxLayout()
		mid.addStretch(1)
		mid.addWidget(inner, alignment=Qt.AlignmentFlag.AlignCenter)
		mid.addStretch(1)
		outer.addLayout(mid)
		outer.addStretch(1)

	def dragEnterEvent(self, e: QDragEnterEvent) -> None:
		if e.mimeData().hasUrls():
			e.acceptProposedAction()
		else:
			e.ignore()

	def dragMoveEvent(self, e: QDragMoveEvent) -> None:
		if e.mimeData().hasUrls():
			e.acceptProposedAction()
		else:
			e.ignore()

	def dropEvent(self, e: QDropEvent) -> None:
		urls = e.mimeData().urls()
		paths = [
			abspath2(u.toLocalFile())
			for u in urls
			if u.isLocalFile() and u.toLocalFile().strip()
		]
		if paths:
			self._on_path(paths[0])
			e.acceptProposedAction()
		else:
			e.ignore()


class _NavBarFileDropFilter(QObject):
	"""Accept drops on the nav bar while the input or output step is visible."""

	def __init__(self, ui: UI) -> None:
		super().__init__(ui._mw)
		self._ui = ui

	def eventFilter(self, _obj: QObject, event: QEvent) -> bool:  # noqa: N802
		t = event.type()
		if t not in {QEvent.Type.DragEnter, QEvent.Type.DragMove, QEvent.Type.Drop}:
			return False
		idx = self._ui.stack.currentIndex()
		if idx not in {0, 1}:
			return False
		if t == QEvent.Type.DragEnter:
			de = cast("QDragEnterEvent", event)
			if de.mimeData().hasUrls():
				de.acceptProposedAction()
				return True
			return False
		if t == QEvent.Type.DragMove:
			dm = cast("QDragMoveEvent", event)
			if dm.mimeData().hasUrls():
				dm.acceptProposedAction()
				return True
			return False
		dp = cast("QDropEvent", event)
		if not dp.mimeData().hasUrls():
			return False
		urls = dp.mimeData().urls()
		paths = [
			abspath2(u.toLocalFile())
			for u in urls
			if u.isLocalFile() and u.toLocalFile().strip()
		]
		if not paths:
			return False
		path = paths[0]
		if idx == 0:
			self._ui._drop_input_path(path)
		else:
			self._ui._drop_output_path(path)
		dp.acceptProposedAction()
		return True


class UI(UIBase):
	fcd_dir_save_path = join(confDir, "ui-tk-fcd-dir")

	def __init__(self, progressbar: bool = True) -> None:  # noqa: ARG002 — API parity
		UIBase.__init__(self)
		# Runner constructs UI before `run()`, so widgets must wait for QApplication.
		if QApplication.instance() is None:
			QApplication(sys.argv)

		self._qt_app_icon: QIcon | None = None
		logo_abs = ""
		if logo and Path(logo).is_file():
			logo_abs = logo
			self._qt_app_icon = QIcon(logo)
			app_inst = QApplication.instance()
			if app_inst:
				app_inst.setWindowIcon(self._qt_app_icon)
			if sys.platform == "darwin":
				configure_macos_dock_icon(logo_abs)

		self._base_title = "PyGlossary Wizard (Qt6)"
		self.progressbar_enabled = progressbar
		self._progress_title = ""
		self.infoOverride: dict[str, Any] = {}
		self.convertOptions: dict[str, Any] = {}
		self.readOptions: dict[str, Any] = {}
		self.writeOptions: dict[str, Any] = {}
		self.pathI = ""
		self.pathO = ""
		self.currentPage = 0
		self._glossarySetAttrs: dict[str, Any] = {}
		self._output_step_syncing = False
		self._last_valid_output_dir_label = ""

		fcd_dir = join(homeDir, "Desktop")
		if isfile(self.fcd_dir_save_path):
			try:
				with open(self.fcd_dir_save_path, encoding="utf-8") as fp:
					fcd_dir = fp.read().strip("\n")
			except OSError:
				log.exception("")
		self.fcd_dir = fcd_dir

		self._in_format_display = ""
		self._out_format_display = ""

		self._mw = QMainWindow()
		self._mw.setWindowTitle(self._base_title)
		if self._qt_app_icon is not None:
			self._mw.setWindowIcon(self._qt_app_icon)

		central = QWidget()
		self._mw.setCentralWidget(central)
		root = QVBoxLayout(central)
		self.stack = QStackedWidget()
		root.addWidget(self.stack, stretch=1)
		self._nav_bar_w = self._nav_bar()
		root.addWidget(self._nav_bar_w)
		self._nav_drop_filter = _NavBarFileDropFilter(self)
		self._nav_bar_w.setAcceptDrops(True)
		self._nav_bar_w.installEventFilter(self._nav_drop_filter)

		self._page_input = self._build_page_input()
		self._page_output = self._build_page_output()
		self._page_formats = self._build_page_formats()
		self._page_convert = self._build_page_convert()
		for pw in (
			self._page_input,
			self._page_output,
			self._page_formats,
			self._page_convert,
		):
			self.stack.addWidget(pw)

		esc_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self._mw)
		esc_shortcut.activated.connect(self._mw.close)

		self._qt_log_handler: QtLogHandler | None = None
		self._show_page(0)

	def _step_path_wrap_width(self) -> int:
		app = QApplication.instance()
		screen = app.primaryScreen() if app else None
		sw = screen.availableGeometry().width() if screen else 1024
		return min(520, max(280, sw - 160))

	def _center_step_host(
		self,
		inner: QWidget,
		*,
		file_drop: Callable[[str], None] | None = None,
	) -> QWidget:
		"""Center ``inner`` vertically and horizontally in the stacked page."""
		if file_drop is not None:
			return _IoStepDropSurface(inner, file_drop)
		host = QWidget()
		outer = QVBoxLayout(host)
		outer.setContentsMargins(8, 4, 8, 4)
		outer.addStretch(1)
		mid = QHBoxLayout()
		mid.addStretch(1)
		mid.addWidget(inner, alignment=Qt.AlignmentFlag.AlignCenter)
		mid.addStretch(1)
		outer.addLayout(mid)
		outer.addStretch(1)
		return host

	def _nav_bar(self) -> QWidget:
		bar = QWidget()
		h = QHBoxLayout(bar)
		self.about_btn = QPushButton("About")
		self.about_btn.clicked.connect(lambda: exec_about_dialog(self._mw))
		h.addWidget(self.about_btn)
		h.addStretch()
		self.console_clear_btn = QPushButton("Clear")
		self.console_clear_btn.hide()
		self.console_clear_btn.clicked.connect(self._console_clear)
		h.addWidget(self.console_clear_btn)
		self.prev_btn = QPushButton("Previous")
		self.prev_btn.clicked.connect(self._prev_page)
		h.addWidget(self.prev_btn)
		self.next_btn = QPushButton("Next")
		self.next_btn.clicked.connect(self._next_clicked)
		h.addWidget(self.next_btn)
		return bar

	def _build_page_input(self) -> QWidget:
		panel = QWidget()
		v = QVBoxLayout(panel)
		v.setSpacing(14)
		v.setContentsMargins(0, 0, 0, 0)
		title = QLabel("Input File")
		tf = title.font()
		tf.setBold(True)
		title.setFont(tf)
		title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
		v.addWidget(title)
		# Path lives in a hidden line edit (like Tk wizard); only the button is visible.
		self.entry_input = QLineEdit(panel)
		self.entry_input.hide()
		self.entry_input.textChanged.connect(self._input_changed)
		self.input_path_btn = QPushButton(PATH_BTN_EMPTY)
		self.input_path_btn.setMinimumWidth(280)
		self.input_path_btn.clicked.connect(self._browse_input)
		row = QHBoxLayout()
		row.addStretch(1)
		row.addWidget(self.input_path_btn)
		row.addStretch(1)
		v.addLayout(row)
		return self._center_step_host(panel, file_drop=self._drop_input_path)

	def _build_page_output(self) -> QWidget:
		panel = QWidget()
		main = QVBoxLayout(panel)
		main.setSpacing(14)
		main.setContentsMargins(0, 0, 0, 0)
		t = QLabel("Output File")
		tf = t.font()
		tf.setBold(True)
		t.setFont(tf)
		t.setAlignment(Qt.AlignmentFlag.AlignHCenter)
		main.addWidget(t)
		grid = QGridLayout()
		grid.setHorizontalSpacing(12)
		grid.setVerticalSpacing(10)
		ld = QLabel("Directory:")
		ld.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
		grid.addWidget(ld, 0, 0)
		self.output_dir_combo = QComboBox()
		self.output_dir_combo.currentIndexChanged.connect(self._on_output_dir_combo)
		grid.addWidget(self.output_dir_combo, 0, 1)
		lf = QLabel("File name:")
		lf.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
		grid.addWidget(lf, 1, 0)
		self.entry_basename = QLineEdit()
		self.entry_basename.textChanged.connect(lambda _t: self._compose_output_full())
		grid.addWidget(self.entry_basename, 1, 1)
		grid.setColumnStretch(1, 1)
		main.addLayout(grid)
		self.entry_output = QLineEdit(panel)
		self.entry_output.textChanged.connect(self._output_changed)
		self.entry_output.hide()
		return self._center_step_host(panel, file_drop=self._drop_output_path)

	def _build_page_formats(self) -> QWidget:
		panel = QWidget()
		layout = QGridLayout(panel)
		layout.setHorizontalSpacing(12)
		layout.setVerticalSpacing(12)
		wrap_w = self._step_path_wrap_width()

		def lbl_right(text: str) -> QLabel:
			lb = QLabel(text)
			lb.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
			return lb

		self.lbl_f_in = QLabel()
		self.lbl_f_in.setWordWrap(True)
		self.lbl_f_in.setMaximumWidth(wrap_w)
		self.lbl_f_in.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
		self.lbl_f_in.setSizePolicy(
			QSizePolicy.Policy.Preferred,
			QSizePolicy.Policy.Maximum,
		)
		self.lbl_f_out = QLabel()
		self.lbl_f_out.setWordWrap(True)
		self.lbl_f_out.setMaximumWidth(wrap_w)
		self.lbl_f_out.setAlignment(
			Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
		)
		self.lbl_f_out.setSizePolicy(
			QSizePolicy.Policy.Preferred,
			QSizePolicy.Policy.Maximum,
		)
		self.btn_pick_in = QPushButton("[Select Input Format]")
		self.btn_pick_in.clicked.connect(self._pick_input_format_click)
		self.btn_pick_out = QPushButton("[Select Output Format]")
		self.btn_pick_out.clicked.connect(self._pick_output_format_click)

		layout.addWidget(lbl_right("Input File:"), 0, 0)
		layout.addWidget(self.lbl_f_in, 0, 1, alignment=Qt.AlignmentFlag.AlignTop)
		layout.addWidget(lbl_right("Output File:"), 1, 0)
		layout.addWidget(self.lbl_f_out, 1, 1, alignment=Qt.AlignmentFlag.AlignTop)
		layout.addWidget(lbl_right("Input Format:"), 2, 0)
		layout.addWidget(
			self.btn_pick_in,
			2,
			1,
			alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
		)
		layout.addWidget(lbl_right("Output Format:"), 3, 0)
		layout.addWidget(
			self.btn_pick_out,
			3,
			1,
			alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
		)
		layout.setColumnStretch(1, 1)
		return self._center_step_host(panel)

	def _build_page_convert(self) -> QWidget:
		w = QWidget()
		layout = QVBoxLayout(w)
		self.summary_lbl = QLabel()
		self.summary_lbl.setWordWrap(True)
		layout.addWidget(self.summary_lbl)
		btns = QHBoxLayout()
		for lbl, handler in (
			("Read Options", self._read_opts_click),
			("Write Options", self._write_opts_click),
			("General Options", self._general_opts_click),
			("Info / Metadata", self._info_clicked),
		):
			b = QPushButton(lbl)
			b.clicked.connect(handler)
			btns.addWidget(b)
		layout.addLayout(btns)

		self.console = QPlainTextEdit()
		self.console.setReadOnly(True)
		self.console.setMaximumHeight(260)
		self.console.setPlainText("Console:\n")
		layout.addWidget(self.console)

		self.pbar = QProgressBar()
		self.pbar.setRange(0, 100)
		self.pbar.hide()
		layout.addWidget(self.pbar)
		return w

	def _drop_input_path(self, path: str) -> None:
		p = (path or "").strip()
		if not p:
			return
		p = abspath2(p)
		if not os.path.exists(p):
			return
		self.entry_input.setText(p)
		if os.path.isfile(p):
			self.fcd_dir = os.path.dirname(p)
		else:
			self.fcd_dir = self._norm_abs(p)
		self.save_fcd_dir()

	def _drop_output_path(self, path: str) -> None:
		p = (path or "").strip()
		if not p:
			return
		p = abspath2(p)
		if not os.path.exists(p):
			return
		self.entry_output.setText(p)

	def _browse_input(self) -> None:
		def norm(p: str) -> str:
			return os.path.normpath(os.path.abspath(p))

		dir_path = (self.fcd_dir or "").strip()
		if not dir_path or not os.path.isdir(dir_path):
			dir_path = norm(homeDir)

		selected_existing = ""

		cur = os.path.expanduser(self.entry_input.text().strip())
		if cur:
			ap = norm(abspath2(cur))
			if os.path.isfile(ap):
				selected_existing = ap
				d = os.path.dirname(ap)
				if d:
					dir_path = d
			elif os.path.isdir(ap):
				dir_path = ap
			else:
				parent = os.path.dirname(ap)
				if parent and os.path.isdir(parent):
					dir_path = parent

		dlg = QFileDialog(self._mw)
		dlg.setWindowTitle("Open glossary")
		dlg.setFileMode(QFileDialog.FileMode.ExistingFile)
		dlg.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
		# Native macOS panel often ignores selectFile; non-native honours it
		# (see INPUT_FILE_DIALOG_USE_NON_NATIVE_QT).
		dlg.setDirectory(dir_path)
		if selected_existing and INPUT_FILE_DIALOG_USE_NON_NATIVE_QT:
			dlg.setOption(QFileDialog.Option.DontUseNativeDialog, True)
			dlg.selectFile(selected_existing)

		if dlg.exec() != QFileDialog.DialogCode.Accepted:
			return
		sel = dlg.selectedFiles()
		if not sel:
			return
		fn = sel[0]
		self.entry_input.setText(abspath2(fn))
		self.fcd_dir = os.path.dirname(abspath2(fn))
		self.save_fcd_dir()

	def _xdg_user_dir(self, kind: str) -> str | None:
		if sysName not in {"linux", "freebsd"}:
			return None
		try:
			completed = subprocess.run(
				["xdg-user-dir", kind],
				capture_output=True,
				text=True,
				check=False,
				timeout=3,
			)
		except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
			return None
		path = (completed.stdout or "").strip()
		if not path or os.path.normpath(path) == os.path.normpath(homeDir):
			return None
		return os.path.normpath(os.path.abspath(path))

	def _downloads_dir(self) -> str:
		if sysName in {"linux", "freebsd"}:
			xdg = self._xdg_user_dir("DOWNLOAD")
			if xdg:
				return xdg
		return os.path.normpath(join(homeDir, "Downloads"))

	def _documents_dir(self) -> str:
		if sysName in {"linux", "freebsd"}:
			xdg = self._xdg_user_dir("DOCUMENTS")
			if xdg:
				return xdg
		return os.path.normpath(join(homeDir, "Documents"))

	def _norm_abs(self, path: str) -> str:
		return os.path.normpath(os.path.abspath(path))

	def _dir_menu_label(self, abs_path: str) -> str:
		path = self._norm_abs(abs_path)
		if sysName == "windows":
			stripped = path.rstrip("\\/")
			name = os.path.basename(stripped)
			return name or path
		h = self._norm_abs(homeDir)
		if path == h:
			return "~"
		try:
			rel = os.path.relpath(path, h)
		except ValueError:
			return path
		if rel.startswith(".."):
			return path
		if rel == ".":
			return "~"
		return "~/" + rel.replace(os.sep, "/")

	def _output_dir_abs_from_label(self, label: str) -> str:
		label = label.strip()
		if not label or label == OUTPUT_DIR_CUSTOM:
			return ""
		m = getattr(self, "_output_labels_map", {})
		if label in m:
			return self._norm_abs(m[label])
		if label == "~":
			return self._norm_abs(homeDir)
		if label.startswith("~/"):
			rest = label[2:].replace("/", os.sep)
			return self._norm_abs(join(homeDir, rest))
		return self._norm_abs(label)

	def _uniq_dir_labels(self, paths: list[str]) -> list[str]:
		seen: set[str] = set()
		out: list[str] = []
		for p in paths:
			lbl = self._dir_menu_label(p)
			if lbl in seen:
				lbl = self._norm_abs(p)
			seen.add(lbl)
			out.append(lbl)
		return out

	def _default_out_dir(self) -> str:
		inp = self.entry_input.text().strip()
		if inp:
			return self._norm_abs(os.path.dirname(os.path.abspath(inp)))
		return self._norm_abs(self.fcd_dir or homeDir)

	def _output_dir_candidates(self) -> list[str]:
		seen: set[str] = set()
		out: list[str] = []
		for cand in (
			self._default_out_dir(),
			self.fcd_dir,
			homeDir,
			join(homeDir, "Desktop"),
			self._downloads_dir(),
			self._documents_dir(),
			os.getcwd(),
		):
			if not cand:
				continue
			n = os.path.normpath(os.path.abspath(cand))
			if n not in seen:
				seen.add(n)
				out.append(n)
		return out

	def _mount_output_combo(
		self, abs_dirs: list[str], labels: list[str] | None = None
	) -> None:
		if labels is None:
			labels = self._uniq_dir_labels(abs_dirs) + [OUTPUT_DIR_CUSTOM]
		else:
			lbl_copy = list(labels)
			if OUTPUT_DIR_CUSTOM not in lbl_copy:
				lbl_copy.append(OUTPUT_DIR_CUSTOM)
			if len(lbl_copy) != len(abs_dirs) + 1:
				labels = self._uniq_dir_labels(abs_dirs) + [OUTPUT_DIR_CUSTOM]
			else:
				labels = lbl_copy

		first_n = labels[: len(abs_dirs)]
		self._output_labels_map = dict(zip(first_n, abs_dirs, strict=True))
		self.output_dir_combo.blockSignals(True)
		self.output_dir_combo.clear()
		for lbl in labels:
			self.output_dir_combo.addItem(lbl)
		self.output_dir_combo.blockSignals(False)

	def _apply_full_path_to_step(self) -> None:
		self._output_step_syncing = True
		try:
			full = self.entry_output.text().strip()
			choices = self._output_dir_candidates()
			if not choices:
				choices = [self._norm_abs(os.getcwd())]
			if full:
				d_abs = self._norm_abs(os.path.dirname(os.path.abspath(full)))
				base = os.path.basename(os.path.normpath(full))
				if d_abs not in choices:
					choices = [d_abs, *choices]
				labs = self._uniq_dir_labels(choices)
				idx = choices.index(d_abs)
				self.output_dir_combo.blockSignals(True)
				self._mount_output_combo(choices, labs + [OUTPUT_DIR_CUSTOM])
				self.output_dir_combo.setCurrentIndex(idx)
				self.output_dir_combo.blockSignals(False)
				self.entry_basename.setText(base)
			else:
				labs = self._uniq_dir_labels(choices)
				self.output_dir_combo.blockSignals(True)
				self._mount_output_combo(choices, labs + [OUTPUT_DIR_CUSTOM])
				self.output_dir_combo.setCurrentIndex(0)
				self.output_dir_combo.blockSignals(False)
				self.entry_basename.setText("")
			lbl = self.output_dir_combo.currentText()
			if lbl and lbl != OUTPUT_DIR_CUSTOM:
				self._last_valid_output_dir_label = lbl
		finally:
			self._output_step_syncing = False

	def _compose_output_full(self) -> None:
		if getattr(self, "_output_step_syncing", False):
			return
		t = self.output_dir_combo.currentText()
		if t == OUTPUT_DIR_CUSTOM:
			return
		d_abs = self._output_dir_abs_from_label(t)
		base = self.entry_basename.text().strip()
		if d_abs and base:
			full = os.path.normpath(join(d_abs, base))
		elif base:
			full = os.path.normpath(base)
		else:
			full = ""
		if full:
			full = self._norm_abs(full)
		cur_txt = self.entry_output.text().strip()
		cur = self._norm_abs(cur_txt) if cur_txt else ""
		if cur == full:
			self._refresh_summary_labels()
			return
		self.entry_output.blockSignals(True)
		self.entry_output.setText(full)
		self.entry_output.blockSignals(False)
		self.outputEntryChanged()

	def _browse_output_custom(self) -> None:
		prev = self._last_valid_output_dir_label
		cur_dir = ""
		if prev:
			cur_dir = self._output_dir_abs_from_label(prev)
		out_full = self.entry_output.text().strip()
		if not cur_dir and out_full:
			cur_dir = self._norm_abs(os.path.dirname(os.path.abspath(out_full)))
		if not cur_dir:
			cur_dir = self.fcd_dir or self._default_out_dir()
		path = QFileDialog.getExistingDirectory(
			self._mw,
			"Output directory",
			cur_dir or homeDir,
		)
		if not path:
			self._output_step_syncing = True
			try:
				if prev:
					idx = self.output_dir_combo.findText(prev)
					if idx >= 0:
						self.output_dir_combo.setCurrentIndex(idx)
				else:
					self._apply_full_path_to_step()
			finally:
				self._output_step_syncing = False
			return
		norm = self._norm_abs(path)
		self.fcd_dir = norm
		self.save_fcd_dir()
		choices = self._output_dir_candidates()
		if norm not in choices:
			choices = [norm] + choices
		labs = self._uniq_dir_labels(choices)
		idx = choices.index(norm)
		self._output_step_syncing = True
		try:
			self._mount_output_combo(choices, labs + [OUTPUT_DIR_CUSTOM])
			self.output_dir_combo.setCurrentIndex(idx)
		finally:
			self._output_step_syncing = False
		self._last_valid_output_dir_label = labs[idx]
		self._compose_output_full()

	def _on_output_dir_combo(self, _idx: int) -> None:
		if getattr(self, "_output_step_syncing", False):
			return
		if self.output_dir_combo.currentText() == OUTPUT_DIR_CUSTOM:
			self._browse_output_custom()
			return
		lbl = self.output_dir_combo.currentText()
		if lbl:
			self._last_valid_output_dir_label = lbl
		self._compose_output_full()

	def save_fcd_dir(self) -> None:
		if not self.fcd_dir:
			return
		try:
			with open(self.fcd_dir_save_path, mode="w", encoding="utf-8") as fp:
				fp.write(self.fcd_dir)
		except OSError:
			log.exception("")

	def run(  # noqa: PLR0913
		self,
		inputFilename: str = "",
		outputFilename: str = "",
		inputFormat: str = "",
		outputFormat: str = "",
		reverse: bool = False,
		config: ConfigType | None = None,
		readOptions: dict[str, Any] | None = None,
		writeOptions: dict[str, Any] | None = None,
		convertOptions: dict[str, Any] | None = None,
		glossarySetAttrs: dict[str, Any] | None = None,
	) -> None:
		conf = dict(config or {})
		self.loadConfig(**conf)
		self.config = conf
		app = QApplication.instance()
		if app is None:
			app = QApplication(sys.argv)
		self._mw.resize(840, 480)
		self._mw.show()

		self._qt_log_handler = QtLogHandler(self.console)
		self._qt_log_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
		log.addHandler(self._qt_log_handler)

		if inputFilename:
			self.entry_input.setText(abspath2(inputFilename))
			self._input_changed()
		if outputFilename:
			self.entry_output.setText(abspath2(outputFilename))
			self._output_changed()

		if inputFormat and inputFormat not in Glossary.readFormats:
			log.error(f"invalid {inputFormat=}")
			inputFormat = ""
		if outputFormat and outputFormat not in Glossary.writeFormats:
			log.error(f"invalid {outputFormat=}")
			outputFormat = ""

		if inputFormat:
			self._in_format_display = Glossary.plugins[inputFormat].description
			self.btn_pick_in.setText(self._in_format_display or "[Select Input Format]")
			self._input_format_effect()
		if outputFormat:
			self._out_format_display = Glossary.plugins[outputFormat].description
			self.btn_pick_out.setText(
				self._out_format_display or "[Select Output Format]"
			)
			self.outputFormatChangedAuto()

		if reverse:
			log.error("Qt6 wizard interface does not support Reverse feature")

		if readOptions:
			self.readOptions = dict(readOptions)
		if writeOptions:
			self.writeOptions = dict(writeOptions)
		self.convertOptions = dict(convertOptions or {})
		if convertOptions:
			log.info(f"Using {convertOptions=!r}")

		self._glossarySetAttrs = glossarySetAttrs or {}
		if self.progressbar_enabled:
			self.pbar.show()
		self._refresh_summary_labels()
		self._mw.raise_()

		app.exec()
		try:
			log.removeHandler(self._qt_log_handler)
		except ValueError:
			pass

	def _pick_input_format_click(self) -> None:
		got = format_pick_dialog(
			self._mw,
			"Select Input Format",
			READ_DESC,
			self._in_format_display,
		)
		self._set_in_display(got)
		self.btn_pick_in.setText(got or "[Select Input Format]")
		self.input_format_changed(got)

	def _pick_output_format_click(self) -> None:
		got = format_pick_dialog(
			self._mw,
			"Select Output Format",
			WRITE_DESC,
			self._out_format_display,
		)
		self._set_out_display(got)
		self.btn_pick_out.setText(got or "[Select Output Format]")
		self.output_format_changed(got)

	def _set_in_display(self, desc: str) -> None:
		self._in_format_display = desc

	def _set_out_display(self, desc: str) -> None:
		self._out_format_display = desc

	def _input_format_effect(self) -> None:
		if self._in_format_display:
			self.input_format_changed(self._in_format_display)

	def inputFormatChangedAuto(self) -> None:
		self.input_format_changed(self._in_format_display)

	def outputFormatChangedAuto(self) -> None:
		self.output_format_changed(self._out_format_display)

	def _input_changed(self) -> None:
		path_i = self.entry_input.text().strip()
		if path_i.startswith("file://"):
			path_i = urlToPath(path_i)
			self.entry_input.blockSignals(True)
			self.entry_input.setText(path_i)
			self.entry_input.blockSignals(False)
		if self.pathI == path_i:
			return

		self.pathI = path_i
		if path_i:
			btn_txt = Path(path_i).name
			if len(btn_txt) > 20:
				btn_txt = btn_txt[:10] + "…" + btn_txt[-10:]
			self.input_path_btn.setText(btn_txt or PATH_BTN_EMPTY)

		desc = self._in_format_display
		if not desc and path_i and self.config.get("ui_autoSetFormat", False):
			try:
				detected = Glossary.detectInputFormat(path_i)
				pl = Glossary.plugins.get(detected.formatName)
				if pl:
					self._in_format_display = pl.description
					self.btn_pick_in.setText(pl.description)
					self.input_format_changed(pl.description)
			except Error:
				pass

		self._maybe_refresh_empty_output_paths()
		self._refresh_summary_labels()

	def _maybe_refresh_empty_output_paths(self) -> None:
		if not self.entry_output.text().strip():
			self._apply_full_path_to_step()

	def _output_changed(self) -> None:
		path_o = self.entry_output.text().strip()
		if path_o.startswith("file://"):
			path_o = urlToPath(path_o)
			self.entry_output.blockSignals(True)
			self.entry_output.setText(path_o)
			self.entry_output.blockSignals(False)
		if self.pathO == path_o:
			self._refresh_summary_labels()
			return

		desc = self._out_format_display
		if not desc and path_o and self.config.get("ui_autoSetFormat", False):
			try:
				out_args = Glossary.detectOutputFormat(
					filename=path_o,
					inputFilename=self.entry_input.text(),
				)
				self._out_format_display = Glossary.plugins[
					out_args.formatName
				].description
				self.btn_pick_out.setText(self._out_format_display)
				self.output_format_changed(self._out_format_display)
			except Error:
				pass
			else:
				return

		self.pathO = self.entry_output.text().strip()
		self._apply_full_path_to_step()
		self._refresh_summary_labels()

	def outputEntryChanged(self) -> None:
		self.pathO = ""
		self._output_changed()

	def input_format_changed(self, format_desc: str) -> None:
		if not format_desc:
			return
		self.readOptions.clear()

	def output_format_changed(self, format_desc: str) -> None:
		if not format_desc:
			return
		pl = PLUGIN_BY_DESC[format_desc]
		format_name = pl.name
		if format_name not in Glossary.plugins:
			log.error(f"plugin {format_name} not found")
			return
		self.writeOptions.clear()

		path_i = self.entry_input.text().strip()
		if (
			path_i
			and not self.entry_output.text().strip()
			and self._in_format_display
			and pl.extensionCreate
		):
			path_no_ext, _ext = splitext(path_i)
			self.entry_output.setText(path_no_ext + pl.extensionCreate)
		self.outputEntryChanged()

	def _read_opts_click(self) -> None:
		if not self._in_format_display:
			return
		dlg = FormatOptionsQtDialog(
			self._in_format_display,
			"Read",
			self.readOptions,
			self._mw,
		)
		dlg.exec()
		self._refresh_summary_labels()

	def _write_opts_click(self) -> None:
		if not self._out_format_display:
			return
		dlg = FormatOptionsQtDialog(
			self._out_format_display,
			"Write",
			self.writeOptions,
			self._mw,
		)
		dlg.exec()
		self._refresh_summary_labels()

	def _general_opts_click(self) -> None:
		dlg = GeneralOptionsQtDialog(self, self._mw)
		dlg.exec()
		self._refresh_summary_labels()

	def _info_clicked(self) -> None:
		dlg = PreConvertInfoQtDialog(self.infoOverride, self._mw)
		dlg.exec()
		self._refresh_summary_labels()

	def _pages_complete(self, page_ix: int | None = None) -> bool:
		idx = page_ix if page_ix is not None else self.currentPage
		if idx == 0:
			return bool(self.entry_input.text().strip())
		if idx == 1:
			return bool(self.entry_output.text().strip())
		if idx == 2:
			return (
				bool(self.entry_input.text().strip())
				and bool(self.entry_output.text().strip())
				and bool(self._in_format_display)
				and bool(self._out_format_display)
			)
		return (
			bool(self.entry_input.text().strip())
			and bool(self.entry_output.text().strip())
			and bool(self._out_format_display)
		)

	def _refresh_nav(self) -> None:
		step = self.currentPage + 1
		self._mw.setWindowTitle(f"{self._base_title} - Step {step}")
		self.prev_btn.setVisible(self.currentPage > 0)
		last = self.currentPage == self.stack.count() - 1
		self.console_clear_btn.setVisible(last)
		self.next_btn.setText("Convert" if last else "Next")
		self.next_btn.setEnabled(self._pages_complete())

	def _show_page(self, index: int) -> None:
		self.currentPage = index
		self.stack.setCurrentIndex(index)
		if index == 1:
			self._apply_full_path_to_step()
		self._refresh_summary_labels()

	def _refresh_summary_labels(self) -> None:
		in_path = self.entry_input.text().strip()
		out_path = self.entry_output.text().strip()
		in_fmt = self._in_format_display or "-"
		out_fmt = self._out_format_display or "-"
		self.lbl_f_in.setText(Path(in_path or "-").name)
		self.lbl_f_out.setText(Path(out_path or "-").name)
		self.summary_lbl.setText(
			f'Converting {in_fmt} at "{in_path or "—"}" '
			f'to {out_fmt} at "{out_path or "—"}"',
		)
		self._refresh_nav()

	def _next_clicked(self) -> None:
		last = self.currentPage == self.stack.count() - 1
		if last:
			self.convert()
		else:
			self.any_entry_changed()
			self._show_page(self.currentPage + 1)

	def _prev_page(self) -> None:
		if self.currentPage > 0:
			self.any_entry_changed()
			self._show_page(self.currentPage - 1)

	def any_entry_changed(self) -> None:
		self._input_changed()
		self._output_changed()

	def _console_clear(self) -> None:
		self.console.setPlainText("Console:\n")

	def convert(self) -> None:
		in_path = self.entry_input.text().strip()
		if not in_path:
			log.critical("Input file path is empty!")
			return
		in_format_desc = self._in_format_display
		in_format = PLUGIN_BY_DESC[in_format_desc].name if in_format_desc else ""

		out_path = self.entry_output.text().strip()
		if not out_path:
			log.critical("Output file path is empty!")
			return
		out_format_desc = self._out_format_display
		if not out_format_desc:
			log.critical("Output format is empty!")
			return
		out_format = PLUGIN_BY_DESC[out_format_desc].name

		log.debug(f"config: {self.config}")

		glos = Glossary(ui=self)
		glos.config = self.config
		glos.progressbar = self.progressbar_enabled

		for attr, value in self._glossarySetAttrs.items():
			setattr(glos, attr, value)

		if self.infoOverride:
			log.info(f"infoOverride = {self.infoOverride}")

		if self.convertOptions:
			log.info(f"convertOptions: {self.convertOptions}")

		try:
			glos.convert(
				ConvertArgs(
					in_path,
					inputFormat=in_format,
					outputFilename=out_path,
					outputFormat=out_format,
					readOptions=self.readOptions,
					writeOptions=self.writeOptions,
					infoOverride=self.infoOverride or None,
					**self.convertOptions,
				),
			)
		except Error as e:
			log.critical(str(e))
			glos.cleanup()
			return

	def progressInit(self, title: str) -> None:
		self._progress_title = title

	def progress(self, ratio: float, text: str = "") -> None:
		if not text:
			text = "%" + str(int(ratio * 100))
		title = self._progress_title
		if (ratio >= 1.0 or int(ratio * 100) >= 100) and title == "Converting":
			title = "Done"
		label = f"{text} - {title}" if title else text
		self.pbar.setValue(min(100, max(0, int(ratio * 100))))
		self.pbar.setFormat(label)
		app = QApplication.instance()
		if app is not None:
			app.processEvents()
