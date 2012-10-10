## (VAR_NAME, bool, CHECKBUTTON_TEXT) ## CheckButton
## (VAR_NAME, list, LABEL_TEXT, (ITEM1, ITEM2, ...)) ## ComboBox
## (VAR_NAME, int, LABEL_TEXT, MIN, MAX) ## SpinButton
## (VAR_NAME, float, LABEL_TEXT, MIN, MAX, DIGITS) ## SpinButton
## (VAR_NAME, str, LABEL_TEXT, WIDTH_CHARS) ## Entry
class ModuleOptionItem():
    def __init__(self, module, opt):
        t = opt[1]
        self.opt = opt ## needed??
        self.module = module
        self.type = t
        self.var_name = opt[0]
        hbox = gtk.HBox()
        if t==bool:
            w = gtk.CheckButton(_(opt[2]))
            self.get_value = w.get_active
            self.set_value = w.set_active
        elif t==list:
            hbox.pack_start(gtk.Label(_(opt[2])), 0, 0)
            w = gtk.combo_box_new_text() ### or RadioButton
            for s in opt[3]:
                w.append_text(_(s))
            self.get_value = w.get_active
            self.set_value = w.set_active
        elif t==int:
            hbox.pack_start(gtk.Label(_(opt[2])), 0, 0)
            w = gtk.SpinButton()
            w.set_increments(1, 10)
            w.set_range(opt[3], opt[4])
            w.set_digits(0)
            w.set_direction(gtk.TEXT_DIR_LTR)
            self.get_value = w.get_value
            self.set_value = w.set_value
        elif t==float:
            hbox.pack_start(gtk.Label(_(opt[2])), 0, 0)
            w = gtk.SpinButton()
            w.set_increments(0.1, 1)
            w.set_range(opt[3], opt[4])
            w.set_digits(opt[5])
            w.set_direction(gtk.TEXT_DIR_LTR)
            self.get_value = w.get_value
            self.set_value = w.set_value
        elif t==str:
            hbox.pack_start(gtk.Label(_(opt[2])), 0, 0)
            w = gtk.Entry()
            w.set_width_chars(opt[3])
            self.get_value = w.get_text
            self.set_value = w.set_text
        else:
            raise TypeError('bad option type "%s"'%t)
        hbox.pack_start(w, 0, 0)
        self.widget = hbox
        ####
        self.updateVar = lambda: setattr(self.module, self.var_name, self.get_value())
        self.updateWidget = lambda: self.set_value(getattr(self.module, self.var_name))







