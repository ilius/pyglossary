
from pyglossary.plugin_lib.slob import *


def find(word, slobs, match_prefix=True):
	seen = set()
	if isinstance(slobs, Slob):
		slobs = [slobs]

	variants = []

	for strength in (QUATERNARY, TERTIARY, SECONDARY, PRIMARY):
		variants.append((strength, None))

	if match_prefix:
		for strength in (QUATERNARY, TERTIARY, SECONDARY, PRIMARY):
			variants.append((strength, sortkey_length(strength, word)))

	for strength, maxlength in variants:
		for slob in slobs:
			d = slob.as_dict(strength=strength, maxlength=maxlength)
			for item in d[word]:
				dedup_key = (slob.id, item.id, item.fragment)
				if dedup_key in seen:
					continue
				else:
					seen.add(dedup_key)
					yield slob, item
