# -*- coding: utf-8 -*-
## ui_gtk.py
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

import shutil, sys, os
import logging
import traceback

from pyglossary.text_utils import urlToPath, click_website, startRed, endFormat
from pyglossary.glossary import *
from base import *
import gtk, gtk.glade

log = logging.getLogger('root')

#use_psyco_file = join(srcDir, 'use_psyco')
use_psyco_file = '%s_use_psyco'%confPath
psyco_found = None

gtk.window_set_default_icon_from_file(logo)

buffer_get_text = lambda b: b.get_text(b.get_start_iter(), b.get_end_iter())


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
            buff.get_tag_table().add(gtk.TextTag(levelname))
            ###
            self.buffers[levelname] = buff
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






class UI(UIBase):
    def write(self, tag):
        pass
    def about_init(self):
        about = gtk.AboutDialog()
        about.set_name('PyGlossary')
        about.set_version(VERSION)
        about.set_authors(authors)
        about.set_comments(aboutText)
        #about.set_license('PyGlossary is licensed by GNU General Public License version 3 (or later)')
        vbox = about.get_children()[0].get_children()[0]
        try:
            link=gtk.LinkButton(homePage)
        except:## May be an old PyGTK version, that has not gtk.LinkButton
            about.set_website(homePage) ## A palin label (not link)
        else:
            vbox.pack_start(link, 0, 0)
            link.show()
            gtk.link_button_set_uri_hook(click_website) ## click_website defined in text_utils.py
        about.set_license(licenseText)
        about.set_wrap_license(True)
        about.connect('delete-event', self.about_close)
        buttons = about.get_children()[0].get_children()[1].get_children()## List of buttons of about dialogs
        buttons[2].connect('clicked', self.about_close) ## Fix the PyGTK bug that Close button does not work!
        about.set_logo(gtk.gdk.pixbuf_new_from_file(logo))
        self.about = about
    def about_clicked(self, widget):
        self.about.show()
    def about_close(self, *args):
        self.about.hide()
        return True
    def def_widgets(self, names):
        for name in names:
            #try:
            exec('self.%s = self.xml.get_widget("%s")'%(name, name))
            #except:
            #    log.debug(name)
                #sys.exit(1)
    def __init__(self, **options):
        #UIBase.__init__(self, **options)
        self.xml= gtk.glade.XML(os.path.join(rootDir, 'ui', 'glade', 'maindialog.glade'))
        self.d = self.xml.get_widget('maindialog')
        self.d.connect('delete-event', self.close_button_clicked)
        self.about_init()
        signals={}##{'browse1':self.browse1}
        for attr in dir(self):
            signals[attr] = getattr(self, attr)
        self.xml.signal_autoconnect(signals)
        self.def_widgets(('quitdialog', 'textview_out', 'textview_err', 'maindialog',\
            'vpaned1', 'notebook1', 'entry_i', 'entry_o',\
            'combobox_i', 'combobox_o', 'checkb_o_det', 'combobox_r_i',\
            'entry_r_i', 'entry_r_o', 'combobox_sr', 'progressbar', 'textview_edit',\
            'label_convert', 'label_reverse', 'combobox_mode', 'textview_merge', 'button_conv'))

        """## changing colors
        self.textview_err.modify_base(0, gtk.gdk.Color(10000, 0, 0))#textview bg color
        #self.textview_err.modify_base(1, gtk.gdk.Color(-1, 0, 0))#selected text bg color, when deselect window!
        self.textview_err.modify_text(0, gtk.gdk.Color(-1, -1, -1))#normal text color
        #self.textview_err.modify_text(1, gtk.gdk.Color(-1, -1, -1))#selected test color, when deselect window!
        # modify_bg modify_fg
        self.textview_out.modify_base(0, gtk.gdk.Color(0, 10000, 0))#textview bg color
        self.textview_out.modify_text(0, gtk.gdk.Color(-1, -1, -1))#normal text color
        """
        self.quitdialog.connect('delete-event', self.quitdialog_close)
        self.assert_quit = False
        self.path = ''
        self.glos = Glossary(ui=self)
        for f in Glossary.readFormats:
            self.combobox_i.append_text(Glossary.formatsDesc[f])
            self.combobox_r_i.append_text(Glossary.formatsDesc[f])
        for f in Glossary.writeFormats:
            self.combobox_o.append_text(Glossary.formatsDesc[f])
        self.combobox_sr.set_active(0)
        self.dbe_init()
        self.editor_path = ''
        self.tabIndex = 0
        self.fcd_dir = ''
        ###################################
        t_table = gtk.TextTagTable()
        tag = gtk.TextTag('filelist')
        t_table.add(tag)
        self.merge_buffer = gtk.TextBuffer(t_table)
        self.textview_merge.set_buffer(self.merge_buffer)
        self.merge_buffer.connect('changed', self.textview_merge_changed)
        self.combobox_mode.set_active(2)
        ####################################
        self.reverseStop = False
        self.pref_init(**options)
        #thread.start_new_thread(UI.progressListen,(self,))
        #################### Comment folowing two line to see the output in the terminal
        self.setupLogging()
        ####################
        #self.d.show_all()
        #self.d.vbox.do_realize()
    def run(self, editPath=None, read_options=None):
        if read_options is None:
            read_options = {}
        if editPath:
            self.notebook1.set_current_page(3)
            log.info('Opening file "%s" for edit. please wait...'%editPath)
            while gtk.events_pending():
                gtk.main_iteration_do(False)
            self.dbe_open(editPath, **read_options)
        gtk.main()
    def textview_merge_changed(self, *args):
        (stderr, sys.stderr) = (sys.stderr, sys.__stderr__)
        b = self.merge_buffer
        lines = buffer_get_text(b).split('\n')
        for i in xrange(len(lines)):
            if len(lines[i]) > 7:
                if lines[i][:7]=='file://':
                    lines[i] = urlToPath(lines[i])
        #if not lines[-1]:
        #    lines.pop(-1)
        b.set_text('\n'.join(lines))
        sys.stderr = stderr
    def show_msg(self, key, icon='error', buttons='close'):
        ## From program pySQLiteGUI writen by 'Milad Rastian'
        ## Show message dialog
        msgicon = 0
        msgbuttons = 0
        if icon=='error':
            msgicon = gtk.MESSAGE_ERROR
        elif icon=='info':
            msgicon = gtk.MESSAGE_INFO
        elif icon=='question':
            msgicon = gtk.MESSAGE_QUESTION
        elif icon=='warning':
            msgicon = gtk.MESSAGE_WARNING
        if buttons=='close':
            msgbuttons = gtk.BUTTONS_CLOSE
        elif buttons=='yesno':
            msgbuttons = gtk.BUTTONS_YES_NO
        msgWindow = gtk.MessageDialog(
            None,
            0,
            msgicon,
            msgbuttons,
            ERRORS[key][0],
        )
        msgWindow.format_secondary_text(ERRORS[key][1])
        response = msgWindow.run()
        msgWindow.destroy()
        return response
