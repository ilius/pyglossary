#!/bin/bash
grep -roh 'https://pypi.org/project/[^)]*' doc/p/ | sort | uniq --count

