# -*- coding: utf-8 -*-
# progressbar.py - Text progressbar library for python
#
# Copyright (C) 2006 Nilton Volpato <nilton.volpato@gmail.com>
#                    (until version 2.2)
# Copyright (C) 2009-2010 Saeed Rasooli <saeed.gnu@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library. Or on Debian systems, from:
# /usr/share/common-licenses/LGPL
# If not, see <http://www.gnu.org/licenses/lgpl.txt>.


"""
    Text progressbar library for python.

    This library provides a text mode progressbar. This is tipically used
    to display the progress of a long running operation, providing a
    visual clue that processing is underway.

    The ProgressBar class manages the progress, and the format of the line
    is given by a number of widgets. A widget is an object that may
    display diferently depending on the state of the progress. There are
    three types of widget:
    - a string, which always shows itself;
    - a ProgressBarWidget, which may return a diferent value every time
    it's update method is called; and
    - a ProgressBarWidgetHFill, which is like ProgressBarWidget, except it
    expands to fill the remaining width of the line.

    The progressbar module is very easy to use, yet very powerful. And
    automatically supports features like auto-resizing when available.
"""

# Changelog
#
# 2009-??-??: used in PyGlossary by Saeed Rasooli with some modifications
# 2006-05-07: v2.2 fixed bug in windows
# 2005-12-04: v2.1 autodetect terminal width, added start method
# 2005-12-04: v2.0 everything is now a widget (wow!)
# 2005-12-03: v1.0 rewrite using widgets
# 2005-06-02: v0.5 rewrite
# 2004-??-??: v0.1 first version

import sys
import time
from array import array
import signal

import logging
log = logging.getLogger('root')


class ProgressBarWidget(object):
    """
        This is an element of ProgressBar formatting.

        The ProgressBar object will call it's update value when an update
        is needed. It's size may change between call, but the results will
        not be good if the size changes drastically and repeatedly.
    """
    def update(self):
        """
            Returns the string representing the widget.

            The parameter pbar is a reference to the calling ProgressBar,
            where one can access attributes of the class for knowing how
            the update must be made.

            At least this function must be overriden.
        """
        pass

    def __str__(self):
        return self.update()

    def __add__(self, other):
        if isinstance(other, bytes):
            return str(self) + other.encode('utf-8')
        return str(self) + str(other)

    def __radd__(self, other):
        if isinstance(other, bytes):
            return other.encode('utf-8') + str(self)
        return str(other) + str(self)


class ProgressBarWidgetHFill(object):
    """
        This is a variable width element of ProgressBar formatting.

        The ProgressBar object will call it's update value, informing the
        width this object must the made. This is like TeX \\hfill, it will
        expand to fill the line. You can use more than one in the same
        line, and they will all have the same width, and together will
        fill the line.
    """
    def update(self, width):
        """
            Returns the string representing the widget.

            The parameter pbar is a reference to the calling ProgressBar,
            where one can access attributes of the class for knowing how
            the update must be made. The parameter width is the total
            horizontal width the widget must have.

            At least this function must be overriden.
        """
        pass


class ETA(ProgressBarWidget):
    """
        Widget for the Estimated Time of Arrival
    """
    def __init__(self, text='ETA: '):
        self.text = text

    def format_time(self, seconds):
        return time.strftime('%H:%M:%S', time.gmtime(seconds))

    def update(self):
        pbar = self.pbar
        if pbar.currval == 0:
            return 'ETA: --:--:--'
        elif pbar.finished:
            return 'Time: %s' % self.format_time(pbar.seconds_elapsed)
        else:
            elapsed = pbar.seconds_elapsed
            eta = elapsed * pbar.maxval / pbar.currval - elapsed
            return '%s%s' % (self.text, self.format_time(eta))


class FileTransferSpeed(ProgressBarWidget):
    """
        Widget for showing the transfer speed (useful for file transfers).
    """
    def __init__(self):
        self.fmt = '%6.2f %s'
        self.units = ['B', 'K', 'M', 'G', 'T', 'P']

    def update(self):
        pbar = self.pbar
        if pbar.seconds_elapsed < 2e-6:  # == 0:
            bps = 0.0
        else:
            bps = float(pbar.currval) / pbar.seconds_elapsed
        spd = bps
        for u in self.units:
            if spd < 1000:
                break
            spd /= 1000
        return self.fmt % (spd, u+'/s')


class RotatingMarker(ProgressBarWidget):
    """
        A rotating marker for filling the bar of progress.
    """
    def __init__(self, markers='|/-\\'):
        # Some cool exmaple for markers:
        # u'░▒▓█'
        # u'⬅⬉⬆⬈➡⬊⬇⬋' , u'⬌⬉⬆⬈⬌⬊⬇⬋', u'➚➙➘➙', u'➝➞➡➞'
        # u' ⚊⚌☰⚌⚊', u' ⚋⚊⚍⚌☱☰☱⚌⚍⚊⚋' ,
        # '<(|)>)|(', u'❘❙❚❙', u'❢❣❤❣'
        self.markers = markers
        self.curmark = -1

    def __len__(self):
        return 1

    def update(self):
        pbar = self.pbar
        if pbar.finished:
            return self.markers[0]
        self.curmark = (self.curmark + 1) % len(self.markers)
        return self.markers[self.curmark]


class Percentage(ProgressBarWidget):
    """
        Just the percentage done.
    """
    def update(self):
        pbar = self.pbar
        return '%5.1f' % pbar.percentage()


