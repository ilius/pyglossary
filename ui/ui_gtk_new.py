# -*- coding: utf-8 -*-
## ui_gtk_ng.py
##
## Copyright © 2008-2010 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
## Thanks to 'Pier Carteri' <m3tr0@dei.unipd.it> for program Py_Shell.py
## Thanks to 'Milad Rastian' for program pySQLiteGUI
##
## This program is a free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3, or (at your option)
## any later version.
##
## You can get a copy of GNU General Public License along this program
## But you can always get it from http://www.gnu.org/licenses/gpl.txt
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
## GNU General Public License for more details.

import shutil
import sys
import os
from os.path import join, isabs
import logging
import traceback

from pyglossary.text_utils import urlToPath, click_website, startRed, endFormat
from pyglossary.glossary import *
from base import *
from pyglossary import core

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GdkPixbuf

log = logging.getLogger('root')

#use_psyco_file = join(srcDir, 'use_psyco')
use_psyco_file = '%s_use_psyco'%confPath
psyco_found = None

gtk.Window.set_default_icon_from_file(logo)

_ = str ## later replace with translator function

pixDir = join(rootDir, 'res') ## FIXME

def getCopressedFileExt(fpath):
    fname, ext = os.path.splitext(fpath.lower())
    if ext in ('.gz', '.bz2', '.zip'):
        fname, ext = os.path.splitext(fname)
    return ext

buffer_get_text = lambda b: b.get_text(b.get_start_iter(), b.get_end_iter(), True)

def pack(box, child, expand=False, fill=False, padding=0):
    if isinstance(box, gtk.Box):
        box.pack_start(child, expand, fill, padding)
    elif isinstance(box, gtk.CellLayout):
        box.pack_start(child, expand)
    else:
        raise TypeError('pack: unkown type %s'%type(box))

def imageFromFile(path):## the file must exist
    if not isabs(path):
        path = join(pixDir, path)
    im = gtk.Image()
    try:
        im.set_from_file(path)
    except:
        myRaise()
    return im


class FormatComboBox(gtk.ComboBox):
    def __init__(self):
        gtk.ComboBox.__init__(self)
        self.model = gtk.ListStore(
            str,## format name, hidden
            #GdkPixbuf.Pixbuf,## icon
            str,## format description, shown
        )
        self.set_model(self.model)
        ###
        cell = gtk.CellRendererText()
        self.add_attribute(cell, 'text', 0)
        ###
        #cell = gtk.CellRendererPixbuf()
        #pack(self, cell, False)
        #self.add_attribute(cell, 'pixbuf', 1)
        ###
        cell = gtk.CellRendererText()
        pack(self, cell, True)
        self.add_attribute(cell, 'text', 1)
    def addFormat(self, _format):
        self.get_model().append((
            _format,
            #icon,
            Glossary.formatsDesc[_format],
        ))
    def getActive(self):
        index = gtk.ComboBox.get_active(self)
        if index is None or index < 0:
            return ''
        return self.get_model()[index][0]
    def setActive(self, _format):
        for i, row in enumerate(self.get_model()):
            if row[0] == _format:
                gtk.ComboBox.set_active(self, i)
                return
        


class InputFormatComboBox(FormatComboBox):
    def __init__(self):
        FormatComboBox.__init__(self)
        for _format in Glossary.readFormats:
            self.addFormat(_format)

class OutputFormatComboBox(FormatComboBox):
    def __init__(self):
        FormatComboBox.__init__(self)
        for _format in Glossary.writeFormats:
            self.addFormat(_format)




class GtkTextviewLogHandler(logging.Handler):
    def __init__(self, treeview_dict):
        logging.Handler.__init__(self)
        #####
        self.buffers = {}
        for levelname in (
            'CRITICAL',
            'ERROR',
            'WARNING',
            'INFO',
            'DEBUG',
        ):
            textview = treeview_dict[levelname]
            ###
            buff = textview.get_buffer()
            tag = gtk.TextTag.new(levelname)
            buff.get_tag_table().add(tag)
            ###
            self.buffers[levelname] = buff
    def getTag(self, levelname):
        return self.buffers[levelname].get_tag_table().lookup(levelname)
    def setColor(self, levelname, color):## FIXME
        self.getTag(levelname).set_property('foreground-gdk', color)
    def emit(self, record):
        #print('GtkTextviewLogHandler.emit', record.levelname, record.getMessage(), record.exc_info)
        msg = record.getMessage()
        #msg = msg.replace('\x00', '')
        ###
        if record.exc_info:
            _type, value, tback = record.exc_info
            tback_text = ''.join(traceback.format_exception(_type, value, tback))
            if msg:
                msg += '\n'
            msg += tback_text
        ###
        buff = self.buffers[record.levelname]
        ###
        buff.insert_with_tags_by_name(
            buff.get_end_iter(),
            msg + '\n',
            record.levelname,
        )


