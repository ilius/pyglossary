# -*- coding: utf-8 -*-

import logging
from typing import Tuple, List, Dict, Optional, Any


log = logging.getLogger("root")


class Option(object):
	def __init__(
		self,
		typ: str,
		customValue: bool = False,
		values: Optional[List[str]] = None,
		comment: str = "",
	):
		if values is None:
			customValue = True # otherwise there would not be any valid value
		self.typ = typ
		self.values = values
		self.customValue = customValue
		self.comment = comment

	def evaluate(self, raw: str) -> Tuple[Any, bool]:
		"returns (value, isValid)"
		return raw, True

	def validate(self, value):
		if not self.customValue:
			if not self.values:
				log.error("invalid option: customValue=%r, values=%r" % (
					self.customValue,
					self.values,
				))
				return False
			return value in self.values
		if value is None:
			return self.typ in ("dict", "list")
		valueType = type(value).__name__
		return self.typ == valueType


class BoolOption(Option):
	def __init__(self, **kwargs):
		Option.__init__(
			self,
			"bool",
			customValue=False,
			values=[False, True],
			**kwargs,
		)

	def evaluate(self, raw: str) -> Tuple[bool, bool]:
		if raw.lower() in ("yes", "true", "1"):
			return True, True
		if raw.lower() in ("no", "false", "0"):
			return False, True
		return None, False # not valid


class StrOption(Option):
	def __init__(self, **kwargs):
		Option.__init__(self, "str", **kwargs)

	def validate(self, value):
		if not self.customValue:
			if not self.values:
				log.error("invalid option: customValue=%r, values=%r" % (
					self.customValue,
					self.values,
				))
				return False
			return value in self.values
		return type(value).__name__ == "str"


class DictOption(Option):
	def __init__(self, **kwargs):
		Option.__init__(
			self,
			"dict",
			customValue=True,
			**kwargs,
		)

	def evaluate(self, raw: str) -> Tuple[Optional[Dict], bool]:
		import ast
		if raw == "":
			return None, True # valid
		try:
			value = ast.literal_eval(raw)
		except SyntaxError:
			return None, False # not valid
		if type(value).__name__ != "dict":
			return None, False # not valid
		return value, True # valid


class IntOption(Option):
	def __init__(self, **kwargs):
		Option.__init__(self, "int", **kwargs)

	def evaluate(self, raw: str) -> Tuple[int, bool]:
		"returns (value, isValid)"
		try:
			value = int(raw)
		except ValueError:
			return raw, False
		else:
			return value, True


class EncodingOption(Option):
	def __init__(self, customValue=True, values=None, **kwargs):
		if values is None:
			values = [
				"utf-8",
				"utf-16",
			]
		Option.__init__(
			self,
			"str",
			customValue=customValue,
			values=values,
			**kwargs
		)


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
