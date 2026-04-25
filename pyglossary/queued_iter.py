from __future__ import annotations

import queue
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Iterator

__all__ = ["QueuedIterator"]


class QueuedIterator[T]:
	def __init__(
		self,
		iterator: Iterator[T],
		max_size: int,
	) -> None:
		self.iterator = iterator
		self.queue: queue.Queue[T | type[StopIteration]] = queue.Queue(max_size)
		self.thread = threading.Thread(target=self._background_job)
		self.thread.start()

	def _background_job(self) -> None:
		for item in self.iterator:
			self.queue.put(item)
		self.queue.put(StopIteration)

	def __iter__(self) -> Iterator[T]:
		return self

	def __next__(self) -> T:
		item = self.queue.get()
		if item is StopIteration:
			raise StopIteration
		return item  # type: ignore[return-value]