class GtkSingleTextviewLogHandler(GtkTextviewLogHandler):
    def __init__(self, textview):
        GtkTextviewLogHandler.__init__(self, {
            'CRITICAL': textview,
            'ERROR': textview,
            'WARNING': textview,
            'INFO': textview,
            'DEBUG': textview,
        })


class BrowseButton(gtk.Button):
    def __init__(self, setFilePathFunc, label='Browse', actionSave=False, title='Select File'):
        gtk.Button.__init__(self)
        ###
        self.set_label(label)
        self.set_image(gtk.Image.new_from_icon_name(
            'document-save' if actionSave else 'document-open',
            gtk.IconSize.BUTTON,
        ))
        ###
        self.actionSave = actionSave
        self.setFilePathFunc = setFilePathFunc
        self.title = title
        ###
        self.connect('clicked', self.onClick)
    def onClick(self, widget):
        fcd = gtk.FileChooserDialog(
            parent=self.get_toplevel(),
            action=gtk.FileChooserAction.SAVE if self.actionSave else gtk.FileChooserAction.OPEN,
            title=self.title,
        )
        fcd.add_button(gtk.STOCK_CANCEL, gtk.ResponseType.CANCEL)
        fcd.add_button(gtk.STOCK_OK, gtk.ResponseType.OK)
        fcd.connect('response', lambda w, e: fcd.hide())
        fcd.connect('file-activated', lambda w: fcd.response(gtk.ResponseType.OK))
        if fcd.run()==gtk.ResponseType.OK:
            self.setFilePathFunc(fcd.get_filename())
        fcd.destroy()

