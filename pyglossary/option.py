# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import re
from typing import Any

__all__ = [
	"BoolOption",
	"DictOption",
	"EncodingOption",
	"FileSizeOption",
	"FloatOption",
	"HtmlColorOption",
	"IntOption",
	"ListOption",
	"NewlineOption",
	"Option",
	"StrOption",
	"optionFromDict",
]

log = logging.getLogger("pyglossary")


def optionFromDict(data: dict[str, Any]) -> Option:
	className = data.pop("class")
	optClass: type
	if className == "Option":
		data["typ"] = data.pop("type")
		optClass = Option
	else:
		data.pop("type")
		optClass = Option.classes[className]
	return optClass(**data)


class Option:
	classes: dict[str, type] = {}

	@classmethod
	def register(cls: type[Option], optClass: type) -> type:
		cls.classes[optClass.__name__] = optClass
		return optClass

	def __init__(  # noqa: PLR0913
		self,
		typ: str,
		customValue: bool = False,
		values: list[Any] | None = None,
		allowNone: bool = False,
		comment: str = "",
		multiline: bool = False,
		disabled: bool = False,
		hasFlag: bool = False,
		customFlag: str = "",
		falseComment: str = "",
	) -> None:
		if values is None:
			# otherwise there would not be any valid value
			customValue = True
		self.typ = typ
		self.values = values
		self.allowNone = allowNone
		self.customValue = customValue
		self.comment = comment
		self.multiline = multiline
		self.disabled = disabled
		self.hasFlag = hasFlag
		self.customFlag = customFlag
		self.falseComment = falseComment

	@property
	def typeDesc(self) -> str:
		return self.typ

	@property
	def longComment(self) -> str:
		comment = self.typeDesc
		if self.comment:
			if comment:
				comment += ", "
			comment += self.comment
		return comment

	def toDict(self) -> dict[str, Any]:
		data = {
			"class": self.__class__.__name__,
			"type": self.typ,
			"customValue": self.customValue,
		}
		if self.values:
			data["values"] = self.values
		if self.comment:
			data["comment"] = self.comment
		if self.disabled:
			data["disabled"] = True
		if self.hasFlag:
			data["hasFlag"] = True
			data["customFlag"] = self.customFlag
		if self.falseComment:
			data["falseComment"] = self.falseComment
		return data

	@classmethod
	def evaluate(cls, raw: str) -> tuple[Any, bool]:
		"""Return (value, isValid)."""
		if raw == "None":
			return None, True
		return raw, True

	def validate(self, value: Any) -> bool:  # noqa: ANN401
		if not self.customValue:
			if not self.values:
				log.error(
					f"invalid option: customValue={self.customValue!r}"
					f", values={self.values!r}",
				)
				return False
			return value in self.values
		if value is None:
			return self.allowNone
		valueType = type(value).__name__
		return self.typ == valueType

	def validateRaw(self, raw: str) -> bool:
		"""Return isValid."""
		value, isValid = self.evaluate(raw)
		if not isValid:
			return False
		return self.validate(value)

	def groupValues(self) -> dict[str, Any] | None:  # noqa: PLR6301
		return None


@Option.register
class BoolOption(Option):
	def __init__(
		self,
		allowNone: bool = False,
		**kwargs,  # noqa: ANN003
	) -> None:
		values: list[bool | None] = [False, True]
		if allowNone:
			values.append(None)
		Option.__init__(
			self,
			typ="bool",
			customValue=False,
			values=values,
			allowNone=allowNone,
			**kwargs,  # noqa: ANN003
		)

	def toDict(self) -> dict[str, Any]:
		data = Option.toDict(self)
		del data["customValue"]
		del data["values"]
		return data

	@classmethod
	def evaluate(
		cls,
		raw: str | bool,
	) -> tuple[bool | None, bool]:
		if raw is None:
			return None, True
		if isinstance(raw, bool):
			return raw, True
		if isinstance(raw, str):
			raw = raw.lower()
			if raw == "none":
				return None, True
			if raw in {"yes", "true", "1"}:
				return True, True
			if raw in {"no", "false", "0"}:
				return False, True
		return None, False  # not valid


