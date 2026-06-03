from __future__ import annotations

import argparse
from typing import Any

__all__ = ["StoreConstAction"]


class StoreConstAction(argparse.Action):
	def __init__(
		self,
		option_strings: str | list[str],
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

	def __call__(self, *args: Any, **_kwargs: Any) -> Any:
		# During parsing, argparse calls:
		# `action(parser, namespace, values, option_string)`
		# ``registerConfigOption`` passes a pre-built action instance as ``action=``; then
		# ``add_argument`` does ``action_instance(**kw)`` and expects that call to return
		# the same instance (see CPython ``ArgumentParser.add_argument``).
		if (
			len(args) >= 2
			and isinstance(args[0], argparse.ArgumentParser)
			and isinstance(args[1], argparse.Namespace)
		):
			parser = args[0]
			namespace = args[1]
			dest = self.dest
			current = getattr(namespace, dest, None)
			if current is not None:
				flag = self.option_strings[0]
				if current == self.const_value:
					parser.error(f"multiple {flag} options")
				else:
					parser.error(f"conflicting options: {self.same_dest} and {flag}")
			setattr(namespace, dest, self.const_value)
			return None
		return self
