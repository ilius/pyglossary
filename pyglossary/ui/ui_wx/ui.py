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
from typing import TYPE_CHECKING, Any

import wx

from pyglossary.core import confDir, homeDir, sysName
from pyglossary.glossary_utils import Error
from pyglossary.glossary_v2 import ConvertArgs, Glossary
from pyglossary.os_utils import abspath2
from pyglossary.text_utils import urlToPath
from pyglossary.ui.base import UIBase, logo

from .about import exec_about_dialog
from .constants import (
	OUTPUT_DIR_CUSTOM,
	PATH_BTN_EMPTY,
	PLUGIN_BY_DESC,
	READ_DESC,
	WRITE_DESC,
)
from .format_widgets import FormatOptionsWxDialog, format_pick_dialog
from .general_options import GeneralOptionsWxDialog
from .info import PreConvertInfoWxDialog
from .log_handler import WxLogHandler
from .macos_icons import configure_macos_dock_icon

if TYPE_CHECKING:
	from collections.abc import Callable

	from pyglossary.config_type import ConfigType

__all__ = ["UI"]

log = logging.getLogger("pyglossary")


class _FileDropTarget(wx.FileDropTarget):
	def __init__(self, on_path: Callable[[str], None]) -> None:
		super().__init__()
		self._on_path = on_path

	def OnDropFiles(self, _x: int, _y: int, filenames: list[str]) -> bool:  # noqa: N802
		if filenames:
			self._on_path(filenames[0])
		return True


class _IoStepDropSurface(wx.Panel):
	"""Centers ``inner`` and accepts file drops on the full step area."""

	def __init__(
		self,
		parent: wx.Window,
		on_path: Callable[[str], None],
	) -> None:
		super().__init__(parent)
		self.inner = wx.Panel(self)
		outer = wx.BoxSizer(wx.VERTICAL)
		outer.AddStretchSpacer(1)
		mid = wx.BoxSizer(wx.HORIZONTAL)
		mid.AddStretchSpacer(1)
		mid.Add(self.inner, 0, wx.ALIGN_CENTER)
		mid.AddStretchSpacer(1)
		outer.Add(mid, 0, wx.EXPAND)
		outer.AddStretchSpacer(1)
		self.SetSizer(outer)
		self.SetDropTarget(_FileDropTarget(on_path))


