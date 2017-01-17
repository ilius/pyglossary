# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'Omnidic'
description = 'Omnidic'
extentions = ['.omni', '.omnidic']
readOptions = []
writeOptions = []


def write(glos, filename, dicIndex=16):
	if not isinstance(dicIndex, int):
		raise TypeError(
			'invalid dicIndex=%r, must be integer' % dicIndex
		)
	with indir(filename, create=True):
		indexFp = open(str(dicIndex), 'w')

		for bucketIndex, bucket in enumerate(glos.iterEntryBuckets(100)):
			if bucketIndex == 0:
				bucketFilename = '%s99' % dicIndex
			else:
				bucketFilename = '%s%s' % (
					dicIndex,
					bucketIndex * 100 + len(bucket) - 1,
				)

			indexFp.write('%s#%s#%s\n' % (
				bucket[0].getWord(),
				bucket[-1].getWord(),
				bucketFilename,
			))

			bucketFileObj = open(bucketFilename, 'w')
			for entry in bucket:
				word = entry.getWord()
				defi = entry.getDefi()
				defi = defi.replace('\n', '  ')  # FIXME
				bucketFileObj.write('%s#%s\n' % (word, defi))
			bucketFileObj.close()

		indexFp.close()
