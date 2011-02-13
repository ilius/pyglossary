#!/usr/bin/python
# -*- coding: utf-8 -*-
##   ui_gtk_noglade.py 
##
##   Copyright © 2008-2010 Saeed Rasooli <saeed.gnu@gmail.com>  (ilius)
##   Thanks to 'Pier Carteri' <m3tr0@dei.unipd.it> for program Py_Shell.py
##   Thanks to 'Milad Rastian' for program pySQLiteGUI
##
##   This program is a free software; you can redistribute it and/or modify
##   it under the terms of the GNU General Public License as published by
##   the Free Software Foundation; either version 3, or (at your option)
##   any later version.
##
##   You can get a copy of GNU General Public License along this program
##   But you can always get it from http://www.gnu.org/licenses/gpl.txt
##
##   This program is distributed in the hope that it will be useful,
##   but WITHOUT ANY WARRANTY; without even the implied warranty of
##   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##   GNU General Public License for more details.

import shutil
from text_utils import urlToPath, click_website
from glossary import *
import gtk, gtk.glade



stderr_saved = sys.stderr
stdout_saved = sys.stdout

startRed	= '\x1b[31m'
endFormat	= '\x1b[0;0;0m'		# End Format		#len=8

#use_psyco_file='%s%suse_psyco'%(srcDir,os.sep)
use_psyco_file='%s%s.pyglossary_use_psyco'%(confDir,os.sep)
psyco_found=None

## Thanks to 'Pier Carteri' <m3tr0@dei.unipd.it> for program Py_Shell.py
class BufferFile:
    ## Implements a file-like object for redirect the stream to the buffer
    def __init__(self, buff, tag, mode='stdout'):
      self.buffer = buff
      self.tag = tag
      self.mode = mode
    ## Write text into the buffer and apply self.tag
    def write(self, text):
        iter=self.buffer.get_end_iter()
        self.buffer.insert_with_tags(iter, text, self.tag)
        if self.mode=='stdout':
          stdout_saved.write(text)
        elif self.mode=='stderr':
          stderr_saved.write(startRed+text+endFormat)
    writelines = lambda self, l: map(self.write, l)
    flush = lambda self: None
    isatty = lambda self: 1


