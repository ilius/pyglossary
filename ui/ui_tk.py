# -*- coding: utf-8 -*-
# ui_tk.py
#
# Copyright © 2009-2010 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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


from pyglossary.core import homeDir
from pyglossary.glossary import *
from pyglossary.text_utils import urlToPath
from .base import *
from os.path import join
import logging
import traceback

import tkinter as tk
from tkinter import filedialog
from tkinter import tix

log = logging.getLogger('root')

# startBold = '\x1b[1m'  # Start Bold #len=4
# startUnderline = '\x1b[4m'  # Start Underline #len=4
endFormat = '\x1b[0;0;0m'  # End Format #len=8
# redOnGray = '\x1b[0;1;31;47m'
startRed = '\x1b[31m'


noneItem = 'Not Selected'


bitmapLogo = join(rootDir, 'res', 'pyglossary.ico') if "nt" == os.name \
    else '@' + join(rootDir, 'res', 'pyglossary.xbm')


def set_window_icon(window):
    # window.wm_iconbitmap(bitmap=bitmapLogo)
    window.iconphoto(
        True,
        tk.PhotoImage(file=join(rootDir, 'res', 'pyglossary.png')),
    )


class TkTextLogHandler(logging.Handler):
    def __init__(self, tktext):
        logging.Handler.__init__(self)
        #####
        tktext.tag_config('CRITICAL', foreground='#ff0000')
        tktext.tag_config('ERROR', foreground='#ff0000')
        tktext.tag_config('WARNING', foreground='#ffff00')
        tktext.tag_config('INFO', foreground='#00ff00')
        tktext.tag_config('DEBUG', foreground='#ffffff')
        ###
        self.tktext = tktext

    def emit(self, record):
        msg = record.getMessage()
        ###
        if record.exc_info:
            _type, value, tback = record.exc_info
            tback_text = ''.join(
                traceback.format_exception(_type, value, tback)
            )
            if msg:
                msg += '\n'
            msg += tback_text
        ###
        self.tktext.insert(
            'end',
            msg + '\n',
            record.levelname,
        )


# Monkey-patch Tkinter
# http://stackoverflow.com/questions/5191830/python-exception-logging
def CallWrapper__call__(self, *args):
    """
        Apply first function SUBST to arguments, than FUNC.
    """
    if self.subst:
        args = self.subst(*args)
    try:
        return self.func(*args)
    except:
        log.exception('Exception in Tkinter callback:')
tk.CallWrapper.__call__ = CallWrapper__call__


class ProgressBar(tix.Frame):
    """
    This comes from John Grayson's book "Python and Tkinter programming"
    Edited by Saeed Rasooli
    """
    def __init__(
        self,
        rootWin=None,
        orientation='horizontal',
        min_=0,
        max_=100,
        width=100,
        height=18,
        appearance='sunken',
        fillColor='blue',
        background='gray',
        labelColor='yellow',
        labelFont='Verdana',
        labelFormat='%d%%',
        value=0,
        bd=2,
    ):
        # preserve various values
        self.rootWin = rootWin
        self.orientation = orientation
        self.min = min_
        self.max = max_
        self.width = width
        self.height = height
        self.fillColor = fillColor
        self.labelFont = labelFont
        self.labelColor = labelColor
        self.background = background
        self.labelFormat = labelFormat
        self.value = value
        tix.Frame.__init__(self, rootWin, relief=appearance, bd=bd)
        self.canvas = tix.Canvas(
            self,
            height=height,
            width=width,
            bd=0,
            highlightthickness=0,
            background=background,
        )
        self.scale = self.canvas.create_rectangle(
            0,
            0,
            width,
            height,
            fill=fillColor,
        )
        self.label = self.canvas.create_text(
            width/2,
            height/2,
            text='',
            anchor='c',
            fill=labelColor,
            font=self.labelFont,
        )
        self.update()
        self.bind('<Configure>', self.update)
        self.canvas.pack(side='top', fill='x', expand='no')

    def updateProgress(self, newVal, newMax=None, text=''):
        if newMax:
            self.max = newMax
        self.value = newVal
        self.update(None, text)

    def update(self, event=None, labelText=''):
        # Trim the values to be between min and max
        value = self.value
        if value > self.max:
            value = self.max
        if value < self.min:
            value = self.min
        # Adjust the rectangle
        width = int(self.winfo_width())
        # width = self.width
        ratio = float(value)/self.max
        if self.orientation == 'horizontal':
            self.canvas.coords(
                self.scale,
                0,
                0,
                width * ratio,
                self.height,
            )
        else:
            self.canvas.coords(
                self.scale,
                0,
                self.height * (1 - ratio),
                width,
                self.height,
            )
        # Now update the colors
        self.canvas.itemconfig(self.scale, fill=self.fillColor)
        self.canvas.itemconfig(self.label, fill=self.labelColor)
        # And update the label
        if not labelText:
            labelText = self.labelFormat % int(ratio * 100)
        self.canvas.itemconfig(self.label, text=labelText)
        # FIXME:
        # self.canvas.move(self.label, width/2, self.height/2)
        # self.canvas.scale(self.label, 0, 0, float(width)/self.width, 1)
        self.canvas.update_idletasks()


