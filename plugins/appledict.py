#!/usr/bin/python
# -*- coding: utf-8 -*-
enable = True
format = 'AppleDict'
description = 'AppleDict Source (xml)'
extentions = ['.xml']
readOptions = []
writeOptions = []

from BeautifulSoup import BeautifulSoup

import os
import re

def write_plist(glos, filename):
    f = open(filename, 'w')
    basename = os.path.splitext(os.path.basename(filename))[0]
    # identifier must be unique
    # use file base name
    identifier = basename.replace(' ','')
    # strip html tags
    copyright = BeautifulSoup(glos.getInfo('copyright')).text

    f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
            '<plist version="1.0">\n'
            '<dict>\n')

    f.write('    <key>CFBundleDevelopmentRegion</key>\n'
            '    <string>English</string>\n')
    f.write('    <key>CFBundleIdentifier</key>\n'
            '    <string>com.babylon.%s</string>\n' % identifier)
    f.write('    <key>CFBundleDisplayName</key>\n'
            '    <string>%s</string>\n' % glos.getInfo('name'))
    f.write('    <key>CFBundleName</key>\n'
            '    <string>%s</string>\n' % basename)
    f.write('    <key>CFBundleShortVersionString</key>\n'
            '    <string>1.0</string>\n')
    f.write((u'    <key>DCSDictionaryCopyright</key>\n'
             u'    <string>%s.</string>\n' % copyright).encode('utf8'))
    f.write('    <key>DCSDictionaryManufacturerName</key>\n'
            '    <string>%s.</string>\n' % glos.getInfo('author'))
    f.write('</dict>\n'
            '</plist>\n')
    f.close()

def write_xml(glos, filename):
    f = open(filename, 'w')

    # write header
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<d:dictionary xmlns="http://www.w3.org/1999/xhtml" xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng">\n')

    # write entries
    entry_ids= []
    for item in glos.data:
        # strip double quotes and html tags
        title = re.sub('<[^<]+?>|"|[<>]', '', item[0])
        if not title:
            continue
        # id contains no white space
        id = title.replace(' ','_')
        # check entry id duplicates
        while id in entry_ids:
            id = id + '_'
        entry_ids.append(id)
        # get alternatives list
        try:
            alts = item[2]['alts']
        except:
            alts = []
        
        # begin entry
        f.write('<d:entry id="%(id)s" d:title="%(title)s">\n'%{'id':id, 'title':title})

        # index values
        #   title as index
        f.write('    <d:index d:value="%s"/>\n'%title)
        #   alternative items as index also
        for alt in alts:
            if alt != title:
                f.write('    <d:index d:value="%s"/>\n'%alt)

        # nice header to display
        f.write('<h1>%s</h1>\n'%title)

        # xhtml is stict
        content = item[1]
        soup  = BeautifulSoup(content)
        content = soup.prettify()
        f.write(content)

        # end entry
        f.write('\n</d:entry>\n')

    # end dictionary
    f.write('</d:dictionary>\n')
    f.close()

def write_css(fname):
    f = open(fname, "w")
    f.write("""
@charset "UTF-8";
@namespace d url(http://www.apple.com/DTDs/DictionaryService-1.0.rng);
 
d|entry {
}

h1  {
    font-size: 150%;
}
 
h3  {
    font-size: 100%;
}
""")
    f.close()

def write_makefile(fname):
    f = open(os.path.join(os.path.dirname(fname),"Makefile"), "w")
    f.write("""
DICT_NAME       =   "%(dict_name)s"
DICT_SRC_PATH   =   "%(dict_name)s.xml"
CSS_PATH        =   "%(dict_name)s.css"
PLIST_PATH      =   "%(dict_name)s.plist"


# The DICT_BUILD_TOOL_DIR value is used also in "build_dict.sh" script.
# You need to set it when you invoke the script directly.

DICT_BUILD_TOOL_DIR =   "/Developer/Extras/Dictionary Development Kit"
DICT_BUILD_TOOL_BIN =   "$(DICT_BUILD_TOOL_DIR)/bin"

DICT_DEV_KIT_OBJ_DIR    =   ./objects
export  DICT_DEV_KIT_OBJ_DIR

DESTINATION_FOLDER  =   ~/Library/Dictionaries
RM          =   /bin/rm

all:
	"$(DICT_BUILD_TOOL_BIN)/build_dict.sh" $(DICT_BUILD_OPTS) $(DICT_NAME) $(DICT_SRC_PATH) $(CSS_PATH) $(PLIST_PATH)
	echo "Done."


install:
	echo "Installing into $(DESTINATION_FOLDER)".
	mkdir -p $(DESTINATION_FOLDER)
	ditto --noextattr --norsrc $(DICT_DEV_KIT_OBJ_DIR)/$(DICT_NAME).dictionary  $(DESTINATION_FOLDER)/$(DICT_NAME).dictionary
	touch $(DESTINATION_FOLDER)
	echo "Done."
	echo "To test the new dictionary, try Dictionary.app."

clean:
	$(RM) -rf $(DICT_DEV_KIT_OBJ_DIR)
""" % {"dict_name" :  os.path.basename(fname)})

def write(glos, fname):
    basename = os.path.splitext(fname)[0]
    write_plist(glos, basename + '.plist')
    write_xml(glos, basename + '.xml')
    write_css(basename + '.css')
    write_makefile(basename)

if __name__ == '__main__':
    import sys, os.path
    import glossary as gl
    glos = gl.Glossary()

    informat = gl.Glossary.descFormat["Babylon (bgl)"]
    outformat = gl.Glossary.descFormat["AppleDict Source (xml)"]

    filename = sys.argv[1]
    basename = os.path.splitext(os.path.basename(filename))[0]

    outdir = sys.argv[2]
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    glos.read(filename, format=informat, resPath=os.path.join(outdir, "OtherResources"))


    glos.write(os.path.join(outdir, basename), format=outformat)

