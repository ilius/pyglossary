# -*- coding: utf-8 -*-

from typing import List, Optional

class Option(object):
	def __init__(self, typ: str, customValue: bool = False, values: Optional[List[str]] = None, comment: str = ""):
		self.typ = typ
		self.values = values
		self.customValue = customValue
		self.comment = comment


class BoolOption(Option):
	def __init__(self, **kwargs):
		Option.__init__(self, "bool", **kwargs)


class StrOption(Option):
	def __init__(self, **kwargs):
		Option.__init__(self, "str", **kwargs)


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


