#!/usr/bin/env python2

try:
    import py2exe
except ImportError:
    py2exe = None

import glob, os, sys
from os.path import join, dirname

from distutils.core import setup
from distutils.command.install import install

from pyglossary.glossary import VERSION

relRootDir = 'share/pyglossary'


class my_install(install):
    def run(self):
        install.run(self)
        if os.sep == '/':
            binPath = join(self.install_scripts, 'pyglossary')
            print 'creating script file "%s"'%binPath
            open(binPath, 'w').write(join(self.install_data, relRootDir, 'pyglossary.pyw'))
            os.chmod(binPath, 0755)


data_files = [
    (relRootDir, [
        'about',
        'license',
        'help',
        'pyglossary.pyw',
    ]),
    (relRootDir+'/ui', glob.glob('ui/*.py')),
    (relRootDir+'/ui/glade', glob.glob('ui/glade/*')),
    (relRootDir+'/res', glob.glob('res/*')),
    ('share/doc/pyglossary', []),
    ('share/doc/pyglossary/non-gui_examples', glob.glob('doc/non-gui_examples/*')),
    ('share/doc/pyglossary/Babylon', glob.glob('doc/Babylon/*')),
    ('share/doc/pyglossary/DSL', glob.glob('doc/DSL/*')),
    ('share/doc/pyglossary/Octopus MDict', glob.glob('doc/Octopus MDict/*')),
    ('share/applications', ['pyglossary.desktop']),
    ('share/pixmaps', ['res/pyglossary.png']),
]

def files(folder):
    for path in glob.glob(folder+'/*'):
        if os.path.isfile(path):
            yield path
if py2exe:
    py2exeoptions = {
        'script_args': ['py2exe'],
        'bundle_files': 1,
        'windows': [
            {
                'script': 'pyglossary.pyw',
                'icon_resources': [
                    (1, 'res/pyglossary.ico'),
                ],
            },
        ],
        'zipfile': None,
        'options': {
            'py2exe': {
                'packages': [
                    'pyglossary',
                    'ui.ui_tk',
                    #'ui.ui_gtk',
                    #'BeautifulSoup',
                    #'xml',
                    'Tkinter', 'tkFileDialog', 'Tix',
                    #'gtk', 'glib', 'gobject',
                ],
            },
        },
    }
    data_files = [
        ('tcl/tix8.1', files(join(sys.prefix, 'tcl', 'tix8.4.3'))),
        ('tcl/tix8.1/bitmaps', files(join(sys.prefix, 'tcl', 'tix8.4.3', 'bitmaps'))),
        ('tcl/tix8.1/pref', files(join(sys.prefix, 'tcl', 'tix8.4.3', 'pref'))),
        ('tcl/tcl8.1/init.tcl', [join(sys.prefix, 'tcl', 'tix8.4.3', 'init.tcl')]),
        ('', ['about', 'license', 'help']),
        ('ui', glob.glob('ui/*.py')),
        ('ui/glade', glob.glob('ui/glade/*')),
        ('res', glob.glob('res/*')),
        ('plugins', glob.glob('pyglossary/plugins/*')),
        ('doc/pyglossary', ['doc/bgl_structure.svgz', ]),
        ('doc/pyglossary/non-gui_examples', glob.glob('doc/non-gui_examples/*')),
    ]
else:
    py2exeoptions = {}


setup(
    name = 'pyglossary',
    version = VERSION,
    cmdclass = {
        'install': my_install,
    },
    description = 'A tool for workig with dictionary databases',
    author = 'Saeed Rasooli',
    author_email = 'saeed.gnu@gmail.com',
    license = 'GPLv3',
    url = 'https://github.com/ilius/pyglossary',
    scripts = [
        #'pyglossary.pyw',
    ],
    packages = [
        'pyglossary',
    ],
    package_data = {
        'pyglossary': [
            'plugins/*.py',
        ],
    },
    data_files = data_files,
    **py2exeoptions
)



