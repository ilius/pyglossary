# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# progressbar  - Text progress bar library for Python.
# Copyright (c) 2023 Saeed Rasooli
# Copyright (c) 2005 Nilton Volpato
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from __future__ import annotations

"""Main ProgressBar class."""


import math
import os
import signal
import sys
import time

try:
    import termios
    from array import array
    from fcntl import ioctl
except ImportError:
    pass

from . import widgets


class ProgressBar:

    """
    The ProgressBar class which updates and prints the bar.

    A common way of using it is like:
    >>> pbar = ProgressBar().start()
    >>> for i in range(100):
    ...    # do something
    ...    pbar.update(i+1)
    ...
    >>> pbar.finish()

    You can also use a ProgressBar as an iterator:
    >>> progress = ProgressBar()
    >>> for i in progress(some_iterable):
    ...    # do something
    ...

    Since the progress bar is incredibly customizable you can specify
    different widgets of any type in any order. You can even write your own
    widgets! However, since there are already a good number of widgets you
    should probably play around with them before moving on to create your own
    widgets.

    The term_width parameter represents the current terminal width. If the
    parameter is set to an integer then the progress bar will use that,
    otherwise it will attempt to determine the terminal width falling back to
    80 columns if the width cannot be determined.

    When implementing a widget's update method you are passed a reference to
    the current progress bar. As a result, you have access to the
    ProgressBar's methods and attributes. Although there is nothing preventing
    you from changing the ProgressBar you should treat it as read only.

    Useful methods and attributes include (Public API):
     - currval: current progress (0 <= currval <= maxval)
     - maxval: maximum (and final) value
     - finished: True if the bar has finished (reached 100%)
     - start_time: the time when start() method of ProgressBar was called
     - seconds_elapsed: seconds elapsed since start_time and last call to
                        update
     - percentage(): progress in percent [0..100]
    """

    __slots__ = (
        "__iterable",
        "_time_sensitive",
        "currval",
        "fd",
        "finished",
        "last_update_time",
        "left_justify",
        "maxval",
        "next_update",
        "num_intervals",
        "poll",
        "seconds_elapsed",
        "signal_set",
        "start_time",
        "term_width",
        "update_interval",
        "widgets",
    )

    _DEFAULT_MAXVAL = 100
    _DEFAULT_TERMSIZE = 80
    _DEFAULT_WIDGETS = [widgets.Percentage(), " ", widgets.Bar()]

    def __init__(
        self,
        maxval=None,
        widgets=None,
        term_width=None,
        poll=1,
        left_justify=True,
        fd=None,
    ) -> None:
        """Initializes a progress bar with sane defaults."""
        # Don't share a reference with any other progress bars
        if widgets is None:
            widgets = self._DEFAULT_WIDGETS.copy()

        self.maxval = maxval
        self.widgets = widgets
        self.fd = fd if fd is not None else sys.stderr
        self.left_justify = left_justify

        self.signal_set = False
        if term_width is not None:
            self.term_width = term_width
        else:
            try:
                self._handle_resize()
                signal.signal(signal.SIGWINCH, self._handle_resize)
                self.signal_set = True
            except (SystemExit, KeyboardInterrupt):
                raise
            except:  # noqa: E722
                self.term_width = self._env_size()

        self.__iterable = None
        self._update_widgets()
        self.currval = 0
        self.finished = False
        self.last_update_time = None
        self.poll = poll
        self.seconds_elapsed = 0
        self.start_time = None
        self.update_interval = 1
        self.next_update = 0

    def __call__(self, iterable):
        """Use a ProgressBar to iterate through an iterable."""
        try:
            self.maxval = len(iterable)
        except TypeError:
            if self.maxval is None:
                self.maxval = widgets.UnknownLength

        self.__iterable = iter(iterable)
        return self

    def __iter__(self):
        return self

    def __next__(self):
        try:
            value = next(self.__iterable)
            if self.start_time is None:
                self.start()
            else:
                self.update(self.currval + 1)
            return value
        except StopIteration:
            if self.start_time is None:
                self.start()
            self.finish()
            raise

    def _env_size(self):
        """Tries to find the term_width from the environment."""
        return int(os.environ.get("COLUMNS", self._DEFAULT_TERMSIZE)) - 1

    def _handle_resize(self, signum=None, frame=None):
        """Tries to catch resize signals sent from the terminal."""
        h, w = array("h", ioctl(self.fd, termios.TIOCGWINSZ, "\0" * 8))[:2]
        self.term_width = w

    def percentage(self):
        """Returns the progress as a percentage."""
        if self.maxval is widgets.UnknownLength:
            return float("NaN")
        if self.currval >= self.maxval:
            return 100.0
        return (self.currval * 100.0 / self.maxval) if self.maxval else 100.00

    percent = property(percentage)

    def _format_widgets(self):
        result = []
        expanding = []
        width = self.term_width

        for index, widget in enumerate(self.widgets):
            if isinstance(widget, widgets.WidgetHFill):
                result.append(widget)
                expanding.insert(0, index)
            else:
                widget = widgets.format_updatable(widget, self)
                result.append(widget)
                width -= len(widget)

        count = len(expanding)
        while count:
            portion = max(int(math.ceil(width * 1. / count)), 0)
            index = expanding.pop()
            count -= 1

            widget = result[index].update(self, portion)
            width -= len(widget)
            result[index] = widget

        return result

    def _format_line(self):
        """Joins the widgets and justifies the line."""
        widgets = "".join(self._format_widgets())

        if self.left_justify:
            return widgets.ljust(self.term_width)
        return widgets.rjust(self.term_width)

    def _need_update(self):
        """Returns whether the ProgressBar should redraw the line."""
        if self.currval >= self.next_update or self.finished:
            return True

        return self._time_sensitive and time.perf_counter() - self.last_update_time > self.poll

    def _update_widgets(self):
        """Checks all widgets for the time sensitive bit."""
        self._time_sensitive = any(
            getattr(w, "TIME_SENSITIVE", False)
            for w in self.widgets
        )

    def update(self, value=None):
        """Updates the ProgressBar to a new value."""
        if value is not None and value is not widgets.UnknownLength:
            if (
                self.maxval is not widgets.UnknownLength and
                not 0 <= value <= self.maxval
            ):
                raise ValueError("Value out of range")

            self.currval = value

        if not self._need_update():
            return
        if self.start_time is None:
            raise RuntimeError('You must call "start" before calling "update"')

        now = time.perf_counter()
        self.seconds_elapsed = now - self.start_time
        self.next_update = self.currval + self.update_interval
        self.fd.write(self._format_line() + "\r")
        self.fd.flush()
        self.last_update_time = now

    def start(self, num_intervals=0):
        """
        Starts measuring time, and prints the bar at 0%.

        It returns self so you can use it like this:
        >>> pbar = ProgressBar().start()
        >>> for i in range(100):
        ...    # do something
        ...    pbar.update(i+1)
        ...
        >>> pbar.finish()
        """
        if self.maxval is None:
            self.maxval = self._DEFAULT_MAXVAL

        if num_intervals > 0:
            self.num_intervals = num_intervals
        else:
            self.num_intervals = max(100, self.term_width)
        self.next_update = 0

        if self.maxval is not widgets.UnknownLength:
            if self.maxval < 0:
                raise ValueError("Value out of range")
            self.update_interval = self.maxval / self.num_intervals

        self.start_time = self.last_update_time = time.perf_counter()
        self.update(0)

        return self

    def finish(self):
        """Puts the ProgressBar bar in the finished state."""
        if self.finished:
            return
        self.finished = True
        self.update(self.maxval)
        self.fd.write("\n")
        if self.signal_set:
            signal.signal(signal.SIGWINCH, signal.SIG_DFL)
