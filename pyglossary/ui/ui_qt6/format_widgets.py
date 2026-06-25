# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)

from __future__ import annotations

import ast
import logging
from typing import TYPE_CHECKING, Any, Protocol

from pyglossary.glossary_v2 import Glossary
from pyglossary.option import IntOption
from pyglossary.text_utils import escapeNTB, unescapeNTB

from .constants import PLUGIN_BY_DESC
from .qt_imports import (
	QAbstractItemView,
	QCheckBox,
	QComboBox,
	QDialog,
	QDialogButtonBox,
	QHBoxLayout,
	QLabel,
	QLineEdit,
	QListWidget,
	QScrollArea,
	QSpinBox,
	QVBoxLayout,
	QWidget,
)

if TYPE_CHECKING:
	from pyglossary.logger import Logger
	from pyglossary.option import Option

__all__ = [
	"FormatOptionsQtDialog",
	"OptionQtType",
	"format_pick_dialog",
]


log: Logger = logging.getLogger("pyglossary")


class OptionQtType(Protocol):
	def __init__(self, opt: Option, parent: QWidget) -> None: ...

	@property
	def value(self) -> Any: ...

	@value.setter
	def value(self, x: Any) -> None: ...

	@property
	def widget(self) -> QWidget: ...


class BoolOptionQt:
	def __init__(
		self,
		opt: Option,
		parent: QWidget,  # noqa: ARG002
	) -> None:
		self._box = QCheckBox(f"{opt.displayName} ({opt.comment})")

	@property
	def value(self) -> Any:
		return self._box.isChecked()

	@value.setter
	def value(self, x: Any) -> None:
		self._box.setChecked(bool(x))

	@property
	def widget(self) -> QWidget:
		return self._box


class IntOptionQt:
	def __init__(
		self,
		opt: Option,
		parent: QWidget,  # noqa: ARG002
	) -> None:
		assert isinstance(opt, IntOption)
		w = QWidget()
		lay = QHBoxLayout(w)
		minim = opt.minim if opt.minim is not None else 0
		maxim = opt.maxim if opt.maxim is not None else 1_000_000_000
		lay.addWidget(QLabel(f"{opt.displayName}: "))
		self._spin = QSpinBox()
		self._spin.setRange(int(minim), int(maxim))
		lay.addWidget(self._spin)
		lay.addWidget(QLabel(opt.comment))
		self._widget = w

	@property
	def value(self) -> Any:
		return self._spin.value()

	@value.setter
	def value(self, x: Any) -> None:
		self._spin.setValue(int(x))

	@property
	def widget(self) -> QWidget:
		return self._widget


class StrOptionQt:
	def __init__(
		self,
		opt: Option,
		parent: QWidget,  # noqa: ARG002
	) -> None:
		self._opt = opt
		self._combo: QComboBox | None = None
		self._widget = QWidget()
		lay = QHBoxLayout(self._widget)
		lay.addWidget(QLabel(f"{opt.displayName} ({opt.comment}): "))
		self._edit = QLineEdit()
		lay.addWidget(self._edit, stretch=1)
		if opt.values:
			combo = QComboBox()
			combo.addItems(list(opt.values))
			combo.currentTextChanged.connect(self._edit.setText)
			self._combo = combo
			lay.addWidget(combo)

	@property
	def value(self) -> Any:
		return self._opt.evaluate(self._edit.text())[0]

	@value.setter
	def value(self, x: Any) -> None:
		s = str(x)
		self._edit.setText(s)
		if self._combo:
			idx = self._combo.findText(s)
			if idx >= 0:
				self._combo.setCurrentIndex(idx)

	@property
	def widget(self) -> QWidget:
		return self._widget


class FileSizeOptionQt(StrOptionQt):
	pass


class HtmlColorOptionQt(StrOptionQt):
	pass


class MultiLineStrOptionQt:
	def __init__(
		self,
		opt: Option,
		parent: QWidget,  # noqa: ARG002
	) -> None:
		self._widget = QWidget()
		lay = QHBoxLayout(self._widget)
		lay.addWidget(QLabel(f"{opt.displayName}: {opt.comment} (escaped \\n\\t): "))
		self._edit = QLineEdit()
		lay.addWidget(self._edit, stretch=1)

	@property
	def value(self) -> Any:
		return unescapeNTB(self._edit.text())

	@value.setter
	def value(self, x: Any) -> None:
		self._edit.setText(escapeNTB(str(x)))

	@property
	def widget(self) -> QWidget:
		return self._widget


class NewlineOptionQt(MultiLineStrOptionQt):
	pass


