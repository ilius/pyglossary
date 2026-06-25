# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)

from __future__ import annotations

import ast
import logging
from typing import TYPE_CHECKING, Any, Protocol

import wx

from pyglossary.glossary_v2 import Glossary
from pyglossary.option import IntOption
from pyglossary.text_utils import escapeNTB, unescapeNTB

from .constants import PLUGIN_BY_DESC

if TYPE_CHECKING:
	from pyglossary.logger import Logger
	from pyglossary.option import Option

__all__ = [
	"FormatOptionsWxDialog",
	"OptionWxType",
	"format_pick_dialog",
]

log: Logger = logging.getLogger("pyglossary")


class OptionWxType(Protocol):
	def __init__(self, opt: Option, parent: wx.Window) -> None: ...

	@property
	def value(self) -> Any: ...

	@value.setter
	def value(self, x: Any) -> None: ...

	@property
	def widget(self) -> wx.Window: ...


class BoolOptionWx:
	def __init__(
		self,
		opt: Option,
		parent: wx.Window,  # noqa: ARG002
	) -> None:
		self._box = wx.CheckBox(parent, label=f"{opt.displayName} ({opt.comment})")

	@property
	def value(self) -> Any:
		return self._box.GetValue()

	@value.setter
	def value(self, x: Any) -> None:
		self._box.SetValue(bool(x))

	@property
	def widget(self) -> wx.Window:
		return self._box


class IntOptionWx:
	def __init__(
		self,
		opt: Option,
		parent: wx.Window,
	) -> None:
		assert isinstance(opt, IntOption)
		w = wx.Panel(parent)
		lay = wx.BoxSizer(wx.HORIZONTAL)
		minim = opt.minim if opt.minim is not None else 0
		maxim = opt.maxim if opt.maxim is not None else 1_000_000_000
		lay.Add(
			wx.StaticText(w, label=f"{opt.displayName}: "), 0, wx.ALIGN_CENTER_VERTICAL
		)
		self._spin = wx.SpinCtrl(
			w,
			min=int(minim),
			max=int(maxim),
			initial=int(minim),
		)
		lay.Add(self._spin, 0, wx.ALIGN_CENTER_VERTICAL)
		lay.Add(
			wx.StaticText(w, label=opt.comment), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 6
		)
		w.SetSizer(lay)
		self._widget = w

	@property
	def value(self) -> Any:
		return self._spin.GetValue()

	@value.setter
	def value(self, x: Any) -> None:
		self._spin.SetValue(int(x))

	@property
	def widget(self) -> wx.Window:
		return self._widget


class StrOptionWx:
	def __init__(
		self,
		opt: Option,
		parent: wx.Window,
	) -> None:
		self._opt = opt
		self._combo: wx.Choice | None = None
		self._widget = wx.Panel(parent)
		lay = wx.BoxSizer(wx.HORIZONTAL)
		lay.Add(
			wx.StaticText(self._widget, label=f"{opt.displayName} ({opt.comment}): "),
			0,
			wx.ALIGN_CENTER_VERTICAL,
		)
		self._edit = wx.TextCtrl(self._widget)
		lay.Add(self._edit, 1, wx.EXPAND)
		if opt.values:
			combo = wx.Choice(self._widget, choices=list(opt.values))
			combo.Bind(wx.EVT_CHOICE, self._on_combo)
			self._combo = combo
			lay.Add(combo, 0, wx.LEFT, 6)
		self._widget.SetSizer(lay)

	def _on_combo(self, evt: wx.CommandEvent) -> None:
		if self._combo is None:
			return
		self._edit.SetValue(self._combo.GetString(evt.GetSelection()))

	@property
	def value(self) -> Any:
		return self._opt.evaluate(self._edit.GetValue())[0]

	@value.setter
	def value(self, x: Any) -> None:
		s = str(x)
		self._edit.SetValue(s)
		if self._combo:
			idx = self._combo.FindString(s)
			if idx != wx.NOT_FOUND:
				self._combo.SetSelection(idx)

	@property
	def widget(self) -> wx.Window:
		return self._widget


class FileSizeOptionWx(StrOptionWx):
	pass


class HtmlColorOptionWx(StrOptionWx):
	pass


class MultiLineStrOptionWx:
	def __init__(
		self,
		opt: Option,
		parent: wx.Window,
	) -> None:
		self._widget = wx.Panel(parent)
		lay = wx.BoxSizer(wx.HORIZONTAL)
		lay.Add(
			wx.StaticText(
				self._widget,
				label=f"{opt.displayName}: {opt.comment} (escaped \\n\\t): ",
			),
			0,
			wx.ALIGN_CENTER_VERTICAL,
		)
		self._edit = wx.TextCtrl(self._widget)
		lay.Add(self._edit, 1, wx.EXPAND)
		self._widget.SetSizer(lay)

	@property
	def value(self) -> Any:
		return unescapeNTB(self._edit.GetValue())

	@value.setter
	def value(self, x: Any) -> None:
		self._edit.SetValue(escapeNTB(str(x)))

	@property
	def widget(self) -> wx.Window:
		return self._widget


class NewlineOptionWx(MultiLineStrOptionWx):
	pass


class LiteralEvalOptionWx:
	typeHint = ""

	def __init__(
		self,
		opt: Option,
		parent: wx.Window,
	) -> None:
		self._widget = wx.Panel(parent)
		lay = wx.BoxSizer(wx.HORIZONTAL)
		lay.Add(
			wx.StaticText(
				self._widget,
				label=f"{opt.displayName} ({opt.comment}, {self.typeHint}): ",
			),
			0,
			wx.ALIGN_CENTER_VERTICAL,
		)
		self._edit = wx.TextCtrl(self._widget)
		lay.Add(self._edit, 1, wx.EXPAND)
		self._widget.SetSizer(lay)

	@property
	def value(self) -> Any:
		return ast.literal_eval(self._edit.GetValue())

	@value.setter
	def value(self, x: Any) -> None:
		self._edit.SetValue(repr(x))

	@property
	def widget(self) -> wx.Window:
		return self._widget


