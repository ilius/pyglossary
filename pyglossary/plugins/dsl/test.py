import sys
from os.path import dirname

sys.path.insert(0, dirname(dirname(dirname(dirname(__file__)))))  # noqa: E402

from pyglossary.plugins.dsl.transform import Transformer

if __name__ == "__main__":
	inputStr = sys.argv[1]
	tr = Transformer(
		inputStr,
		currentKey="HEADWORD",
	)
	result, err = tr.transform()
	if err:
		print(f"Error: {err} in {inputStr!r}")
	elif result is None:
		print("ERROR: result is None")
	else:
		print(result.output)
