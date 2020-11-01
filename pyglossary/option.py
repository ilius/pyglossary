# -*- coding: utf-8 -*-

import re
import logging


log = logging.getLogger("pyglossary")


class Option(object):
	def __init__(
		self,
		typ: str,
		customValue: bool = False,
		values: "Optional[List[str]]" = None,
		comment: str = "",
		disabled: bool = False,
		cmd: bool = False,
		cmdFlag: str = "",
		falseComment: str = "",
	) -> None:
		if values is None:
			# otherwise there would not be any valid value
			customValue = True
		self.typ = typ
		self.values = values
		self.customValue = customValue
		self.comment = comment
		self.disabled = disabled
		self.cmd = cmd
		self.cmdFlag = cmdFlag
		self.falseComment = falseComment

	def evaluate(self, raw: str) -> "Tuple[Any, bool]":
		"returns (value, isValid)"
		if raw == "None":
			return None, True
		return raw, True

	def validate(self, value):
		if not self.customValue:
			if not self.values:
				log.error(
					f"invalid option: customValue={self.customValue!r}"
					f", values={self.values!r}"
				)
				return False
			return value in self.values
		if value is None:
			return self.typ in ("dict", "list")
		valueType = type(value).__name__
		return self.typ == valueType

	def validateRaw(self, raw: str) -> bool:
		"returns isValid"
		value, isValid = self.evaluate(raw)
		if not isValid:
			return False
		if not self.validate(value):
			return False
		return True

	def groupValues(self) -> "Optional[Dict[str, Any]]":
		return None


class BoolOption(Option):
	def __init__(self, **kwargs):
		Option.__init__(
			self,
			"bool",
			customValue=False,
			values=[False, True],
			**kwargs,
		)

	def evaluate(self, raw: "Union[str, bool]") -> "Tuple[Optional[bool], bool]":
		if isinstance(raw, bool):
			return raw, True
		if raw.lower() in ("yes", "true", "1"):
			return True, True
		if raw.lower() in ("no", "false", "0"):
			return False, True
		return None, False  # not valid


class StrOption(Option):
	def __init__(self, **kwargs):
		Option.__init__(self, "str", **kwargs)

	def validate(self, value):
		if not self.customValue:
			if not self.values:
				log.error(
					f"invalid option: customValue={self.customValue!r}"
					f", values={self.values!r}"
				)
				return False
			return value in self.values
		return type(value).__name__ == "str"

	def groupValues(self) -> "Optional[Dict[str, Any]]":
		return None


class IntOption(Option):
	def __init__(self, **kwargs):
		Option.__init__(self, "int", **kwargs)

	def evaluate(self, raw: "Union[str, int]") -> "Tuple[Optional[int], bool]":
		"returns (value, isValid)"
		try:
			value = int(raw)
		except ValueError:
			return None, False
		else:
			return value, True


class FloatOption(Option):
	def __init__(self, **kwargs):
		Option.__init__(self, "float", **kwargs)

	def evaluate(
		self,
		raw: "Union[str, float, int]",
	) -> "Tuple[Optional[float], bool]":
		"returns (value, isValid)"
		try:
			value = float(raw)
		except ValueError:
			return None, False
		else:
			return value, True


class DictOption(Option):
	def __init__(self, **kwargs):
		Option.__init__(
			self,
			"dict",
			customValue=True,
			**kwargs,
		)

	def evaluate(self, raw: "Union[str, dict]") -> "Tuple[Optional[Dict], bool]":
		import ast
		if isinstance(raw, dict):
			return raw, True
		if raw == "":
			return None, True  # valid
		try:
			value = ast.literal_eval(raw)
		except SyntaxError:
			return None, False  # not valid
		if type(value).__name__ != "dict":
			return None, False  # not valid
		return value, True  # valid


class ListOption(Option):
	def __init__(self, **kwargs):
		Option.__init__(
			self,
			"list",
			customValue=True,
			**kwargs,
		)

	def evaluate(self, raw: str) -> "Tuple[Optional[List], bool]":
		import ast
		if raw == "":
			return None, True  # valid
		try:
			value = ast.literal_eval(raw)
		except SyntaxError:
			return None, False  # not valid
		if type(value).__name__ != "list":
			return None, False  # not valid
		return value, True  # valid


class EncodingOption(Option):
	re_category = re.compile("^[a-z]+")

	def __init__(self, customValue=True, values=None, **kwargs):
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
		Option.__init__(
			self,
			"str",
			customValue=customValue,
			values=values,
			**kwargs
		)

	def groupValues(self) -> "Optional[Dict[str, Any]]":
		from collections import OrderedDict
		groups = OrderedDict()  # type: Dict[str, List[str]]
		others = []  # type: List[str]
		for value in self.values:
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


class NewlineOption(Option):
	def __init__(self, customValue=True, values=None, **kwargs):
		if values is None:
			values = [
				"\r\n",
				"\n",
				"\r",
			]
		Option.__init__(
			self,
			"str",
			customValue=customValue,
			values=values,
			**kwargs
		)


class HtmlColorOption(Option):
	def __init__(self, **kwargs):
		Option.__init__(self, "str", customValue=True, **kwargs)
		# FIXME: use a specific type?