class UI(gtk.Dialog, UIBase):
    def write(self, tag):## FIXME
        pass
    def __init__(self, **options):
        gtk.Dialog.__init__(self)
        self.set_title('PyGlossary (Gtk3)')
        self.resize(600, 600)
        self.connect('delete-event', self.onDeleteEvent)
        self.prefPages = []
        #####
        self.pref = {}
        self.pref_load(**options)
        #log.pretty(self.pref, 'ui.pref=')
        #####
        self.assert_quit = False
        self.path = ''
        self.glos = Glossary(ui=self)
        ##################### Tab 1 - Convert #############################
        sizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
        ####
        vbox = gtk.VBox()
        vbox.label = _('Convert')
        vbox.icon = '' ## '*.png'
        self.prefPages.append(vbox)
        ######
        hbox = gtk.HBox(spacing=3)
        hbox.label = gtk.Label(label=_('Input Format')+':')
        pack(hbox, hbox.label)
        sizeGroup.add_widget(hbox.label) 
        hbox.label.set_property('xalign', 0)
        self.convertInputFormatCombo = InputFormatComboBox()
        pack(hbox, self.convertInputFormatCombo)
        pack(vbox, hbox)
        ###
        hbox = gtk.HBox(spacing=3)
        hbox.label = gtk.Label(label=_('Input File')+':')
        pack(hbox, hbox.label)
        sizeGroup.add_widget(hbox.label) 
        hbox.label.set_property('xalign', 0)
        self.convertInputEntry = gtk.Entry()
        pack(hbox, self.convertInputEntry, 1, 1)
        button = BrowseButton(
            self.convertInputEntry.set_text,
            label='Browse',
            actionSave=False,
            title='Select Input File',
        )
        pack(hbox, button)
        pack(vbox, hbox)
        ##
        self.convertInputEntry.connect('changed', self.convertInputEntryChanged)
        #####
        vbox.sep1 = gtk.Label(label='')
        vbox.sep1.show()
        pack(vbox, vbox.sep1)
        #####
        hbox = gtk.HBox(spacing=3)
        hbox.label = gtk.Label(label=_('Output Format')+':')
        pack(hbox, hbox.label)
        sizeGroup.add_widget(hbox.label)
        hbox.label.set_property('xalign', 0)
        self.convertOutputFormatCombo = OutputFormatComboBox()
        pack(hbox, self.convertOutputFormatCombo)
        pack(vbox, hbox)
        ###
        hbox = gtk.HBox(spacing=3)
        hbox.label = gtk.Label(label=_('Output File')+':')
        pack(hbox, hbox.label)
        sizeGroup.add_widget(hbox.label)
        hbox.label.set_property('xalign', 0)
        self.convertOutputEntry = gtk.Entry()
        pack(hbox, self.convertOutputEntry, 1, 1)
        button = BrowseButton(
            self.convertOutputEntry.set_text,
            label='Browse',
            actionSave=True,
            title='Select Output File',
        )
        pack(hbox, button)
        pack(vbox, hbox)
        ##
        self.convertOutputEntry.connect('changed', self.convertOutputEntryChanged)
        #####
        hbox = gtk.HBox(spacing=10)
        label = gtk.Label(label='')
        pack(hbox, label, 1, 1, 10)
        self.convertButton = gtk.Button()
        self.convertButton.set_label('Convert')
        self.convertButton.connect('clicked', self.convertClicked)
        pack(hbox, self.convertButton, 1, 1, 10)
        pack(vbox, hbox, 0, 0, 15)
        ##################### Tab 1 - Reverse #############################
        sizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
        ####
        vbox = gtk.VBox()
        vbox.label = _('Reverse')
        vbox.icon = '' ## '*.png'
        self.prefPages.append(vbox)
        ######

        #####
        ###################################################################
        notebook = gtk.Notebook()
        self.notebook = notebook
        #####################################
        for vbox in self.prefPages:
            l = gtk.Label(label=vbox.label)
            l.set_use_underline(True)
            vb = gtk.VBox(spacing=3)
            if vbox.icon:
                vbox.image = imageFromFile(vbox.icon)
                pack(vb, vbox.image)
            pack(vb, l)
            vb.show_all()
            notebook.append_page(vbox, vb)
            try:
                notebook.set_tab_reorderable(vbox, True)
            except AttributeError:
                pass
        #######################
        #notebook.set_property('homogeneous', True)## not in gtk3 FIXME
        #notebook.set_property('tab-border', 5)## not in gtk3 FIXME
        #notebook.set_property('tab-hborder', 15)## not in gtk3 FIXME
        pack(self.vbox, notebook, 0, 0)
        #for i in ui.prefPagesOrder:
        #    try:
        #        j = prefPagesOrder[i]
        #    except IndexError:
        #        continue
        #    notebook.reorder_child(self.prefPages[i], j)
        ###################################################################
        self.consoleTextview = textview = gtk.TextView()
        frame = gtk.Frame()
        frame.add(textview)
        frame.set_border_width(3)
        pack(self.vbox, frame, 1, 1)
        ###
        handler = GtkSingleTextviewLogHandler(textview)
        log.addHandler(handler)
        ###
        textview.override_background_color(gtk.StateFlags.NORMAL, gdk.RGBA(0, 0, 0, 1))
        ###
        handler.setColor('CRITICAL', gdk.color_parse('red'))
        handler.setColor('ERROR', gdk.color_parse('red'))
        handler.setColor('WARNING', gdk.color_parse('yellow'))
        handler.setColor('INFO', gdk.color_parse('white'))
        handler.setColor('DEBUG', gdk.color_parse('white'))
        ###
        textview.get_buffer().set_text('Output & Error Console:\n')
        textview.set_editable(False)
        ###
        #self.verbosityCombo.connect('changed', self.verbosityComboChanged)
        #self.verbosityComboChanged()
        ################################################################
        self.vbox.show_all()
    def run(self, editPath=None, read_options=None):
        if read_options is None:
            read_options = {}
        #if editPath:
            #self.notebook.set_current_page(3)
            #log.info('Opening file "%s" for edit. please wait...'%editPath)
            #while gtk.events_pending():
            #    gtk.main_iteration_do(False)
            #self.dbe_open(editPath, **read_options)
        gtk.Dialog.present(self)
        gtk.main()
    def onDeleteEvent(self, widget, event):
        self.destroy()
        gtk.main_quit()
    def convertClicked(self, widget=None):
        inPath = self.convertInputEntry.get_text()
        if not inPath:
            log.critical('Input file path is empty!');return
        inFormat = self.convertInputFormatCombo.getActive()
        if inFormat:
            inFormatDesc = Glossary.formatsDesc[inFormat]
        else:
            inFormatDesc = ''
            #log.critical('Input format is empty!');return

        outPath = self.convertOutputEntry.get_text()
        if not outPath:
            log.critical('Output file path is empty!');return
        outFormat = self.convertOutputFormatCombo.getActive()
        if outFormat:
            outFormatDesc = Glossary.formatsDesc[outFormat]
        else:
            outFormatDesc = ''
            #log.critical('Output format is empty!');return
            

        while gtk.events_pending():
            gtk.main_iteration_do(False)

        self.convertButton.set_sensitive(False)
        try:
            t0 = time.time()
            #if inFormat=='Omnidic':
            #    dicIndex = self.xml.get_widget('spinbutton_omnidic_i').get_value_as_int()
            #    ex = self.glos.readOmnidic(inPath, dicIndex=dicIndex)
            #else:
            log.info('Reading %s, please wait...'%inFormatDesc)
            succeed = self.glos.read(inPath, format=inFormat)
            if succeed:
                log.info('reading %s file: "%s" done'%(
                    inFormat,
                    inPath,
                ))
            else:
                log.error('reading %s file: "%s" failed.'%(inFormat, inPath))
                return False
            #self.inFormat = inFormat
            #self.inPath = inPath
            self.glos.uiEdit()
            #self.progress(1.0, 'Loading Comleted')
            log.debug('running time of read: %3f seconds'%(time.time()-t0))
            for x in self.glos.info:
                log.info('%s="%s"'%(x[0], x[1]))

            while gtk.events_pending():
                gtk.main_iteration_do(False)

            log.info('Writing %s, please wait...'%outFormatDesc)
            succeed = self.glos.write(outPath, format=outFormat)
            if succeed:
                log.info('writing %s file: "%s" done.'%(outFormat, outPath))
                log.debug('running time of write: %3f seconds'%(time.time()-t0))
            else:
                log.error('writing %s file: "%s" failed.'%(outFormat, outPath))
            return succeed

        finally:
            self.convertButton.set_sensitive(True)
            self.assert_quit = False

        return True


    def convertInputEntryChanged(self, widget=None):
        inPath = self.convertInputEntry.get_text()
        inFormat = self.convertInputFormatCombo.getActive()
        if len(inPath) > 7:
            if inPath[:7]=='file://':
                inPath = urlToPath(inPath)
                self.convertInputEntry.set_text(inPath)

        if self.pref['auto_set_for']:## and not inFormat:
            inExt = getCopressedFileExt(inPath)
            try:
                inFormatNew = Glossary.extFormat[inExt]
            except KeyError:
                pass
            else:
                self.convertInputFormatCombo.setActive(inFormatNew)
            
        if self.pref['auto_set_out']:
            outFormat = self.convertOutputFormatCombo.getActive()
            outPath = self.convertOutputEntry.get_text()
            if outFormat and not outPath and '.' in inPath:
                outPath = os.path.splitext(inPath)[0] + Glossary.formatsExt[outFormat][0]
                self.convertOutputEntry.set_text(outPath)

    def convertOutputEntryChanged(self, widget=None):
        outPath = self.convertOutputEntry.get_text()
        outFormat = self.convertOutputFormatCombo.getActive()
        if not outPath:
            return
        #outFormat = self.combobox_o.get_active_text()
        if len(outPath)>7:
            if outPath[:7]=='file://':
                outPath = urlToPath(outPath)
                self.convertOutputEntry.set_text(outPath)
        if self.pref['auto_set_for']:## and not outFormat:
            outExt = getCopressedFileExt(outPath)
            try:
                outFormatNew = Glossary.extFormat[outExt]
            except KeyError:
                pass
            else:
                self.convertOutputFormatCombo.setActive(outFormatNew)
        



    