class UI(gtk.Dialog):
  prefKeys=['save','auto_update','auto_set_for','auto_set_out','sort','lower',\
    'utf8_check','remove_tags','tags','wrap_out','wrap_err',  'wrap_edit','wrap_dbe',\
    'color_bg_out','color_bg_err','color_bg_edit','color_bg_dbe',\
    'color_font_out','color_font_err','color_font_edit','color_font_dbe',\
    'matchWord', 'showRel', 'autoSaveStep', 'minRel', 'maxNum', 'includeDefs']## 'newline' # Reverse Options
  def write(self, tag):
    pass
  def about_init(self):
    about = gtk.AboutDialog()
    about.set_name('PyGlossary')
    about.set_version(VERSION)
    about.set_authors([	'Saeed Rasooli <saeed.gnu@gmail.com> (Maintainer & Supporter)',
    			'Raul Fernandes <rgfbr@yahoo.com.br> (C++ code for BGL)',
    			'Karl Grill (C++ code for BGL)',
    			'Mehdi Bayazee <bayazee@gmail.com> (Program bgl2x.py)',
    			'Nilton Volpato (Program python-progressbar)'])
    about.set_comments(
'''A tool for workig with dictionary databases
Copyleft © 2008-2009 Saeed Rasooli
PyGlossary is licensed by the GNU General Public License''')
    #about.set_license('PyGlossary is licensed by GNU General Public License')
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
    about.connect('delete_event', self.about_close)
    buttons = about.get_children()[0].get_children()[1].get_children()## List of buttons of about dialogs
    buttons[2].connect('clicked', self.about_close) ## Fix the PyGTK bug that Close button not works!
    about.set_icon_from_file('%s%spyglossary.png'%(srcDir,os.sep))
    about.set_logo(gtk.gdk.pixbuf_new_from_file('%s%spyglossary.png'%(srcDir,os.sep)))
    self.about = about
  def about_clicked(self, widget):
    self.about.show()
  def about_close(self, *args):
    self.about.hide()
    return True
  def __init__(self, editPath=''):
    gtk.Dialog.__init__(self)
    try:
      self.set_icon_from_file('%s%spyglossary.png'%(srcDir,os.sep))
    except:
      pass
    button_start = self.add_button('Start', 0)
    button_start.set_image(gtk.image_new_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON))
    button_start.set_sensitive(False)
    button_start.connect('clicked', self.r_dynamic_button_clicked)
    button_apply = self.add_button(gtk.STOCK_APPLY, 0)
    button_apply.connect('clicked', self.apply_clicked)
    button_close = self.add_button(gtk.STOCK_CLOSE, 0)
    button_close.connect('clicked', self.close_button_clicked)
    button_about = self.add_button(gtk.STOCK_ABOUT, 0)
    button_about.connect('clicked', self.about_clicked)
    try:
      button_start.set_tooltip_text('reversing glossary')
      button_close.set_tooltip_text('Close window and exit')
    except AttributeError:
      pass
    ##############################
    vpan = gtk.VPaned()
    self.vbox.add(vpan)
    notebook = gtk.Notebook()
    vpan.add1(notebook)
    vbox_down = gtk.VBox()
    vpan.add2(vbox_down)
    #######
    # Console Vbox (vbox_down)
    hpan = gtk.HPaned()
    swin1 = gtk.ScrolledWindow()
    swin2 = gtk.ScrolledWindow()
    hpan.add1(swin1)
    hpan.add2(swin2)
    textview_out = gtk.TextView()
    textview_err = gtk.TextView()
    self.textview_out = textview_out
    self.textview_err = textview_err
    swin1.add(textview_out)
    swin2.add(textview_err)
    swin1.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    swin2.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    hbox_d = gtk.HBox()
    clear_o = gtk.Button()
    clear_o.set_image(gtk.image_new_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_BUTTON))
    clear_o.connect('clicked', self.clear_output)
    hbox_d.pack_start(clear_o, 0, 0)
    self.checkb_o_det = gtk.CheckButton('Details')
    self.checkb_o_det.set_active(True)
    hbox_d.pack_start(self.checkb_o_det, 0, 0)
    self.progressbar = gtk.ProgressBar()
    self.progressbar.set_text('Progress Bar')
    hbox_d.pack_start(self.progressbar, 1, 1)
    clear_e = gtk.Button()
    clear_e.set_image(gtk.image_new_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_BUTTON))
    clear_e.connect('clicked', self.clear_errors)
    hbox_d.pack_start(clear_e, 0, 0)
    ################## tab Convert ##########################
    swin_conv = gtk.ScrolledWindow()
    vbox_conv = gtk.VBox()
    ##vbox_conv.pack_start(swin_conv, 1, 1)
    swin_conv.add_with_viewport(vbox_conv)
    swin_conv.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    lab = gtk.Label('_Convert')
    lab.set_use_underline(True)
    notebook.append_page(swin_conv, lab)
    #vbox_read = 
    hbox = gtk.HBox()
    label1 = gtk.Label('<b>Read from format:</b>')
    label1.set_use_markup(True)
    hbox.pack_start(label1, 0, 0)
    self.combobox_i = gtk.combo_box_new_text()
    hbox.pack_start(self.combobox_i, 0, 0)
    #####
    hbox_ind = gtk.HBox()
    hbox_ind.pack_start(gtk.Label('Dictionary index:'), 0, 0)
    spin = gtk.SpinButton()
    spin.set_increments(1, 5)
    spin.set_range(0, 999)
    spin.set_width_chars(3)
    hbox_ind.pack_start(spin, 0, 0)
    hbox.pack_start(hbox_ind, 1, 0)
    self.hbox_index = hbox_ind
    #####
    self.checkb_i_ext = gtk.CheckButton('Use external module')
    hbox.pack_start(self.checkb_i_ext, 1, 0)
    vbox_conv.pack_start(hbox, 0, 0)
    ##############
    hbox = gtk.HBox()
    hbox.pack_start(gtk.Label('File Path:'), 0, 0)
    self.entry_i = gtk.Entry()
    hbox.pack_start(self.entry_i, 1, 1)
    browse = gtk.Button('Browse')
    browse.set_image(gtk.image_new_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON))
    browse.connect('clicked', self.browse_i)
    hbox.pack_start(browse, 0, 0)
    load = gtk.Button('Load')
    load.set_image(gtk.image_new_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_BUTTON))
    load.connect('clicked', self.load)
    try:
      conv.set_tooltip_text('Load input glossary into RAM.\nYou can click on "Apply" instead of clicking "Load" and then "Convert"')
    except:
      pass
    hbox.pack_start(load, 0, 0)
    vbox_conv.pack_start(hbox, 0, 0)
    ##############
    exp = gtk.Expander('<b>Read from multiple files</b>')
    exp.set_use_markup(True)
    hbox = gtk.HBox()
    swin = gtk.ScrolledWindow()
    swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    self.textview_merge = gtk.TextView()
    swin.add(self.textview_merge)
    hbox.pack_start(swin, 1, 1)
    vbox = gtk.VBox()
    hbox2 = gtk.HBox()
    browse_mb = gtk.Button('Add Files')
    browse_mb.set_image(gtk.image_new_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON))
    browse_mb.connect('clicked', self.browse_m)
    hbox2.pack_start(browse_mb, 0, 0)
    load_mb = gtk.Button('Load')
    load_mb.set_image(gtk.image_new_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_BUTTON))
    load_mb.connect('clicked', self.load_m)
    hbox2.pack_start(load_mb, 0, 0)
    vbox.pack_start(hbox2, 0, 0)
    hbox3 = gtk.HBox()
    hbox3.pack_start(gtk.Label('Mode:'), 0, 0)
    combo = gtk.combo_box_new_text()
    combo.append_text('Attach (no sorting)')
    combo.append_text('Merge(sort, repeted words)')
    combo.append_text('Deep Merge(merge similars)')
    hbox3.pack_start(combo, 0, 0)
    self.combobox_mode = combo
    vbox.pack_start(hbox3, 0, 0)
    hbox.pack_start(vbox, 0, 0)
    exp.add(hbox)
    vbox_conv.pack_start(exp, 0, 0)
    #############################
    hbox = gtk.HBox()
    label2 = gtk.Label('<b>Write to format:</b>')
    label2.set_use_markup(True)
    hbox.pack_start(label2, 0, 0)
    #####
    group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
    group.add_widget(label1)
    group.add_widget(label2)
    #####
    self.combobox_o = gtk.combo_box_new_text()
    hbox.pack_start(self.combobox_o, 0, 0)
    #####
    hbox_ind = gtk.HBox()
    hbox_ind.pack_start(gtk.Label('Dictionary index:'), 0, 0)
    spin = gtk.SpinButton()
    spin.set_increments(1, 5)
    spin.set_range(0, 999)
    spin.set_width_chars(3)
    hbox_ind.pack_start(spin, 0, 0)
    hbox.pack_start(hbox_ind, 1, 0)
    self.hbox_index_o = hbox_ind
    #####
    self.checkb_o_ext = gtk.CheckButton('Use external module')
    hbox.pack_start(self.checkb_o_ext, 1, 0)
    #####
    hbox_enc = gtk.HBox()
    hbox_enc.pack_start(gtk.Label('Encoding'), 0, 0)
    self.comboentry_enc = gtk.combo_box_entry_new_text()
    hbox_enc.pack_start(self.comboentry_enc, 0, 0)
    hbox.pack_start(hbox_enc, 1, 0)
    #####
    vbox_conv.pack_start(hbox, 0, 0)
    ###########################
    hbox = gtk.HBox()
    hbox.pack_start(gtk.Label('File Path:'), 0, 0)
    self.entry_o = gtk.Entry()
    hbox.pack_start(self.entry_o, 1, 1)
    browse = gtk.Button('Browse')
    browse.set_image(gtk.image_new_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON))
    browse.connect('clicked', self.browse_o)
    hbox.pack_start(browse, 0, 0)
    conv = gtk.Button('Convert')
    conv.set_image(gtk.image_new_from_stock(gtk.STOCK_OK, gtk.ICON_SIZE_BUTTON))
    conv.connect('clicked', self.convert_clicked)
    try:
      conv.set_tooltip_text('Convert loaded glossary from specific format, and write to specific file')
    except:
      pass
    hbox.pack_start(conv, 0, 0)
    vbox_conv.pack_start(hbox, 0, 0)
    ###############################
    ########## tab Reverse ###############################################
    swin_rev = gtk.ScrolledWindow()
    vbox_rev = gtk.VBox()
    swin_rev.add_with_viewport(vbox_rev)
    swin_rev.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    lab = gtk.Label('_Reverse')
    lab.set_use_underline(True)
    notebook.append_page(swin_rev, lab)
    ########################    
    hbox = gtk.HBox()
    label1 = gtk.Label('<b>Read from format:</b>')
    label1.set_use_markup(True)
    hbox.pack_start(label1, 0, 0)
    self.combobox_r_i = gtk.combo_box_new_text()
    hbox.pack_start(self.combobox_r_i, 0, 0)
    #####
    hbox_ind = gtk.HBox()
    hbox_ind.pack_start(gtk.Label('Dictionary index:'), 0, 0)
    spin = gtk.SpinButton()
    spin.set_increments(1, 5)
    spin.set_range(0, 999)
    spin.set_width_chars(3)
    hbox_ind.pack_start(spin, 0, 0)
    hbox.pack_start(hbox_ind, 1, 0)
    self.hbox_index = hbox_ind
    #####
    self.checkb_r_i_ext = gtk.CheckButton('Use external module')##?????????
    hbox.pack_start(self.checkb_r_i_ext, 1, 0)
    vbox_rev.pack_start(hbox, 0, 0)
    ##############
    hbox = gtk.HBox()
    hbox.pack_start(gtk.Label('File Path:'), 0, 0)
    self.entry_r_i = gtk.Entry()
    hbox.pack_start(self.entry_r_i, 1, 1)
    browse = gtk.Button('Browse')
    browse.set_image(gtk.image_new_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON))
    browse.connect('clicked', self.browse_r_i)
    hbox.pack_start(browse, 0, 0)
    load = gtk.Button('Load')
    load.set_image(gtk.image_new_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_BUTTON))
    load.connect('clicked', self.r_load)
    try:
      load.set_tooltip_text('Load input glossary into RAM.\nYou can click on "Apply" instead of clicking "Load" and then "Start"')##????????????????
    except:
      pass
    hbox.pack_start(load, 0, 0)
    vbox_rev.pack_start(hbox, 0, 0)
    #########################
    hbox = gtk.HBox()
    hbox.pack_start(gtk.Label('Output Tabfile:'), 0, 0)
    self.entry_r_o = gtk.Entry()
    hbox.pack_start(self.entry_r_o, 1, 1)
    browse = gtk.Button('Browse')
    browse.set_image(gtk.image_new_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON))
    browse.connect('clicked', self.browse_r_o)
    hbox.pack_start(browse, 0, 0)
    ########
    button = gtk.Button('Start')
    image = gtk.image_new_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON)
    button.set_image(image)
    try:
      button.set_tooltip_text('Start Reversing')
    except:
      pass
    hbox.pack_start(button, 0, 0)
    vbox_rev.pack_start(hbox, 0, 0)
    self.r_dy_button = button
    self.r_dy_image = image
    ##########################
    exp = gtk.Expander('<b>Options</b>')
    exp.set_use_markup(True)
    vbox = gtk.VBox()
    self.vbox_options = vbox
    ########
    hbox = gtk.HBox()
    hbox.pack_start(gtk.Label(' Minimum relation: %'), 0, 0)
    spin = gtk.SpinButton()
    spin.set_increments(1, 10)
    spin.set_range(0, 100)
    #spin.set_width_chars(3)
    self.spinbutton_minrel = spin
    hbox.pack_start(gtk.Label(''), 1, 1)
    hbox.pack_start(spin, 0, 0)
    hbox.pack_start(gtk.Label(''), 1, 1)
    self.checkb_mw = gtk.CheckButton('Match word')
    hbox.pack_start(self.checkb_mw, 0, 0)
    hbox.pack_start(gtk.Label(''), 1, 1)
    hbox.pack_start(gtk.Label('Maximum results:'), 0, 0)
    spin = gtk.SpinButton()
    spin.set_increments(1, 10)
    spin.set_range(-1, 1000000)
    #spin.set_width_chars(3)
    self.spinbutton_maxnum = spin
    vbox.pack_start(hbox, 0, 0)
    ########
    hbox = gtk.HBox()
    hbox.pack_start(gtk.Label(' Auto save step: '), 0, 0)
    spin = gtk.SpinButton()
    spin.set_increments(1, 10)
    spin.set_range(0, 100)
    #spin.set_width_chars(3)
    self.spinbutton_autosave = spin
    hbox.pack_start(spin, 0, 0)
    hbox.pack_start(gtk.Label('words'), 0, 0)
    hbox.pack_start(gtk.Label(''), 1, 1)
    self.checkb_defs = gtk.CheckButton('Include Definitions')
    hbox.pack_start(self.checkb_defs, 0, 0)
    hbox.pack_start(gtk.Label(''), 1, 1)
    hbox.pack_start(gtk.Label('Show relation:'), 0, 0)
    self.combobox_sr = gtk.combo_box_new_text()
    hbox.pack_start(self.combobox_sr)
    ########## tab Text Editor ###############################################
    #swin_edit = gtk.ScrolledWindow()
    vbox_edit = gtk.VBox()
    #swin_edit.add(vbox_edit)
    #swin_edit.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    lab = gtk.Label('_Text Editor')
    lab.set_use_underline(True)
    notebook.append_page(vbox_edit, lab)
    ##############
    hbox = gtk.HBox()
    hbox.pack_start(gtk.Label('This is a UTF-8 smiple editor'), 0, 0)
    hbox.pack_start(gtk.Label(''), 1, 1)
    ####
    button = gtk.Button(gtk.STOCK_OPEN)
    button.connect('clicked', self.editor_open)
    hbox.pack_start(button, 0, 0)
    ####
    button = gtk.Button(gtk.STOCK_SAVE)
    button.connect('clicked', self.editor_save)
    hbox.pack_start(button, 0, 0)
    ####
    button = gtk.Button(gtk.STOCK_SAVE_AS)
    button.connect('clicked', self.editor_save_as)
    hbox.pack_start(button, 0, 0)
    ####
    vbox_edit.pack_start(hbox, 0, 0)
    ################
    swin = gtk.ScrolledWindow()
    self.textview_edit = gtk.TextView()
    swin.add(self.textview_edit)
    vbox_edit.pack_start(swin, 1, 1)
    ########## tab DB Editor ###############################################
    #swin_edit = gtk.ScrolledWindow()
    vbox_dbe = gtk.VBox()
    #swin_dbe.add(vbox_dbe)
    #swin_dbe.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    lab = gtk.Label('_DB Editor')
    lab.set_use_underline(True)
    notebook.append_page(vbox_dbe, lab)
    ##############
    hbox = gtk.HBox()
    hbox.pack_start(gtk.Label('Word'), 0, 0)
    self.entry_dbe = gtk.Entry()
    hbox.pack_start(self.entry_dbe, 1, 1)
    ##self.checkb_dbe_ro = gtk.CheckButton('read only')##?????????????????
    ##hbox.pack_start(self.checkb_dbe_ro, 0, 0)
    hbox.pack_start(gtk.VSeparator(), 0, 0)
    ###
    button = gtk.Button()
    button.set_image(gtk.image_new_from_stock(gtk.STOCK_GOTO_FIRST, gtk.ICON_SIZE_SMALL_TOOLBAR))
    button.connect('clicked', self.dbe_first)
    hbox.pack_start(button, 0, 0)
    try:
      button.set_tooltip_text('goto first word')
    except AttributeError:
      pass
    ###
    button = gtk.Button()
    button.set_image(gtk.image_new_from_stock(gtk.STOCK_GO_BACK, gtk.ICON_SIZE_SMALL_TOOLBAR))
    button.connect('clicked', self.dbe_prev)
    hbox.pack_start(button, 0, 0)
    try:
      button.set_tooltip_text('goto previous word')
    except AttributeError:
      pass
    ###
    button = gtk.Button()
    button.set_image(gtk.image_new_from_stock(gtk.STOCK_GO_FORWARD, gtk.ICON_SIZE_SMALL_TOOLBAR))
    button.connect('clicked', self.dbe_next)
    hbox.pack_start(button, 0, 0)
    try:
      button.set_tooltip_text('goto next word')
    except AttributeError:
      pass
    ###
    button = gtk.Button()
    button.set_image(gtk.image_new_from_stock(gtk.STOCK_GOTO_LAST, gtk.ICON_SIZE_SMALL_TOOLBAR))
    button.connect('clicked', self.dbe_last)
    hbox.pack_start(button, 0, 0)
    try:
      button.set_tooltip_text('goto last word')
    except AttributeError:
      pass
    ###
    entry = gtk.Entry()
    entry.connect('activate', self.dbe_goto_clicked)
    entry.set_width_chars(6)
    vbox_dbe.pack_start(entry, 0, 0)
    self.entry_db_index = entry
    ###
    button = gtk.Button('Go')
    button.connect('clicked', self.dbe_goto_clicked)
    try:
      button.set_tooltip_text('goto index ...')
    except AttributeError:
      pass
    ###
    hbox.pack_start(gtk.VSeparator(), 0, 0)
    ###
    button = gtk.Button()
    button.set_image(gtk.image_new_from_stock(gtk.STOCK_NEW, gtk.ICON_SIZE_SMALL_TOOLBAR))
    button.connect('clicked', self.dbe_new_w)
    hbox.pack_start(button, 0, 0)
    try:
      button.set_tooltip_text('new word (after selected word)')
    except AttributeError:
      pass
    ###
    button = gtk.Button()
    button.set_image(gtk.image_new_from_stock(gtk.STOCK_DELETE, gtk.ICON_SIZE_SMALL_TOOLBAR))
    button.connect('clicked', self.dbe_del_w)
    hbox.pack_start(button, 0, 0)
    try:
      button.set_tooltip_text('new word (at the end if words)')
    except AttributeError:
      pass
    ###
    button = gtk.Button()
    button.set_image(gtk.image_new_from_stock(gtk.STOCK_SORT_ASCENDING, gtk.ICON_SIZE_SMALL_TOOLBAR))
    button.connect('clicked', self.dbe_sort)
    hbox.pack_start(button, 0, 0)
    try:
      button.set_tooltip_text('delete word')
    except AttributeError:
      pass
    ###
    #hbox.pack_start(gtk.VSeparator(), 0, 0)
    #button = gtk.Button()
    #button.set_image(gtk.image_new_from_stock(gtk.STOCK_APPLY, gtk.ICON_SIZE_SMALL_TOOLBAR))
    #button.connect('clicked', self....)
    #hbox.pack_start(button, 0, 0)
    #try:
    #  button.set_tooltip_text('update current entry')
    #except AttributeError:
    #  pass
    ###
    vbox_dbe.pack_start(hbox, 0, 0)
    #################
    hpan = gtk.HPaned()
    ###
    swin = gtk.ScrolledWindow()
    swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    self.treeview = gtk.TreeView()
    swin.add(self.treeview)
    hpan.add1(swin)
    ###
    swin = gtk.ScrolledWindow()
    swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    self.textview_dbe = gtk.TextView()
    swin.add(self.textview_dbe)
    hpan.add1(swin)
    ###
    hpan.set_position(100)
    vbox_dbe.pack_start(hpan, 0, 0)
    ########## tab Preferences ###############################################
    swin_pref = gtk.ScrolledWindow()
    vbox_pref = gtk.VBox()
    swin_pref.add_with_viewport(vbox_pref)
    swin_pref.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    lab = gtk.Label('_Preferences')
    lab.set_use_underline(True)
    notebook.append_page(swin_pref, lab)
    ##################
    exp = gtk.Expander('<b>General</b>')
    exp.set_use_markup(True)
    vbox = gtk.VBox()
    ####
    hbox = gtk.HBox()
    hbox.pack_start(gtk.Label('Save preferences on exit'), 0, 0)
    combo = gtk.combo_box_new_text()
    combo.append_text('In home directory')
    combo.append_text('In PyGlossary root directory')
    combo.append_text('None')
    hbox.pack_start(combo, 0, 0)
    self.combobox_save = combo
    self.cb_auto_update = gtk.CheckButton('Auto update preferences')
    hbox.pack_start(gtk.Label(''), 1, 1)
    hbox.pack_start(self.cb_auto_update, 0, 0)
    ####
    hbox = gtk.HBox()
    self.cb_psyco = gtk.CheckButton('Use psyco to speed up execution')
    hbox.pack_start(self.cb_psyco, 0, 0)
    hbox.pack_start(gtk.Label(''), 1, 1)
    ## gtk.Label('Newline character')
    ## Unix/Linux		Dos/Windows		Old Mac
    ####
    exp.add(vbox)
    vbox_pref.pack_start(exp, 0, 0)
    ##################
    exp = gtk.Expander('<b>Convert</b>')
    exp.set_use_markup(True)
    table = gtk.Table(3, 2)
    #vbox = gtk.VBox()
    #sgroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
    ####
    #hbox = gtk.HBox()
    self.checkb_autofor = gtk.CheckButton('Auto set formats')
    table.attach(self.checkb_autofor, 0, 1, 0, 1)
    ###
    self.checkb_autoout = gtk.CheckButton('Auto set output file path')
    table.attach(self.checkb_autoout, 1, 2, 1, 2)
    ###
    self.cb_c_sort = gtk.CheckButton('Auto set formats')
    table.attach(self.cb_c_sort, 0, 1, 2, 3)
    ###
    self.checkb_lower = gtk.CheckButton('Lowercase words after loading')
    table.attach(self.checkb_lower, 1, 2, 0, 1)
    ###
    self.cb_rm_tags = gtk.CheckButton('Remove tags after loading')
    table.attach(self.cb_rm_tags, 0, 1, 1, 2)
    ###
    self.checkb_utf8 = gtk.CheckButton('Check UTF-8 after loading')
    table.attach(self.checkb_utf8, 1, 2, 2, 3)
    ###
    exp.add(table)
    vbox_pref.pack_start(exp, 0, 0)
    ##################
    exp = gtk.Expander('<b>Text Wrapping</b>')
    exp.set_use_markup(True)
    table = gtk.Table(2, 2)
    ###
    self.cb_wrap_out = gtk.CheckButton('Output console')
    table.attach(self.cb_wrap_out, 0, 1, 0, 1)
    ###
    self.cb_wrap_err = gtk.CheckButton('Error console')
    table.attach(self.cb_wrap_err, 0, 1, 0, 1)
    ###
    self.cb_wrap_edit = gtk.CheckButton('Text editor')
    table.attach(self.cb_wrap_edit, 0, 1, 0, 1)
    ###
    self.cb_wrap_dbe = gtk.CheckButton('DB editor (description)')
    table.attach(self.cb_wrap_dbe, 0, 1, 0, 1)
    ###
    exp.add(table)
    vbox_pref.pack_start(exp, 0, 0)
    ##################
    exp = gtk.Expander('<b>Text Background Colors</b>')
    exp.set_use_markup(True)
    ####
    table = gtk.Table()
    table.attach(gtk.Label('Output console'), 0, 1, 0, 1)
    self.colorpicker_bg_out = gtk.ColorButton()
    table.attach(self.colorpicker_bg_out, 1, 2, 0, 1)
    table.attach(gtk.Label('Text editor'), 0, 1, 1, 2)
    self.colorpicker_bg_edit = gtk.ColorButton()
    table.attach(self.colorpicker_bg_edit, 1, 2, 1, 2)
    hbox.pack_start(table, 1, 1)
    ####
    table = gtk.Table()
    table.attach(gtk.Label('Error console'), 0, 1, 0, 1)
    self.colorpicker_bg_err = gtk.ColorButton()
    table.attach(self.colorpicker_bg_err, 1, 2, 0, 1)
    table.attach(gtk.Label('DB editor (description)'), 0, 1, 1, 2)
    self.colorpicker_bg_dbe = gtk.ColorButton()
    table.attach(self.colorpicker_bg_dbe, 1, 2, 1, 2)
    hbox.pack_start(table, 1, 1)
    ####
    exp.add(hbox)
    vbox_pref.pack_start(exp, 0, 0)
    ##################
    exp = gtk.Expander('<b>Text Font Colors</b>')
    exp.set_use_markup(True)
    hbox = gtk.HBox()
    ####
    table = gtk.Table()
    table.attach(gtk.Label('Output console'), 0, 1, 0, 1)
    self.colorpicker_font_out = gtk.ColorButton()
    table.attach(self.colorpicker_font_out, 1, 2, 0, 1)
    table.attach(gtk.Label('Text editor'), 0, 1, 1, 2)
    self.colorpicker_font_edit = gtk.ColorButton()
    table.attach(self.colorpicker_font_edit, 1, 2, 1, 2)
    hbox.pack_start(table, 1, 1)
    ####
    table = gtk.Table()
    table.attach(gtk.Label('Error console'), 0, 1, 0, 1)
    self.colorpicker_font_err = gtk.ColorButton()
    table.attach(self.colorpicker_font_err, 1, 2, 0, 1)
    table.attach(gtk.Label('DB editor (description)'), 0, 1, 1, 2)
    self.colorpicker_font_dbe = gtk.ColorButton()
    table.attach(self.colorpicker_font_dbe, 1, 2, 1, 2)
    hbox.pack_start(table, 1, 1)
    ####
    exp.add(hbox)
    vbox_pref.pack_start(exp, 0, 0)
    #################################################
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    self.about_init()
    signals={}##{'browse1':self.browse1}
    for attr in dir(self):
      signals[attr] = getattr(self, attr)
    """self.def_widgets(['quitdialog', 'textview_out','textview_err','maindialog',\
      'vpaned1','notebook1','entry_i','entry_o',\
      'combobox_i','combobox_o','checkb_o_det','combobox_r_i','checkb_i_ext',\
      'entry_r_i','entry_r_o','combobox_sr','progressbar','textview_edit',\
      'label_convert','label_reverse','combobox_mode','textview_merge','button_conv'])
    """
    """## changing colors
    self.textview_err.modify_base(0, gtk.gdk.Color(10000, 0, 0))#textview bg color
    #self.textview_err.modify_base(1, gtk.gdk.Color(-1, 0, 0))#selected text bg color, when deselect window!
    self.textview_err.modify_text(0, gtk.gdk.Color(-1, -1, -1))#normal text color
    #self.textview_err.modify_text(1, gtk.gdk.Color(-1, -1, -1))#selected test color, when deselect window!
    # modify_bg modify_fg 
    self.textview_out.modify_base(0, gtk.gdk.Color(0, 10000, 0))#textview bg color
    self.textview_out.modify_text(0, gtk.gdk.Color(-1, -1, -1))#normal text color
    """
    #self.quitdialog.connect('delete-event', self.quitdialog_close)
    self.running = False
    self.glos=Glossary()
    self.glos.ui = self
    for f in Glossary.readFormats:
      self.combobox_i.append_text(Glossary.formatsDesc[f])
      self.combobox_r_i.append_text(Glossary.formatsDesc[f])
    for f in Glossary.writeFormats:
      self.combobox_o.append_text(Glossary.formatsDesc[f])
    self.combobox_sr.set_active(0)
    #self.checkb_i_ext.set_active(0)
    #self.checkb_o_ext.set_active(1)
    self.dbe_init()
    self.editor_path=''
    self.tabIndex=0
    self.fcd_dir = ''
    ###################################
    t_table = gtk.TextTagTable()
    tag = gtk.TextTag("filelist")
    t_table.add(tag)
    self.merge_buffer = gtk.TextBuffer(t_table)
    self.textview_merge.set_buffer(self.merge_buffer)
    self.merge_buffer.connect('changed', self.textview_merge_changed)
    self.combobox_mode.set_active(2)
    ####################################
    self.reverseStop = False
    self.pref_init()
    #thread.start_new_thread(UI.progressListen,(self,))
    #################### Comment folowing two line to see the output in the terminal
    self.redirectStdOut()
    self.redirectStdErr()
    if editPath:
      self.notebook1.set_current_page(3)
      print('Opening file "%s" for edit. please wait...'%editPath)
      while gtk.events_pending():
        gtk.main_iteration_do(False)
      self.dbe_open(editPath)
  def textview_merge_changed(self, *args):
    (stderr,sys.stderr) = (sys.stderr,stderr_saved)
    b = self.merge_buffer
    lines = b.get_text(b.get_start_iter(),b.get_end_iter()).split('\n')
    for i in range(len(lines)):
      if len(lines[i])>7:
        if lines[i][:7]=='file://':
          lines[i]=urlToPath(lines[i])
    #if lines[-1]=='':
    #  lines.pop(-1)
    b.set_text('\n'.join(lines))
    sys.stderr = stderr
  def show_msg(self,key,icon="error",buttons="close"):
        ## From program pySQLiteGUI writen by 'Milad Rastian'
        ## Show message dialog
        msgicon=0
        msgbuttons=0
        if icon=="error":
            msgicon=gtk.MESSAGE_ERROR
        elif icon=="info":
            msgicon=gtk.MESSAGE_INFO
        elif icon=="question":
            msgicon=gtk.MESSAGE_QUESTION
        elif icon=="warning":
            msgicon=gtk.MESSAGE_WARNING
        if buttons=="close":
            msgbuttons=gtk.BUTTONS_CLOSE
        elif buttons=="yesno":
            msgbuttons=gtk.BUTTONS_YES_NO
        msgWindow=gtk.MessageDialog(None,0,msgicon,msgbuttons,ERRORS[key][0] )
        msgWindow.format_secondary_text(ERRORS[key][1])
        response=msgWindow.run()
        msgWindow.destroy()
        return response