class Bar(ProgressBarWidgetHFill):
    """
        The bar of progress. It will strech to fill the line.
    """
    def __init__(self, marker='#', left='|', right='|'):
        self.marker = marker
        self.left = left
        self.right = right

    def _format_marker(self, pbar):
        if type(self.marker) in (str, str):
            return self.marker
        else:
            return self.marker.update(pbar)

    def update(self, width):
        width = int(width)
        pbar = self.pbar
        percent = pbar.percentage()
        cwidth = width - len(self.left) - len(self.right)
        marked_width = int(percent * cwidth / 100.0)
        m = self._format_marker(pbar)
        bar = (self.left + (m*marked_width).ljust(cwidth) + self.right)
        return bar


class ReverseBar(Bar):
    """
        The reverse bar of progress, or bar of regress. :)
    """
    def update(self, width):
        pbar = self.pbar
        percent = pbar.percentage()
        cwidth = width - len(self.left) - len(self.right)
        marked_width = int(percent * cwidth / 100.0)
        m = self._format_marker(pbar)
        bar = (self.left + (m*marked_width).rjust(cwidth) + self.right)
        return bar


class ProgressBar(object):
    """
        This is the ProgressBar class, it updates and prints the bar.

        The term_width parameter may be an integer. Or None, in which case
        it will try to guess it, if it fails it will default to 80 columns.

        The simple use is like this:
        >>> pbar = ProgressBar().start()
        >>> for i in xrange(100):
        ...    # do something
        ...    pbar.update(i+1)
        ...
        >>> pbar.finish()

        But anything you want to do is possible (well, almost anything).
        You can supply different widgets of any type in any order. And you
        can even write your own widgets! There are many widgets already
        shipped and you should experiment with them.

        When implementing a widget update method you may access any
        attribute or function of the ProgressBar object calling the
        widget's update method. The most important attributes you would
        like to access are:
        - currval: current value of the progress, 0 <= currval <= maxval
        - maxval: maximum (and final) value of the progress
        - finished: True if the bar is have finished (reached 100%), False o/w
        - start_time: first time update() method of ProgressBar was called
        - seconds_elapsed: seconds elapsed since start_time
        - percentage(): percentage of the progress (this is a method)
    """
    default_widgets = [Percentage(), ' ', Bar()]

    def __init__(
        self,
        maxval=100.0,
        widgets=None,
        update_step=0.1,
        term_width=None,
        fd=sys.stderr,
    ):
        assert maxval > 0
        self.maxval = maxval

        if widgets is None:
            widgets = self.default_widgets
        self.widgets = widgets

        for w in self.widgets:
            # log.debug( type(w) is ProgressBarWidget )
            # if not isinstance(w, str):
            try:
                w.pbar = self
            except:
                pass
        self.update_step = update_step
        self.fd = fd
        self.signal_set = False
        if term_width is None:
            try:
                self.handle_resize(None, None)
                signal.signal(signal.SIGWINCH, self.handle_resize)
                self.signal_set = True
            except:
                self.term_width = 79
        else:
            self.term_width = term_width

        self.currval = 0
        self.finished = False
        self.prev_percentage = -1
        self.start_time = None
        self.seconds_elapsed = 0

    def handle_resize(self, signum, frame):
        try:
            from fcntl import ioctl
            import termios
        except:
            pass
        else:
            h, w = array('h', ioctl(self.fd, termios.TIOCGWINSZ, '\0'*8))[:2]
            self.term_width = w

    def percentage(self):
        """
            Returns the percentage of the progress.
        """
        return self.currval*100.0 / self.maxval

    def _format_widgets(self):
        r = []
        hfill_inds = []
        num_hfill = 0
        currwidth = 0
        for (i, w) in enumerate(self.widgets):
            if isinstance(w, ProgressBarWidgetHFill):
                r.append(w)
                hfill_inds.append(i)
                num_hfill += 1
            elif isinstance(w, str):  # OR isinstance(w, (str, unicode))
                r.append(w)
                currwidth += len(w)
            else:
                weval = w.update()
                currwidth += len(weval)
                r.append(weval)
        for iw in hfill_inds:
            r[iw] = r[iw].update((self.term_width-currwidth)/num_hfill)
        return r

    def _format_line(self):
        return ''.join(self._format_widgets()).ljust(self.term_width)

    def _need_update(self):
        # return int(self.percentage()) != int(self.prev_percentage)
        return int(self.percentage() / self.update_step) != \
            int(self.prev_percentage / self.update_step)

    def update(self, value):
        """
            Updates the progress bar to a new value.
        """
        assert 0 <= value <= self.maxval
        self.currval = value
        if not self._need_update() or self.finished:
            return
        if not self.start_time:
            self.start_time = time.time()
        self.seconds_elapsed = time.time() - self.start_time
        self.prev_percentage = self.percentage()
        if value != self.maxval:
            self.fd.write(self._format_line() + '\r')
        else:
            self.finished = True
            self.fd.write(self._format_line() + '\n')

    def start(self):
        """
            Start measuring time, and prints the bar at 0%.

            It returns self so you can use it like this:
            >>> pbar = ProgressBar().start()
            >>> for i in xrange(100):
            ...    # do something
            ...    pbar.update(i+1)
            ...
            >>> pbar.finish()
        """
        self.update(0)
        return self

    def finish(self):
        """
            Used to tell the progress is finished.
        """
        self.update(self.maxval)
        if self.signal_set:
            signal.signal(signal.SIGWINCH, signal.SIG_DFL)

if __name__ == '__main__':
    def example1():
        pbar = ProgressBar(
            widgets=[
                'Test: ',
                Bar(),
                ' ',
                RotatingMarker(),
                Percentage(),
                ' ',
                ETA(),
            ],
            maxval=1.0,
            update_step=0.2,
        )
        pbar.start()
        for i in range(1000):
            # do something
            time.sleep(0.1)
            pbar.update(i/1000.0)
        pbar.finish()
        print('')
    example1()