@Option.register
class StrOption(Option):
	def __init__(
		self,
		**kwargs,  # noqa: ANN003
	) -> None:
		Option.__init__(
			self,
			typ="str",
			**kwargs,
		)

	def validate(self, value: Any) -> bool:  # noqa: ANN401
		if not self.customValue:
			if not self.values:
				log.error(
					f"invalid option: customValue={self.customValue!r}"
					f", values={self.values!r}",
				)
				return False
			return value in self.values
		return type(value).__name__ == "str"

	def groupValues(self) -> dict[str, Any] | None:  # noqa: PLR6301
		return None


@Option.register
class IntOption(Option):
	def __init__(
		self,
		**kwargs,  # noqa: ANN003
	) -> None:
		Option.__init__(
			self,
			typ="int",
			**kwargs,
		)

	@classmethod
	def evaluate(cls, raw: str | int) -> tuple[int | None, bool]:
		"""Return (value, isValid)."""
		try:
			value = int(raw)
		except ValueError:
			return None, False
		return value, True


@Option.register
class FileSizeOption(IntOption):
	factors = {
		"KiB": 1024,
		"kib": 1024,
		"Ki": 1024,
		"ki": 1024,
		# ------------
		"MiB": 1048576,
		"mib": 1048576,
		"Mi": 1048576,
		"mi": 1048576,
		# ------------
		"GiB": 1073741824,
		"gib": 1073741824,
		"Gi": 1073741824,
		"gi": 1073741824,
		# ------------
		"kB": 1000,
		"kb": 1000,
		"KB": 1000,
		"k": 1000,
		"K": 1000,
		# ------------
		"MB": 1000000,
		"mb": 1000000,
		"mB": 1000000,
		"M": 1000000,
		"m": 1000000,
		# ------------
		"GB": 1000000000,
		"gb": 1000000000,
		"gB": 1000000000,
		"G": 1000000000,
		"g": 1000000000,
	}
	validPattern = "^([0-9.]+)([kKmMgG]i?[bB]?)$"

	@property
	def typeDesc(self) -> str:
		return ""

	@classmethod
	def evaluate(cls, raw: str | int) -> tuple[int | None, bool]:
		if not raw:
			return 0, True
		factor = 1
		if isinstance(raw, str):
			m = re.match(cls.validPattern, raw)
			if m is not None:
				raw, unit = m.groups()
				factorTmp = cls.factors.get(unit)
				if factorTmp is None:
					return None, False
				factor = factorTmp
		try:
			value = float(raw)
		except ValueError:
			return None, False
		if value < 0:
			return None, False
		return int(value * factor), True


@Option.register
class FloatOption(Option):
	def __init__(
		self,
		**kwargs,  # noqa: ANN003
	) -> None:
		Option.__init__(
			self,
			typ="float",
			**kwargs,
		)

	@classmethod
	def evaluate(
		cls,
		raw: str | float,
	) -> tuple[float | None, bool]:
		"""Return (value, isValid)."""
		try:
			value = float(raw)
		except ValueError:
			return None, False
		return value, True


@Option.register
class DictOption(Option):
	def __init__(
		self,
		**kwargs,  # noqa: ANN003
	) -> None:
		Option.__init__(
			self,
			typ="dict",
			customValue=True,
			allowNone=True,
			multiline=True,
			**kwargs,
		)

	def toDict(self) -> dict[str, Any]:
		data = Option.toDict(self)
		del data["customValue"]
		return data

	@classmethod
	def evaluate(
		cls,
		raw: str | dict,
	) -> tuple[dict | None, bool]:
		import ast

		if isinstance(raw, dict):
			return raw, True
		if raw == "":  # noqa: PLC1901
			return None, True  # valid
		try:
			value = ast.literal_eval(raw)
		except SyntaxError:
			return None, False  # not valid
		if type(value).__name__ != "dict":
			return None, False  # not valid
		return value, True  # valid


