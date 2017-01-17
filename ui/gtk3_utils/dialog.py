from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk


class MyDialog(object):
	def startWaiting(self):
		self.queue_draw()
		self.vbox.set_sensitive(False)
		self.get_window().set_cursor(gdk.Cursor.new(gdk.CursorType.WATCH))
		while gtk.events_pending():
			gtk.main_iteration_do(False)

	def endWaiting(self):
		self.get_window().set_cursor(gdk.Cursor.new(gdk.CursorType.LEFT_PTR))
		self.vbox.set_sensitive(True)

	def waitingDo(self, func, *args, **kwargs):
		self.startWaiting()
		try:
			func(*args, **kwargs)
		except Exception as e:
			raise e
		finally:
			self.endWaiting()