######################################################################
    def setupLogging(self):
        log.addHandler(
            GtkTextviewLogHandler({
                'CRITICAL': self.textview_err,
                'ERROR': self.textview_err,
                'WARNING': self.textview_out,
                'INFO': self.textview_out,
                'DEBUG': self.textview_out,
            })
        )
        self.clear_output()
        self.clear_errors()
        #####
        self.checkb_o_det.connect('toggled', self.detailsCheckChanged)
        self.detailsCheckChanged()
    def detailsCheckChanged(self, widget=None):
        if self.checkb_o_det.get_active():
            verbosity = 4
        else:
            verbosity = 2
        print('verbosity=%s'%verbosity)
        log.setVerbosity(verbosity)
#################################################################################
    #def maindialog_resized(self, *args):
    #    self.vpaned1.set_position(185)
    #    log.debug(args)
    #ok_clicked=lambda self, *args: pass
    def apply_clicked(self, *args):
        i = self.tabIndex
        if i==0:
            if self.load():
                self.convert_clicked()
        elif i==1:
            if self.r_load():
                self.r_start()
        elif i==3:
            self.dbe_update()
        elif i==4:
            self.pref_update_var()
            log.info('Preferences updated')
            self.pref_save()
            log.info('Preferences saved')
    def close_button_clicked(self, *args):
        if self.assert_quit:
            self.quitdialog.show()
            return True
        else:
            self.quit()
    def quitdialog_close(self, obj, event=None):
        self.quitdialog.hide()
        return True
    #quit=lambda self, *args: sys.exit(0)
    def quit(self, *args):
        self.pref_update_var()
        self.pref_save()
        log.info('Preferences saved')
        #sys.exit(0)
        gtk.main_quit()
    #def help_clicked(self, *args):
    #    HelpDialog().run()
    def browse_i(self, *args):
        FileChooserDialog(self, action='open').run()
        if self.path:
            self.entry_i.set_text(self.path)
            self.fcd_dir = os.path.dirname(self.path)
            self.path = ''
    def browse_o(self, *args):
        FileChooserDialog(self, action='save').run()
        if self.path:
            self.entry_o.set_text(self.path)
            self.fcd_dir = os.path.dirname(self.path)
            self.path = ''
    def load(self, *args):
        iPath = self.entry_i.get_text()
        if not iPath:
            log.critical('Input file path is empty!');return
        formatD = self.combobox_i.get_active_text()
        if formatD:
            format = Glossary.descFormat[formatD]
            log.info('Reading from %s, please wait...'%formatD)
        else:
            #log.critical('Input format is empty!');return
            format = ''
            log.info('Please wait...')
        while gtk.events_pending():
            gtk.main_iteration_do(False)
        t0 = time.time()
        if format=='Omnidic':
            dicIndex = self.xml.get_widget('spinbutton_omnidic_i').get_value_as_int()
            ex = self.glos.readOmnidic(iPath, dicIndex=dicIndex)
        else:
            ex = self.glos.read(iPath, format=format)
        if ex:
            log.info('reading %s file: "%s" done.\n%d words found.'%(
                format,
                iPath,
                len(self.glos.data),
            ))
        else:
            log.info('reading %s file: "%s" failed.'%(format, iPath))
            return False
        #self.iFormat = format
        self.iPath = iPath
        self.button_conv.set_sensitive(True)
        self.progress(1.0, 'Loading Comleted')
        log.debug('time left = %3f seconds'%(time.time()-t0))
        for x in self.glos.info:
            log.info('%s="%s"'%(x[0], x[1]))
        return True
    def load_m(self, *args):
        b = self.merge_buffer
        text = buffer_get_text(b)
        if not text:
            return
        paths = text.split('\n')
        n = len(paths)
        if n==0:
            return
        mode = self.combobox_mode.get_active()
        for i in xrange(n):
            path = paths[i]
            if not path:
                continue
            g = Glossary(ui=self)
            self.ptext = ' of file %s from %s files'%(i+1, n)
            log.info('Loading "%s" ...'%path)
            g.read(path)
            log.info('%s words found'%len(g.data))
            if mode==0:
                self.glos = self.glos.attach(g)
            elif mode==1:
                self.glos = self.glos.merge(g)
            elif mode==2:
                self.glos = self.glos.deepMerge(g)
            del g
            #try:
            #    self.progress(float(i+1)/n, '%s / %s files loaded'%(i+1,n))
            #except:
            #    pass
            if i==0:
                self.button_conv.set_sensitive(True)
            while gtk.events_pending():
                gtk.main_iteration_do(False)
        self.glos.ui = self
    def convert_clicked(self, *args):
        #if self.assert_quit:
        #    log.error('Can not convert glossary, because another operation is running. '+\
        #        'Please open a new PyGlossary window, or wait until that operation be completed.')
        #    return False
        if len(self.glos.data)==0:
            log.error('Input glossary has no word! Be sure to click "Load" before "Convert", '+\
                'or just click "Apply" instead.')
            return False
        oPath = self.entry_o.get_text()
        if not oPath:
            log.critical('Output file path is empty!');return
        formatD = self.combobox_o.get_active_text()
        if not formatD:
            log.critical('Output format is empty!');return
        log.info('Converting to %s, please wait...'%formatD)
        while gtk.events_pending():
            gtk.main_iteration_do(False)
        self.assert_quit=True
        format = Glossary.descFormat[formatD]
        t0=time.time()
        if format=='Omnidic':
            dicIndex=self.xml.get_widget('spinbutton_omnidic_o').get_value_as_int()
            self.glos.writeOmnidic(oPath, dicIndex=dicIndex)
        elif format=='Babylon':
            encoding = self.xml.get_widget('comboentry_enc').get_active_text()
            self.glos.writeBabylon(oPath, encoding=encoding)
        else:
            self.glos.write(oPath, format=format)
        #self.oFormat = format
        self.oPath = oPath
        log.info('writing %s file: "%s" done.'%(format, oPath))
        log.debug('time left = %3f seconds'%(time.time()-t0))
        self.assert_quit=False
        return True

    def combobox_i_changed(self, *args):
        formatD = self.combobox_i.get_active_text()
        format = Glossary.descFormat[formatD]
        if format=='Omnidic':
            self.xml.get_widget('label_omnidic_i').show()
            self.xml.get_widget('spinbutton_omnidic_i').show()
        else:
            self.xml.get_widget('label_omnidic_i').hide()
            self.xml.get_widget('spinbutton_omnidic_i').hide()

    def combobox_o_changed(self, *args):
        formatD = self.combobox_o.get_active_text()
        format = Glossary.descFormat[formatD]
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
        if self.pref['auto_set_out']:## not format:
            pathI = self.entry_i.get_text()
            pathO = self.entry_o.get_text()
            formatOD = self.combobox_o.get_active_text()
            if formatOD and not pathO and '.' in pathI:
                extO = Glossary.descExt[formatOD]
                pathO = os.path.splitext(pathI)[0] + extO
                self.entry_o.set_text(pathO)
    def entry_i_changed(self, *args):
        pathI = self.entry_i.get_text()
        formatD = self.combobox_i.get_active_text()
        if len(pathI) > 7:
            if pathI[:7]=='file://':
                pathI = urlToPath(pathI)
                self.entry_i.set_text(pathI)
        if self.pref['auto_set_for']:## not format:
            pathI = self.entry_i.get_text()
            (name, ext) = os.path.splitext(pathI)
            if ext.lower() in ('.gz', '.bz2', '.zip'):
                ext = os.path.splitext(name)[1].lower()
            for i in xrange(len(Glossary.readExt)):
                if ext in Glossary.readExt[i]:
                    self.combobox_i.set_active(i)
                    break
        if self.pref['auto_set_out']:## not format:
            #pathI = self.entry_i.get_text()
            formatOD = self.combobox_o.get_active_text()
            pathO = self.entry_o.get_text()
            if formatOD and not pathO and '.' in pathI:
                extO = Glossary.descExt[formatOD]
                pathO = os.path.splitext(pathI)[0] + extO
                self.entry_o.set_text(pathO)
    def entry_o_changed(self,*args):
        path = self.entry_o.get_text()
        if not path:
            return
        #format = self.combobox_o.get_active_text()
        if len(path)>7:
            if path[:7]=='file://':
                path = urlToPath(path)
                self.entry_o.set_text(path)
        #if True:## not format:
        path = self.entry_o.get_text()
        (name, ext) = os.path.splitext(path)
        if ext.lower() in ('.gz', '.bz2', '.zip'):
            ext = os.path.splitext(name)[1].lower()
        for i in xrange(len(Glossary.writeExt)):
            if ext in Glossary.writeExt[i]:
                self.combobox_o.set_active(i)
                break
    #################################
    def browse_m(self, *args):
        fcd = FileChooserDialog(self, action='open', multiple=True)
        #if fcd.run() != gtk.RESPONSE_ACCEPT:
        #    return
        fcd.run()
        filelist = fcd.fd.get_filenames()
        text = buffer_get_text(self.merge_buffer)
        if text:
            text += '\n'
        text += '\n'.join(filelist)
        self.merge_buffer.set_text(text)
        #self.fcd_dir = os.path.dirname(self.path)
        self.path = ''

    #################################
    def tab_switched(self, *args):
        ##oldTabIndex = self.xml.get_widget('notebook1').get_current_page()
        i = self.tabIndex = args[-1]
        if i==1:
            self.xml.get_widget('button_r_d').set_sensitive(True)#show()
            self.xml.get_widget('button_apply').set_sensitive(False)
        else:
            self.xml.get_widget('button_r_d').set_sensitive(False)#hide()
            self.xml.get_widget('button_apply').set_sensitive(True)
        #if i in (0,1):
            #self.notebook1.set_resize_mode(0)
            #pass
        #else:
        #    pass
    clear_output = lambda self, *args: self.textview_out.get_buffer().set_text('Output console:\n')
    clear_errors = lambda self, *args: self.textview_err.get_buffer().set_text('Error console:\n')
    #######################################################
    ################################# Reverse tab:
    def r_browse_i(self, *args):
        FileChooserDialog(self, action='open').run()
        if self.path:
            self.entry_r_i.set_text(self.path)
            self.fcd_dir = os.path.dirname(self.path)
            self.path = ''
    def r_browse_o(self, *args):
        FileChooserDialog(self, action='save').run()
        if self.path:
            self.entry_r_o.set_text(self.path)
            self.fcd_dir = os.path.dirname(self.path)
            self.path = ''
    def entry_r_i_changed(self,*args):
        format=self.combobox_r_i.get_active_text()
        path = self.entry_r_i.get_text()
        if len(path)>7:
            if path[:7]=='file://':
                path=urlToPath(path)
                self.entry_r_i.set_text(path)
        #if True:## not format:
        path = self.entry_r_i.get_text()
        (name, ext) = os.path.splitext(path)
        if ext.lower() in ('.gz', '.bz2', '.zip'):
            (name, ext) = os.path.splitext(name)
            ext = ext.lower()
        for i in xrange(len(Glossary.readExt)):
            if ext in Glossary.readExt[i]:
                self.combobox_r_i.set_active(i)
                self.entry_r_o.set_text(name+'-reversed.txt')
                return
    def r_load(self, *args):
        iPath = self.entry_r_i.get_text()
        formatD = self.combobox_r_i.get_active_text()
        if not iPath:
            log.critical('Input file path is empty!')
            return False
        if not formatD:
            log.critical('Input format is empty!')
            return False
        log.info('Reading from %s, please wait...'%formatD)
        format = Glossary.descFormat[formatD]
        self.glosR = Glossary(ui=self)
        while gtk.events_pending():
            gtk.main_iteration_do(False)
        t0 = time.time()
        self.glosR.read(iPath, format=format)
        log.debug('time left = %3f seconds'%(time.time()-t0))
        for x in self.glos.info:
            log.info('%s="%s"'%(x[0], x[1]))
        #self.riFormat = format
        #self.riPath = iPath
        log.info('reading %s file: "%s" done.\n%d words found.'%(
            formatD,
            iPath,
            len(self.glosR.data),
        ))
        self.assert_quit = False
        return True
    def r_dynamic_button_clicked(self, *args):
        text=self.xml.get_widget('label_r_d').get_text()
        if text=='Start':
            self.r_start()
        elif text=='Stop':
            self.r_stop()
        elif text=='Resume':
            self.r_resume()
        else:
            #raise RuntimeError, 'unknown label %s on dynamic button!'%text
            raise RuntimeError('unknown label %s on dynamic button!'%text)
    def r_start(self, *args):
        try:
            self.glosR
        except AttributeError:
            if not self.r_load():
                return False
        #if len(self.glosR.data)==0:
        #    log.error('Input glossary has no word! Be sure to click "Load" before "Start", or just click "Apply" instead.')
        #    return
        oPath = self.entry_r_o.get_text()
        if not oPath:
            log.critical('Output file path is empty!');return
        self.progress(0.0, 'Starting....')
        self.pref_rev_update_var()
        self.pref['savePath']=oPath
        while gtk.events_pending():
            gtk.main_iteration_do(False)
        self.rWords = self.glosR.takeOutputWords()
        self.assert_quit=True
        #revTh = thread.start_new_thread(self.glosR.reverseDic, (self.rWords, self.pref))
        self.xml.get_widget('image_r_d').set_from_stock('gtk-media-pause', 'button')
        self.xml.get_widget('label_r_d').set_text('Stop')
        self.entry_r_i.set_editable(False)
        self.entry_r_o.set_editable(False)
        self.xml.get_widget('button_r_i').set_sensitive(False)
        self.xml.get_widget('button_r_load').set_sensitive(False)
        self.xml.get_widget('button_r_o').set_sensitive(False)
        self.xml.get_widget('vbox_options').set_sensitive(False)
        log.info('Number of input words:', len(self.rWords))
        log.info('Reversing glossary...')
        self.glosR.reverseDic(self.rWords, self.pref)
        while True:## FIXME
        #while not self.reverseStop:
            while gtk.events_pending():
                gtk.main_iteration_do(False)
    def r_stop(self, *args):
        self.reverseStop = True
        self.xml.get_widget('image_r_d').set_from_stock('gtk-media-play', 'button')
        self.xml.get_widget('label_r_d').set_text('Resume')
        self.xml.get_widget('vbox_options').set_sensitive(True)
    def r_resume(self, *args):
        if self.glosR.stoped==True:
            self.pref['autoSaveStep']=int(self.xml.get_widget('spinbutton_autosave').get_value())
            self.reverseStop = False
            #revTh = thread.start_new_thread(self.glosR.reverseDic, (self.rWords, self.pref))
            self.xml.get_widget('image_r_d').set_from_stock('gtk-media-pause', 'button')
            self.xml.get_widget('label_r_d').set_text('Stop')
            self.xml.get_widget('vbox_options').set_sensitive(False)
            log.info('continue reversing from index %d ...'%self.glosR.continueFrom)
            self.glosR.reverseDic(self.rWords, self.pref)
            while True:## FIXME
            #while not self.reverseStop:
                while gtk.events_pending():
                    gtk.main_iteration_do(False)
        else:
            log.debug('self.glosR.stoped=%s'%self.glosR.stoped)
            log.info('Not stoped yet. Wait many seconds and press "Resume" again...')
    def r_finished(self, *args):
        self.glosR.continueFrom=0
        self.assert_quit=False
        self.xml.get_widget('image_r_d').set_from_stock('gtk-media-play', 'button')
        self.xml.get_widget('label_r_d').set_text('Start')
        self.entry_r_i.set_editable(True)
        self.entry_r_o.set_editable(True)
        self.xml.get_widget('button_r_i').set_sensitive(True)
        self.xml.get_widget('button_r_load').set_sensitive(True)
        self.xml.get_widget('button_r_o').set_sensitive(True)
        self.xml.get_widget('vbox_options').set_sensitive(True)
        self.progressbar.set_text('Reversing completed')
        log.info('Reversing completed.')
        #thread.exit_thread() # ???????????????????????????
        ## A PROBLEM: CPU is busy even when reversing completed!

    #######################################################################################
    #######################################################################################

    def editor_open(self, *args):
        step = 1000
        fcd = FileChooserDialog(self, action='open')
        fcd.run()
        if not self.path:
            return
        self.editor_path = self.path
        self.fcd_dir = os.path.dirname(self.path)
        self.path = ''
        text = open(self.editor_path).read()
        self.path = ''
        t_table = gtk.TextTagTable()
        tag = gtk.TextTag('output')
        t_table.add(tag)
        self.editor_buffer = gtk.TextBuffer(t_table)
        self.textview_edit.set_buffer(self.editor_buffer)
        self.assert_quit = True
        size=len(text)
        if size < step:
            self.editor_buffer.set_text(text)
        else:
            self.editor_buffer.set_text(text[:step])
            while gtk.events_pending():
                gtk.main_iteration_do(False)
            i = step
            while i < size-step:
                self.editor_buffer.insert(self.editor_buffer.get_end_iter(), text[i:i+step])
                i += step
                while gtk.events_pending():
                    gtk.main_iteration_do(False)
            self.editor_buffer.insert(self.editor_buffer.get_end_iter(), text[i:])


    def editor_save(self, *args):
        exit = self.editor_save_as(self.editor_path)
        if exit==True:
            log.info('File saved: "%s"'%self.editor_path)
            return True
        elif exit==False:
            log.info('File not saved: "%s"'%self.editor_path)
            return False
        else:
            return exit
    def editor_save_as(self, *args):
        if args[0]:
            self.editor_path = args[0]
        else:
            fcd = FileChooserDialog(self, action='save')
            fcd.run()
            if not self.path:
                return
            self.editor_path = self.path
            self.fcd_dir = os.path.dirname(self.path)
            self.path = ''
        open(self.editor_path, 'w').write(buffer_get_text(self.editor_buffer))
        self.assert_quit = False
        return True
    ################################################################################
    ################################# DB Editor ####################################
    def dbe_init(self, *args):
        self.def_widgets(['entry_dbe', 'checkb_db_ro', 'entry_db_index', 'textview_dbe',
            'treeview', 'dbe_info_dialog', 'entry_dbe_info', 'textview_dbe_info', 'treeview_info'])
        table = gtk.TextTagTable()
        tag = gtk.TextTag('definition')
        table.add(tag)
        self.buffer_dbe = gtk.TextBuffer(table)
        self.textview_dbe.set_buffer(self.buffer_dbe)
        self.treestore = gtk.ListStore(str, int)
        self.treeview.set_model(self.treestore)
        self.cell = gtk.CellRendererText()
        self.cell2 = gtk.CellRendererText()
        col = gtk.TreeViewColumn('Word', self.cell, text=0)
        col2 = gtk.TreeViewColumn('Index', self.cell2, text=1)
        col.set_resizable(True)
        self.treeview.append_column(col)
        self.treeview.append_column(col2)
        ###
        table2 = gtk.TextTagTable()
        tag2 = gtk.TextTag('info')
        table2.add(tag2)
        self.buffer_dbe_info = gtk.TextBuffer(table2)
        self.textview_dbe_info.set_buffer(self.buffer_dbe_info)
        self.treestore_info = gtk.ListStore(str)
        self.treeview_info.set_model(self.treestore_info)
        self.cell = gtk.CellRendererText()
        self.cell2 = gtk.CellRendererText()
        col = gtk.TreeViewColumn('Key', self.cell, text=0)
        col.set_resizable(True)
        self.treeview_info.append_column(col)
        self.ptext = ''
        #self.vbox4 = self.xml.get_widget('vbox4')
        #ag = gtk.AccelGroup()
        #log.debug(dir(gtk.keysyms))
        #ag.connect_by_path('gtk.keysym.Control_L', self.dbe_open)
        self.info_i = -1
    def dbe_new(self, *args):
        self.glosE = Glossary(ui=self)
        self.glosE.data.append(('##name', ''))
        self.treestore.clear()
        self.treestore.append(('##name', 0))
        self.db_ind = 0
        self.db_format = ''
        self.dbe_goto(0, save=False)
        self.dbe_save_as('')
    def dbe_open(self, arg=None, **read_options):
        format = ''
        if isinstance(arg, basestring):
            self.path = arg
            self.fcd_format = ''
        else:
            fcd = FileChooserDialog(self, combo_items=Glossary.readDesc, action='open')
            fcd.hbox_format.show()
            fcd.combobox.set_active(0)
            fcd.run()
            if not self.path:
                return False
        self.dbe_path = self.path
        self.fcd_dir = os.path.dirname(self.path)
        self.path = ''
        self.glosE = Glossary(ui=self)
        while gtk.events_pending():
            gtk.main_iteration_do(False)
        self.set_cursor(gtk.gdk.WATCH)
        t0 = time.time()
        if self.fcd_format in ('Auto (by extention)', ''):
            self.glosE.read(self.dbe_path, **read_options)
        else:
            format = Glossary.descFormat[self.fcd_format]
            self.glosE.read(self.dbe_path, format=format, **read_options)
        self.assert_quit = True
        log.debug('time left = %3f seconds'%(time.time()-t0))
        for x in self.glos.info:
            log.info('%s="%s"'%(x[0], x[1]))
        self.fcd_format = ''
        self.db_ind = None
        d = self.glosE.data
        t = self.treestore
        #self.entry_db_index.set_width_chars(len(str(len(d)))+1)#???????????? DOES NOT WORK
        #self.entry_db_index.show()
        t.clear()
        for i in xrange(len(d)):
            t.append((d[i][0], i))
            ##d[i]=(x[0], x[1], True) ## read only
        self.dbe_goto(0, save=False)
        self.db_format = format
        #########
        t = self.treestore_info
        t.clear()
        for key in self.glosE.infoKeys():
            t.append((key,))
        #########
        self.info_i=0
        self.dbe_info_goto(0, save=False)
        self.set_cursor(gtk.gdk.LEFT_PTR)
    def set_cursor(self, cursor_type):
        c = gtk.gdk.Cursor(cursor_type)
        for w in (self.d, self.textview_out, self.textview_err, self.textview_dbe):
            if not w.window:
                pass #????????????????????????
                #w.connect('realize', lambda obj: w.window.set_cursor(c))
            else:
                w.window.set_cursor(c)
    def dbe_save(self, *args):
        shutil.copy(self.dbe_path, self.dbe_path+'~')
        if self.dbe_save_as(self.dbe_path):
            os.remove(self.dbe_path+'~')
        else:
            os.remove(self.dbe_path)
            os.rename(self.dbe_path+'~', self.dbe_path)
            log.error('Saving file "%s" failed! Backup file restored instaed.'%self.dbe_path)
    def dbe_save_as(self, *args):
        #self.glosE.data[self.db_ind] = (self.entry_dbe.get_text(),self.buffer_dbe.get_text())
        self.dbe_update()
        format = self.db_format
        if args[0] and format in Glossary.writeFormats + ['']:
            self.dbe_path = args[0]
            ex = self.glosE.write(self.dbe_path, format=format)
        else:
            fcd = FileChooserDialog(self, combo_items=Glossary.writeDesc, action='save')
            fcd.hbox_format.show()
            fcd.combobox.set_active(0)
            fcd.run()
            if not self.path:
                return False
            path = self.dbe_path = self.path
            self.path = ''
            self.fcd_dir = os.path.dirname(path)
            if self.fcd_format=='Auto (by extention)':
                ex = self.glosE.write(path)
            else:
                format = Glossary.descFormat[self.fcd_format]
                ex = self.glosE.write(path, format=format)
            self.dbe_path = path
        if ex != False:
            log.info('DB file "%s" saved'%self.dbe_path)
            self.assert_quit = False
            self.db_format = format
            return True
    def dbe_ro_clicked(self, *args):
        ro = self.checkb_db_ro.get_active()
        self.entry_dbe.set_editable(not ro)
        self.textview_dbe.set_editable(not ro)
    dbe_prev = lambda self, *args: self.dbe_goto(self.db_ind-1)
    dbe_next = lambda self, *args: self.dbe_goto(self.db_ind+1)
    dbe_first = lambda self, *args: self.dbe_goto(0)
    dbe_last = lambda self, *args: self.dbe_goto(-1)
    def dbe_goto_clicked(self, *args):
        ind = self.entry_db_index.get_text()
        try:
            n_ind=int(ind)
        except:
            log.error('bad index: "%s"'%ind)
            return False
        self.dbe_goto(n_ind)
    def dbe_update(self):
        d = (self.entry_dbe.get_text(), buffer_get_text(self.buffer_dbe))
        self.glosE.data[self.db_ind] = d
        self.treestore[self.db_ind][0] = d[0]
    def dbe_update_info(self):
        d = (self.entry_dbe_info.get_text(), buffer_get_text(self.buffer_dbe_info))
        self.glosE.info[self.info_i] = d
        self.treestore_info[self.info_i][0] = d[0]
    def dbe_goto(self, n_ind, save=True):
        p_ind = self.db_ind
        if n_ind==p_ind and save:
            self.dbe_update()
            return
        if save:
            p_data = (self.entry_dbe.get_text(), buffer_get_text(self.buffer_dbe))
        n = len(self.glosE.data)
        if 0 <= n_ind < n:
            pass
        elif n_ind == n:
            n_ind = 0
        elif -n < n_ind < 0:
            n_ind += n
        else:
            log.error('index out of range: "%s"'%n_ind)
            return False
        self.db_ind = n_ind
        try:
            d = self.glosE.data[n_ind]
        except IndexError:
            return
        self.entry_dbe.set_text(d[0])
        try:
            self.entry_db_index.set_text(str(n_ind))### ????????????????????????????????????
        except:
            pass
        #log.debug('Setting text "%s"'%d[1])
        self.buffer_dbe.set_text(d[1])
        self.treeview.set_cursor(n_ind)
        if save:
            self.glosE.data[p_ind] = p_data
            self.treestore[p_ind][0] = p_data[0]
    def dbe_info_goto(self, n_ind, save=True):
        p_ind = self.info_i
        if save:
            p_info = (self.entry_dbe_info.get_text(), buffer_get_text(self.buffer_dbe_info))
        n = len(self.glosE.info)
        """if 0 <= n_ind < n:
            pass
        elif n_ind == n:
            n_ind = 0
        elif -n < n_ind < 0:
            n_ind += n
        else:
            log.error('index out of range: "%s"'%n_ind)
            return False"""
        self.info_i = n_ind
        try:
            inf = self.glosE.info[n_ind]
        except:
            #log.exception('info does not exist:')
            return
        self.entry_dbe_info.set_text(inf[0])
        self.buffer_dbe_info.set_text(inf[1])
        self.treeview_info.set_cursor(n_ind)
        if save:
            self.glosE.info[p_ind] = p_info
            self.treestore_info[p_ind][0] = p_info[0]
    def dbe_new_w(self, *args):## new Word after selected
        n = len(self.glosE.data)
        cur = self.treeview.get_cursor()[0]
        if cur:
            try:
                n = cur[0] + 1
            except:
                log.exception('could not get index of treeview curser:')
                return False
        else:
            n = 0
        word = 'word%s'%n
        self.glosE.data.insert(n, (word, ''))
        self.treestore.insert(n, (word, str(n)))
        self.dbe_goto(n)
        self.entry_dbe.select_region(0, -1)
        self.entry_dbe.do_focus(self.entry_dbe, 0)
        ######???????????????????????
        while gtk.events_pending():
            gtk.main_iteration_do(False)
        for i in xrange(n+1, len(self.glosE.data)):
            #self.treestore[i]=[self.glosE.data[i][0], str(i)]
            self.treestore[i][1]=str(i)
    def dbe_new_we(self, *args):## new Word at the End
        n = len(self.glosE.data)
        word = 'word%s'%n
        self.glosE.data.append((word, ''))
        self.treestore.append((word, n))
        self.dbe_goto(n)
        self.entry_dbe.select_region(0, -1)
        self.entry_dbe.do_focus(self.entry_dbe, 0)
    def dbe_del_w(self, *args):
        n = len(self.glosE.data)
        ind = self.db_ind
        log.debug('Deleting index %s word "%s"'%(ind,    self.glosE.data[ind][0]))
        try:
            self.glosE.data.pop(ind)
        except IndexError:
            log.exception('data record %s not found'%ind)
            return
        #del self.glosE.data[ind]
        del self.treestore[ind]
        if n==1:
            return
        if ind==n-1:
            self.dbe_goto(n-2, False)
        else:
            self.treestore[ind][1] = ind
            self.dbe_goto(ind, False)
            for i in xrange(ind+1, min(ind+30, n-1)):
                try:
                    self.treestore[i][1] = i
                except IndexError:
                    break
            while gtk.events_pending():
                gtk.main_iteration_do(False)
            for i in xrange(ind+1, n-1):
                try:
                    self.treestore[i][1] = i
                except IndexError:
                    break
                if i%1000==0:
                    while gtk.events_pending():
                        gtk.main_iteration_do(False)
    def treeview_changed(self, *args):
        try:
            i = self.treeview.get_cursor()[0][0]
        except:
            log.exception('could not get index of treeview curser!')
            return False
        #self.dbe_update()
        self.dbe_goto(i)
    def treeview_info_changed(self, *args):
        try:
            i = self.treeview_info.get_cursor()[0][0]
        except:
            log.error('can not get index of treeview_info curser!')
        else:
            self.dbe_info_goto(i)
    def dbe_info_move_back(self, *args):
        g = self.glosE
        s = self.treestore_info
        i = self.info_i
        if i<1:
            return
        (g.info[i], g.info[i-1]) = (g.info[i-1], g.info[i])
        (s[i], s[i-1] ) = (s[i-1], s[i] )
        self.info_i = i-1
        self.dbe_info_goto(self.info_i)
    def dbe_info_move_next(self, *args):
        g = self.glosE
        s = self.treestore_info
        i = self.info_i
        n = len(g.info)
        if i>n-2:
            return
        (g.info[i], g.info[i+1]) = (g.info[i+1], g.info[i])
        (s[i], s[i+1] ) = (s[i+1], s[i] )
        self.info_i = i+1
        self.dbe_info_goto(self.info_i)
    def dbe_info_del(self, *args):
        g = self.glosE
        s = self.treestore_info
        i = self.info_i
        n = len(g.info)
        try:
            g.info.pop(i)
        except:
            log.exception('info does not exist:')
            return
        del s[i]
        if i>n-2:
            self.info_i=n-2
        if n==1:
            self.entry_dbe_info.set_text('')
            self.buffer_dbe_info.set_text('')
            self.info_i = -1
        else:
            self.dbe_info_goto(self.info_i, save=False)
    def dbe_info_new(self, *args):
        g = self.glosE
        n = len(g.info)
        if n>0:
            self.dbe_update_info()
        else:
            self.info_i = -1
        i = self.info_i
        nkey = 'key%s'%(i+1)
        g.info.insert(i+1, (nkey, ''))
        self.treestore_info.insert(i+1, (nkey,))
        for j in xrange(i+1, n+1):
            self.treestore_info[j][0] = g.info[j][0]
        self.info_i += 1
        self.dbe_info_goto(self.info_i, False)
        self.entry_dbe_info.select_region(0, -1)
        self.entry_dbe_info.do_focus(self.entry_dbe_info, 0)
    def entry_dbe_activate(self, *args):
        w = self.entry_dbe.get_text()
        i = self.db_ind
        g = self.glosE
        g.data[i] = (w, g.data[i][1]) + g.data[i][2:]
        self.treestore[i][0] = w
    def entry_dbe_info_activate(self, *args):
        k = self.entry_dbe_info.get_text()
        i = self.info_i
        self.glosE.info[i] = k
        self.treestore_info[i][0] = k
    def dbe_sort(self, *args):
        if len(self.glosE.data)<2:
            return
        self.dbe_update()
        if len(self.glosE.data)!=len(self.treestore):
            log.info(len(self.glosE.data), len(self.treestore))
        self.glosE.data.sort()
        for i in xrange(len(self.glosE.data)):
            self.treestore[i]=[self.glosE.data[i][0], str(i)]
        self.dbe_goto(self.db_ind, False)
    def dbe_info_clicked(self, *args):
        self.dbe_info_dialog.show()
        #log.debug(self.glosE.info)
    def dbe_info_close(self, *args):
        if self.info_i!=-1:
            try:
                self.glosE
            except AttributeError:
                pass
            else:
                try:
                    self.glosE.info[self.info_i] = buffer_get_text(self.entry_dbe_info)
                except:## IndexError
                    pass
        self.dbe_info_dialog.hide()
        return True
    def pref_init(self, **options):
        self.pref={}
        self.def_widgets(['combobox_save', 'combobox_newline', 'cb_psyco', 'checkb_autofor', 'checkb_autoout',\
            'cb_auto_update', 'cb_c_sort', 'cb_rm_tags', 'checkb_lower', 'checkb_utf8', 'checkb_defs'])
        self.combobox_save.set_active(0)
        self.newlineItems = ('\\n', '\\r\\n', '\\n\\r')
        self.showRelItems = ['None', 'Percent At First', 'Percent']
        for item in self.showRelItems:
            self.combobox_sr.append_text(item)
        for name in ('out', 'err', 'edit', 'dbe'):
            self.def_widgets(['cb_wrap_%s'%name, 'colorpicker_bg_%s'%name, 'colorpicker_font_%s'%name])
        self.pref['auto_update'] = self.cb_auto_update.get_active()
        if os.path.isfile(use_psyco_file):
            self.cb_psyco.set_active(True)
        else:
            self.cb_psyco.set_active(False)
        self.pref_load(**options)
        self.pref_update_var()
        self.pref_rev_update_gui()
    def pref_load(self, **options):
        if not UIBase.pref_load(self, **options):
            return False
        self.combobox_save.set_active(self.pref['save'])
        self.cb_auto_update.set_active(self.pref['auto_update'])
        for i in xrange(len(self.newlineItems)):
            if self.pref['newline']==eval('"'+self.newlineItems[i]+'"'):
                self.combobox_newline.set_active(i)
                break
        self.checkb_autofor.set_active(self.pref['auto_set_for'])
        self.checkb_autoout.set_active(self.pref['auto_set_out'])
        self.cb_c_sort.set_active(self.pref['sort'])
        self.checkb_lower.set_active(self.pref['lower'])
        self.cb_rm_tags.set_active(self.pref['remove_tags'])
        self.checkb_utf8.set_active(self.pref['utf8_check'])
        for name in ('out', 'err', 'edit', 'dbe'):
            eval('self.cb_wrap_%s'%name).set_active(self.pref['wrap_%s'%name])
        for name in ('out', 'err', 'edit', 'dbe'):
            color=self.pref['color_bg_%s'%name]
            eval('self.colorpicker_bg_%s'%name).set_color(gtk.gdk.Color(*color))
        for name in ('out', 'err', 'edit', 'dbe'):
            color=self.pref['color_font_%s'%name]
            eval('self.colorpicker_font_%s'%name).set_color(gtk.gdk.Color(*color))
        return True
    def pref_update_var(self, *args):
        self.pref['auto_update'] = self.xml.get_widget('cb_auto_update').get_active()
        k = self.combobox_newline.get_active()
        self.pref['newline'] = self.newlineItems[k]
        for name in ('out', 'err', 'edit', 'dbe'):
            exec('\
self.pref["wrap_%s"]=self.cb_wrap_%s.get_active()\n\
if self.pref["wrap_%s"]:\n\
    self.textview_%s.set_wrap_mode(gtk.WRAP_WORD)\n\
else:\n\
    self.textview_%s.set_wrap_mode(gtk.WRAP_NONE)'%((name,)*5))
            col=eval('self.colorpicker_bg_%s'%name).get_property('color')
            exec('self.textview_%s.modify_base(0, gtk.gdk.Color(%s, %s, %s))'%(name, col.red, col.green, col.blue))
            exec('self.pref["color_bg_%s"]=(col.red,col.green,col.blue)'%name)
            exec('col=self.colorpicker_font_%s.get_property(\'color\')'%name)
            exec('self.textview_%s.modify_text(0, gtk.gdk.Color(%s, %s, %s))'%(name, col.red, col.green, col.blue))
            exec('self.pref["color_font_%s"]=(col.red,col.green,col.blue)'%name)
        self.pref['auto_set_for']=self.checkb_autofor.get_active()
        self.pref['auto_set_out']=self.checkb_autoout.get_active()
        self.pref['sort']=self.xml.get_widget('cb_c_sort').get_active()
        self.pref['lower']=self.xml.get_widget('checkb_lower').get_active()
        self.pref['remove_tags']=self.cb_rm_tags.get_active()
        self.pref['utf8_check']=self.checkb_utf8.get_active()
    def pref_rev_update_var(self):
        self.pref['matchWord']=self.xml.get_widget('checkb_mw').get_active()
        self.pref['showRel']=self.combobox_sr.get_active_text()
        self.pref['autoSaveStep']=int(self.xml.get_widget('spinbutton_autosave').get_value())##get_value() returns a float
        self.pref['minRel']=self.xml.get_widget('spinbutton_minrel').get_value()/100.0
        self.pref['maxNum']=int(self.xml.get_widget('spinbutton_maxnum').get_value())
        self.pref['includeDefs']=self.checkb_defs.get_active()
    def pref_rev_update_gui(self):
        self.xml.get_widget('checkb_mw').set_active(self.pref['matchWord'])
        for i in xrange(len(self.showRelItems)):
            if self.showRelItems[i]==self.pref['showRel']:
                self.combobox_sr.set_active(i)
        self.xml.get_widget('spinbutton_autosave').set_value(self.pref['autoSaveStep'])
        self.xml.get_widget('spinbutton_minrel').set_value(self.pref['minRel']*100.0)
        self.xml.get_widget('spinbutton_maxnum').set_value(self.pref['maxNum'])
        self.xml.get_widget('checkb_defs').set_active(self.pref['includeDefs'])
        while gtk.events_pending():
            gtk.main_iteration_do(False)
    def pref_save(self, *args):
        self.pref_rev_update_var()
        self.pref['save']=self.combobox_save.get_active()
        if self.pref['save']==0:
            try:
                fp = open(self.prefSavePath[0], 'w')
            except:
                log.exception('error while opening save file %s'%self.prefSavePath[0])
                return
        elif self.pref['save']==1:
            try:
                fp = open(self.prefSavePath[1], 'w')
            except IOError:
                log.exception('error while opening save file %s'%self.prefSavePath[1])
                try:
                    fp = open(self.prefSavePath[0], 'w')
                except:
                    log.exception('error while opening save file %s'%self.prefSavePath[0])
                    return
                self.pref['save']=0
        else:
            return
        ex = os.path.isfile(use_psyco_file)
        if psyco_found==False:
            self.cb_psyco.set_active(False)
            self.cb_psyco.set_sensitive(False)
        elif self.cb_psyco.get_active():
            if not ex:
                open(use_psyco_file, 'w').close()
        else:
            if ex:
                os.remove(use_psyco_file)
        if self.pref['save']==1:
            fp.write('save=%r\n'%self.pref['save'])
        for key in self.prefKeys:
            fp.write('%s=%r\n'%(key, self.pref[key]))
    def pref_auto_clicked(self, *args):
        self.pref['auto_update'] = self.cb_auto_update.get_active()
    def pref_changed(self, *args):
        if self.pref['auto_update']:
            self.pref_update_var()
    def grab_focus_reverse(self, *args):
        self.label_reverse.grab_focus()
    def progressStart(self):
        while gtk.events_pending():
            gtk.main_iteration_do(False)
    def progress(self, rat, text=None):
        (stderr, sys.stderr) = (sys.stderr, sys.__stderr__)
        if not text:
            text = '%%%d%s'%(rat*100, self.ptext)
        self.progressbar.update(rat)
        self.progressbar.set_text(text)
        while gtk.events_pending():
            gtk.main_iteration_do(False)
        sys.stderr = stderr
    def progressEnd(self):
        self.progress(1.0)
        while gtk.events_pending():
            gtk.main_iteration_do(False)
    def progressListen(self, sleep=0.1):
        f = open(fifoPath)
        msg=f.readline()
        while msg!='end':
            if not msg:
                pass
            else:
                if '\n' in msg:
                    msg = msg.split('\n')[-1]
                if '\t' in msg:
                    parts = msg.split('\t')
                    self.progress(float(parts[0]), parts[1])
                else:
                    try:
                        rat = float(msg)
                    except:
                        self.progressbar.set_text(msg)
                    else:
                        self.progressbar.update(rat)
                        self.progressbar.set_text('%%%s'%msg)
            while gtk.events_pending():
                gtk.main_iteration_do(True)
            #time.sleep(sleep)
            msg = f.readline()