class UI(UIBase):
	fcd_dir_save_path = join(confDir, "ui-tk-fcd-dir")

	def __init__(self, progressbar: bool = True) -> None:  # noqa: ARG002 — API parity
		UIBase.__init__(self)
		self._app = wx.App() if wx.GetApp() is None else wx.GetApp()

		logo_abs = ""
		if logo and Path(logo).is_file():
			logo_abs = logo
			if sys.platform == "darwin":
				configure_macos_dock_icon(logo_abs)

		self._base_title = "PyGlossary Wizard (wx)"
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

		self._frame = wx.Frame(None, title=self._base_title, size=(840, 480))
		if logo_abs:
			self._frame.SetIcon(wx.Icon(logo_abs, wx.BITMAP_TYPE_ANY))

		root = wx.BoxSizer(wx.VERTICAL)
		self._stack_host = wx.Panel(self._frame)
		self._stack_sizer = wx.BoxSizer(wx.VERTICAL)
		self._stack_host.SetSizer(self._stack_sizer)
		root.Add(self._stack_host, 1, wx.EXPAND)

		self._nav_bar_w = self._nav_bar(self._frame)
		root.Add(self._nav_bar_w, 0, wx.EXPAND)
		self._frame.SetSizer(root)
		self._nav_bar_w.SetDropTarget(_FileDropTarget(self._nav_bar_drop_path))

		self._page_input = self._build_page_input()
		self._page_output = self._build_page_output()
		self._page_formats = self._build_page_formats()
		self._page_convert = self._build_page_convert()
		self._pages = (
			self._page_input,
			self._page_output,
			self._page_formats,
			self._page_convert,
		)
		for pw in self._pages:
			self._stack_sizer.Add(pw, 1, wx.EXPAND)

		self._frame.Bind(wx.EVT_CHAR_HOOK, self._on_char_hook)

		self._wx_log_handler: WxLogHandler | None = None
		self._show_page(0)

	def _on_char_hook(self, event: wx.KeyEvent) -> None:
		if event.GetKeyCode() == wx.WXK_ESCAPE:
			self._frame.Close()
			return
		event.Skip()

	def _step_path_wrap_width(self) -> int:
		display = wx.Display(0)
		geom = display.GetClientArea()
		sw = geom.GetWidth() if geom.GetWidth() > 0 else 1024
		return min(520, max(280, sw - 160))

	def _center_step_host(
		self,
		parent: wx.Window,
		*,
		file_drop: Callable[[str], None] | None = None,
	) -> wx.Window | _IoStepDropSurface:
		if file_drop is not None:
			return _IoStepDropSurface(parent, file_drop)
		host = wx.Panel(parent)
		host.inner = wx.Panel(host)  # type: ignore[attr-defined]
		outer = wx.BoxSizer(wx.VERTICAL)
		outer.AddStretchSpacer(1)
		mid = wx.BoxSizer(wx.HORIZONTAL)
		mid.AddStretchSpacer(1)
		mid.Add(host.inner, 0, wx.ALIGN_CENTER)
		mid.AddStretchSpacer(1)
		outer.Add(mid, 0, wx.EXPAND)
		outer.AddStretchSpacer(1)
		host.SetSizer(outer)
		return host

	def _nav_bar(self, parent: wx.Window) -> wx.Panel:
		bar = wx.Panel(parent)
		h = wx.BoxSizer(wx.HORIZONTAL)
		self.about_btn = wx.Button(bar, label="About")
		self.about_btn.Bind(wx.EVT_BUTTON, lambda _e: exec_about_dialog(self._frame))
		h.Add(self.about_btn, 0, wx.ALL, 4)
		h.AddStretchSpacer(1)
		self.console_clear_btn = wx.Button(bar, label="Clear")
		self.console_clear_btn.Hide()
		self.console_clear_btn.Bind(wx.EVT_BUTTON, lambda _e: self._console_clear())
		h.Add(self.console_clear_btn, 0, wx.ALL, 4)
		self.prev_btn = wx.Button(bar, label="Previous")
		self.prev_btn.Bind(wx.EVT_BUTTON, lambda _e: self._prev_page())
		h.Add(self.prev_btn, 0, wx.ALL, 4)
		self.next_btn = wx.Button(bar, label="Next")
		self.next_btn.Bind(wx.EVT_BUTTON, lambda _e: self._next_clicked())
		h.Add(self.next_btn, 0, wx.ALL, 4)
		bar.SetSizer(h)
		return bar

	def _build_page_input(self) -> wx.Window:
		page = self._center_step_host(self._stack_host, file_drop=self._drop_input_path)
		panel = page.inner
		v = wx.BoxSizer(wx.VERTICAL)
		title = wx.StaticText(panel, label="Input File")
		font = title.GetFont()
		font.SetWeight(wx.FONTWEIGHT_BOLD)
		title.SetFont(font)
		v.Add(title, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM, 14)
		self.entry_input = wx.TextCtrl(panel)
		self.entry_input.Hide()
		self.entry_input.Bind(wx.EVT_TEXT, lambda _e: self._input_changed())
		self.input_path_btn = wx.Button(panel, label=PATH_BTN_EMPTY, size=(280, -1))
		self.input_path_btn.Bind(wx.EVT_BUTTON, lambda _e: self._browse_input())
		row = wx.BoxSizer(wx.HORIZONTAL)
		row.AddStretchSpacer(1)
		row.Add(self.input_path_btn, 0, wx.ALIGN_CENTER)
		row.AddStretchSpacer(1)
		v.Add(row, 0, wx.EXPAND)
		panel.SetSizer(v)
		return page

	def _build_page_output(self) -> wx.Window:
		page = self._center_step_host(self._stack_host, file_drop=self._drop_output_path)
		panel = page.inner
		main = wx.BoxSizer(wx.VERTICAL)
		t = wx.StaticText(panel, label="Output File")
		tf = t.GetFont()
		tf.SetWeight(wx.FONTWEIGHT_BOLD)
		t.SetFont(tf)
		main.Add(t, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM, 14)
		grid = wx.FlexGridSizer(cols=2, hgap=12, vgap=10)
		grid.AddGrowableCol(1, 1)
		ld = wx.StaticText(panel, label="Directory:")
		grid.Add(ld, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
		self.output_dir_combo = wx.Choice(panel)
		self.output_dir_combo.Bind(wx.EVT_CHOICE, self._on_output_dir_combo)
		grid.Add(self.output_dir_combo, 1, wx.EXPAND)
		lf = wx.StaticText(panel, label="File name:")
		grid.Add(lf, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
		self.entry_basename = wx.TextCtrl(panel)
		self.entry_basename.Bind(wx.EVT_TEXT, lambda _e: self._compose_output_full())
		grid.Add(self.entry_basename, 1, wx.EXPAND)
		main.Add(grid, 0, wx.EXPAND)
		self.entry_output = wx.TextCtrl(panel)
		self.entry_output.Bind(wx.EVT_TEXT, lambda _e: self._output_changed())
		self.entry_output.Hide()
		panel.SetSizer(main)
		return page

	def _build_page_formats(self) -> wx.Window:
		page = self._center_step_host(self._stack_host)
		panel = page.inner
		layout = wx.FlexGridSizer(cols=2, hgap=12, vgap=12)
		layout.AddGrowableCol(1, 1)
		wrap_w = self._step_path_wrap_width()

		def lbl_right(text: str) -> wx.StaticText:
			return wx.StaticText(panel, label=text)

		self.lbl_f_in = wx.StaticText(panel, label="", size=(wrap_w, -1))
		self.lbl_f_out = wx.StaticText(panel, label="", size=(wrap_w, -1))
		self.btn_pick_in = wx.Button(panel, label="[Select Input Format]")
		self.btn_pick_in.Bind(wx.EVT_BUTTON, lambda _e: self._pick_input_format_click())
		self.btn_pick_out = wx.Button(panel, label="[Select Output Format]")
		self.btn_pick_out.Bind(wx.EVT_BUTTON, lambda _e: self._pick_output_format_click())

		layout.Add(lbl_right("Input File:"), 0, wx.ALIGN_RIGHT | wx.ALIGN_TOP)
		layout.Add(self.lbl_f_in, 1, wx.EXPAND)
		layout.Add(lbl_right("Output File:"), 0, wx.ALIGN_RIGHT | wx.ALIGN_TOP)
		layout.Add(self.lbl_f_out, 1, wx.EXPAND)
		layout.Add(
			lbl_right("Input Format:"), 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL
		)
		layout.Add(self.btn_pick_in, 1, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
		layout.Add(
			lbl_right("Output Format:"), 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL
		)
		layout.Add(self.btn_pick_out, 1, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
		panel.SetSizer(layout)
		return page

	def _build_page_convert(self) -> wx.Window:
		w = wx.Panel(self._stack_host)
		layout = wx.BoxSizer(wx.VERTICAL)
		self.summary_lbl = wx.StaticText(w, label="")
		self.summary_lbl.Wrap(780)
		layout.Add(self.summary_lbl, 0, wx.ALL | wx.EXPAND, 4)
		btns = wx.BoxSizer(wx.HORIZONTAL)
		for lbl, handler in (
			("Read Options", self._read_opts_click),
			("Write Options", self._write_opts_click),
			("General Options", self._general_opts_click),
			("Info / Metadata", self._info_clicked),
		):
			b = wx.Button(w, label=lbl)
			b.Bind(wx.EVT_BUTTON, lambda _e, h=handler: h())
			btns.Add(b, 0, wx.RIGHT, 4)
		layout.Add(btns, 0, wx.ALL, 4)

		self.console = wx.TextCtrl(
			w,
			style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
			size=(-1, 260),
		)
		self.console.SetValue("Console:\n")
		layout.Add(self.console, 0, wx.ALL | wx.EXPAND, 4)

		self.pbar = wx.Gauge(w, range=100)
		self.pbar.Hide()
		layout.Add(self.pbar, 0, wx.ALL | wx.EXPAND, 4)
		self.pbar_label = wx.StaticText(w, label="")
		self.pbar_label.Hide()
		layout.Add(self.pbar_label, 0, wx.ALL, 4)
		w.SetSizer(layout)
		return w

	def _nav_bar_drop_path(self, path: str) -> None:
		idx = self.currentPage
		if idx not in {0, 1}:
			return
		p = abspath2(path)
		if not p.strip():
			return
		if idx == 0:
			self._drop_input_path(p)
		else:
			self._drop_output_path(p)

	def _drop_input_path(self, path: str) -> None:
		p = (path or "").strip()
		if not p:
			return
		p = abspath2(p)
		if not os.path.exists(p):
			return
		self.entry_input.ChangeValue(p)
		if os.path.isfile(p):
			self.fcd_dir = os.path.dirname(p)
		else:
			self.fcd_dir = self._norm_abs(p)
		self.save_fcd_dir()
		self._input_changed()

	def _drop_output_path(self, path: str) -> None:
		p = (path or "").strip()
		if not p:
			return
		p = abspath2(p)
		if not os.path.exists(p):
			return
		self.entry_output.ChangeValue(p)
		self.outputEntryChanged()

	def _browse_input(self) -> None:
		def norm(p: str) -> str:
			return os.path.normpath(os.path.abspath(p))

		dir_path = (self.fcd_dir or "").strip()
		if not dir_path or not os.path.isdir(dir_path):
			dir_path = norm(homeDir)

		selected_existing = ""

		cur = os.path.expanduser(self.entry_input.GetValue().strip())
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

		default_file = os.path.basename(selected_existing) if selected_existing else ""
		with wx.FileDialog(
			self._frame,
			"Open glossary",
			defaultDir=dir_path,
			defaultFile=default_file,
			wildcard="All files (*.*)|*.*",
			style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
		) as dlg:
			if dlg.ShowModal() != wx.ID_OK:
				return
			fn = dlg.GetPath()
		self.entry_input.ChangeValue(abspath2(fn))
		self.fcd_dir = os.path.dirname(abspath2(fn))
		self.save_fcd_dir()
		self._input_changed()

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
		inp = self.entry_input.GetValue().strip()
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
		self.output_dir_combo.Set(list(labels))

	def _apply_full_path_to_step(self) -> None:
		self._output_step_syncing = True
		try:
			full = self.entry_output.GetValue().strip()
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
				self._mount_output_combo(choices, labs + [OUTPUT_DIR_CUSTOM])
				self.output_dir_combo.SetSelection(idx)
				self.entry_basename.ChangeValue(base)
			else:
				labs = self._uniq_dir_labels(choices)
				self._mount_output_combo(choices, labs + [OUTPUT_DIR_CUSTOM])
				self.output_dir_combo.SetSelection(0)
				self.entry_basename.ChangeValue("")
			lbl = self.output_dir_combo.GetStringSelection()
			if lbl and lbl != OUTPUT_DIR_CUSTOM:
				self._last_valid_output_dir_label = lbl
		finally:
			self._output_step_syncing = False

	def _compose_output_full(self) -> None:
		if getattr(self, "_output_step_syncing", False):
			return
		t = self.output_dir_combo.GetStringSelection()
		if t == OUTPUT_DIR_CUSTOM:
			return
		d_abs = self._output_dir_abs_from_label(t)
		base = self.entry_basename.GetValue().strip()
		if d_abs and base:
			full = os.path.normpath(join(d_abs, base))
		elif base:
			full = os.path.normpath(base)
		else:
			full = ""
		if full:
			full = self._norm_abs(full)
		cur_txt = self.entry_output.GetValue().strip()
		cur = self._norm_abs(cur_txt) if cur_txt else ""
		if cur == full:
			self._refresh_summary_labels()
			return
		self.entry_output.ChangeValue(full)
		self.outputEntryChanged()

	def _browse_output_custom(self) -> None:
		prev = self._last_valid_output_dir_label
		cur_dir = ""
		if prev:
			cur_dir = self._output_dir_abs_from_label(prev)
		out_full = self.entry_output.GetValue().strip()
		if not cur_dir and out_full:
			cur_dir = self._norm_abs(os.path.dirname(os.path.abspath(out_full)))
		if not cur_dir:
			cur_dir = self.fcd_dir or self._default_out_dir()
		with wx.DirDialog(
			self._frame,
			"Output directory",
			defaultPath=cur_dir or homeDir,
		) as dlg:
			if dlg.ShowModal() != wx.ID_OK:
				self._output_step_syncing = True
				try:
					if prev:
						idx = self.output_dir_combo.FindString(prev)
						if idx != wx.NOT_FOUND:
							self.output_dir_combo.SetSelection(idx)
					else:
						self._apply_full_path_to_step()
				finally:
					self._output_step_syncing = False
				return
			path = dlg.GetPath()
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
			self.output_dir_combo.SetSelection(idx)
		finally:
			self._output_step_syncing = False
		self._last_valid_output_dir_label = labs[idx]
		self._compose_output_full()

	def _on_output_dir_combo(self, _evt: wx.CommandEvent) -> None:
		if getattr(self, "_output_step_syncing", False):
			return
		if self.output_dir_combo.GetStringSelection() == OUTPUT_DIR_CUSTOM:
			self._browse_output_custom()
			return
		lbl = self.output_dir_combo.GetStringSelection()
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

		self._wx_log_handler = WxLogHandler(self.console)
		self._wx_log_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
		log.addHandler(self._wx_log_handler)

		if inputFilename:
			self.entry_input.ChangeValue(abspath2(inputFilename))
			self._input_changed()
		if outputFilename:
			self.entry_output.ChangeValue(abspath2(outputFilename))
			self._output_changed()

		if inputFormat and inputFormat not in Glossary.readFormats:
			log.error(f"invalid {inputFormat=}")
			inputFormat = ""
		if outputFormat and outputFormat not in Glossary.writeFormats:
			log.error(f"invalid {outputFormat=}")
			outputFormat = ""

		if inputFormat:
			self._in_format_display = Glossary.plugins[inputFormat].description
			self.btn_pick_in.SetLabel(self._in_format_display or "[Select Input Format]")
			self._input_format_effect()
		if outputFormat:
			self._out_format_display = Glossary.plugins[outputFormat].description
			self.btn_pick_out.SetLabel(
				self._out_format_display or "[Select Output Format]"
			)
			self.outputFormatChangedAuto()

		if reverse:
			log.error("wx wizard interface does not support Reverse feature")

		if readOptions:
			self.readOptions = dict(readOptions)
		if writeOptions:
			self.writeOptions = dict(writeOptions)
		self.convertOptions = dict(convertOptions or {})
		if convertOptions:
			log.info(f"Using {convertOptions=!r}")

		self._glossarySetAttrs = glossarySetAttrs or {}
		if self.progressbar_enabled:
			self.pbar.Show()
			self.pbar_label.Show()
		self._refresh_summary_labels()
		self._frame.Show()
		self._frame.Raise()
		self._app.MainLoop()
		try:
			log.removeHandler(self._wx_log_handler)
		except ValueError:
			pass

	def _pick_input_format_click(self) -> None:
		got = format_pick_dialog(
			self._frame,
			"Select Input Format",
			READ_DESC,
			self._in_format_display,
		)
		self._set_in_display(got)
		self.btn_pick_in.SetLabel(got or "[Select Input Format]")
		self.input_format_changed(got)

	def _pick_output_format_click(self) -> None:
		got = format_pick_dialog(
			self._frame,
			"Select Output Format",
			WRITE_DESC,
			self._out_format_display,
		)
		self._set_out_display(got)
		self.btn_pick_out.SetLabel(got or "[Select Output Format]")
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
		path_i = self.entry_input.GetValue().strip()
		if path_i.startswith("file://"):
			path_i = urlToPath(path_i)
			self.entry_input.ChangeValue(path_i)
		if self.pathI == path_i:
			return

		self.pathI = path_i
		if path_i:
			btn_txt = Path(path_i).name
			if len(btn_txt) > 20:
				btn_txt = btn_txt[:10] + "…" + btn_txt[-10:]
			self.input_path_btn.SetLabel(btn_txt or PATH_BTN_EMPTY)

		desc = self._in_format_display
		if not desc and path_i and self.config.get("ui_autoSetFormat", False):
			try:
				detected = Glossary.detectInputFormat(path_i)
				pl = Glossary.plugins.get(detected.formatName)
				if pl:
					self._in_format_display = pl.description
					self.btn_pick_in.SetLabel(pl.description)
					self.input_format_changed(pl.description)
			except Error:
				pass

		self._maybe_refresh_empty_output_paths()
		self._refresh_summary_labels()

	def _maybe_refresh_empty_output_paths(self) -> None:
		if not self.entry_output.GetValue().strip():
			self._apply_full_path_to_step()

	def _output_changed(self) -> None:
		path_o = self.entry_output.GetValue().strip()
		if path_o.startswith("file://"):
			path_o = urlToPath(path_o)
			self.entry_output.ChangeValue(path_o)
		if self.pathO == path_o:
			self._refresh_summary_labels()
			return

		desc = self._out_format_display
		if not desc and path_o and self.config.get("ui_autoSetFormat", False):
			try:
				out_args = Glossary.detectOutputFormat(
					filename=path_o,
					inputFilename=self.entry_input.GetValue(),
				)
				self._out_format_display = Glossary.plugins[
					out_args.formatName
				].description
				self.btn_pick_out.SetLabel(self._out_format_display)
				self.output_format_changed(self._out_format_display)
			except Error:
				pass
			else:
				return

		self.pathO = self.entry_output.GetValue().strip()
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

		path_i = self.entry_input.GetValue().strip()
		if (
			path_i
			and not self.entry_output.GetValue().strip()
			and self._in_format_display
			and pl.extensionCreate
		):
			path_no_ext, _ext = splitext(path_i)
			self.entry_output.ChangeValue(path_no_ext + pl.extensionCreate)
		self.outputEntryChanged()

	def _read_opts_click(self) -> None:
		if not self._in_format_display:
			return
		dlg = FormatOptionsWxDialog(
			self._in_format_display,
			"Read",
			self.readOptions,
			self._frame,
		)
		dlg.ShowModal()
		dlg.Destroy()
		self._refresh_summary_labels()

	def _write_opts_click(self) -> None:
		if not self._out_format_display:
			return
		dlg = FormatOptionsWxDialog(
			self._out_format_display,
			"Write",
			self.writeOptions,
			self._frame,
		)
		dlg.ShowModal()
		dlg.Destroy()
		self._refresh_summary_labels()

	def _general_opts_click(self) -> None:
		dlg = GeneralOptionsWxDialog(self, self._frame)
		dlg.ShowModal()
		dlg.Destroy()
		self._refresh_summary_labels()

	def _info_clicked(self) -> None:
		dlg = PreConvertInfoWxDialog(self.infoOverride, self._frame)
		dlg.ShowModal()
		dlg.Destroy()
		self._refresh_summary_labels()

	def _pages_complete(self, page_ix: int | None = None) -> bool:
		idx = page_ix if page_ix is not None else self.currentPage
		if idx == 0:
			return bool(self.entry_input.GetValue().strip())
		if idx == 1:
			return bool(self.entry_output.GetValue().strip())
		if idx == 2:
			return (
				bool(self.entry_input.GetValue().strip())
				and bool(self.entry_output.GetValue().strip())
				and bool(self._in_format_display)
				and bool(self._out_format_display)
			)
		return (
			bool(self.entry_input.GetValue().strip())
			and bool(self.entry_output.GetValue().strip())
			and bool(self._out_format_display)
		)

	def _refresh_nav(self) -> None:
		step = self.currentPage + 1
		self._frame.SetTitle(f"{self._base_title} - Step {step}")
		self.prev_btn.Show(self.currentPage > 0)
		last = self.currentPage == len(self._pages) - 1
		self.console_clear_btn.Show(last)
		self.next_btn.SetLabel("Convert" if last else "Next")
		self.next_btn.Enable(self._pages_complete())
		self._nav_bar_w.Layout()

	def _show_page(self, index: int) -> None:
		self.currentPage = index
		for i, page in enumerate(self._pages):
			page.Show(i == index)
		self._stack_host.Layout()
		if index == 1:
			self._apply_full_path_to_step()
		self._refresh_summary_labels()

	def _refresh_summary_labels(self) -> None:
		in_path = self.entry_input.GetValue().strip()
		out_path = self.entry_output.GetValue().strip()
		in_fmt = self._in_format_display or "-"
		out_fmt = self._out_format_display or "-"
		self.lbl_f_in.SetLabel(Path(in_path or "-").name)
		self.lbl_f_out.SetLabel(Path(out_path or "-").name)
		self.summary_lbl.SetLabel(
			f'Converting {in_fmt} at "{in_path or "—"}" '
			f'to {out_fmt} at "{out_path or "—"}"',
		)
		self.summary_lbl.Wrap(780)
		self._refresh_nav()

	def _next_clicked(self) -> None:
		last = self.currentPage == len(self._pages) - 1
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
		self.console.SetValue("Console:\n")

	def convert(self) -> None:
		in_path = self.entry_input.GetValue().strip()
		if not in_path:
			log.critical("Input file path is empty!")
			return
		in_format_desc = self._in_format_display
		in_format = PLUGIN_BY_DESC[in_format_desc].name if in_format_desc else ""

		out_path = self.entry_output.GetValue().strip()
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
		self.pbar.SetValue(min(100, max(0, int(ratio * 100))))
		self.pbar_label.SetLabel(label)
		app = wx.GetApp()
		if app is not None:
			app.Yield(True)