class UI(tix.Frame, UIBase):
    def __init__(self, path='', **options):
        self.glos = Glossary(ui=self)
        self.pref = {}
        self.pref_load(**options)
        #############################################
        rootWin = self.rootWin = tix.Tk()
        tix.Frame.__init__(self, rootWin)
        rootWin.title('PyGlossary (Tkinter)')
        rootWin.resizable(True, False)
        ########
        set_window_icon(rootWin)
        ########
        self.pack(fill='x')
        # rootWin.bind('<Configure>', self.resized)
        ######################
        self.glos = Glossary(ui=self)
        self.pref = {}
        self.pref_load()
        self.pathI = ''
        self.pathO = ''
        self.fcd_dir = join(homeDir, 'Desktop')
        ######################
        vpaned = tk.PanedWindow(self, orient=tk.VERTICAL)
        notebook = tix.NoteBook(vpaned)
        notebook.add('tab1', label='Convert', underline=0)
        notebook.add('tab2', label='Reverse', underline=0)
        convertFrame = tix.Frame(notebook.tab1)
        ######################
        frame = tix.Frame(convertFrame)
        ##
        label = tix.Label(frame, text='Read from format')
        label.pack(side='left')
        ##
        comboVar = tk.StringVar()
        combo = tk.OptionMenu(frame, comboVar, *Glossary.readDesc)
        # comboVar.set(Glossary.readDesc[0])
        comboVar.set(noneItem)
        combo.pack(side='left')
        self.combobox_i = comboVar
        ##
        frame.pack(fill='x')
        ###################
        frame = tix.Frame(convertFrame)
        ##
        label = tix.Label(frame, text='  Path:')
        label.pack(side='left')
        ##
        entry = tix.Entry(frame)
        entry.pack(side='left', fill='x', expand=True)
        entry.bind_all('<KeyPress>', self.entry_changed)
        self.entry_i = entry
        ##
        button = tix.Button(
            frame,
            text='Browse',
            command=self.browse_i,
            # bg='#f0f000',
            # activebackground='#f6f622',
        )
        button.pack(side='left')
        ##
        frame.pack(fill='x')
        ######################
        frame = tix.Frame(convertFrame)
        ##
        label = tix.Label(frame, text='Write to format    ')
        label.pack(side='left')
        ##
        comboVar = tk.StringVar()
        combo = tk.OptionMenu(frame, comboVar, *Glossary.writeDesc)
        # comboVar.set(Glossary.writeDesc[0])
        comboVar.set(noneItem)
        combo.pack(side='left')
        combo.bind('<Configure>', self.combobox_o_changed)
        self.combobox_o = comboVar
        ##
        frame.pack(fill='x')
        ###################
        frame = tix.Frame(convertFrame)
        ##
        label = tix.Label(frame, text='  Path:')
        label.pack(side='left')
        ##
        entry = tix.Entry(frame)
        entry.pack(side='left', fill='x', expand=True)
        # entry.bind_all('<KeyPress>', self.entry_changed)
        self.entry_o = entry
        ##
        button = tix.Button(
            frame,
            text='Browse',
            command=self.browse_o,
            # bg='#f0f000',
            # activebackground='#f6f622',
        )
        button.pack(side='left')
        ##
        frame.pack(fill='x')
        #######
        frame = tix.Frame(convertFrame)
        label = tix.Label(frame, text=' '*15)
        label.pack(
            side='left',
            fill='x',
            expand=True,
        )
        button = tix.Button(
            frame,
            text='Convert',
            command=self.convert,
            # bg='#00e000',
            # activebackground='#22f022',
        )
        button.pack(
            side='left',
            fill='x',
            expand=True,
        )
        ###
        frame.pack(fill='x')
        ######
        convertFrame.pack(fill='x')
        vpaned.add(notebook)
        #################
        console = tix.Text(vpaned, height=15, background='#000000')
        # self.consoleH = 15
        # sbar = Tix.Scrollbar(
        #    vpaned,
        #    orien=Tix.VERTICAL,
        #    command=console.yview
        # )
        # sbar.grid ( row=0, column=1)
        # console['yscrollcommand'] = sbar.set
        # console.grid()
        console.pack(fill='both', expand=True)
        log.addHandler(
            TkTextLogHandler(console),
        )
        console.insert('end', 'Console:\n')
        ####
        vpaned.add(console)
        vpaned.pack(fill='both', expand=True)
        self.console = console
        ##################
        frame2 = tix.Frame(self)
        clearB = tix.Button(
            frame2,
            text='Clear',
            command=self.console_clear,
            # bg='black',
            # fg='#ffff00',
            # activebackground='#333333',
            # activeforeground='#ffff00',
        )
        clearB.pack(side='left')
        ####
        label = tix.Label(frame2, text='Verbosity')
        label.pack(side='left')
        ##
        comboVar = tk.StringVar()
        combo = tk.OptionMenu(
            frame2,
            comboVar,
            0, 1, 2, 3, 4,
        )
        comboVar.set(log.getVerbosity())
        comboVar.trace('w', self.verbosityChanged)
        combo.pack(side='left')
        self.verbosityCombo = comboVar
        #####
        pbar = ProgressBar(frame2, width=400)
        pbar.pack(side='left', fill='x', expand=True)
        self.pbar = pbar
        frame2.pack(fill='x')
        self.progressTitle = ''
        #############
        # vpaned.grid()
        # bottomFrame.grid()
        # self.grid()
        #####################
        # lbox = Tix.Listbox(convertFrame)
        # lbox.insert(0, 'aaaaaaaa', 'bbbbbbbbbbbbbbbbbbbb')
        # lbox.pack(fill='x')
        ##############
        frame3 = tix.Frame(self)
        aboutB = tix.Button(
            frame3,
            text='About',
            command=self.about_clicked,
            # bg='#e000e0',
            # activebackground='#f030f0',
        )
        aboutB.pack(side='right')
        closeB = tix.Button(
            frame3,
            text='Close',
            command=self.quit,
            # bg='#ff0000',
            # activebackground='#ff5050',
        )
        closeB.pack(side='right')
        frame3.pack(fill='x')
        # __________________________ Reverse Tab __________________________ #
        revFrame = tix.Frame(notebook.tab2)
        revFrame.pack(fill='x')
        ######################
        frame = tix.Frame(revFrame)
        ##
        label = tix.Label(frame, text='Read from format')
        label.pack(side='left')
        ##
        comboVar = tk.StringVar()
        combo = tk.OptionMenu(frame, comboVar, *Glossary.readDesc)
        # comboVar.set(Glossary.readDesc[0])
        comboVar.set(noneItem)
        combo.pack(side='left')
        self.combobox_r_i = comboVar
        ##
        frame.pack(fill='x')
        ###################
        frame = tix.Frame(revFrame)
        ##
        label = tix.Label(frame, text='  Path:')
        label.pack(side='left')
        ##
        entry = tix.Entry(frame)
        entry.pack(side='left', fill='x', expand=True)
        # entry.bind_all('<KeyPress>', self.entry_r_i_changed)
        self.entry_r_i = entry
        ##
        button = tix.Button(
            frame,
            text='Browse',
            command=self.r_browse_i,
            # bg='#f0f000',
            # activebackground='#f6f622',
        )
        button.pack(side='left')
        ##
        button = tix.Button(
            frame,
            text='Load',
            command=self.r_load,
            # bg='#7777ff',
        )
        button.pack(side='left')
        ###
        frame.pack(fill='x')
        ###################
        frame = tix.Frame(revFrame)
        ##
        label = tix.Label(frame, text='Output Tabfile')
        label.pack(side='left')
        ###
        entry = tix.Entry(frame)
        entry.pack(side='left', fill='x', expand=True)
        # entry.bind_all('<KeyPress>', self.entry_r_i_changed)
        self.entry_r_o = entry
        ##
        button = tix.Button(
            frame,
            text='Browse',
            command=self.r_browse_o,
            # bg='#f0f000',
            # activebackground='#f6f622',
        )
        button.pack(side='left')
        ##
        frame.pack(fill='x')
        ##############################
        if path:
            self.entry_i.insert(0, path)
            self.entry_changed()
            self.load()

    def verbosityChanged(self, index, value, op):
        log.setVerbosity(
            int(self.verbosityCombo.get())
        )

    def about_clicked(self):
        about = tix.Toplevel(width=600)  # bg='#0f0' does not work
        about.title('About PyGlossary')
        about.resizable(False, False)
        set_window_icon(about)
        ###
        msg1 = tix.Message(
            about,
            width=350,
            text='PyGlossary %s (Tkinter)' % VERSION,
            font=('DejaVu Sans', 13, 'bold'),
        )
        msg1.pack(fill='x', expand=True)
        ###
        msg2 = tix.Message(
            about,
            width=350,
            text=aboutText,
            font=('DejaVu Sans', 9, 'bold'),
            justify=tix.CENTER,
        )
        msg2.pack(fill='x', expand=True)
        ###
        msg3 = tix.Message(
            about,
            width=350,
            text=homePage,
            font=('DejaVu Sans', 8, 'bold'),
            fg='#3333ff',
        )
        msg3.pack(fill='x', expand=True)
        ###
        msg4 = tix.Message(
            about,
            width=350,
            text='Install PyGTK to have a better interface!',
            font=('DejaVu Sans', 8, 'bold'),
            fg='#00aa00',
        )
        msg4.pack(fill='x', expand=True)
        ###########
        frame = tix.Frame(about)
        ###
        button = tix.Button(
            frame,
            text='Close',
            command=about.destroy,
            # bg='#ff0000',
            # activebackground='#ff5050',
        )
        button.pack(side='right')
        ###
        button = tix.Button(
            frame,
            text='License',
            command=self.about_license_clicked,
            # bg='#00e000',
            # activebackground='#22f022',
        )
        button.pack(side='right')
        ###
        button = tix.Button(
            frame,
            text='Credits',
            command=self.about_credits_clicked,
            # bg='#0000ff',
            # activebackground='#5050ff',
        )
        button.pack(side='right')
        ###
        frame.pack(fill='x')

    def about_credits_clicked(self):
        about = tix.Toplevel()  # bg='#0f0' does not work
        about.title('Credits')
        about.resizable(False, False)
        set_window_icon(about)
        ###
        msg1 = tix.Message(
            about,
            width=500,
            text='\n'.join(authors),
            font=('DejaVu Sans', 9, 'bold'),
        )
        msg1.pack(fill='x', expand=True)
        ###########
        frame = tix.Frame(about)
        closeB = tix.Button(
            frame,
            text='Close',
            command=about.destroy,
            # bg='#ff0000',
            # activebackground='#ff5050',
        )
        closeB.pack(side='right')
        frame.pack(fill='x')

    def about_license_clicked(self):
        about = tix.Toplevel()  # bg='#0f0' does not work
        about.title('License')
        about.resizable(False, False)
        set_window_icon(about)
        ###
        msg1 = tix.Message(
            about,
            width=420,
            text=licenseText,
            font=('DejaVu Sans', 9, 'bold'),
        )
        msg1.pack(fill='x', expand=True)
        ###########
        frame = tix.Frame(about)
        closeB = tix.Button(
            frame,
            text='Close',
            command=about.destroy,
            # bg='#ff0000',
            # activebackground='#ff5050',
        )
        closeB.pack(side='right')
        frame.pack(fill='x')

    def quit(self):
        self.rootWin.destroy()

    def resized(self, event):
        dh = self.rootWin.winfo_height() - self.winfo_height()
        # log.debug(dh, self.consoleH)
        # if dh > 20:
        #    self.consoleH += 1
        #    self.console['height'] = self.consoleH
        #    self.console['width'] = int(self.console['width']) + 1
        #    self.console.grid()
        # for x in dir(self):
        #    if 'info' in x:
        #        log.debug(x)

    def combobox_o_changed(self, event):
        # log.debug(self.combobox_o.get())
        formatD = self.combobox_o.get()
        if formatD == noneItem:
            return
        format = Glossary.descFormat[formatD]
        """
        if format=='Omnidic':
            self.xml.get_widget('label_omnidic_o').show()
            self.xml.get_widget('spinbutton_omnidic_o').show()
        else:
            self.xml.get_widget('label_omnidic_o').hide()
            self.xml.get_widget('spinbutton_omnidic_o').hide()
        if format=='Babylon':
            self.xml.get_widget('label_enc').show()
            self.xml.get_widget('comboentry_enc').show()
        else:
            self.xml.get_widget('label_enc').hide()
            self.xml.get_widget('comboentry_enc').hide()
        """
        if not self.pref['ui_autoSetOutputFileName']:  # and format is None:
            return

        pathI = self.entry_i.get()
        pathO = self.entry_o.get()
        formatOD = self.combobox_o.get()

        if formatOD is None:
            return
        if pathO:
            return
        if '.' not in pathI:
            return

        extO = Glossary.descExt[formatOD]
        pathO = ''.join(os.path.splitext(pathI)[:-1])+extO
        # self.entry_o.delete(0, 'end')
        self.entry_o.insert(0, pathO)

    def entry_changed(self, event=None):
        # log.debug('entry_changed')
        # char = event.keysym
        pathI = self.entry_i.get()
        if self.pathI != pathI:
            formatD = self.combobox_i.get()
            if pathI.startswith('file://'):
                pathI = urlToPath(pathI)
                self.entry_i.delete(0, 'end')
                self.entry_i.insert(0, pathI)
            if self.pref['ui_autoSetFormat']:  # format==noneItem:
                ext = os.path.splitext(pathI)[-1].lower()
                if ext in ('.gz', '.bz2', '.zip'):
                    ext = os.path.splitext(pathI[:-len(ext)])[-1].lower()
                for i in range(len(Glossary.readExt)):
                    if ext in Glossary.readExt[i]:
                        self.combobox_i.set(Glossary.readDesc[i])
                        break
            if self.pref['ui_autoSetOutputFileName']:  # format==noneItem:
                # pathI = self.entry_i.get()
                formatOD = self.combobox_o.get()
                pathO = self.entry_o.get()
                if formatOD != noneItem and not pathO and '.' in pathI:
                    extO = Glossary.descExt[formatOD]
                    pathO = ''.join(os.path.splitext(pathI)[:-1]) + extO
                    self.entry_o.delete(0, 'end')
                    self.entry_o.insert(0, pathO)
            self.pathI = pathI
        ##############################################
        pathO = self.entry_o.get()
        if self.pathO != pathO:
            formatD = self.combobox_o.get()
            if pathO.startswith('file://'):
                pathO = urlToPath(pathO)
                self.entry_o.delete(0, 'end')
                self.entry_o.insert(0, pathO)
            if self.pref['ui_autoSetFormat']:  # format==noneItem:
                ext = os.path.splitext(pathO)[-1].lower()
                if ext in ('.gz', '.bz2', '.zip'):
                    ext = os.path.splitext(pathO[:-len(ext)])[-1].lower()
                for i in range(len(Glossary.writeExt)):
                    if ext in Glossary.writeExt[i]:
                        self.combobox_o.set(Glossary.writeDesc[i])
                        break
            self.pathO = pathO

    def browse_i(self):
        path = filedialog.askopenfilename(initialdir=self.fcd_dir)
        if path:
            self.entry_i.delete(0, 'end')
            self.entry_i.insert(0, path)
            self.entry_changed()
            self.fcd_dir = os.path.dirname(path)  # FIXME

    def browse_o(self):
        path = filedialog.asksaveasfilename()
        if path:
            self.entry_o.delete(0, 'end')
            self.entry_o.insert(0, path)
            self.entry_changed()
            self.fcd_dir = os.path.dirname(path)  # FIXME

    def convert(self):
        inPath = self.entry_i.get()
        if not inPath:
            log.critical('Input file path is empty!')
            return
        inFormatDesc = self.combobox_i.get()
        if inFormatDesc == noneItem:
            # log.critical('Input format is empty!');return
            inFormat = ''
        else:
            inFormat = Glossary.descFormat[inFormatDesc]

        outPath = self.entry_o.get()
        if not outPath:
            log.critical('Output file path is empty!')
            return
        outFormatDesc = self.combobox_o.get()
        if outFormatDesc in (noneItem, ''):
            log.critical('Output format is empty!')
            return
        outFormat = Glossary.descFormat[outFormatDesc]

        finalOutputFile = self.glos.convert(
            inPath,
            inputFormat=inFormat,
            outputFilename=outPath,
            outputFormat=outFormat,
        )
        # if finalOutputFile:
            # self.status('Convert finished')
        # else:
            # self.status('Convert failed')
        return bool(finalOutputFile)

    def run(self, editPath=None, readOptions=None):
        if readOptions is None:
            readOptions = {}
        # editPath and readOptions are for DB Editor
        # which is not implemented
        self.mainloop()

    def progressInit(self, title):
        self.progressTitle = title

    def progress(self, rat, text=''):
        if not text:
            text = '%%%d' % (rat*100)
        text += ' - %s' % self.progressTitle
        self.pbar.updateProgress(rat*100, None, text)
        # self.pbar.value = rat*100
        # self.pbar.update()
        self.rootWin.update()

    def console_clear(self, event=None):
        self.console.delete('1.0', 'end')
        self.console.insert('end', 'Console:\n')

    def r_browse_i(self):
        pass

    def r_browse_o(self):
        pass

    def r_load(self):
        pass


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = ''
    ui = UI(path)
    ui.run()
