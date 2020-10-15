import sys
try:
	import json
except ImportError:
	import simplejson as json

from collections import OrderedDict

JsonEncodable = "Union[Dict, List]"
# OrderedDict is also subclass of Dict, issubclass(OrderedDict, Dict) == True


def dataToPrettyJson(
	data: "JsonEncodable",
	ensure_ascii: bool = False,
	sort_keys: bool = False,
):
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