################ Redirecting standart output and standard error #################
##############    Using program Py_Shell.py writen by Pier Carteri     ##########
  def redirectStdOut(self):							#
    t_table_out = gtk.TextTagTable()						#
    tag_out = gtk.TextTag('output')						#
    t_table_out.add(tag_out)							#
    self.buffer_out = gtk.TextBuffer(t_table_out)				#
    self.textview_out.set_buffer(self.buffer_out)				#
    self.dummy_out = BufferFile(self.buffer_out, tag_out, 'stdout')		#
    sys.stdout = self.dummy_out							#
    print('Output console:')							#
  def redirectStdErr(self):							#
    t_table_err = gtk.TextTagTable()						#
    tag_err = gtk.TextTag('error')						#
    t_table_err.add(tag_err)							#
    self.buffer_err = gtk.TextBuffer(t_table_err)				#
    self.textview_err.set_buffer(self.buffer_err)				#
    self.dummy_err = BufferFile(self.buffer_err, tag_err, 'stderr')		#
    sys.stderr = self.dummy_err							#
    printAsError('Error console:')						#
  def redirectStdOutErrToOne(self):						#
    t_table_rev = gtk.TextTagTable()						#
    tag_out = gtk.TextTag('output')						#
    t_table_rev.add(tag_out)							#
    tag_err = gtk.TextTag('error')						#
    t_table_rev.add(tag_err)							#
    self.buffer_rev = gtk.TextBuffer(t_table_rev)				#
    self.textview_rev.set_buffer(self.buffer_rev)				#
    self.dummy_rev_out = BufferFile(self.buffer_rev,tag_out)			#
    sys.stdout = self.dummy_rev_out						#
    self.dummy_rev_err = BufferFile(self.buffer_rev,tag_err)			#
    sys.stderr = self.dummy_rev_err						#
  def restoreStdOutErr(self):							#
    (sys.stdout,sys.stderr) = (stdout_saved,stderr_saved)			#
