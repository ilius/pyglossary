from __future__ import annotations

import argparse


class StoreConstAction(argparse.Action):
	def __init__(
		self,
		option_strings: list[str],
		same_dest: str = "",
		const_value: bool | None = None,
		nargs: int = 0,
		**kwargs,
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

	def __call__(  # noqa: PLR0913
		self,
		parser: argparse.ArgumentParser | None = None,
		namespace: argparse.Namespace | None = None,
		values: list | None = None,  # noqa: ARG002
		option_strings: list[str] | None = None,  # noqa: ARG002
		required: bool = False,  # noqa: ARG002
		dest: str | None = None,
	) -> StoreConstAction:
		if not parser:
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