class LiteralEvalOptionQt:
	typeHint = ""

	def __init__(
		self,
		opt: Option,
		parent: QWidget,  # noqa: ARG002
	) -> None:
		self._widget = QWidget()
		lay = QHBoxLayout(self._widget)
		lay.addWidget(
			QLabel(f"{opt.displayName} ({opt.comment}, {self.typeHint}): "),
		)
		self._edit = QLineEdit()
		lay.addWidget(self._edit, stretch=1)

	@property
	def value(self) -> Any:
		return ast.literal_eval(self._edit.text())

	@value.setter
	def value(self, x: Any) -> None:
		self._edit.setText(repr(x))

	@property
	def widget(self) -> QWidget:
		return self._widget


class ListOptionQt(LiteralEvalOptionQt):
	typeHint = "Python list"


class DictOptionQt(LiteralEvalOptionQt):
	typeHint = "Python dict"


_OPTION_QT_MAP: dict[str, type] = {
	"BoolOption": BoolOptionQt,
	"IntOption": IntOptionQt,
	"StrOption": StrOptionQt,
	"EncodingOption": StrOptionQt,
	"FileSizeOption": FileSizeOptionQt,
	"UnicodeErrorsOption": StrOptionQt,
	"HtmlColorOption": HtmlColorOptionQt,
	"NewlineOption": NewlineOptionQt,
	"ListOption": ListOptionQt,
	"DictOption": DictOptionQt,
}


def format_pick_dialog(
	parent: QWidget,
	title: str,
	items: list[str],
	current: str,
) -> str:
	d = QDialog(parent)
	d.setWindowTitle(title)
	lay = QVBoxLayout(d)
	search = QLineEdit()
	search.setPlaceholderText("Search…")
	listw = QListWidget()
	listw.addItems(items)
	listw.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
	listw.itemDoubleClicked.connect(d.accept)

	def filter_items(text: str) -> None:
		t = text.lower().strip()
		for i in range(listw.count()):
			it = listw.item(i)
			s = it.text().lower()
			it.setHidden(bool(t and t not in s and not s.startswith(t)))

	search.textChanged.connect(filter_items)

	if current and current in items:
		idx = items.index(current)
		listw.setCurrentRow(idx)
		listw.scrollToItem(listw.item(idx))

	lay.addWidget(QLabel(title))
	lay.addWidget(search)
	lay.addWidget(listw)

	buttons = QDialogButtonBox(
		QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
	)
	buttons.accepted.connect(d.accept)
	buttons.rejected.connect(d.reject)
	lay.addWidget(buttons)
	search.setFocus()

	if d.exec() == QDialog.DialogCode.Accepted and listw.currentItem():
		return listw.currentItem().text()
	return current


class FormatOptionsQtDialog(QDialog):
	kind_formats_options = {
		"Read": Glossary.formatsReadOptions,
		"Write": Glossary.formatsWriteOptions,
	}

	def __init__(
		self,
		format_desc: str,
		kind: str,
		values: dict[str, Any],
		parent: QWidget | None,
	) -> None:
		super().__init__(parent)
		format_name = PLUGIN_BY_DESC[format_desc].name
		self._values_ref = values
		self.format = format_name
		self.kind = kind
		self._widgets: dict[str, OptionQtType] = {}
		self.setWindowTitle(f"{format_desc} {kind} Options")
		self.resize(560, 360)

		scroll = QScrollArea()
		scroll.setWidgetResizable(True)
		holder = QWidget()
		v = QVBoxLayout(holder)
		self.options_map = self.kind_formats_options[kind][format_name]
		options_prop = Glossary.plugins[format_name].optionsProp
		for opt_name, default in self.options_map.items():
			prop = options_prop[opt_name]
			wclass = _OPTION_QT_MAP.get(prop.__class__.__name__)
			if not wclass:
				log.warning(f"No Qt widget class for option class {prop.__class__}")
				continue
			w = wclass(prop, holder)  # type: ignore[arg-type]
			try:
				w.value = values.get(opt_name, default)
			except (TypeError, ValueError):
				w.value = default
			v.addWidget(w.widget)
			self._widgets[opt_name] = w
		v.addStretch()

		widget = QWidget()
		w_layout = QVBoxLayout(widget)
		w_layout.addWidget(scroll)
		scroll.setWidget(holder)
		buttons = QDialogButtonBox(
			QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
		)
		buttons.accepted.connect(self._ok)
		buttons.rejected.connect(self.reject)
		w_layout.addWidget(buttons)
		outer = QVBoxLayout(self)
		outer.addWidget(widget)

	def _ok(self) -> None:
		for opt_name, widget in self._widgets.items():
			self._values_ref[opt_name] = widget.value
		self.accept()
