"""
Protocol for UI progress-bar backends.

``UIType`` defines ``progressInit``, ``progress``, and ``progressEnd`` hooks
implemented by CLI, GTK, Qt, and other front ends so glossary conversion can
report read/write progress uniformly.
"""

__all__ = ["UIType"]


from typing import Protocol


class UIType(Protocol):
	"""Supported PyGlossary UI backend."""

	def progressInit(self, title: str) -> None:
		raise NotImplementedError

	def progress(self, ratio: float, text: str = "") -> None:
		raise NotImplementedError

	def progressEnd(self) -> None:
		raise NotImplementedError
