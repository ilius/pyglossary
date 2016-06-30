# -*- coding: utf-8 -*-
# ui_gtk.py
#
# Copyright © 2008-2010 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# Thanks to 'Pier Carteri' <m3tr0@dei.unipd.it> for program Py_Shell.py
# Thanks to 'Milad Rastian' for program pySQLiteGUI
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# You can get a copy of GNU General Public License along this program
# But you can always get it from http://www.gnu.org/licenses/gpl.txt
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

import shutil
import sys
import os
from os.path import join, isfile, isabs, splitext
import logging
import traceback

from pyglossary.text_utils import urlToPath
from pyglossary.os_utils import click_website
from pyglossary.glossary import *
from .base import *
from pyglossary import core

import gi
gi.require_version('Gtk', '3.0')

from .gtk3_utils import *
from .gtk3_utils.utils import *
from .gtk3_utils.dialog import MyDialog
from .gtk3_utils.resize_button import ResizeButton

# from gi.repository import GdkPixbuf

log = logging.getLogger('root')

gtk.Window.set_default_icon_from_file(logo)

_ = str  # later replace with translator function

pixDir = join(rootDir, 'res')  # FIXME


def getCopressedFileExt(fpath):
    fname, ext = splitext(fpath.lower())
    if ext in ('.gz', '.bz2', '.zip'):
        fname, ext = splitext(fname)
    return ext


def buffer_get_text(b):
    return b.get_text(
        b.get_start_iter(),
        b.get_end_iter(),
        True,
    )


def pack(box, child, expand=False, fill=False, padding=0):
    if isinstance(box, gtk.Box):
        box.pack_start(child, expand, fill, padding)
    elif isinstance(box, gtk.CellLayout):
        box.pack_start(child, expand)
    else:
        raise TypeError('pack: unkown type %s' % type(box))


