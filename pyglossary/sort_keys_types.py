from typing import Any, Callable, TypeAlias

sortKeyType: "TypeAlias" = Callable[
	[list[str]],
	Any,
]

sqliteSortKeyType: "TypeAlias" = list[tuple[str, str, sortKeyType]]

__all__ = [
	"sortKeyType",
	"sqliteSortKeyType",
]
