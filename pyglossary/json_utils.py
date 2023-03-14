import json
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from typing import AnyStr, TypeAlias

JsonEncodable: "TypeAlias" = "dict | list"
# OrderedDict is also subclass of Dict, issubclass(OrderedDict, Dict) is True


def dataToPrettyJson(
	data: "JsonEncodable",
	ensure_ascii: bool = False,
	sort_keys: bool = False,
) -> str:
	return json.dumps(
		data,
		sort_keys=sort_keys,
		indent="\t",
		ensure_ascii=ensure_ascii,
	)


def jsonToData(st: "AnyStr") -> "JsonEncodable":
	return json.loads(st)


def jsonToOrderedData(text: str) -> "OrderedDict":
	return json.JSONDecoder(
		object_pairs_hook=OrderedDict,
	).decode(text)
