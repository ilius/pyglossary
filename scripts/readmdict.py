#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
log = logging.getLogger('root')

from struct import pack, unpack
from io import BytesIO
import re
import sys
import os
from os.path import splitext, isfile, isdir, extsep, basename, dirname

from pyglossary.plugin_lib.readmdict import MDX, MDD

# 2x3 compatible
if sys.hexversion >= 0x03000000:
	str, unicode = bytes, str


if __name__ == '__main__':
	import sys
	import os
	import os.path
	import argparse
	import codecs

	def passcode(s):
		try:
			regcode, userid = s.split(',')
		except:
			raise argparse.ArgumentTypeError("Passcode must be regcode,userid")
		try:
			regcode = codecs.decode(regcode, 'hex')
		except:
			raise argparse.ArgumentTypeError("regcode must be a 32 bytes hexadecimal string")
		return regcode, userid

	parser = argparse.ArgumentParser()
	parser.add_argument('-x', '--extract', action="store_true",
						help='extract mdx to source format and extract files from mdd')
	parser.add_argument('-s', '--substyle', action="store_true",
						help='substitute style definition if present')
	parser.add_argument('-d', '--datafolder', default="data",
						help='folder to extract data files from mdd')
	parser.add_argument('-e', '--encoding', default="",
						help='folder to extract data files from mdd')
	parser.add_argument('-p', '--passcode', default=None, type=passcode,
						help='register_code,email_or_deviceid')
	parser.add_argument("filename", nargs='?', help="mdx file name")
	args = parser.parse_args()

	_mdd =[]

	# use GUI to select file, default to extract
	if not args.filename:
		if sys.hexversion >= 0x03000000:
			import tkinter as tk
			import tkinter.filedialog as filedialog
		else:
			import Tkinter as tk
			import tkFileDialog as filedialog

		root = tk.Tk()
		root.withdraw()
		args.filename = filedialog.askopenfilename(parent=root)
		args.extract = True

	if not os.path.exists(args.filename):
		print("Please specify a valid MDX/MDD file")

	base, ext = os.path.splitext(args.filename)

	# read mdx file
	if ext.lower() == os.path.extsep + 'mdx':
		mdx = MDX(args.filename, args.encoding, args.substyle, args.passcode)
		if type(args.filename) is unicode:
			bfname = args.filename.encode('utf-8')
		else:
			bfname = args.filename
		print('======== %s ========' % bfname)
		print('  Number of Entries : %d' % len(mdx))
		for key, value in mdx.header.items():
			print('  %s : %s' % (key, value))
	else:
		mdx = None

	# # find companion mdd file
	# mdd_filename = ''.join([base, os.path.extsep, 'mdd'])
	# if os.path.exists(mdd_filename):
	# 	mdd = MDD(mdd_filename, args.passcode)
	# 	if type(mdd_filename) is unicode:
	# 		bfname = mdd_filename.encode('utf-8')
	# 	else:
	# 		bfname = mdd_filename
	# 	print('======== %s ========' % bfname)
	# 	print('  Number of Entries : %d' % len(mdd))
	# 	for key, value in mdd.header.items():
	# 		print('  %s : %s' % (key, value))
	# else:
	# 	mdd = None


	mddBase = "".join([base, os.path.extsep])
	for fname in (f"{mddBase}mdd", f"{mddBase}1.mdd"):
		if isfile(fname):
			mdd = MDD(fname)
			_mdd.append(mdd)

			if type(fname) is unicode:
				bfname = fname.encode('utf-8')
			else:
				bfname = fname
			print('======== %s ========' % bfname)
			print('  Number of Entries : %d' % len(mdd))
			for key, value in mdd.header.items():
				print('  %s : %s' % (key, value))

	mddN = 2
	while isfile(f"{mddBase}{mddN}.mdd"):
		mdd_filename = f"{mddBase}{mddN}.mdd"

		mdd = MDD(f"{mddBase}{mddN}.mdd")
		_mdd.append(mdd)
		mddN += 1


		if type(mdd_filename) is unicode:
			bfname = mdd_filename.encode('utf-8')
		else:
			bfname = mdd_filename
		print('======== %s ========' % bfname)
		print('  Number of Entries : %d' % len(mdd))
		for key, value in mdd.header.items():
			print('  %s : %s' % (key, value))


	log.info(f"Found {len(_mdd)} mdd files")



	if args.extract:
		# write out glos
		if mdx:
			output_fname = ''.join([base, os.path.extsep, 'txt'])
			tf = open(output_fname, 'wb')
			for key, value in mdx.items():
				tf.write(key)
				tf.write(b'\r\n')
				tf.write(value)
				if not value.endswith(b'\n'):
					tf.write(b'\r\n')
				tf.write(b'</>\r\n')
			tf.close()
			# write out style
			if mdx.header.get('StyleSheet'):
				style_fname = ''.join([base, '_style', os.path.extsep, 'txt'])
				sf = open(style_fname, 'wb')
				sf.write(b'\r\n'.join(mdx.header['StyleSheet'].splitlines()))
				sf.close()
		# write out optional data files
		if _mdd:
			for mdd in _mdd:
				datafolder = os.path.join(os.path.dirname(args.filename), args.datafolder)
				if not os.path.exists(datafolder):
					os.makedirs(datafolder)
				for key, value in mdd.items():
					fname = key.decode('utf-8').replace('\\', os.path.sep)
					dfname = datafolder + fname
					if not os.path.exists(os.path.dirname(dfname)):
						os.makedirs(os.path.dirname(dfname))
					df = open(dfname, 'wb')
					df.write(value)
					df.close()
