"""Read/Write format options dialog for the Slint UI."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import slint

from pyglossary.glossary_v2 import Glossary

from .utils import load_slint, weakCallback

if TYPE_CHECKING:
	from collections.abc import Callable

	from pyglossary.plugin_prop import PluginProp

__all__ = ["FormatOptionsDialog"]

log = logging.getLogger("pyglossary")


def _widgetKind(opt: Any) -> str:
	if opt.typ in {"bool", "int"}:  # FileSizeOption.typ is "int" too
		return opt.typ
	return "choice" if opt.values else "str"


class FormatOptionsDialog:
	"""Non-modal; on OK replaces the contents of `values` in place."""

	def __init__(
		self,
		plugin: PluginProp,
		kind: str,  # "Read" or "Write"
		values: dict[str, Any],
		onClose: Callable[[FormatOptionsDialog], None],
	) -> None:
		defaults = (
			Glossary.formatsReadOptions
			if kind == "Read"
			else Glossary.formatsWriteOptions
		).get(plugin.name, {})
		self._valuesOut = values
		self._onClose = onClose
		self._opts = [
			(name, plugin.optionsProp[name])
			for name in defaults
			if name in plugin.optionsProp
		]
		self._values = {name: values.get(name, defaults[name]) for name, _ in self._opts}

		rows = []
		for name, prop in self._opts:
			current = self._values[name]
			widget = _widgetKind(prop)
			rows.append(
				{
					"name": prop.displayName,
					"comment": prop.longComment,
					"kind": widget,
					"bool-value": widget == "bool" and bool(current),
					"str-value": str(current) if widget in {"str", "choice"} else "",
					"int-value": int(current) if widget == "int" else 0,
					"choices": slint.ListModel(
						[str(v) for v in prop.values or []] if widget == "choice" else []
					),
				},
			)

		self.dialog = load_slint("dialogs.slint").OptionsDialog()
		self.dialog.title_text = f"{plugin.description} {kind} Options"
		self.dialog.options = slint.ListModel(rows)
		setValue = weakCallback(self._setValue)
		self.dialog.set_bool = setValue
		self.dialog.set_int = setValue
		self.dialog.set_str = setValue
		self.dialog.ok = weakCallback(self._onOk)
		self.dialog.cancel = weakCallback(self._close)
		self.dialog.show()

	def _setValue(self, i: int, value: Any) -> None:
		self._values[self._opts[i][0]] = value

	def _onOk(self) -> None:
		result: dict[str, Any] = {}
		for name, opt in self._opts:
			raw = self._values[name]
			try:
				value, isValid = opt.evaluate(raw)
			except Exception:
				log.exception(f"failed to evaluate option {name!r}={raw!r}")
				continue
			if not isValid:
				log.warning(f"invalid value {raw!r} for option {name!r}")
				continue
			result[name] = value
		self._valuesOut.clear()
		self._valuesOut.update(result)
		self._close()

	def _close(self) -> None:
		self.dialog.hide()
		self._onClose(self)