def imageFromFile(path):  # the file must exist
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
            str,  # format name, hidden
            # GdkPixbuf.Pixbuf,# icon
            str,  # format description, shown
        )
        self.set_model(self.model)

        cell = gtk.CellRendererText()
        self.add_attribute(cell, 'text', 0)

        # cell = gtk.CellRendererPixbuf()
        # pack(self, cell, False)
        # self.add_attribute(cell, 'pixbuf', 1)

        cell = gtk.CellRendererText()
        pack(self, cell, True)
        self.add_attribute(cell, 'text', 1)

    def addFormat(self, _format):
        self.get_model().append((
            _format,
            # icon,
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

        self.buffers = {}
        for levelname in (
            'CRITICAL',
            'ERROR',
            'WARNING',
            'INFO',
            'DEBUG',
        ):
            textview = treeview_dict[levelname]

            buff = textview.get_buffer()
            tag = gtk.TextTag.new(levelname)
            buff.get_tag_table().add(tag)

            self.buffers[levelname] = buff

    def getTag(self, levelname):
        return self.buffers[levelname].get_tag_table().lookup(levelname)

    def setColor(self, levelname, color):  # FIXME
        self.getTag(levelname).set_property('foreground-gdk', color)

    def emit(self, record):
        msg = record.getMessage()
        # msg = msg.replace('\x00', '')

        if record.exc_info:
            _type, value, tback = record.exc_info
            tback_text = ''.join(
                traceback.format_exception(_type, value, tback)
            )
            if msg:
                msg += '\n'
            msg += tback_text

        buff = self.buffers[record.levelname]

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
    def __init__(
        self,
        setFilePathFunc,
        label='Browse',
        actionSave=False,
        title='Select File',
    ):
        gtk.Button.__init__(self)

        self.set_label(label)
        self.set_image(gtk.Image.new_from_icon_name(
            'document-save' if actionSave else 'document-open',
            gtk.IconSize.BUTTON,
        ))

        self.actionSave = actionSave
        self.setFilePathFunc = setFilePathFunc
        self.title = title

        self.connect('clicked', self.onClick)

    def onClick(self, widget):
        fcd = gtk.FileChooserDialog(
            parent=self.get_toplevel(),
            action=gtk.FileChooserAction.SAVE if self.actionSave
            else gtk.FileChooserAction.OPEN,
            title=self.title,
        )
        fcd.add_button(gtk.STOCK_CANCEL, gtk.ResponseType.CANCEL)
        fcd.add_button(gtk.STOCK_OK, gtk.ResponseType.OK)
        fcd.connect('response', lambda w, e: fcd.hide())
        fcd.connect(
            'file-activated',
            lambda w: fcd.response(gtk.ResponseType.OK)
        )
        if fcd.run() == gtk.ResponseType.OK:
            self.setFilePathFunc(fcd.get_filename())
        fcd.destroy()


class UI(gtk.Dialog, MyDialog, UIBase):
    def write(self, tag):  # FIXME
        pass

    def status(self, msg):
        # try:
        #    _id = self.statusMsgDict[msg]
        # except KeyError:
        #    _id = self.statusMsgDict[msg] = self.statusNewId
        #    self.statusNewId += 1
        _id = self.statusBar.get_context_id(msg)
        self.statusBar.push(_id, msg)

    def __init__(self, **options):
        gtk.Dialog.__init__(self)
        self.set_title('PyGlossary (Gtk3)')
        self.resize(800, 800)
        self.connect('delete-event', self.onDeleteEvent)
        self.prefPages = []
        # self.statusNewId = 0
        # self.statusMsgDict = {}## message -> id
        #####
        self.pref = {}
        self.pref_load(**options)
        # log.pretty(self.pref, 'ui.pref=')
        #####
        self.assert_quit = False
        self.path = ''
        self.glos = Glossary(ui=self)
        # ____________________ Tab 1 - Convert ____________________ #
        sizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
        ####
        vbox = gtk.VBox()
        vbox.label = _('Convert')
        vbox.icon = ''  # '*.png'
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
        self.convertInputEntry.connect(
            'changed',
            self.convertInputEntryChanged,
        )
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
        self.convertOutputEntry.connect(
            'changed',
            self.convertOutputEntryChanged,
        )
        #####
        hbox = gtk.HBox(spacing=10)
        label = gtk.Label(label='')
        pack(hbox, label, 1, 1, 10)
        self.convertButton = gtk.Button()
        self.convertButton.set_label('Convert')
        self.convertButton.connect('clicked', self.convertClicked)
        pack(hbox, self.convertButton, 1, 1, 10)
        pack(vbox, hbox, 0, 0, 15)
        # ____________________ Tab 2 - Reverse ____________________ #
        self.reverseStatus = ''
        ####
        sizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
        ####
        vbox = gtk.VBox()
        vbox.label = _('Reverse')
        vbox.icon = ''  # '*.png'
        # self.prefPages.append(vbox)
        ######
        hbox = gtk.HBox(spacing=3)
        hbox.label = gtk.Label(label=_('Input Format')+':')
        pack(hbox, hbox.label)
        sizeGroup.add_widget(hbox.label)
        hbox.label.set_property('xalign', 0)
        self.reverseInputFormatCombo = InputFormatComboBox()
        pack(hbox, self.reverseInputFormatCombo)
        pack(vbox, hbox)
        ###
        hbox = gtk.HBox(spacing=3)
        hbox.label = gtk.Label(label=_('Input File')+':')
        pack(hbox, hbox.label)
        sizeGroup.add_widget(hbox.label)
        hbox.label.set_property('xalign', 0)
        self.reverseInputEntry = gtk.Entry()
        pack(hbox, self.reverseInputEntry, 1, 1)
        button = BrowseButton(
            self.reverseInputEntry.set_text,
            label='Browse',
            actionSave=False,
            title='Select Input File',
        )
        pack(hbox, button)
        pack(vbox, hbox)
        ##
        self.reverseInputEntry.connect(
            'changed',
            self.reverseInputEntryChanged,
        )
        #####
        vbox.sep1 = gtk.Label(label='')
        vbox.sep1.show()
        pack(vbox, vbox.sep1)
        #####
        hbox = gtk.HBox(spacing=3)
        hbox.label = gtk.Label(label=_('Output Tabfile')+':')
        pack(hbox, hbox.label)
        sizeGroup.add_widget(hbox.label)
        hbox.label.set_property('xalign', 0)
        self.reverseOutputEntry = gtk.Entry()
        pack(hbox, self.reverseOutputEntry, 1, 1)
        button = BrowseButton(
            self.reverseOutputEntry.set_text,
            label='Browse',
            actionSave=True,
            title='Select Output File',
        )
        pack(hbox, button)
        pack(vbox, hbox)
        ##
        self.reverseOutputEntry.connect(
            'changed',
            self.reverseOutputEntryChanged,
        )
        #####
        hbox = gtk.HBox(spacing=3)
        label = gtk.Label(label='')
        pack(hbox, label, 1, 1, 5)
        ###
        self.reverseStartButton = gtk.Button()
        self.reverseStartButton.set_label(_('Start'))
        self.reverseStartButton.connect('clicked', self.reverseStartClicked)
        pack(hbox, self.reverseStartButton, 1, 1, 2)
        ###
        self.reversePauseButton = gtk.Button()
        self.reversePauseButton.set_label(_('Pause'))
        self.reversePauseButton.set_sensitive(False)
        self.reversePauseButton.connect('clicked', self.reversePauseClicked)
        pack(hbox, self.reversePauseButton, 1, 1, 2)
        ###
        self.reverseResumeButton = gtk.Button()
        self.reverseResumeButton.set_label(_('Resume'))
        self.reverseResumeButton.set_sensitive(False)
        self.reverseResumeButton.connect('clicked', self.reverseResumeClicked)
        pack(hbox, self.reverseResumeButton, 1, 1, 2)
        ###
        self.reverseStopButton = gtk.Button()
        self.reverseStopButton.set_label(_('Stop'))
        self.reverseStopButton.set_sensitive(False)
        self.reverseStopButton.connect('clicked', self.reverseStopClicked)
        pack(hbox, self.reverseStopButton, 1, 1, 2)
        ###
        pack(vbox, hbox, 0, 0, 5)
        #####
        # ____________________________________________________________ #
        notebook = gtk.Notebook()
        self.notebook = notebook
        #########
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
        # notebook.set_property('homogeneous', True)  # not in gtk3 FIXME
        # notebook.set_property('tab-border', 5)  # not in gtk3 FIXME
        # notebook.set_property('tab-hborder', 15)  # not in gtk3 FIXME
        pack(self.vbox, notebook, 0, 0)
        # for i in ui.prefPagesOrder:
        #    try:
        #        j = prefPagesOrder[i]
        #    except IndexError:
        #        continue
        #    notebook.reorder_child(self.prefPages[i], j)
        # ____________________________________________________________ #
        self.consoleTextview = textview = gtk.TextView()
        swin = gtk.ScrolledWindow()
        swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
        swin.set_border_width(0)
        swin.add(textview)
        pack(self.vbox, swin, 1, 1)
        ###
        handler = GtkSingleTextviewLogHandler(textview)
        log.addHandler(handler)
        ###
        textview.override_background_color(
            gtk.StateFlags.NORMAL,
            gdk.RGBA(0, 0, 0, 1),
        )
        ###
        handler.setColor('CRITICAL', gdk.color_parse('red'))
        handler.setColor('ERROR', gdk.color_parse('red'))
        handler.setColor('WARNING', gdk.color_parse('yellow'))
        handler.setColor('INFO', gdk.color_parse('white'))
        handler.setColor('DEBUG', gdk.color_parse('white'))
        ###
        textview.get_buffer().set_text('Output & Error Console:\n')
        textview.set_editable(False)
        # ____________________________________________________________ #
        self.progressTitle = ''
        self.progressBar = pbar = gtk.ProgressBar()
        pbar.set_fraction(0)
        # pbar.set_text(_('Progress Bar'))
        # pbar.get_style_context()
        # pbar.set_property('height-request', 20)
        pack(self.vbox, pbar, 0, 0)
        ############
        hbox = gtk.HBox(spacing=5)
        clearButton = gtk.Button(
            use_stock=gtk.STOCK_CLEAR,
            always_show_image=True,
            label=_('Clear'),
        )
        clearButton.show_all()
        # image = gtk.Image()
        # image.set_from_stock(gtk.STOCK_CLEAR, gtk.IconSize.MENU)
        # clearButton.add(image)
        clearButton.set_border_width(0)
        clearButton.connect('clicked', self.consoleClearButtonClicked)
        set_tooltip(clearButton, 'Clear Console')
        pack(hbox, clearButton, 0, 0)
        ####
        # hbox.sepLabel1 = gtk.Label(label='')
        # pack(hbox, hbox.sepLabel1, 1, 1)
        ######
        hbox.verbosityLabel = gtk.Label(label=_('Verbosity')+':')
        pack(hbox, hbox.verbosityLabel, 0, 0)
        ##
        self.verbosityCombo = combo = gtk.ComboBoxText()
        for level, levelName in enumerate(log.levelNamesCap):
            combo.append_text('%s - %s' % (
                level,
                _(levelName)
            ))
        combo.set_active(log.getVerbosity())
        combo.set_border_width(0)
        combo.connect('changed', self.verbosityComboChanged)
        pack(hbox, combo, 0, 0)
        ####
        # hbox.sepLabel2 = gtk.Label(label='')
        # pack(hbox, hbox.sepLabel2, 1, 1)
        ####
        self.statusBar = sbar = gtk.Statusbar()
        pack(hbox, self.statusBar, 1, 1)
        ####
        hbox.resizeButton = ResizeButton(self)
        pack(hbox, hbox.resizeButton, 0, 0)
        ######
        pack(self.vbox, hbox, 0, 0)
        # ____________________________________________________________ #
        self.vbox.show_all()
        ########
        self.status('Select input file')

    def run(self, editPath=None, readOptions=None):
        if readOptions is None:
            readOptions = {}
        # if editPath:
        #    self.notebook.set_current_page(3)
        #    log.info('Opening file "%s" for edit. please wait...'%editPath)
        #    while gtk.events_pending():
        #        gtk.main_iteration_do(False)
        #    self.dbe_open(editPath, **readOptions)
        gtk.Dialog.present(self)
        gtk.main()

    def onDeleteEvent(self, widget, event):
        self.destroy()
        gtk.main_quit()

    def consoleClearButtonClicked(self, widget=None):
        self.consoleTextview.get_buffer().set_text('')

    def verbosityComboChanged(self, widget=None):
        verbosity = self.verbosityCombo.get_active()
        # or int(self.verbosityCombo.get_active_text())
        log.setVerbosity(verbosity)

    def convertClicked(self, widget=None):
        inPath = self.convertInputEntry.get_text()
        if not inPath:
            self.status('Input file path is empty!')
            log.critical('Input file path is empty!')
            return
        inFormat = self.convertInputFormatCombo.getActive()
        if inFormat:
            inFormatDesc = Glossary.formatsDesc[inFormat]
        else:
            inFormatDesc = ''
            # log.critical('Input format is empty!');return

        outPath = self.convertOutputEntry.get_text()
        if not outPath:
            self.status('Output file path is empty!')
            log.critical('Output file path is empty!')
            return
        outFormat = self.convertOutputFormatCombo.getActive()
        if outFormat:
            outFormatDesc = Glossary.formatsDesc[outFormat]
        else:
            outFormatDesc = ''
            # log.critical('Output format is empty!');return

        while gtk.events_pending():
            gtk.main_iteration_do(False)

        self.convertButton.set_sensitive(False)
        self.progressTitle = 'Converting'
        try:
            # if inFormat=='Omnidic':
            #    dicIndex = self.xml.get_widget('spinbutton_omnidic_i')\
            #        .get_value_as_int()
            #    ex = self.glos.readOmnidic(inPath, dicIndex=dicIndex)
            # else:
            finalOutputFile = self.glos.convert(
                inPath,
                inputFormat=inFormat,
                outputFilename=outPath,
                outputFormat=outFormat,
            )
            if finalOutputFile:
                self.status('Convert finished')
            else:
                self.status('Convert failed')
            return bool(finalOutputFile)

        finally:
            self.convertButton.set_sensitive(True)
            self.assert_quit = False
            self.progressTitle = ''

        return True

    def convertInputEntryChanged(self, widget=None):
        inPath = self.convertInputEntry.get_text()
        inFormat = self.convertInputFormatCombo.getActive()
        if inPath.startswith('file://'):
            inPath = urlToPath(inPath)
            self.convertInputEntry.set_text(inPath)

        inExt = getCopressedFileExt(inPath)
        inFormatNew = Glossary.extFormat.get(inExt)

        if not inFormatNew:
            return

        if not isfile(inPath):
            return

        if self.pref['ui_autoSetFormat']:  # and not inFormat:
            self.convertInputFormatCombo.setActive(inFormatNew)

        self.status('Select output file')
        if self.pref['ui_autoSetOutputFileName']:
            outFormat = self.convertOutputFormatCombo.getActive()
            outPath = self.convertOutputEntry.get_text()
            if outFormat:
                if not outPath and '.' in inPath:
                    outPath = splitext(inPath)[0] + \
                        Glossary.formatsExt[outFormat][0]
                    self.convertOutputEntry.set_text(outPath)
                    self.status('Press "Convert"')

    def convertOutputEntryChanged(self, widget=None):
        outPath = self.convertOutputEntry.get_text()
        outFormat = self.convertOutputFormatCombo.getActive()
        if not outPath:
            return
        # outFormat = self.combobox_o.get_active_text()
        if outPath.startswith('file://'):
            outPath = urlToPath(outPath)
            self.convertOutputEntry.set_text(outPath)

        if self.pref['ui_autoSetFormat']:  # and not outFormat:
            outExt = getCopressedFileExt(outPath)
            try:
                outFormatNew = Glossary.extFormat[outExt]
            except KeyError:
                pass
            else:
                self.convertOutputFormatCombo.setActive(outFormatNew)

        if self.convertOutputFormatCombo.getActive():
            self.status('Press "Convert"')
        else:
            self.status('Select output format')

    def reverseLoad(self):
        pass

    def reverseStartLoop(self):
        pass

    def reverseStart(self):
        if not self.reverseLoad():
            return
        ###
        self.reverseStatus = 'doing'
        self.reverseStartLoop()
        ###
        self.reverseStartButton.set_sensitive(False)
        self.reversePauseButton.set_sensitive(True)
        self.reverseResumeButton.set_sensitive(False)
        self.reverseStopButton.set_sensitive(True)

    def reverseStartClicked(self, widget=None):
        self.waitingDo(self.reverseStart)

    def reversePause(self):
        self.reverseStatus = 'pause'
        ###
        self.reverseStartButton.set_sensitive(False)
        self.reversePauseButton.set_sensitive(False)
        self.reverseResumeButton.set_sensitive(True)
        self.reverseStopButton.set_sensitive(True)

    def reversePauseClicked(self, widget=None):
        self.waitingDo(self.reversePause)

    def reverseResume(self):
        self.reverseStatus = 'doing'
        ###
        self.reverseStartButton.set_sensitive(False)
        self.reversePauseButton.set_sensitive(True)
        self.reverseResumeButton.set_sensitive(False)
        self.reverseStopButton.set_sensitive(True)

    def reverseResumeClicked(self, widget=None):
        self.waitingDo(self.reverseResume)

    def reverseStop(self):
        self.reverseStatus = 'stop'
        ###
        self.reverseStartButton.set_sensitive(True)
        self.reversePauseButton.set_sensitive(False)
        self.reverseResumeButton.set_sensitive(False)
        self.reverseStopButton.set_sensitive(False)

    def reverseStopClicked(self, widget=None):
        self.waitingDo(self.reverseStop)

    def reverseInputEntryChanged(self, widget=None):
        inPath = self.reverseInputEntry.get_text()
        inFormat = self.reverseInputFormatCombo.getActive()
        if inPath.startswith('file://'):
            inPath = urlToPath(inPath)
            self.reverseInputEntry.set_text(inPath)

        inExt = getCopressedFileExt(inPath)
        inFormatNew = Glossary.extFormat.get(inExt)

        if inFormatNew and self.pref['ui_autoSetFormat']:  # and not inFormat:
            self.reverseInputFormatCombo.setActive(inFormatNew)

        if self.pref['ui_autoSetOutputFileName']:
            outExt = '.txt'
            outPath = self.reverseOutputEntry.get_text()
            if inFormatNew and not outPath:
                outPath = splitext(inPath)[0] + '-reversed' + outExt
                self.reverseOutputEntry.set_text(outPath)

    def reverseOutputEntryChanged(self, widget=None):
        pass

    def progressInit(self, title):
        self.progressTitle = title

    def progress(self, rat, text=None):
        if not text:
            text = '%%%d' % (rat*100)
        text += ' - %s' % self.progressTitle
        self.progressBar.set_fraction(rat)
        # self.progressBar.set_text(text)  # not working
        self.status(text)
        while gtk.events_pending():
            gtk.main_iteration_do(False)
