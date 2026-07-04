from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import slint

from pyglossary.glossary_v2 import Glossary

from .utils import load_slint, weakCallback

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = ["FormatOptionsDialog"]

log = logging.getLogger("pyglossary")


def _kindForOption(opt: Any) -> str:
	cls = opt.__class__.__name__
	if cls == "BoolOption":
		return "bool"
	if cls in ("IntOption", "FileSizeOption"):
		return "int"
	if getattr(opt, "values", None):
		return "choice"
	return "str"


class FormatOptionsDialog:
	"""
	Non-modal editor for the read or write options of a single format.
	`onOk(dict)` is invoked on OK with the (possibly evaluated) option values;
	on cancel nothing happens. The owner must keep a reference (see
	`UI._ref_dialog`).
	"""

	_kindFormatsOptions = {
		"Read": Glossary.formatsReadOptions,
		"Write": Glossary.formatsWriteOptions,
	}

	def __init__(
		self,
		formatDesc: str,
		kind: str,  # "Read" or "Write"
		values: dict[str, Any],
		onOk: Callable[[dict[str, Any]], None],
		onClose: Callable[[FormatOptionsDialog], None],
	) -> None:
		pluginByDesc = {p.description: p for p in Glossary.plugins.values()}
		plugin = pluginByDesc.get(formatDesc)
		if plugin is None:
			log.error(f"FormatOptionsDialog: unknown format {formatDesc!r}")
			onClose(self)
			return
		formatName = plugin.name
		optionsDefaults: dict[str, Any] = self._kindFormatsOptions[kind].get(
			formatName,
			{},
		)
		optionsProp = plugin.optionsProp

		self._onOk = onOk
		self._onClose = onClose
		self._optNames: list[str] = []
		self._opts: list[Any] = []
		self._values: dict[str, Any] = {}

		rows: list[dict[str, Any]] = []
		for optName, default in optionsDefaults.items():
			prop = optionsProp.get(optName)
			if prop is None:
				continue
			current = values.get(optName, default)
			self._optNames.append(optName)
			self._opts.append(prop)
			self._values[optName] = current
			# do NOT reuse the name `kind` here: that would shadow the
			# "Read"/"Write" parameter still needed for title_text below
			optKind = _kindForOption(prop)
			row: dict[str, Any] = {
				"name": prop.displayName,
				"comment": prop.longComment,
				"kind": optKind,
				"bool-value": bool(current) if optKind == "bool" else False,
				"str-value": str(current) if optKind == "str" else "",
				"int-value": int(current) if optKind == "int" else 0,
				"choices": slint.ListModel(
					[str(v) for v in (prop.values or [])],
				)
				if optKind == "choice"
				else slint.ListModel([]),
				"current-choice": str(current) if optKind == "choice" else "",
			}
			rows.append(row)

		comp = load_slint("dialogs.slint").OptionsDialog
		self.dialog = comp()
		self.dialog.title_text = f"{formatDesc} {kind} Options"
		self.dialog.options = slint.ListModel(rows)

		# Bind weakly (see utils.weakCallback) so the Slint component is never
		# part of a reference cycle with this controller.
		self.dialog.set_bool = weakCallback(self._setBool)
		self.dialog.set_str = weakCallback(self._setStr)
		self.dialog.set_int = weakCallback(self._setInt)
		self.dialog.set_choice = weakCallback(self._setChoice)
		self.dialog.ok = weakCallback(self._onOkCb)
		self.dialog.cancel = weakCallback(self._onCancel)

		self.dialog.show()

	# ----------------------------------------------------------
	# callbacks (Slint event-loop thread)
	# ----------------------------------------------------------
	def _setBool(self, i: int, v: bool) -> None:
		self._values[self._optNames[i]] = bool(v)

	def _setInt(self, i: int, v: int) -> None:
		self._values[self._optNames[i]] = int(v)

	def _setStr(self, i: int, v: str) -> None:
		self._values[self._optNames[i]] = v

	def _setChoice(self, i: int, v: str) -> None:
		self._values[self._optNames[i]] = v

	def _onOkCb(self) -> None:
		result: dict[str, Any] = {}
		for optName, opt in zip(self._optNames, self._opts, strict=True):
			raw = self._values.get(optName)
			try:
				value, isValid = opt.evaluate(raw)
			except Exception:
				log.exception(f"failed to evaluate option {optName!r}={raw!r}")
				continue
			if not isValid:
				log.warning(f"invalid value {raw!r} for option {optName!r}")
				continue
			result[optName] = value
		self._onOk(result)
		self._close()

	def _onCancel(self) -> None:
		self._close()

	def _close(self) -> None:
		self.dialog.hide()
		self._onClose(self)
