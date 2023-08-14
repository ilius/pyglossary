import json
import sys
from collections import Counter
from collections import OrderedDict as odict
from dataclasses import dataclass
from typing import Any


@dataclass
class Node:
	Type: str = ""

	Dict: "dict[str, Node] | None" = None
	KeyScore: "Counter | None" = None

	ListOf: "Node | None" = None

	def keyScoreList(self):
		return [
			f"{count:.1f}: {key}" for key, count in self.KeyScore.most_common()
		]

	@property
	def __dict__(self):
		if self.Dict:
			assert self.ListOf is None
			keys = [
				key for key, _ in self.KeyScore.most_common()
			]
			try:
				keys.remove("word")
			except ValueError:
				pass
			else:
				keys.insert(0, "word")
			return {
				"__dict__": odict(
					(key, self.Dict[key].__dict__)
					for key in keys
				),
				# "__key_score__": self.keyScoreList(),
			}

		if self.ListOf:
			return {"__list_of__": self.ListOf.__dict__}

		return self.Type


schema = Node(Type="dict")
valueSet: "dict[str, set]" = {}


def addToValueSet(value: "str | int | float | bool", path: "list[str]"):
	if isinstance(value, str) and "://" in value:
		return
	pathStr = ".".join(path)
	if pathStr in valueSet:
		valueSet[pathStr].add(value)
		return
	valueSet[pathStr] = {value}


def getSchemaNode(path: "list[str]"):
	node = schema
	for name in path:
		if name == "[]":
			node.Type = "list"
			if not node.ListOf:
				node.ListOf = Node()
			node = node.ListOf
			continue
		node.Type = "dict"
		if not node.Dict:
			node.Dict = {}
			node.KeyScore = Counter()
		if name in node.Dict:
			node = node.Dict[name]
		else:
			newNode = Node()
			node.Dict[name] = newNode
			node = newNode
	return node


def updateSchema(_type: str, path: "list[str]"):
	node = getSchemaNode(path)
	prevType = node.Type
	if prevType and prevType != _type:
		print(
			f"mismatch types for path={'.'.join(path)}, "
			f"{prevType} and {_type}",
		)
	node.Type = _type


def parseList(data: "list[Any]", path: "list[str]", node: Node):
	node.Type = "list"
	if not node.ListOf:
		node.ListOf = Node()
	if not data:
		return
	itemsPath = path + ["[]"]
	itemTypes = set()
	for item in data:
		itemTypes.add(type(item).__name__)
		if isinstance(item, dict):
			parseDict(item, itemsPath, node.ListOf)
			continue
		if isinstance(item, list):
			parseList(item, itemsPath, node.ListOf)
			continue
		if isinstance(item, (str, int, float, bool)):
			addToValueSet(item, path)

	itemTypesStr = " | ".join(sorted(itemTypes))
	updateSchema(itemTypesStr, path+["[]"])


def parseDict(data: "dict[str, Any]", path: "list[str]", node: Node):
	if not node.Dict:
		node.Dict = {}
		node.KeyScore = Counter()

	for index, (key, value) in enumerate(data.items()):
		node.KeyScore[key] += min(1, 50 - index) / 50

		if key in node.Dict:
			childNode = node.Dict[key]
		else:
			childNode = node.Dict[key] = Node()

		if isinstance(value, dict):
			parseDict(value, path+[key], childNode)
			continue
		if isinstance(value, list):
			parseList(value, path+[key], childNode)
			continue
		if isinstance(value, (str, int, float, bool)):
			updateSchema(type(value).__name__, path+[key])
			addToValueSet(value, path+[key])


jsonl_path = sys.argv[1]

with open(jsonl_path, encoding="utf-8") as _file:
	for line in _file:
		line = line.strip()
		if not line:
			continue
		try:
			data = json.loads(line)
		except Exception:
			print(f"bad line: {line}")
			continue
		parseDict(data, [], schema)

with open(f"{jsonl_path}.schema.json", mode="w", encoding="utf-8") as _file:
	json.dump(
		schema.__dict__,
		_file,
		indent="\t",
	)


commonValuesList = [
	(key, sorted(values))
	for key, values in valueSet.items()
	if len(values) < 20 and len(str(values)) < 100
]

def commonValuesSortKey(item):
	key, values = item
	return abs(len(values)-5)

commonValuesList.sort(key=commonValuesSortKey)

with open(f"{jsonl_path}-common-values.json", mode="w", encoding="utf-8") as _file:
	json.dump(dict(commonValuesList), _file, indent="\t")
