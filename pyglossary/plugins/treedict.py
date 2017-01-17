# -*- coding: utf-8 -*-

from formats_common import *
import subprocess

enable = True
format = 'Treedict'
description = 'TreeDict'
extentions = ['.tree', '.treedict']
readOptions = []
writeOptions = [
	'encoding',  # str
]


def write(glos, filename, encoding='utf-8', archive='tar.bz2', sep=os.sep):
	if os.path.exists(filename):
		if os.path.isdir(filename):
			if os.listdir(filename):
				log.warning('Warning: directory "%s" is not empty.')
		else:
			raise IOError('"%s" is not a directory')
	for entry in glos:
		defi = entry.getDefi()
		for word in entry.getWords():
			if not word:
				log.error('empty word')
				continue
			chars = list(word)
			try:
				os.makedirs(filename + os.sep + sep.join(chars[:-1]))
			except:
				pass
			entryFname = '%s%s%s.m' % (
				filename,
				os.sep,
				sep.join(chars),
			)
			try:
				with open(entryFname, 'a', encoding=encoding) as entryFp:
					entryFp.write(defi)
			except:
				log.exception('')
	if archive:
		if archive == 'tar.gz':
			(output, error) = subprocess.Popen(
				['tar', '-czf', filename+'.tar.gz', filename],
				stdout=subprocess.PIPE
			).communicate()
		elif archive == 'tar.bz2':
			(output, error) = subprocess.Popen(
				['tar', '-cjf', filename+'.tar.bz2', filename],
				stdout=subprocess.PIPE
			).communicate()
		elif archive == 'zip':
			(output, error) = subprocess.Popen(
				['zip', '-r', filename+'.zip', filename],
				stdout=subprocess.PIPE
			).communicate()
		else:
			log.error('Undefined archive format: "%s"' % archive)
		try:
			shutil.rmtree(filename, ignore_errors=True)
		except:
			pass
