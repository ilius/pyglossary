from collections.abc import Callable
from typing import Any, TypeAlias

sortKeyType: "TypeAlias" = Callable[
	[list[str]],
	Any,
]

sqliteSortKeyType: "TypeAlias" = list[tuple[str, str, sortKeyType]]

__all__ = [
	"sortKeyType",
	"sqliteSortKeyType",
]
