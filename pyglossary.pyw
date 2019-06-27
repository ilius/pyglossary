#!/usr/bin/env python3

from os.path import dirname, join

with open(join(dirname(__file__), "main.py")) as fp:
	exec(fp.read())


