import sys
from os.path import dirname, realpath, splitext

sys.path.insert(0, dirname(dirname(dirname(realpath(__file__)))))

from pyglossary.apple_utils import substituteAppleCSS

for fpath in sys.argv[1:]:
	if fpath.endswith("-fixed.css"):
		continue
	fpathNoExt, _ = splitext(fpath)
	fpathNew = fpathNoExt + "-fixed.css"
	with open(fpath, "rb") as _file:
		text = _file.read()
	text = substituteAppleCSS(text)
	with open(fpathNew, "wb") as _file:
		_file.write(text)
	print("Created", fpathNew)
	print()
