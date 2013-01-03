#!/usr/bin/env python2

try:
	import py2exe
except ImportError:
	py2exe = None

import glob, os
from pyglossary.glossary import VERSION

from distutils.core import setup
from distutils.dep_util import newer
from distutils.command.build_scripts \
         import build_scripts as distutils_build_scripts

class build_scripts(distutils_build_scripts):
    description = 'copy scripts to build directory'
    def run(self):
        self.mkpath(self.build_dir)
        for script in self.scripts:
            newpath = os.path.join(self.build_dir, os.path.basename(script))
            if newpath.lower().endswith('.py'): newpath = newpath[:-3]
            elif newpath.lower().endswith('.pyw'): newpath = newpath[:-4]
            if newer(script, newpath) or self.force:
                self.copy_file(script, newpath)
                
data_files = [('share/pyglossary',
	                        ['about','license','help']),
	                ('share/pyglossary/ui',glob.glob('ui/*.py')),
	                ('share/pyglossary/ui/glade',glob.glob('ui/glade/*')),
	                ('share/pyglossary/res',glob.glob('res/*')),
	                ('share/doc/pyglossary',['doc/bgl_structure.svgz']),
	                ('share/doc/pyglossary/non-gui_examples',
	                        glob.glob('doc/non-gui_examples/*')),
	                ('share/applications',['pyglossary.desktop']),
	                ('share/pixmaps',['res/pyglossary.png'])]

if py2exe:
	py2exeoptions = {
		'windows': [ {
			'script': 'pyglossary.pyw',
			'icon_resources': [(1, 'res/pyglossary.ico')]
		} ],
		'zipfile': None,
		'options': {
			'py2exe': {
				'packages': ('pyglossary')
			}
		}
	}
	data_files = [('', ['about','license','help']),
	                ('ui',glob.glob('ui/*.py')),
	                ('ui/glade',glob.glob('ui/glade/*')),
	                ('res',glob.glob('res/*')),
	                ('doc/pyglossary',['doc/bgl_structure.svgz']),
	                ('doc/pyglossary/non-gui_examples',
	                        glob.glob('doc/non-gui_examples/*'))]
else:
	py2exeoptions = {}


setup(
	name         = 'pyglossary',
	version      = VERSION,
	cmdclass     = { 'build_scripts': build_scripts },
	description  = 'Working on glossaries (dictionary databases) using python.',
	author       = 'Saeed Rasooli',
	author_email = 'saeed.gnu@gmail.com',
	license      = 'GPLv3',
	url          = 'https://github.com/ilius/pyglossary',
	scripts      = ['pyglossary.pyw'],
	packages     = ['pyglossary'],
	package_data = {'pyglossary': ['plugins/*.py']},
	data_files   = data_files,
	**py2exeoptions
)

