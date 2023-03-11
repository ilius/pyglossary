
import typing


class UIType:
	def progressInit(self: "typing.Self", title: str) -> None:
		raise NotImplementedError

	def progress(self: "typing.Self", rat: float, text: str = "") -> None:
		raise NotImplementedError

	def progressEnd(self: "typing.Self") -> None:
		raise NotImplementedError
