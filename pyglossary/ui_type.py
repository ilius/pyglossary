__all__ = ["UIType"]


class UIType:
	def progressInit(self, title: str) -> None:
		raise NotImplementedError

	def progress(self, ratio: float, text: str = "") -> None:
		raise NotImplementedError

	def progressEnd(self) -> None:
		raise NotImplementedError
