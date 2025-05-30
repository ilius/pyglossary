__all__ = ["UIType"]


from typing import Protocol


class UIType(Protocol):
	def progressInit(self, title: str) -> None:
		raise NotImplementedError

	def progress(self, ratio: float, text: str = "") -> None:
		raise NotImplementedError

	def progressEnd(self) -> None:
		raise NotImplementedError
