# -*- coding: utf-8 -*-
## ui_tk.py
##
## Copyright © 2009-2010 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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


from pyglossary.glossary import *
from pyglossary.text_utils import toStr
from .base import *
from os.path import join
import logging
import traceback

import tkinter as tk
import tkinter.filedialog
import tkinter.tix

log = logging.getLogger('root')

#startBold	= '\x1b[1m'		# Start Bold		#len=4
#startUnderline	= '\x1b[4m'		# Start Underline	#len=4
endFormat	= '\x1b[0;0;0m'		# End Format		#len=8
#redOnGray	= '\x1b[0;1;31;47m'
startRed	= '\x1b[31m'

#use_psyco_file = join(srcDir, 'use_psyco')
use_psyco_file = '%s_use_psyco'%confPath
psyco_found = None

noneItem = 'Not Selected'


xbmLogo = join(rootDir, 'res', 'pyglossary.xbm')


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
            tback_text = ''.join(traceback.format_exception(_type, value, tback))
            if msg:
                msg += '\n'
            msg += tback_text
        ###
        self.tktext.insert(
            'end',
            msg + '\n',
            record.levelname,
        )


### Monkey-patch Tkinter
## http://stackoverflow.com/questions/5191830/python-exception-logging
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


class ProgressBar(tkinter.tix.Frame):
    #### This comes from John Grayson's book "Python and Tkinter programming"
    #### Edited by Saeed Rasooli
    def __init__(self, master=None, orientation='horizontal',
            min_=0, max_=100, width=100, height=18,
            appearance='sunken', fillColor='blue', background='gray',
            labelColor='yellow', labelFont='Verdana', labelFormat='%d%%',
            value=0, bd=2):
        # preserve various values
        self.master = master
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
        tkinter.tix.Frame.__init__(self, master, relief=appearance, bd=bd)
        self.canvas = tkinter.tix.Canvas(
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
        #width = self.width
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
        #self.canvas.move(self.label, width/2, self.height/2)#??????????
        #self.canvas.scale(self.label, 0, 0, float(width)/self.width, 1)#???????????
        self.canvas.update_idletasks()



class UI(tkinter.tix.Frame, UIBase):
    def __init__(self, path='', **options):
        #global sys
        master = tkinter.tix.Tk()
        tkinter.tix.Frame.__init__(self, master)
        master.title('PyGlossary (Tkinter)')
        master.resizable(True, False)
        ########
        #icon = Tix.BitmapImage(file=xbmLogo)
        #master.wm_iconbitmap(icon)
        #master.wm_iconbitmap(xbmLogo)
        #bit = Tix.PhotoImage(file=join(srcDir, 'pyglossary.gif'), format='gif')
        #lb = Tix.Label(None,image=bit)
        #lb.grid()
        #master.iconwindow(icon, 'pyglossary')
        #master.wm_iconimage(bit)
        #master.wm_iconname('dot')
        #help(master.wm_iconbitmap)
        #for x in dir(master):
        #    if 'wm_' in x:
        #        log.debug(x)
        master.wm_iconbitmap('@%s'%xbmLogo)
        ########
        self.pack(fill='x')
        #master.bind('<Configure>', self.resized)
        ######################
        self.running = False
        self.glos = Glossary(ui=self)
        self.pref = {}
        self.pref_load()
        self.pathI = ''
        self.pathO = ''
        self.fcd_dir = join(homeDir, 'Desktop')
        ######################
        vpaned = tk.PanedWindow(self, orient=tk.VERTICAL)
        notebook = tkinter.tix.NoteBook(vpaned)
        notebook.add('tab1', label='Convert', underline=0)
        notebook.add('tab2', label='Reverse', underline=0)
        convertFrame = tkinter.tix.Frame(notebook.tab1)
        ######################
        frame = tkinter.tix.Frame(convertFrame)
        ##
        label = tkinter.tix.Label(frame, text='Read from format')
        label.pack(side='left')
        ##
        comboVar = tk.StringVar()
        combo = tk.OptionMenu(frame, comboVar, *Glossary.readDesc)
        #comboVar.set(Glossary.readDesc[0])
        comboVar.set(noneItem)
        combo.pack(side='left')
        self.combobox_i = comboVar
        ##
        frame.pack(fill='x')
        ###################
        frame = tkinter.tix.Frame(convertFrame)
        ##
        label = tkinter.tix.Label(frame, text='  Path:')
        label.pack(side='left')
        ##
        entry = tkinter.tix.Entry(frame)
        entry.pack(side='left', fill='x', expand=True)
        entry.bind_all('<KeyPress>', self.entry_changed)
        self.entry_i = entry
        ##
        button = tkinter.tix.Button(
            frame,
            text='Browse',
            command=self.browse_i,
            bg='#f0f000',
            activebackground='#f6f622',
        )
        button.pack(side='left')
        ##
        button = tkinter.tix.Button(
            frame,
            text='Load',
            command=self.load,
            bg='#7777ff',
            activebackground='#9999ff',
        )
        button.pack(side='left')
        ###
        frame.pack(fill='x')
        ######################################
        self.running = False
        self.glos = Glossary(ui=self)
        self.pref = {}
        self.pref_load(**options)
        ######################
        frame = tkinter.tix.Frame(convertFrame)
        ##
        label = tkinter.tix.Label(frame, text='Write to format    ')
        label.pack(side='left')
        ##
        comboVar = tk.StringVar()
        combo = tk.OptionMenu(frame, comboVar, *Glossary.writeDesc)
        #comboVar.set(Glossary.writeDesc[0])
        comboVar.set(noneItem)
        combo.pack(side='left')
        combo.bind('<Configure>', self.combobox_o_changed)
        self.combobox_o = comboVar
        ##
        frame.pack(fill='x')
        ###################
        frame = tkinter.tix.Frame(convertFrame)
        ##
        label = tkinter.tix.Label(frame, text='  Path:')
        label.pack(side='left')
        ##
        entry = tkinter.tix.Entry(frame)
        entry.pack(side='left', fill='x', expand=True)
        #entry.bind_all('<KeyPress>', self.entry_changed)
        self.entry_o = entry
        ##
        button = tkinter.tix.Button(
            frame,
            text='Browse',
            command=self.browse_o,
            bg='#f0f000',
            activebackground='#f6f622',
        )
        button.pack(side='left')
        ##
        button = tkinter.tix.Button(
            frame,
            text='Convert',
            command=self.convert,
            bg='#00e000',
            activebackground='#22f022',
        )
        button.pack(side='left')
        ###
        frame.pack(fill='x')
        ######
        convertFrame.pack(fill='x')
        vpaned.add(notebook)
        #################
        console = tkinter.tix.Text(vpaned, height=15, background='#000000')
        #self.consoleH = 15
        #sbar = Tix.Scrollbar(vpaned, orien=Tix.VERTICAL, command=console.yview)
        #sbar.grid ( row=0, column=1)
        #console['yscrollcommand'] = sbar.set
        #console.grid()
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
        frame2 = tkinter.tix.Frame(self)
        clearB = tkinter.tix.Button(
            frame2,
            text='Clear',
            command=self.console_clear,
            bg='black',
            fg='#ffff00',
            activebackground='#333333',
            activeforeground='#ffff00',
        )
        clearB.pack(side='left')
        ####
        label = tkinter.tix.Label(frame2, text='Verbosity')
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
        #############
        #vpaned.grid()
        #bottomFrame.grid()
        #self.grid()
        #####################
        #lbox = Tix.Listbox(convertFrame)
        #lbox.insert(0, 'aaaaaaaa', 'bbbbbbbbbbbbbbbbbbbb')
        #lbox.pack(fill='x')
        ##############
        frame3 = tkinter.tix.Frame(self)
        aboutB = tkinter.tix.Button(
            frame3,
            text='About',
            command=self.about_clicked,
            bg='#e000e0',
            activebackground='#f030f0',
        )
        aboutB.pack(side='right')
        closeB = tkinter.tix.Button(
            frame3,
            text='Close',
            command=self.quit,
            bg='#ff0000',
            activebackground='#ff5050',
        )
        closeB.pack(side='right')
        applyB = tkinter.tix.Button(
            frame3,
            text='Apply',
            command=self.apply_clicked,
            bg='#00e000',
            activebackground='#22f022',
        )
        ## 'underline=0' arg in Tix.Button not affect keyboard shortcut?????????????
        applyB.pack(side='right')
        frame3.pack(fill='x')
        ############### Reverse Tab ####################
        revFrame = tkinter.tix.Frame(notebook.tab2)
        revFrame.pack(fill='x')
        ######################
        frame = tkinter.tix.Frame(revFrame)
        ##
        label = tkinter.tix.Label(frame, text='Read from format')
        label.pack(side='left')
        ##
        comboVar = tk.StringVar()
        combo = tk.OptionMenu(frame, comboVar, *Glossary.readDesc)
        #comboVar.set(Glossary.readDesc[0])
        comboVar.set(noneItem)
        combo.pack(side='left')
        self.combobox_r_i = comboVar
        ##
        frame.pack(fill='x')
        ###################
        frame = tkinter.tix.Frame(revFrame)
        ##
        label = tkinter.tix.Label(frame, text='  Path:')
        label.pack(side='left')
        ##
        entry = tkinter.tix.Entry(frame)
        entry.pack(side='left', fill='x', expand=True)
        #entry.bind_all('<KeyPress>', self.entry_r_i_changed)
        self.entry_r_i = entry
        ##
        button = tkinter.tix.Button(
            frame,
            text='Browse',
            command=self.r_browse_i,
            bg='#f0f000',
            activebackground='#f6f622',
        )
        button.pack(side='left')
        ##
        button = tkinter.tix.Button(
            frame,
            text='Load',
            command=self.r_load,
            bg='#7777ff',
        )
        button.pack(side='left')
        ###
        frame.pack(fill='x')
        ###################
        frame = tkinter.tix.Frame(revFrame)
        ##
        label = tkinter.tix.Label(frame, text='Output Tabfile')
        label.pack(side='left')
        ###
        entry = tkinter.tix.Entry(frame)
        entry.pack(side='left', fill='x', expand=True)
        #entry.bind_all('<KeyPress>', self.entry_r_i_changed)
        self.entry_r_o = entry
        ##
        button = tkinter.tix.Button(
            frame,
            text='Browse',
            command=self.r_browse_o,
            bg='#f0f000',
            activebackground='#f6f622',
        )
        button.pack(side='left')
        ##
        frame.pack(fill='x')
        ##############################
        if path!='':
            self.entry_i.insert(0, path)
            self.entry_changed()
            self.load()
    def verbosityChanged(self, index, value, op):
        log.setVerbosity(
            int(self.verbosityCombo.get())
        )
    def about_clicked(self):
        about = tkinter.tix.Toplevel(width=600)## bg='#0f0' does not work
        about.title('About PyGlossary')
        about.resizable(False, False)
        about.wm_iconbitmap('@%s'%xbmLogo)
        ###
        msg1 = tkinter.tix.Message(
            about,
            width=350,
            text='PyGlossary %s (Tkinter)'%VERSION,
            font=('DejaVu Sans', 13, 'bold'),
        )
        msg1.pack(fill='x', expand=True)
        ###
        msg2 = tkinter.tix.Message(
            about,
            width=350,
            text=aboutText,
            font=('DejaVu Sans', 9, 'bold'),
            justify=tkinter.tix.CENTER,
        )
        msg2.pack(fill='x', expand=True)
        ###
        msg3 = tkinter.tix.Message(
            about,
            width=350,
            text=homePage,
            font=('DejaVu Sans', 8, 'bold'),
            fg='#3333ff',
        )
        msg3.pack(fill='x', expand=True)
        ###
        msg4 = tkinter.tix.Message(
            about,
            width=350,
            text='Install PyGTK to have a better interface!',
            font=('DejaVu Sans', 8, 'bold'),
            fg='#00aa00',
        )
        msg4.pack(fill='x', expand=True)
        ###########
        frame = tkinter.tix.Frame(about)
        ###
        button = tkinter.tix.Button(
            frame,
            text='Close',
            command=about.destroy,
            bg='#ff0000',
            activebackground='#ff5050',
        )
        button.pack(side='right')
        ###
        button = tkinter.tix.Button(
            frame,
            text='License',
            command=self.about_license_clicked,
            bg='#00e000',
            activebackground='#22f022',
        )
        button.pack(side='right')
        ###
        button = tkinter.tix.Button(
            frame,
            text='Credits',
            command=self.about_credits_clicked,
            bg='#0000ff',
            activebackground='#5050ff',
        )
        button.pack(side='right')
        ###
        frame.pack(fill='x')
    def about_credits_clicked(self):
        about = tkinter.tix.Toplevel()## bg='#0f0' does not work
        about.title('Credits')
        about.resizable(False, False)
        about.wm_iconbitmap('@%s'%xbmLogo)
        ###
        msg1 = tkinter.tix.Message(
            about,
            width=500,
            text='\n'.join(authors),
            font=('DejaVu Sans', 9, 'bold'),
        )
        msg1.pack(fill='x', expand=True)
        ###########
        frame = tkinter.tix.Frame(about)
        closeB = tkinter.tix.Button(
            frame,
            text='Close',
            command=about.destroy,
            bg='#ff0000',
            activebackground='#ff5050',
        )
        closeB.pack(side='right')
        frame.pack(fill='x')
    def about_license_clicked(self):
        about = tkinter.tix.Toplevel()## bg='#0f0' does not work
        about.title('License')
        about.resizable(False, False)
        about.wm_iconbitmap('@%s'%xbmLogo)
        ###
        msg1 = tkinter.tix.Message(
            about,
            width=420,
            text=licenseText,
            font=('DejaVu Sans', 9, 'bold'),
        )
        msg1.pack(fill='x', expand=True)
        ###########
        frame = tkinter.tix.Frame(about)
        closeB = tkinter.tix.Button(
            frame,
            text='Close',
            command=about.destroy,
            bg='#ff0000',
            activebackground='#ff5050',
        )
        closeB.pack(side='right')
        frame.pack(fill='x')
    def quit(self):
        #sys.exit(0)
        self.master.destroy()
    def apply_clicked(self):
        if self.load():
            self.convert()
    def resized(self, event):
        dh = self.master.winfo_height() - self.winfo_height()
        #log.debug(dh, self.consoleH)
        #if dh > 20:
        #    self.consoleH += 1
        #    self.console['height'] = self.consoleH
        #    self.console['width'] = int(self.console['width']) + 1
        #    self.console.grid()
        #for x in dir(self):
        #    if 'info' in x:
        #        log.debug(x)
    def combobox_o_changed(self, event):
        #log.debug(self.combobox_o.get())
        formatD = self.combobox_o.get()
        if formatD==noneItem:
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
        if self.pref['auto_set_out']:#format==None:
            pathI = toStr(self.entry_i.get())
            pathO = toStr(self.entry_o.get())
            formatOD = self.combobox_o.get()
            if formatOD != None and not pathO and '.' in pathI:
                extO=Glossary.descExt[formatOD]
                pathO=''.join(os.path.splitext(pathI)[:-1])+extO
                #self.entry_o.delete(0, 'end')
                self.entry_o.insert(0, pathO)
    def entry_changed(self, event=None):
        #log.debug('entry_changed')
        #char = event.keysym
        pathI = toStr(self.entry_i.get())
        if self.pathI != pathI:
            formatD = self.combobox_i.get()
            if len(pathI)>7:
                if pathI[:7]=='file://':
                    pathI=urlToPath(pathI)
                    self.entry_i.delete(0, 'end')
                    self.entry_i.insert(0, pathI)
            if self.pref['auto_set_for']:#format==noneItem:
                ext = os.path.splitext(pathI)[-1].lower()
                if ext in ('.gz', '.bz2', '.zip'):
                    ext = os.path.splitext(pathI[:-len(ext)])[-1].lower()
                for i in range(len(Glossary.readExt)):
                    if ext in Glossary.readExt[i]:
                        self.combobox_i.set(Glossary.readDesc[i])
                        break
            if self.pref['auto_set_out']:#format==noneItem:
                #pathI = self.entry_i.get()
                formatOD = self.combobox_o.get()
                pathO = toStr(self.entry_o.get())
                if formatOD != noneItem and not pathO and '.' in pathI:
                    extO=Glossary.descExt[formatOD]
                    pathO=''.join(os.path.splitext(pathI)[:-1])+extO
                    self.entry_o.delete(0, 'end')
                    self.entry_o.insert(0, pathO)
            self.pathI = pathI
        ##############################################
        pathO = toStr(self.entry_o.get())
        if self.pathO!=pathO:
            formatD = self.combobox_o.get()
            if len(pathO)>7:
                if pathO[:7]=='file://':
                    pathO=urlToPath(pathO)
                    self.entry_o.delete(0, 'end')
                    self.entry_o.insert(0, pathO)
            if self.pref['auto_set_for']:#format==noneItem:
                ext = os.path.splitext(pathO)[-1].lower()
                if ext in ('.gz', '.bz2', '.zip'):
                    ext = os.path.splitext(pathO[:-len(ext)])[-1].lower()
                for i in range(len(Glossary.writeExt)):
                    if ext in Glossary.writeExt[i]:
                        self.combobox_o.set(Glossary.writeDesc[i])
                        break
            self.pathO = pathO
    def browse_i(self):
        path = tkinter.filedialog.askopenfilename(initialdir=self.fcd_dir)
        if path:
            self.entry_i.delete(0, 'end')
            self.entry_i.insert(0, path)
            self.entry_changed()
            self.fcd_dir = os.path.dirname(path)#????????
    def browse_o(self):
        path = tkinter.filedialog.asksaveasfilename()
        if path:
            self.entry_o.delete(0, 'end')
            self.entry_o.insert(0, path)
            self.entry_changed()
            self.fcd_dir = os.path.dirname(path)#????????
    def load(self):
        iPath = toStr(self.entry_i.get())
        if not iPath:
            log.critical('Input file path is empty!');return
        formatD = self.combobox_i.get()
        if formatD==noneItem:
            #log.critical('Input format is empty!');return
            format=''
            log.info('Please wait...')
        else:
            format = Glossary.descFormat[formatD]
            log.info('Reading from %s, please wait...'%formatD)
        #while gtk.events_pending():#??????????????
        #    gtk.main_iteration_do(False)
        t0=time.time()
        """
        if formatD[:7]=='Omnidic':
            dicIndex=self.xml.get_widget('spinbutton_omnidic_i').get_value_as_int()
            ex = self.glos.readOmnidic(iPath, dicIndex=dicIndex)
        elif formatD[:8]=='StarDict' and self.checkb_i_ext.get_active():
            ex = self.glos.readStardict_ext(iPath)
        else:"""
        ex = self.glos.read(iPath, format=format)
        if ex:
            log.info('reading %s file: "%s" done'%(
                format,
                iPath,
            ))
        else:
            log.critical('reading %s file: "%s" failed.'%(format, iPath))
            return False
        #self.iFormat = format
        self.iPath = iPath
        #self.button_conv.set_sensitive(True)
        self.glos.uiEdit()
        self.progress(1.0, 'Loading Comleted')
        log.info('time left = %3f seconds'%(time.time()-t0))
        for x in self.glos.info:
            log.info('%s="%s"'%(x[0], x[1]))
        return True
    def convert(self):
        oPath = toStr(self.entry_o.get())
        if not oPath:
            log.critical('Output file path is empty!');return
        formatD = self.combobox_o.get()
        if formatD in (noneItem, ''):
            log.critical('Output format is empty!');return
        log.info('Converting to %s, please wait...'%formatD)
        #while gtk.events_pending():#??????????
        #    gtk.main_iteration_do(False)
        self.running = True
        format = Glossary.descFormat[formatD]
        t0 = time.time()
        """
        if format=='Omnidic':
            dicIndex=self.xml.get_widget('spinbutton_omnidic_o').get_value_as_int()
            self.glos.writeOmnidic(oPath, dicIndex=dicIndex)
        elif format=='Babylon':
            encoding = self.xml.get_widget('comboentry_enc').get_active_text()
            self.glos.writeBabylon(oPath, encoding=encoding)
        else:"""##???????????????????????
        self.glos.write(oPath, format=format)
        #self.oFormat = format
        self.oPath = oPath
        log.info('writing %s file: "%s" done.'%(format, oPath))
        log.info('time left = %3f seconds'%(time.time()-t0))
        self.running = False
        return True
    def run(self, editPath=None, read_options=None):
        if read_options is None:
            read_options = {}
        ## editPath and read_options are for DB Editor, which is not implemented yet
        self.mainloop()
    def progress(self, rat, text=''):
        self.pbar.updateProgress(rat*100, None, text)
        ##self.pbar.value = rat*100
        ##self.pbar.update()
    def progressStart(self):
        self.pbar.updateProgress(0)
    def progressEnd(self):
        self.pbar.updateProgress(100)
    def r_finished(self):
        pass
    def console_clear(self, event=None):
        self.console.delete('1.0', 'end')
        self.console.insert('end', 'Console:\n')
    def r_browse_i(self):
        pass
    def r_browse_o(self):
        pass
    def r_load(self):
        pass


if __name__=='__main__':
    import sys
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = ''
    ui = UI(path)
    ui.run()


