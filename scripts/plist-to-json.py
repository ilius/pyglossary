#!/usr/bin/env python

import json
import sys

import biplist

plistPath = sys.argv[1]

try:
    data = biplist.readPlist(plistPath)
except (biplist.InvalidPlistException, biplist.NotBinaryPlistException):
    try:
        import plistlib
        with open(plistPath, mode="rb") as plist_file:
            data = plistlib.loads(plist_file.read())
    except Exception as e:
        raise OSError(
            "'Info.plist' file is malformed, "
            f"Please provide 'Contents/' with a correct 'Info.plist'. {e}",
        ) from e

print(json.dumps(data, indent="\t", sort_keys=True))
