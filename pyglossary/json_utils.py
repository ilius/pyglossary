from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from typing import AnyStr, TypeAlias

__all__ = ["dataToPrettyJson", "jsonToData"]

JsonEncodable: TypeAlias = dict | list


def dataToPrettyJson(
	data: JsonEncodable,
	ensure_ascii: bool = False,
	sort_keys: bool = False,
) -> str:
	return json.dumps(
		data,
		sort_keys=sort_keys,
		indent="\t",
		ensure_ascii=ensure_ascii,
	)


def jsonToData(st: AnyStr) -> JsonEncodable:
	return json.loads(st)