@Option.register
class ListOption(Option):
	def __init__(self, **kwargs) -> None:  # noqa: ANN003
		Option.__init__(
			self,
			typ="list",
			customValue=True,
			allowNone=True,
			multiline=True,
			**kwargs,  # noqa: ANN003
		)

	def toDict(self) -> dict[str, Any]:
		data = Option.toDict(self)
		del data["customValue"]
		return data

	@classmethod
	def evaluate(cls, raw: str) -> tuple[list | None, bool]:
		import ast

		if raw == "":  # noqa: PLC1901
			return None, True  # valid
		try:
			value = ast.literal_eval(raw)
		except SyntaxError:
			return None, False  # not valid
		if type(value).__name__ != "list":
			return None, False  # not valid
		return value, True  # valid


@Option.register
class EncodingOption(Option):
	re_category = re.compile("^[a-z]+")

	def __init__(
		self,
		customValue: bool = True,
		values: list[str] | None = None,
		comment: str | None = None,
		**kwargs,  # noqa: ANN003
	) -> None:
		if values is None:
			values = [
				"utf-8",
				"utf-16",
				"windows-1250",
				"windows-1251",
				"windows-1252",
				"windows-1253",
				"windows-1254",
				"windows-1255",
				"windows-1256",
				"windows-1257",
				"windows-1258",
				"mac_cyrillic",
				"mac_greek",
				"mac_iceland",
				"mac_latin2",
				"mac_roman",
				"mac_turkish",
				"cyrillic",
				"arabic",
				"greek",
				"hebrew",
				"latin2",
				"latin3",
				"latin4",
				"latin5",
				"latin6",
			]
		if comment is None:
			comment = "Encoding/charset"
		Option.__init__(
			self,
			typ="str",
			customValue=customValue,
			values=values,
			comment=comment,
			**kwargs,  # noqa: ANN003
		)

	def toDict(self) -> dict[str, Any]:
		data = Option.toDict(self)
		del data["values"]
		return data

	def groupValues(self) -> dict[str, Any] | None:
		groups: dict[str, list[str]] = {}
		others: list[str] = []
		for value in self.values or []:
			cats = self.re_category.findall(value)
			if not cats:
				others.append(value)
				continue
			cat = cats[0]
			if len(cat) == len(value):
				others.append(value)
				continue
			if cat not in groups:
				groups[cat] = []
			groups[cat].append(value)
		if others:
			groups["other"] = others
		return groups


@Option.register
class NewlineOption(Option):
	def __init__(
		self,
		customValue: bool = True,
		values: list[str] | None = None,
		comment: str | None = None,
		**kwargs,  # noqa: ANN003
	) -> None:
		if values is None:
			values = [
				"\r\n",
				"\n",
				"\r",
			]
		if comment is None:
			comment = "Newline string"
		Option.__init__(
			self,
			typ="str",
			customValue=customValue,
			values=values,
			multiline=True,
			comment=comment,
			**kwargs,  # noqa: ANN003
		)


@Option.register
class UnicodeErrorsOption(Option):
	def __init__(
		self,
		comment: str | None = None,
	) -> None:
		if comment is None:
			comment = "Unicode Errors, values: `strict`, `ignore`, `replace`"
		Option.__init__(
			self,
			typ="str",
			customValue=False,
			values=["strict", "ignore", "replace"],
			multiline=False,
			comment=comment,
		)

	def toDict(self) -> dict[str, Any]:
		return {
			"class": "UnicodeErrorsOption",
			"type": "str",
			"comment": self.comment,
		}


@Option.register
class HtmlColorOption(Option):
	def toDict(self) -> dict[str, Any]:
		data = Option.toDict(self)
		del data["customValue"]
		return data

	def __init__(self, **kwargs) -> None:  # noqa: ANN003
		Option.__init__(
			self,
			typ="str",
			customValue=True,
			**kwargs,  # noqa: ANN003
		)
		# TODO: use a specific type?