class FileChooserDialog:
    def __init__(self, main, path='', combo_items=None, action='open', multiple=False):
        if combo_items is None:
            combo_items = []
        self.main = main
        (stderr, sys.stderr) = (sys.stderr, sys.__stderr__)
        self.xml = gtk.glade.XML(join(rootDir, 'ui', 'glade', 'filechooserdialog.glade'))
        sys.stderr = stderr
        self.fd = self.xml.get_widget('filechooserdialog')
        self.fd.set_action(action)
        self.fd.set_select_multiple(multiple)
        self.hbox_format = self.xml.get_widget('hbox_format')
        signals={}
        for attr in dir(self):
            signals[attr] = getattr(self, attr)
        self.xml.signal_autoconnect(signals)
        if not path:
            try:
                path = main.fcd_dir
            except:
                pass
        if combo_items!=[]:
            self.combobox=self.xml.get_widget('combobox1')
            for item in combo_items:
                self.combobox.append_text(item)
        if os.path.isdir(path):
            self.fd.set_current_folder(path)
        elif os.path.isfile(path):
            self.fd.set_filename(path)
        else:
            self.fd.set_current_folder(homeDir)
    run = lambda self: self.fd.run()
    cancel_clicked = lambda self, *args: self.fd.destroy()
    def ok_clicked(self, *args):
        self.main.path = self.fd.get_filename()
        try:
            self.main.fcd_format = self.combobox.get_active_text()
        except:
            pass
        self.fd.hide()

if __name__=='__main__':
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = ''
    ui = UI(path)
    ui.run()

