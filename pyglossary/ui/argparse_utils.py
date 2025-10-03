from __future__ import annotations

import argparse
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from argparse import ArgumentParser, Namespace

__all__ = ["StoreConstAction"]


class StoreConstAction(argparse.Action):
	def __init__(
		self,
		option_strings: list[str],
		same_dest: str = "",
		const_value: bool | None = None,
		nargs: int = 0,
		**kwargs: Any,
	) -> None:
		if isinstance(option_strings, str):
			option_strings = [option_strings]
		argparse.Action.__init__(
			self,
			option_strings=option_strings,
			nargs=nargs,
			**kwargs,
		)
		self.same_dest = same_dest
		self.const_value = const_value

	# if you want to follow mypy about the signature of this function,
	# it will break runtime. Do not touch the signature
	def __call__(  # type: ignore[return, override]
		self,
		*_args: Any,  # DO NOT REMOVE
		parser: ArgumentParser | None = None,
		namespace: Namespace | None = None,
		**_kwargs: Any,
	) -> StoreConstAction:
		if parser is None:
			return self
		if namespace is None:
			return self
		dest = self.dest
		if getattr(namespace, dest) is not None:
			flag = self.option_strings[0]
			if getattr(namespace, dest) == self.const_value:
				parser.error(f"multiple {flag} options")
			else:
				parser.error(f"conflicting options: {self.same_dest} and {flag}")
		setattr(namespace, dest, self.const_value)
		return self
