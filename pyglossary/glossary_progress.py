
import typing
from typing import TYPE_CHECKING

from .core import log

if TYPE_CHECKING:
	from .ui_type import UIType

class GlossaryProgress(object):
	def __init__(
		self: "typing.Self",
		ui: "UIType | None" = None,  # noqa: F821
	) -> None:
		self._ui = ui
		self._progressbar = True

	def clear(self: "typing.Self") -> None:
		self._progressbar = True

	@property
	def progressbar(self: "typing.Self") -> bool:
		return self._ui is not None and self._progressbar

	@progressbar.setter
	def progressbar(self: "typing.Self", enabled: bool) -> None:
		self._progressbar = enabled

	def progressInit(
		self: "typing.Self",
		*args,  # noqa: ANN
	) -> None:
		if self._ui and self._progressbar:
			self._ui.progressInit(*args)

	def progress(self: "typing.Self", pos: int, total: int, unit: str = "entries") -> None:
		if total == 0:
			log.warning(f"{pos=}, {total=}")
			return
		if self._ui is None:
			return
		self._ui.progress(
			min(pos + 1, total) / total,
			f"{pos:,} / {total:,} {unit}",
		)

	def progressEnd(self: "typing.Self") -> None:
		if self._ui and self._progressbar:
			self._ui.progressEnd()

