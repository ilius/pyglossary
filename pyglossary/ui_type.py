class UIType:
	def progressInit(self, title: str) -> None:
		raise NotImplementedError

	def progress(self, rat: float, text: str = "") -> None:
		raise NotImplementedError

	def progressEnd(self) -> None:
		raise NotImplementedError