class ListOptionWx(LiteralEvalOptionWx):
	typeHint = "Python list"


class DictOptionWx(LiteralEvalOptionWx):
	typeHint = "Python dict"


_OPTION_WX_MAP: dict[str, type] = {
	"BoolOption": BoolOptionWx,
	"IntOption": IntOptionWx,
	"StrOption": StrOptionWx,
	"EncodingOption": StrOptionWx,
	"FileSizeOption": FileSizeOptionWx,
	"UnicodeErrorsOption": StrOptionWx,
	"HtmlColorOption": HtmlColorOptionWx,
	"NewlineOption": NewlineOptionWx,
	"ListOption": ListOptionWx,
	"DictOption": DictOptionWx,
}


def format_pick_dialog(
	parent: wx.Window,
	title: str,
	items: list[str],
	current: str,
) -> str:
	d = wx.Dialog(parent, title=title, size=(520, 420))
	panel = wx.Panel(d)
	lay = wx.BoxSizer(wx.VERTICAL)
	search = wx.TextCtrl(panel)
	search.SetHint("Search…")
	listw = wx.ListBox(panel, choices=items, style=wx.LB_SINGLE)

	def filter_items(_evt: wx.CommandEvent) -> None:
		t = search.GetValue().lower().strip()
		filtered = [
			s for s in items if not t or t in s.lower() or s.lower().startswith(t)
		]
		listw.Set(filtered)
		if current in filtered:
			listw.SetSelection(filtered.index(current))

	search.Bind(wx.EVT_TEXT, filter_items)

	def on_dclick(_evt: wx.CommandEvent) -> None:
		d.EndModal(wx.ID_OK)

	listw.Bind(wx.EVT_LISTBOX_DCLICK, on_dclick)

	if current and current in items:
		listw.SetSelection(items.index(current))

	lay.Add(wx.StaticText(panel, label=title), 0, wx.ALL, 4)
	lay.Add(search, 0, wx.ALL | wx.EXPAND, 4)
	lay.Add(listw, 1, wx.ALL | wx.EXPAND, 4)

	btns = wx.StdDialogButtonSizer()
	ok_btn = wx.Button(panel, wx.ID_OK)
	cancel_btn = wx.Button(panel, wx.ID_CANCEL)
	btns.AddButton(ok_btn)
	btns.AddButton(cancel_btn)
	btns.Realize()
	lay.Add(btns, 0, wx.ALL | wx.EXPAND, 4)
	panel.SetSizer(lay)

	if d.ShowModal() == wx.ID_OK and listw.GetSelection() != wx.NOT_FOUND:
		return listw.GetString(listw.GetSelection())
	d.Destroy()
	return current


class FormatOptionsWxDialog(wx.Dialog):
	kind_formats_options = {
		"Read": Glossary.formatsReadOptions,
		"Write": Glossary.formatsWriteOptions,
	}

	def __init__(
		self,
		format_desc: str,
		kind: str,
		values: dict[str, Any],
		parent: wx.Window | None,
	) -> None:
		super().__init__(parent, size=(560, 360))
		format_name = PLUGIN_BY_DESC[format_desc].name
		self._values_ref = values
		self.format = format_name
		self.kind = kind
		self._widgets: dict[str, OptionWxType] = {}
		self.SetTitle(f"{format_desc} {kind} Options")

		panel = wx.Panel(self)
		outer = wx.BoxSizer(wx.VERTICAL)

		scroll = wx.ScrolledWindow(panel, style=wx.VSCROLL)
		scroll.SetScrollRate(0, 10)
		holder = wx.Panel(scroll)
		v = wx.BoxSizer(wx.VERTICAL)
		self.options_map = self.kind_formats_options[kind][format_name]
		options_prop = Glossary.plugins[format_name].optionsProp
		for opt_name, default in self.options_map.items():
			prop = options_prop[opt_name]
			wclass = _OPTION_WX_MAP.get(prop.__class__.__name__)
			if not wclass:
				log.warning(f"No wx widget class for option class {prop.__class__}")
				continue
			w = wclass(prop, holder)  # type: ignore[arg-type]
			try:
				w.value = values.get(opt_name, default)
			except (TypeError, ValueError):
				w.value = default
			v.Add(w.widget, 0, wx.ALL | wx.EXPAND, 4)
			self._widgets[opt_name] = w
		holder.SetSizer(v)
		scroll_sizer = wx.BoxSizer(wx.VERTICAL)
		scroll_sizer.Add(holder, 1, wx.EXPAND)
		scroll.SetSizer(scroll_sizer)
		scroll.FitInside()
		outer.Add(scroll, 1, wx.ALL | wx.EXPAND, 4)

		btns = wx.StdDialogButtonSizer()
		ok_btn = wx.Button(panel, wx.ID_OK)
		cancel_btn = wx.Button(panel, wx.ID_CANCEL)
		btns.AddButton(ok_btn)
		btns.AddButton(cancel_btn)
		btns.Realize()
		outer.Add(btns, 0, wx.ALL | wx.EXPAND, 4)
		panel.SetSizer(outer)
		self.Bind(wx.EVT_BUTTON, self._on_ok, ok_btn)

	def _on_ok(self, _evt: wx.CommandEvent) -> None:
		for opt_name, widget in self._widgets.items():
			self._values_ref[opt_name] = widget.value
		self.EndModal(wx.ID_OK)