#################################################################################
  #def maindialog_resized(self, *args):
  #  self.vpaned1.set_position(185)
  #  print(args)
  #run=lambda self:gtk.main()
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
      print('Preferences updated')
  def close_button_clicked(self, *args):
    if self.running:
      #d = gtk.MessageDialog(self, type=gtk.MESSAGE_WARNING, 
      d = gtk.Dialog()
      hb = gtk.HBox()
      hb.pack_start(gtk.image_new_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG), 0, 0)
      hb.pack_start(gtk.Label('Are you sure to quit?'), 0, 0)
      d.vbox.pack_start(hb, 0, 0)
      ###
      button = d.add_button('No, Continue', 0)
      button.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_BUTTON))
      button = d.add_button('Yes, Quit', 1)
      button.set_image(gtk.image_new_from_stock(gtk.STOCK_QUIT, gtk.ICON_SIZE_BUTTON))
      ###
      ex = d.run()
      if ex==1:
        self.quit()
      else:
        d.destroy()
      return True
    else:
      self.quit()
  #quit=lambda self, *args: sys.exit(0)
  def quit(self, *args):
    self.pref_update_var()
    self.pref_save()
    sys.exit(0)
  #def help_clicked(self, *args):
  #  HelpDialog().run()
  def browse_i(self, *args):
    fcd = gtk.FileChooserDialog('Browse Input File...', self, gtk.FILE_CHOOSER_ACTION_OPEN,
      ((gtk.STOCK_OK, 0), (gtk.STOCK_CANCEL)))
    if fcd.run()!=0:
      return
    path = fcd.get_filename()
    self.entry_i.set_text(path)
    self.fcd_dir = os.path.dirname(path)
    fcd.destroy() #???????????
  def browse_o(self, *args):
    fcd = gtk.FileChooserDialog('Browse Output File...', self, gtk.FILE_CHOOSER_ACTION_SAVE,
      ((gtk.STOCK_OK, 0), (gtk.STOCK_CANCEL)))
    if fcd.run()!=0:
      return
    path = fcd.get_filename()
    self.entry_o.set_text(path)
    self.fcd_dir = os.path.dirname(path)
    fcd.destroy() #???????????
  def load(self, *args):
    iPath = self.entry_i.get_text()
    if iPath=='':
      printAsError('Input file path is empty!');return
    formatD = self.combobox_i.get_active_text()
    if formatD==None:
      #printAsError('Input format is empty!');return
      format=''
      print('Please wait...')
    else:
      format = Glossary.descFormat[formatD]
      print('Reading from %s, please wait...'%formatD)
    while gtk.events_pending():
      gtk.main_iteration_do(False)
    t0=time.time()
    if format=='Omnidic':
      dicIndex=self.spinbutton_omnidic_i.get_value_as_int()
      ex = self.glos.readOmnidic(iPath, dicIndex=dicIndex)
    elif format=='Stardict' and self.checkb_i_ext.get_active():
      ex = self.glos.readStardict_ext(iPath)
    else:
      ex = self.glos.read(iPath, format=format)
    if ex:
      print('reading %s file: "%s"  done.\n%d words found.'%(format,iPath,len(self.glos.data)))
    else:
      print('reading %s file: "%s"  failed.'%(format,iPath))
      return False
    #self.iFormat = format
    self.iPath = iPath
    self.button_conv.set_sensitive(True)
    if self.pref['sort']:
      self.glos.data.sort()
    if self.pref['lower']:
      self.glos.lowercase()
    if self.pref['remove_tags']:
      self.glos.removeTags(self.pref['tags'])
    if self.pref['utf8_check']:
      self.glos.utf8ReplaceErrors()
    if self.checkb_o_det.get_active():
      print('time left = %3f  seconds'%(time.time()-t0))
      for x in self.glos.info:
        print('%s="%s"'%(x[0],x[1]))
    #self.glos.faEdit()
    return True
  def load_m(self, *args):
    b = self.merge_buffer
    text = b.get_text(b.get_start_iter(),b.get_end_iter())
    if text=='':
      return
    paths = text.split('\n')
    n = len(paths)
    if n==0:
      return
    mode=self.combobox_mode.get_active()
    for i in range(n):
      path = paths[i]
      if path=='':
        continue
      g = Glossary()
      self.ptext = ' of file %s from %s files'%(i+1,n)
      g.ui = self
      print('Loading "%s" ...'%path)
      g.read(path)
      if self.pref['sort']:
        g.data.sort()
      if self.pref['lower']:
        g.lowercase()
      if self.pref['remove_tags']:
        g.removeTags(self.pref['tags'])
      if self.pref['utf8_check']:
        g.utf8ReplaceErrors()
      print('  %s words found'%len(g.data))
      if mode==0:
        self.glos = self.glos.attach(g)
      elif mode==1:
        self.glos = self.glos.merge(g)
      elif mode==2:
        self.glos = self.glos.deepMerge(g)
      del g
      #try:
      #  self.progress(float(i+1)/n, '%s / %s files loaded'%(i+1,n))
      #except:
      #  pass
      if i==0:
        self.button_conv.set_sensitive(True)
      while gtk.events_pending():
        gtk.main_iteration_do(False)
    self.glos.ui = self
  def convert_clicked(self, *args):
    #if self.running:
    #  printAsError('Can not convert glossary, because another operation is running. '+\
    #    'Please open a new PyGlossary window, or wait until that operation be completed.')
    #  return False
    if len(self.glos.data)==0:
      printAsError('Input glossary has no word! Be sure to click "Load" before "Convert", '+\
        'or just click "Apply" instead.')
      return False
    oPath = self.entry_o.get_text()
    if oPath=='':
      printAsError('Output file path is empty!');return
    formatD = self.combobox_o.get_active_text()
    if formatD in (None,''):
      printAsError('Output format is empty!');return
    print('Converting to %s, please wait...'%formatD)
    while gtk.events_pending():
      gtk.main_iteration_do(False)
    self.running=True
    format = Glossary.descFormat[formatD]
    t0=time.time()
    if format=='Stardict':
        if self.checkb_o_ext.get_active():
          self.glos.writeStardict(oPath)
        else:
          self.glos.writeStardict_int(oPath)
    elif format=='Omnidic':
        dicIndex=self.spinbutton_omnidic_o.get_value_as_int()
        self.glos.writeOmnidic(oPath, dicIndex=dicIndex)
    elif format=='Babylon':
        encoding = self.comboentry_enc.get_active_text()
        self.glos.writeBabylon(oPath, encoding=encoding)
    else:
      self.glos.write(oPath, format=format)
    #self.oFormat = format
    self.oPath = oPath
    print('writing %s file: "%s" done.'%(format,oPath))
    if self.checkb_o_det.get_active():
      print('time left = %3f  seconds'%(time.time()-t0))
    self.running=False
    return True

  def combobox_i_changed(self, *args):
    formatD = self.combobox_i.get_active_text().lower()
    #"""
    if formatD[:8]=='stardict':
      self.checkb_i_ext.show()
    else:
      self.checkb_i_ext.hide()
    #"""
    if formatD[:7]=='omnidic':
      self.label_omnidic_i.show()
      self.spinbutton_omnidic_i.show()
    else:
      self.label_omnidic_i.hide()
      self.spinbutton_omnidic_i.hide()

  def combobox_o_changed(self, *args):
    formatD = self.combobox_o.get_active_text()
    format = Glossary.descFormat[formatD]
    if format=='Omnidic':
      self.label_omnidic_o.show()
      self.spinbutton_omnidic_o.show()
    else:
      self.label_omnidic_o.hide()
      self.spinbutton_omnidic_o.hide()
    if format=='Babylon':
      self.label_enc.show()
      self.comboentry_enc.show()
    else:
      self.label_enc.hide()
      self.comboentry_enc.hide()
    if format=='Stardict':
      self.checkb_o_ext.show()
    else:
      self.checkb_o_ext.hide()
    if self.pref['auto_set_out']:#format==None:
      pathI = self.entry_i.get_text()
      pathO = self.entry_o.get_text()
      formatOD = self.combobox_o.get_active_text()
      if formatOD != None and pathO=='' and '.' in pathI:
        extO = Glossary.descExt[formatOD]
        pathO = os.path.splitext(pathI)[0] + extO
        self.entry_o.set_text(pathO)
  def entry_i_changed(self, *args):
    path = self.entry_i.get_text()
    formatD = self.combobox_i.get_active_text()
    if len(path)>7:
      if path[:7]=='file://':
        path = urlToPath(path)
        self.entry_i.set_text(path)
    if self.pref['auto_set_for']:#format==None:
      path = self.entry_i.get_text()
      (name, ext) = os.path.splitext(path)
      if ext.lower() in ('.gz','.bz2','.zip'):
        ext = os.path.splitext(name)[1].lower()
      for i in range(len(Glossary.readExt)):
        if ext in Glossary.readExt[i]:
          self.combobox_i.set_active(i)
          break
    if self.pref['auto_set_out']:#format==None:
      #path = self.entry_i.get_text()
      formatOD = self.combobox_o.get_active_text()
      pathO    = self.entry_o.get_text()
      if formatOD != None and pathO=='' and '.' in path:
        extO = Glossary.descExt[formatOD]
        pathO = os.path.splitext(path)[0] + extO
        self.entry_o.set_text(pathO)
  def entry_o_changed(self,*args):
    path = self.entry_o.get_text()
    if path=='':
      return
    #format = self.combobox_o.get_active_text()
    if len(path)>7:
      if path[:7]=='file://':
        path = urlToPath(path)
        self.entry_o.set_text(path)
    if True:#format==None:   
      path = self.entry_o.get_text()
      (name, ext) = os.path.splitext(path)
      if ext.lower() in ('.gz','.bz2','.zip'):
        ext = os.path.splitext(name)[1].lower()
      for i in range(len(Glossary.writeExt)):
        if ext in Glossary.writeExt[i]:
          self.combobox_o.set_active(i)
          break
  #################################
  def browse_m(self, *args):
    fcd = gtk.FileChooserDialog('Browse Input File...', self, gtk.FILE_CHOOSER_ACTION_OPEN,
      ((gtk.STOCK_OK, 0), (gtk.STOCK_CANCEL)))
    fcd.set_select_multiple(True)
    if fcd.run()!=0:
      return
    filelist = fcd.get_filenames()
    text=self.merge_buffer.get_text(self.merge_buffer.get_start_iter(),self.merge_buffer.get_end_iter())
    if text!='':
      text += '\n'
    text += '\n'.join(filelist)
    self.merge_buffer.set_text(text)
    self.fcd_dir = fcd.get_current_folder()##????????????
    fcd.destroy() ##????????????????
  #################################
  clear_output=lambda self, *args: self.buffer_out.set_text('Output console:\n')
  clear_errors=lambda self, *args: self.buffer_err.set_text('Error console:\n')
  #######################################################
  ################################# Reverse tab:
  def browse_r_i(self, *args):
    fcd = gtk.FileChooserDialog('Browse Input File...', self, gtk.FILE_CHOOSER_ACTION_OPEN,
      ((gtk.STOCK_OK, 0), (gtk.STOCK_CANCEL)))
    if fcd.run()!=0:
      return
    path = fcd.get_filename()
    self.entry_r_i.set_text(path)
    self.fcd_dir = os.path.dirname(path)
    fcd.destroy() #???????????
  def browse_r_o(self, *args):
    fcd = gtk.FileChooserDialog('Browse Input File...', self, gtk.FILE_CHOOSER_ACTION_SAVE,
      ((gtk.STOCK_OK, 0), (gtk.STOCK_CANCEL)))
    if fcd.run()!=0:
      return
    path = fcd.get_filename()
    self.entry_r_o.set_text(path)
    self.fcd_dir = os.path.dirname(path)
    fcd.destroy() #???????????
  def entry_r_i_changed(self,*args):
    format=self.combobox_r_i.get_active_text()
    path = self.entry_r_i.get_text()
    if len(path)>7:
      if path[:7]=='file://':
        path=urlToPath(path)
        self.entry_r_i.set_text(path)
    if True:#format==None:
      path = self.entry_r_i.get_text()
      (name, ext) = os.path.splitext(path)
      if ext.lower() in ('.gz','.bz2','.zip'):
        (name, ext) = os.path.splitext(name)
        ext = ext.lower()
      for i in range(len(Glossary.readExt)):
        if ext in Glossary.readExt[i]:
          self.combobox_r_i.set_active(i)
          self.entry_r_o.set_text(name+'-reversed.txt')
          return      
  def r_load(self, *args):
    iPath = self.entry_r_i.get_text()
    formatD = self.combobox_r_i.get_active_text()
    if iPath=='':
      printAsError('Input file path is empty!');return False
    if formatD in (None,''):
      printAsError('Input format is empty!');return
    print('Reading from %s, please wait...'%formatD)
    format = Glossary.descFormat[formatD]
    self.glosR = Glossary()
    while gtk.events_pending():
      gtk.main_iteration_do(False)
    t0=time.time()
    self.glosR.read(iPath, format=format)
    if self.checkb_o_det.get_active():
      print('time left = %3f  seconds'%(time.time()-t0))
      for x in self.glos.info:
        print('%s="%s"'%(x[0],x[1]))
    #self.glosR.faEdit()
    self.glosR.ui = self
    if self.pref['sort']:
      self.glos.data.sort()
    if self.pref['lower']:
      self.glos.lowercase()
    if self.pref['remove_tags']:
      self.glos.removeTags(self.pref['tags'])
    if self.pref['utf8_check']:
      self.glos.utf8ReplaceErrors()
    #self.riFormat = format
    #self.riPath = iPath
    print('reading %s file: "%s" done.\n%d words found.'%(formatD,iPath,len(self.glosR.data)))
    self.running=False ; return True
  def r_dynamic_button_clicked(self, *args):
    text = self.r_dy_button.get_text()
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
    #  printAsError('Input glossary has no word! Be sure to click "Load" before "Start", or just click "Apply" instead.')
    #  return
    oPath = self.entry_r_o.get_text()
    if oPath=='':
      printAsError('Output file path is empty!');return
    self.progress(0.0, 'Starting....')
    self.pref_rev_update_var()
    self.pref['savePath']=oPath
    while gtk.events_pending():
      gtk.main_iteration_do(False)
    self.rWords = self.glosR.takeOutputWords()
    self.running=True
    #revTh = thread.start_new_thread(self.glosR.reverseDic, (self.rWords, self.pref))
    self.r_dy_image.set_from_stock(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_BUTTON)
    self.r_dy_buttob.set_label('Stop')
    self.entry_r_i.set_editable(False)
    self.entry_r_o.set_editable(False)
    self.vbox_options.set_sensitive(False)
    print('Number of input words:', len(self.rWords))
    print('Reversing glossary...')
    self.glosR.reverseDic(self.rWords, self.pref)
    while True:
    #while not self.reverseStop:
      while gtk.events_pending():
        gtk.main_iteration_do(False)
  def r_stop(self, *args):
    self.reverseStop = True
    self.r_dy_image.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON)
    self.r_dy_buttob.set_label('Resume')
    self.vbox_options.set_sensitive(True)
  def r_resume(self, *args):
    if self.glosR.stoped==True:
      self.pref['autoSaveStep']=int(self.spinbutton_autosave.get_value())
      self.reverseStop = False
      #revTh = thread.start_new_thread(self.glosR.reverseDic, (self.rWords, self.pref))
      self.r_dy_image.set_from_stock(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_BUTTON)
      self.r_dy_buttob.set_label('Stop')
      self.vbox_options.set_sensitive(False)
      print('continue reversing from index %d ...'%self.glosR.continueFrom)
      self.glosR.reverseDic(self.rWords, self.pref)
      while True:
      #while not self.reverseStop:
        while gtk.events_pending():
          gtk.main_iteration_do(False)
    else:
      print('self.glosR.stoped=%s'%self.glosR.stoped)
      print('Not stoped yet. Wait many seconds and press "Resume" again...')
  def r_finished(self, *args):
    self.glosR.continueFrom=0
    self.running=False
    self.r_dy_image.set_from_stock(gtk.STOCK_MEDIA_PLAY, gtk.ICON_SIZE_BUTTON)
    self.r_dy_buttob.set_label('Start')
    self.entry_r_i.set_editable(True)
    self.entry_r_o.set_editable(True)
    self.vbox_options.set_sensitive(True)
    self.progressbar.set_text('Reversing completed')
    print("Reversing completed.")
    #thread.exit_thread() # ???????????????????????????
    ## A PROBLEM: CPU is busy even when reversing completed!

  #######################################################################################
  #######################################################################################

  def editor_open(self, *args):
    step=1000
    fcd = gtk.FileChooserDialog('Browse Input File...', self, gtk.FILE_CHOOSER_ACTION_OPEN,
      ((gtk.STOCK_OK, 0), (gtk.STOCK_CANCEL)))
    if fcd.run()!=0:
      return
    self.editor_path = fcd.get_filename()
    self.fcd_dir = os.path.dirname(self.editor_path)
    text = open(self.editor_path).read()
    t_table = gtk.TextTagTable()
    tag = gtk.TextTag("output")
    t_table.add(tag)
    self.editor_buffer = gtk.TextBuffer(t_table)
    self.textview_edit.set_buffer(self.editor_buffer)
    self.running = True
    size=len(text)
    if size < step:
      self.editor_buffer.set_text(text)
    else:
      self.editor_buffer.set_text(text[:step])
      while gtk.events_pending():
        gtk.main_iteration_do(False)
      i=step
      while i < size-step:
        self.editor_buffer.insert(self.editor_buffer.get_end_iter(), text[i:i+step])
        i += step
        while gtk.events_pending():
          gtk.main_iteration_do(False)
      self.editor_buffer.insert(self.editor_buffer.get_end_iter(), text[i:])
    fcd.destroy() #???????????
  def editor_save(self, *args):
    exit = self.editor_save_as(self.editor_path)
    if exit==True:
      print('File saved: "%s"'%self.editor_path)
      return True
    elif exit==False:
      print('File not saved: "%s"'%self.editor_path)
      return False
    else:
      return exit
  def editor_save_as(self, *args):
    if args[0]:
      self.editor_path = args[0]
    else:
      fcd = gtk.FileChooserDialog('Browse Input File...', self, gtk.FILE_CHOOSER_ACTION_SAVE,
        ((gtk.STOCK_OK, 0), (gtk.STOCK_CANCEL)))
      if fcd.run()!=0:
        return
      self.editor_path = fcd.get_filename()
      self.fcd_dir = os.path.dirname(self.editor_path)
    open(self.editor_path,'w').write(self.editor_buffer.get_text(self.editor_buffer.get_start_iter(),self.editor_buffer.get_end_iter()))
    self.running = False
    return True
  #######################################################################################
  #################################     DB Editor    ####################################
  def dbe_init(self, *args):
    d = gtk.Dialog('PyGlossary Info Editor', self)
    d.resize(500, 200)
    self.dbe_info_dialog = d
    hbox = gtk.HBox()
    hbox.pack_start(gtk.Label('Info Key:'), 0, 0)
    self.entry_dbe_info = gtk.Entry()
    hbox.pack_start(self.entry_dbe_info, 1, 1)
    self.entry_dbe_info.connect('activate', self.entry_dbe_info_activate)
    ##########
    """
    hbox.pack_start(gtk.VSeparator(), 0, 0)
    ###
    button = gtk.Button()
    button.set_image(gtk.image_new_from_stock(gtk.STOCK_GO_BACK, gtk.ICON_SIZE_SMALL_TOOLBAR))
    button.connect('clicked', self.dbe_first)
    hbox.pack_start(button, 0, 0)
    try:
      button.set_tooltip_text('move to previous key')
    except AttributeError:
      pass
    """
    d.vbox.pack_start(hbox, 0, 0)
    #########
    hbox = gtk.HBox()
    toolbar=gtk.Toolbar()
    toolbar.set_orientation(gtk.ORIENTATION_VERTICAL)
    #toolbar.set_icon_size(gtk.ICON_SIZE_SMALL_TOOLBAR)
    ###
    tb = gtk.ToolButton(gtk.image_new_from_stock(gtk.STOCK_GO_UP,gtk.ICON_SIZE_SMALL_TOOLBAR))
    tb.set_tooltip(gtk.Tooltips(), 'move back')
    tb.connect('clicked', self.dbe_info_move_back)
    toolbar.insert(tb, 0)
    ###
    tb = gtk.ToolButton(gtk.image_new_from_stock(gtk.STOCK_GO_DOWN,gtk.ICON_SIZE_SMALL_TOOLBAR))
    tb.set_tooltip(gtk.Tooltips(), 'move next')
    tb.connect('clicked', self.dbe_info_move_next)
    toolbar.insert(tb, -1)
    ###
    tb = gtk.ToolButton(gtk.image_new_from_stock(gtk.STOCK_NEW,gtk.ICON_SIZE_SMALL_TOOLBAR))
    tb.set_tooltip(gtk.Tooltips(), 'new item')
    tb.connect('clicked', self.dbe_info_new)
    toolbar.insert(tb, -1)
    ###
    tb = gtk.ToolButton(gtk.image_new_from_stock(gtk.STOCK_DELETE,gtk.ICON_SIZE_SMALL_TOOLBAR))
    tb.set_tooltip(gtk.Tooltips(), 'delete item')
    tb.connect('clicked', self.dbe_info_del)
    toolbar.insert(tb, -1)
    ###
    hbox.pack_start(toolbar, 0, 0)
    ###
    hpan = gtk.HPaned()
    swin = gtk.ScrolledWindow()
    swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    self.treeview_info = gtk.TreeView()
    self.treeview_info.connect('cursor-changed', self.treeview_info_changed)
    swin.add(self.treeview_info)
    hpan.add1(swin)
    ###
    swin = gtk.ScrolledWindow()
    swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    self.textview_dbe_info = gtk.TextView()
    swin.add(self.textview_dbe_info)
    hpan.add2(swin)
    ###
    hbox.pack_start(hpan, 1, 1)
    #########
    d.vbox.pack_start(hbox, 0, 0)
    button = d.add_button(gtk.STOCK_CLOSE, 0)
    button.connect('clicked', self.dbe_info_close)
    self.dbe_info_dialog = d
    #######################################
    table = gtk.TextTagTable()
    tag = gtk.TextTag('definition')
    table.add(tag)
    self.buffer_dbe = gtk.TextBuffer(table)
    self.textview_dbe.set_buffer(self.buffer_dbe)
    self.treestore = gtk.ListStore(str,str)
    self.treeview.set_model(self.treestore)
    self.cell = gtk.CellRendererText()
    self.cell2 = gtk.CellRendererText()
    col = gtk.TreeViewColumn('Word',self.cell,text=0)
    col2 = gtk.TreeViewColumn('Index',self.cell2,text=1)
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
    col = gtk.TreeViewColumn('Key',self.cell,text=0)
    col.set_resizable(True)
    self.treeview_info.append_column(col)
    self.ptext=''
    #ag = gtk.AccelGroup()
    #print(dir(gtk.keysyms))
    #ag.connect_by_path('gtk.keysym.Control_L', self.dbe_open)
    ########################
  def dbe_new(self, *args):
    self.glosE = Glossary()
    self.glosE.data.append(('##name', ''))
    self.treestore.clear()
    self.treestore.append(('##name', 0))
    self.db_ind = 0
    self.db_format = ''
    self.dbe_goto(0, save=False)
    self.dbe_save_as('')
  def dbe_open(self, arg=None):
    format = ''
    if arg:
      path = arg
      self.fcd_format = '' #??????????????????
    else:
      fcd = gtk.FileChooserDialog('Browse Input File...', self, gtk.FILE_CHOOSER_ACTION_OPEN,
       ((gtk.STOCK_OK, 0), (gtk.STOCK_CANCEL)))
      hbox = gtk.HBox()
      hbox.pack_start(gtk.Label(''), 1, 1)
      hbox.pack_start(gtk.Label('Format:'), 0, 0)
      combo = gtk.combo_box_new_text()
      combo.append_text('Auto (by extention)')
      for item in Glossary.readDesc:
        combo.append_text(item)
      combo.set_active(0)
      hbox.pack_start(combo, 0, 0)
      fcd.set_extra_widget(hbox)
      if fcd.run()!=0:
        return
      path = fcd.get_filename()
    self.dbe_path = path
    self.fcd_dir = os.path.dirname(path)
    self.glosE = Glossary()
    self.glosE.ui = self
    while gtk.events_pending():
      gtk.main_iteration_do(False)
    if self.fcd_format in ('Auto (by extention)',''):
      self.glosE.read(self.dbe_path)
    else:
      format = Glossary.descFormat[self.fcd_format]
      self.glosE.read(self.dbe_path, format=format)
    if self.pref['sort']:
      self.glosE.data.sort()
    if self.pref['lower']:
      self.glosE.lowercase()
    if self.pref['remove_tags']:
      self.glosE.removeTags(self.pref['tags'])
    if self.pref['utf8_check']:
      self.glosE.utf8ReplaceErrors()
    self.fcd_format=''
    self.db_ind=None
    (d,t) = (self.glosE.data,self.treestore)
    t.clear()
    for i in range(len(d)):
      x = d[i]
      t.append((x[0], i))
      #d[i]=(x[0], x[1], True) ## read only
    self.dbe_goto(0, save=False)
    self.running = True
    self.db_format = format
    for key in self.glosE.infoKeys():
      self.treestore_info.append((key,))
    self.info_i=0
    self.dbe_info_goto(0, save=False)
  def dbe_save(self, *args):
    shutil.copy(self.dbe_path, self.dbe_path+'~')
    if self.dbe_save_as(self.dbe_path):
      os.remove(self.dbe_path+'~')
    else:
      os.remove(self.dbe_path)
      os.rename(self.dbe_path+'~', self.dbe_path)
      printAsError('Saving file "%s" failed! Backup file restored instaed.'%self.dbe_path)
  def dbe_save_as(self, *args):
    #self.glosE.data[self.db_ind] = (self.entry_dbe.get_text(),self.buffer_dbe.get_text())
    self.dbe_update()
    format = self.db_format
    if args[0] and format in Glossary.writeFormats+['']:
      self.dbe_path = args[0]
      ex = self.glosE.write(self.dbe_path, format=format)
    else:
      fcd = gtk.FileChooserDialog('Browse Input File...', self, gtk.FILE_CHOOSER_ACTION_OPEN,
       ((gtk.STOCK_OK, 0), (gtk.STOCK_CANCEL)))
      hbox = gtk.HBox()
      hbox.pack_start(gtk.Label(''), 1, 1)
      hbox.pack_start(gtk.Label('Format:'), 0, 0)
      combo = gtk.combo_box_new_text()
      combo.append_text('Auto (by extention)')
      for item in Glossary.readDesc:
        combo.append_text(item)
      combo.set_active(0)
      hbox.pack_start(combo, 0, 0)
      fcd.set_extra_widget(hbox)
      if fcd.run()!=0:
        return
      path = fcd.get_filename()
      self.dbe_path = path
      self.fcd_dir = os.path.dirname(path)
      if self.fcd_format=='Auto (by extention)':
        ex = self.glosE.write(path)
      else:
        format = Glossary.descFormat[self.fcd_format]
        ex = self.glosE.write(path, format=format)
    if ex != False:
      print('DB file "%s" saved'%self.dbe_path)
      self.running = False
      self.db_format = format
      return True
  def dbe_ro_clicked(self, *args):
    ro = self.checkb_db_ro.get_active()
    self.entry_dbe.set_editable(not ro)
    self.textview_dbe.set_editable(not ro)
  dbe_prev  = lambda self, *args: self.dbe_goto(self.db_ind-1)
  dbe_next  = lambda self, *args: self.dbe_goto(self.db_ind+1)
  dbe_first = lambda self, *args: self.dbe_goto(0)
  dbe_last  = lambda self, *args: self.dbe_goto(-1)
  def dbe_goto_clicked(self, *args):
    ind = self.entry_db_index.get_text()
    try:
      n_ind=int(ind)
    except:
      printAsError('bad index: "%s"'%ind)
      return False
    self.dbe_goto(n_ind)
  def dbe_update(self):
    d = (self.entry_dbe.get_text(),self.buffer_dbe.get_text\
      (self.buffer_dbe.get_start_iter(),self.buffer_dbe.get_end_iter()))
    self.glosE.data[self.db_ind] = d
    self.treestore[self.db_ind][0] = d[0]
  def dbe_update_info(self):
    d = (self.entry_dbe_info.get_text(),self.buffer_dbe_info.get_text\
      (self.buffer_dbe_info.get_start_iter(),self.buffer_dbe_info.get_end_iter()))
    self.glosE.info[self.info_i] = d
    self.treestore_info[self.info_i][0] = d[0]
  def dbe_goto(self, n_ind, save=True):
    p_ind = self.db_ind
    if n_ind==p_ind and save:
      self.dbe_update()
      return
    if save:
      p_data = (self.entry_dbe.get_text(),self.buffer_dbe.get_text\
      (self.buffer_dbe.get_start_iter(),self.buffer_dbe.get_end_iter()))
    n = len(self.glosE.data)
    if 0 <= n_ind < n:
      pass 
    elif n_ind == n:
      n_ind = 0
    elif -n < n_ind < 0:
      n_ind += n
    else:
      printAsError('index out of range: "%s"'%n_ind)
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
    #print 'Setting text "%s"'%d[1]
    self.buffer_dbe.set_text(d[1])
    self.treeview.set_cursor(n_ind)
    if save:
      self.glosE.data[p_ind] = p_data
      self.treestore[p_ind][0] = p_data[0]
  def dbe_info_goto(self, n_ind, save=True):
    p_ind = self.info_i
    if save:
      p_info = (self.entry_dbe_info.get_text(),self.buffer_dbe_info.get_text\
      (self.buffer_dbe_info.get_start_iter(),self.buffer_dbe_info.get_end_iter()))
    n = len(self.glosE.info)
    """if 0 <= n_ind < n:
      pass 
    elif n_ind == n:
      n_ind = 0
    elif -n < n_ind < 0:
      n_ind += n
    else:
      printAsError('index out of range: "%s"'%n_ind)
      return False"""
    self.info_i = n_ind
    try:
      inf = self.glosE.info[n_ind]
    except:
      #myRaise(__file__)
      return
    self.entry_dbe_info.set_text(inf[0])
    self.buffer_dbe_info.set_text(inf[1])
    self.treeview_info.set_cursor(n_ind)
    if save:
      self.glosE.info[p_ind] = p_info
      self.treestore_info[p_ind][0] = p_info[0]
  def dbe_new_w(self, *args):## new Word after selected
    n = len(self.glosE.data)
    try:
      n = self.treeview.get_cursor()[0][0] + 1
    except:
      printAsError('can not get index of treeview curser!')
      myRaise(__file__)
      return False
    word = 'word%s'%n
    self.glosE.data.insert( n , (word,'') )
    self.treestore.insert( n  , (word,str(n)) )
    self.dbe_goto(n)
    self.entry_dbe.select_region(0, -1)
    self.entry_dbe.do_focus(self.entry_dbe, 0)
    ######???????????????????????
    while gtk.events_pending():
      gtk.main_iteration_do(False)
    for i in range(n+1, len(self.glosE.data)):
      #self.treestore[i]=[self.glosE.data[i][0], str(i)]
      self.treestore[i][1]=str(i)
  def dbe_new_we(self, *args):## new Word at the End 
    n = len(self.glosE.data)
    word = 'word%s'%n
    self.glosE.data.append((word, ''))
    self.treestore.append((word, str(n)))
    self.dbe_goto(n)
    self.entry_dbe.select_region(0, -1)
    self.entry_dbe.do_focus(self.entry_dbe, 0)
  def dbe_del_w(self, *args):
    n = len(self.glosE.data)
    ind = self.db_ind
    #if self.checkb_o_det.get_active():
    #  print('Deleting index %s word "%s"'%(ind,  self.glosE.data[ind][0]))
    self.glosE.data.pop(ind)
    #del self.glosE.data[ind]
    del self.treestore[ind]
    if ind==n-1:
      self.dbe_goto(n-2, False)
    else:
      self.treestore[ind][1] = ind
      self.dbe_goto(ind, False)
      for i in range(ind+1, min(ind+30,n-1)):
        try:
          self.treestore[i][1] = i
        except IndexError:
          break
      while gtk.events_pending():
        gtk.main_iteration_do(False)
      for i in range(ind+1, n-1):
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
      printAsError('can not get index of treeview curser!')
      myRaise(__file__)
      return False
    #self.dbe_update()
    self.dbe_goto(i)
  def treeview_info_changed(self, *args):
    try:
      i = self.treeview_info.get_cursor()[0][0]
    except:
      printAsError('can not get index of treeview_info curser!')
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
      myRaise(__file__)
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
    g.info.insert(i+1, (nkey,''))
    self.treestore_info.insert(i+1, (nkey,))
    for j in range(i+1, n+1):
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
    self.dbe_update()
    if len(self.glosE.data)!=len(self.treestore):
      print(len(self.glosE.data), len(self.treestore))
    self.glosE.data.sort()
    for i in range(len(self.glosE.data)):
      self.treestore[i]=[self.glosE.data[i][0], str(i)]
    self.dbe_goto(self.db_ind, False)
  def dbe_info_clicked(self, *args):
    self.dbe_info_dialog.show()
    #print(self.glosE.info)
  def dbe_info_close(self, *args):
    self.dbe_info_dialog.hide()
    return True
  def pref_init(self, *args):
    self.pref={}
    """self.def_widgets(['combobox_save','combobox_newline','cb_psyco','checkb_autofor','checkb_autoout',\
      'cb_auto_update','cb_c_sort','cb_rm_tags','checkb_lower','checkb_utf8','checkb_defs'])"""
    self.combobox_save.set_active(0)
    self.newlineItems=('\\n', '\\r\\n', '\\n\\r')
    self.showRelItems=['None', 'Percent At First', 'Percent']
    for item in self.showRelItems:
      self.combobox_sr.append_text(item)
    #for name in ('out','err','edit','dbe'):
    #  self.def_widgets(['cb_wrap_%s'%name,'colorpicker_bg_%s'%name,'colorpicker_font_%s'%name])
    self.pref['auto_update'] = self.cb_auto_update.get_active()
    if os.path.isfile(use_psyco_file):
      self.cb_psyco.set_active(True)
    else:
      self.cb_psyco.set_active(False)
    self.prefSavePath = [confPath,  '%s%src.py'%(srcDir,os.sep)]
    self.pref_load()
    self.pref_update_var()
    self.pref_rev_update_gui()
  def pref_load(self, *args):
    fp=open('%s%src.py'%(srcDir,os.sep))
    exec(fp.read())
    if save==0:
      try:
        fp=open(self.prefSavePath[0])
      except:
        myRaise(__file__)
      else:
        exec(fp.read())
    for key in self.prefKeys:
      self.pref[key] = eval(key)
    self.combobox_save.set_active(self.pref['save'])
    self.cb_auto_update.set_active(self.pref['auto_update']) 
    #for i in range(len(self.newlineItems)):
    #  exec('eq=(self.pref["newline"]=="%s")'%self.newlineItems[i])
    #  if eq:
    #    self.combobox_newline.set_active(i)
    #    break
    self.checkb_autofor.set_active(self.pref['auto_set_for'])
    self.checkb_autoout.set_active(self.pref['auto_set_out'])
    self.cb_c_sort.set_active(self.pref['sort'])
    self.checkb_lower.set_active(self.pref['lower'])
    self.cb_rm_tags.set_active(self.pref['remove_tags'])
    self.checkb_utf8.set_active(self.pref['utf8_check'])
    for name in ('out','err','edit','dbe'):
      exec('self.cb_wrap_%s.set_active(self.pref["wrap_%s"])'%(name,name))
    for name in ('out','err','edit','dbe'):
      exec('color=self.pref["color_bg_%s"]'%name)
      exec('self.colorpicker_bg_%s.set_color(gtk.gdk.Color%s)'%(name,color))
    for name in ('out','err','edit','dbe'):
      exec('color=self.pref["color_font_%s"]'%name)
      exec('self.colorpicker_font_%s.set_color(gtk.gdk.Color%s)'%(name,color))
    return True
  def pref_update_var(self, *args):
    self.pref['auto_update'] = self.cb_auto_update.get_active()
    #k = self.combobox_newline.get_active()
    #self.pref['newline'] = self.newlineItems[k]
    for name in ('out','err','edit','dbe'):
      exec('\
self.pref["wrap_%s"]=self.cb_wrap_%s.get_active()\n\
if self.pref["wrap_%s"]:\n\
  self.textview_%s.set_wrap_mode(gtk.WRAP_WORD)\n\
else:\n\
  self.textview_%s.set_wrap_mode(gtk.WRAP_NONE)'%((name,)*5))
      exec('col=self.colorpicker_bg_%s.get_property(\'color\')'%name)
      exec('self.textview_%s.modify_base(0, gtk.gdk.Color(%s, %s, %s))'%(name,col.red,col.green,col.blue))
      exec('self.pref["color_bg_%s"]=(col.red,col.green,col.blue)'%name)
      exec('col=self.colorpicker_font_%s.get_property(\'color\')'%name)
      exec('self.textview_%s.modify_text(0, gtk.gdk.Color(%s, %s, %s))'%(name,col.red,col.green,col.blue))
      exec('self.pref["color_font_%s"]=(col.red,col.green,col.blue)'%name)
    self.pref['auto_set_for']=self.checkb_autofor.get_active()
    self.pref['auto_set_out']=self.checkb_autoout.get_active()
    self.pref['sort']=self.cb_c_sort.get_active()
    self.pref['lower']=self.checkb_lower.get_active()
    self.pref['remove_tags']=self.cb_rm_tags.get_active()
    self.pref['utf8_check']=self.checkb_utf8.get_active()
  def pref_rev_update_var(self):
    self.pref['matchWord']=self.checkb_mw.get_active()
    self.pref['showRel']=self.combobox_sr.get_active_text()
    self.pref['autoSaveStep']=int(self.spinbutton_autosave.get_value())##get_value() returns a float
    self.pref['minRel']=self.spinbutton_minrel.get_value()/100.0
    self.pref['maxNum']=int(self.spinbutton_maxnum.get_value())
    self.pref['includeDefs']=self.checkb_defs.get_active()
  def pref_rev_update_gui(self):
    self.checkb_mw.set_active(self.pref['matchWord'])
    for i in range(len(self.showRelItems)):
      if self.showRelItems[i]==self.pref['showRel']:
        self.combobox_sr.set_active(i)
    self.spinbutton_autosave.set_value(self.pref['autoSaveStep'])
    self.spinbutton_minrel.set_value(self.pref['minRel']*100.0)
    self.spinbutton_maxnum.set_value(self.pref['maxNum'])
    self.checkb_defs.set_active(self.pref['includeDefs'])
    while gtk.events_pending():
      gtk.main_iteration_do(False)
  def pref_save(self, *args):
    self.pref_rev_update_var()
    self.pref['save']=self.combobox_save.get_active()
    if self.pref['save']==0:
      try:
        fp = open(self.prefSavePath[0], 'w')
      except:
        myRaise(__file__)
        return
    elif self.pref['save']==1:
      try:
        fp = open(self.prefSavePath[1], 'w')
      except IOError:
        myRaise(__file__)
        try:
          fp = open(self.prefSavePath[0], 'w')
        except:
          myRaise(__file__)
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
      fp.write('save=%s\n'%self.pref['save'])
    for key in self.prefKeys:
      fp.write("%s=%r\n"%(key, self.pref[key]))
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
    (stderr,sys.stderr) = (sys.stderr,stderr_saved)
    if text==None:
      text = '%%%d%s'%(rat*100,self.ptext)
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
    f=open(fifoPath)
    msg=f.readline()
    while msg!='end':
      if msg=='':
        pass
      else:
        if '\n' in msg:
          msg=msg.split('\n')[-1]
        if '\t' in msg:
          parts=msg.split('\t')
          self.progress(float(parts[0]), parts[1])
        else:
          try:
            rat=float(msg)
          except:
            self.progressbar.set_text(msg)
          else:
            self.progressbar.update(rat)
            self.progressbar.set_text('%%%s'%msg)
      while gtk.events_pending():
        gtk.main_iteration_do(True)
      #time.sleep(sleep)
      msg=f.readline()
  def run(self):
    self.vbox.show_all()
    gtk.Dialog.run(self)

"""
class FileChooserDialog:
  def __init__(self, main, path='', combo_items=[], action='open', multiple=False):
    self.main = main
    (stderr,sys.stderr) = (sys.stderr,stderr_saved)
    self.xml= gtk.glade.XML('%s%sglade%sfilechooserdialog.glade'%(srcDir,os.sep,os.sep))
    sys.stderr = stderr
    self.fd = self.xml.get_widget("filechooserdialog")
    self.fd.set_action(action)
    self.fd.set_select_multiple(multiple)
    self.hbox_format = self.xml.get_widget('hbox_format')
    signals={}
    for attr in dir(self):
      signals[attr] = getattr(self, attr)
    self.xml.signal_autoconnect(signals)
    if path=='':
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
  run=lambda self: self.fd.run()
  cancel_clicked=lambda self, *args: self.fd.destroy()
  def ok_clicked(self, *args):
    self.main.path = self.fd.get_filename()
    try:
      self.main.fcd_format = self.combobox.get_active_text()
    except:
      pass
    self.fd.hide()
"""

if __name__=='__main__':
  import sys
  if len(sys.argv) > 1:
    path = sys.argv[1]
  else:
    path = ''
  ui = UI(path)
  ui.run()
