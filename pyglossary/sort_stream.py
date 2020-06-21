# -*- coding: utf-8 -*-

from heapq import heappush, heappop
from heapq import merge

from typing import (
	TypeVar,
	#Dict,
	#Tuple,
	List,
	Sequence,
	Any,
	Optional,
	Iterator,
	Callable,
)


import logging
log = logging.getLogger("root")


T = TypeVar("T")

def hsortStream(stream: Iterator[T], maxHeapSize: int, key: Optional[Callable[[T], Any]] = None) -> Iterator[T]:
	"""
		stream: a generator or iterable
		maxHeapSize: int, maximum size of heap
		key: a key function, as in `list.sort` method, or `sorted` function
			 if key is None, we consume less memory

		the sort is Stable (unlike normal heapsort) because we include the
			index (after item / output of key function)
	"""
	hp = []
	if key:
		for index, item in enumerate(stream):
			if len(hp) >= maxHeapSize:
				yield heappop(hp)[2]
			heappush(hp, (
				key(item),  # for sorting order
				index,  # for sort being Stable
				item,  # for fetching result
			))
		while hp:
			yield heappop(hp)[2]
	else:  # consume less memory
		for index, item in enumerate(stream):
			if len(hp) >= maxHeapSize:
				yield heappop(hp)[0]
			heappush(hp, (
				item,  # for sorting order, and fetching result
				index,  # for sort being Stable
			))
		while hp:
			yield heappop(hp)[0]


def hsortStreamList(streams: Sequence[Iterator[T]], *args, **kwargs) -> Iterator[T]:
	streams = [
		 hsortStream(stream, *args, **kwargs)
		 for stream in streams
	]
	return merge(*tuple(streams))


def stdinIntegerStream():
	while True:
		line = input(" Input item: ")
		if not line:
			break
		yield int(line)


def stdinStringStream():
	while True:
		line = raw_input(" Input item: ")
		if not line:
			break
		yield line


def randomChoiceGenerator(choices, count):
	import random
	for _ in range(count):
		yield random.choice(choices)


def test_hsortStreamList(count=10):
	for item in hsortStreamList(
		[
			randomChoiceGenerator(range(0, 50), count),
			randomChoiceGenerator(range(30, 50), count),
			randomChoiceGenerator(range(10, 40), count),
		],
		maxHeapSize=5,
		key=None,
	):
		print(item)


def main():
	test_hsortStreamList()
#	stream = stdinIntegerStream()
#	for line in hsortStream(stream, 3):
#		print(f"------ Placed item: {line}")

if __name__ == "__main__":
	main()
