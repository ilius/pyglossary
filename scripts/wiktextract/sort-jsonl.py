#!/usr/bin/env python

# read json lines from stdin,
# sort them by "word" key and print

import operator
import sys
from json import loads

data: "list[tuple[str, str]]" = []

for line in sys.stdin:
	line = line.strip()
	if not line:
		continue
	row = loads(line)
	data.append((row.get("word"), line))

data.sort(key=operator.itemgetter(0))

for _, line in data:
	print(line)
