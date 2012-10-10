# -*- coding: utf-8 -*-

import gtk

class DbEditorFindDialog(gtk.Dialog):
    def __init__(self, glos, current_index=0):
        gtk.Dialog.__init__(self)
        self.connect('delete-event', self.onDeleteEvent)
        ####
        hbox = gtk.HBox()
        self.find_combo = gtk.combo_box_entry_new_text()
        hbox.pack_start(self.find_combo, 1, 1)
        self.find_multiline_check = gtk.CheckButton('Multiline')
        hbox.pack_start(self.find_multiline_check, 0, 0)
        self.vbox.pack_start(hbox, 0, 0)
        ####
        hbox = gtk.HBox()
        self.replace_check = gtk.CheckButton('Replace with:')
        hbox.pack_start(self.replace_check, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.vbox.pack_start(hbox, 0, 0)
        ####
        hbox = gtk.HBox()
        self.replace_combo = gtk.combo_box_entry_new_text()
        hbox.pack_start(self.replace_combo, 1, 1)
        self.replace_multiline_check = gtk.CheckButton('Multiline')
        hbox.pack_start(self.replace_multiline_check, 0, 0)
        self.vbox.pack_start(hbox, 0, 0)
        ####
        options_exp = gtk.Expander('Options')
        options_vbox = gtk.VBox()
        sgroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        ##
        hbox = gtk.HBox()
        self.match_case_check = gtk.CheckButton('Match Case')
        hbox.pack_start(self.match_case_check, 1, 1)
        sgroup.add_widget(self.match_case_check)
        self.match_word_check = gtk.CheckButton('Match Word')
        hbox.pack_start(self.match_word_check, 1, 1)
        sgroup.add_widget(self.match_word_check)
        options_vbox.pack_start(hbox, 0, 0)
        ##
        hbox = gtk.HBox()
        self.regexp_check = gtk.CheckButton('Regexp')
        hbox.pack_start(self.regexp_check, 1, 1)
        sgroup.add_widget(self.regexp_check)
        self.highlight_all_check = gtk.CheckButton('Highlight All')
        hbox.pack_start(self.highlight_all_check, 1, 1)
        sgroup.add_widget(self.highlight_all_check)
        options_vbox.pack_start(hbox, 0, 0)
        ##
        # backward_ckeck
        ##
        hbox = gtk.HBox()
        self.current_entry_radio = gtk.RadioButton()
        self.current_entry_radio.set_label('Current Entry')
        hbox.pack_start(self.current_entry_radio, 1, 1)
        sgroup.add_widget(self.current_entry_radio)
        self.all_entries_radio = gtk.RadioButton()
        self.all_entries_radio.set_label('All Entries')
        self.all_entries_radio.set_group(self.current_entry_radio)
        hbox.pack_start(self.all_entries_radio, 1, 1)
        sgroup.add_widget(self.all_entries_radio)
        options_vbox.pack_start(hbox, 0, 0)
        ##
        hbox = gtk.HBox()
        self.word_check = gtk.CheckButton('Word')
        hbox.pack_start(self.word_check, 1, 1)
        sgroup.add_widget(self.word_check)
        self.defi_check = gtk.CheckButton('Definition')
        hbox.pack_start(self.defi_check, 1, 1)
        sgroup.add_widget(self.defi_check)
        options_vbox.pack_start(hbox, 0, 0)
        ##
        options_exp.add(options_vbox)
        self.vbox.pack_start(options_exp, 0, 0)
        ####
        button_close = self.add_button(gtk.STOCK_CLOSE, 0)
        button_replace_all = self.add_button('Replace All', 0)
        button_replace_all.set_image(gtk.image_new_from_stock(gtk.STOCK_FIND_AND_REPLACE, gtk.ICON_SIZE_BUTTON))
        button_replace = self.add_button('Replace', 0)
        button_replace.set_image(gtk.image_new_from_stock(gtk.STOCK_FIND_AND_REPLACE, gtk.ICON_SIZE_BUTTON))
        button_find = self.add_button(gtk.STOCK_FIND, 0)
        self.action_area.set_homogeneous(False)
        ####
        self.vbox.show_all()
    def onDeleteEvent(self, widget, event):
        self.hide()
        return True


## Warn when replacing in all entries, and show number of occurrences




if __name__=='__main__':
    from glossary import Glossary
    glos = Glossary()
    DbEditorFindDialog(glos).run()



