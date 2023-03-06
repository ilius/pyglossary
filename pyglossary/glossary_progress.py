from .core import log


class GlossaryProgress(object):
	def __init__(
		self,
		ui: "Optional[UIBase]" = None,  # noqa: F821
	):
		self._ui = ui
		self._progressbar = True

	def clear(self) -> None:
		self._progressbar = True

	@property
	def progressbar(self) -> bool:
		return self._ui is not None and self._progressbar

	@progressbar.setter
	def progressbar(self, enabled: bool) -> None:
		self._progressbar = enabled

	def progressInit(
		self,
		*args,  # noqa: ANN
	) -> None:
		if self._ui and self._progressbar:
			self._ui.progressInit(*args)

	def progress(self, pos: int, total: int, unit: str = "entries") -> None:
		if total == 0:
			log.warning(f"{pos=}, {total=}")
			return
		self._ui.progress(
			min(pos + 1, total) / total,
			f"{pos:,} / {total:,} {unit}",
		)

	def progressEnd(self) -> None:
		if self._ui and self._progressbar:
			self._ui.progressEnd()

