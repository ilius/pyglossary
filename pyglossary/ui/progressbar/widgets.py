# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# progressbar  - Text progress bar library for Python.
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

"""Default ProgressBar widgets."""

from __future__ import annotations
from __future__ import division

import datetime
import math

try:
    from abc import ABCMeta, abstractmethod
except ImportError:
    AbstractWidget = object

    def abstractmethod(fn):
        return fn

else:
    AbstractWidget = ABCMeta('AbstractWidget', (object,), {})


class UnknownLength:
    pass


def format_updatable(updatable, pbar):
    if hasattr(updatable, 'update'):
        return updatable.update(pbar)
    return updatable


class Widget(AbstractWidget):

    """
    The base class for all widgets.

    The ProgressBar will call the widget's update value when the widget should
    be updated. The widget's size may change between calls, but the widget may
    display incorrectly if the size changes drastically and repeatedly.

    The boolean TIME_SENSITIVE informs the ProgressBar that it should be
    updated more often because it is time sensitive.
    """

    TIME_SENSITIVE = False
    __slots__ = ()

    @abstractmethod
    def update(self, pbar):
        """
        Updates the widget.

        pbar - a reference to the calling ProgressBar
        """


class WidgetHFill(Widget):

    """
    The base class for all variable width widgets.

    This widget is much like the \\hfill command in TeX, it will expand to
    fill the line. You can use more than one in the same line, and they will
    all have the same width, and together will fill the line.
    """

    @abstractmethod
    def update(self, pbar, width):
        """
        Updates the widget providing the total width the widget must fill.

        pbar - a reference to the calling ProgressBar
        width - The total width the widget must fill
        """


class Timer(Widget):

    """Widget which displays the elapsed seconds."""

    __slots__ = ('format_string',)
    TIME_SENSITIVE = True

    def __init__(self, format='Elapsed Time: %s') -> None:
        self.format_string = format

    @staticmethod
    def format_time(seconds):
        """Formats time as the string "HH:MM:SS"."""
        return str(datetime.timedelta(seconds=int(seconds)))

    def update(self, pbar):
        """Updates the widget to show the elapsed time."""
        return self.format_string % self.format_time(pbar.seconds_elapsed)


class ETA(Timer):

    """Widget which attempts to estimate the time of arrival."""

    TIME_SENSITIVE = True

    def update(self, pbar):
        """Updates the widget to show the ETA or total time when finished."""
        if pbar.maxval is UnknownLength or pbar.currval == 0:
            return 'ETA:  --:--:--'
        if pbar.finished:
            return f'Time: {self.format_time(pbar.seconds_elapsed)}'
        elapsed = pbar.seconds_elapsed
        eta = elapsed * pbar.maxval / pbar.currval - elapsed
        return f'ETA:  {self.format_time(eta)}'


class AdaptiveETA(Timer):

    """
    Widget which attempts to estimate the time of arrival.

    Uses a weighted average of two estimates:
      1) ETA based on the total progress and time elapsed so far
      2) ETA based on the progress as per the last 10 update reports

    The weight depends on the current progress so that to begin with the
    total progress is used and at the end only the most recent progress is
    used.
    """

    TIME_SENSITIVE = True
    NUM_SAMPLES = 10

    def _update_samples(self, currval, elapsed):
        sample = (currval, elapsed)
        if not hasattr(self, 'samples'):
            self.samples = [sample] * (self.NUM_SAMPLES + 1)
        else:
            self.samples.append(sample)
        return self.samples.pop(0)

    def _eta(self, maxval, currval, elapsed):
        return elapsed * maxval / float(currval) - elapsed

    def update(self, pbar):
        """Updates the widget to show the ETA or total time when finished."""
        if pbar.maxval is UnknownLength or pbar.currval == 0:
            return 'ETA:  --:--:--'
        if pbar.finished:
            return f'Time: {self.format_time(pbar.seconds_elapsed)}'
        elapsed = pbar.seconds_elapsed
        currval1, elapsed1 = self._update_samples(pbar.currval, elapsed)
        eta = self._eta(pbar.maxval, pbar.currval, elapsed)
        if pbar.currval > currval1:
            etasamp = self._eta(pbar.maxval - currval1,
                                pbar.currval - currval1,
                                elapsed - elapsed1)
            weight = (pbar.currval / float(pbar.maxval)) ** 0.5
            eta = (1 - weight) * eta + weight * etasamp
        return f'ETA:  {self.format_time(eta)}'


class FileTransferSpeed(Widget):

    """Widget for showing the transfer speed (useful for file transfers)."""

    FMT = '%6.2f %s%s/s'
    PREFIXES = ' kMGTPEZY'
    __slots__ = ('unit',)

    def __init__(self, unit='B') -> None:
        self.unit = unit

    def update(self, pbar):
        """Updates the widget with the current SI prefixed speed."""
        if pbar.seconds_elapsed < 2e-6 or pbar.currval < 2e-6:  # =~ 0
            scaled = power = 0
        else:
            speed = pbar.currval / pbar.seconds_elapsed
            power = int(math.log(speed, 1000))
            scaled = speed / 1000.**power

        return self.FMT % (scaled, self.PREFIXES[power], self.unit)


class AnimatedMarker(Widget):

    """
    An animated marker for the progress bar which defaults to appear as if
    it were rotating.
    """

    __slots__ = ('markers', 'curmark')

    def __init__(self, markers='|/-\\') -> None:
        self.markers = markers
        self.curmark = -1

    def update(self, pbar):
        """
        Updates the widget to show the next marker or the first marker when
        finished.
        """
        if pbar.finished:
            return self.markers[0]

        self.curmark = (self.curmark + 1) % len(self.markers)
        return self.markers[self.curmark]


# Alias for backwards compatibility
RotatingMarker = AnimatedMarker


class Counter(Widget):

    """Displays the current count."""

    __slots__ = ('format_string',)

    def __init__(self, format='%d') -> None:
        self.format_string = format

    def update(self, pbar):
        return self.format_string % pbar.currval


class Percentage(Widget):

    """Displays the current percentage as a number with a percent sign."""

    def __init__(self, prefix="%") -> None:
        Widget.__init__(self)
        self.prefix = prefix

    def update(self, pbar):
        return f"{self.prefix}{pbar.percentage():.1f}"\
            .rjust(5 + len(self.prefix))


class FormatLabel(Timer):

    """Displays a formatted label."""

    mapping = {
        'elapsed': ('seconds_elapsed', Timer.format_time),
        'finished': ('finished', None),
        'last_update': ('last_update_time', None),
        'max': ('maxval', None),
        'seconds': ('seconds_elapsed', None),
        'start': ('start_time', None),
        'value': ('currval', None),
    }

    __slots__ = ('format_string',)

    def __init__(self, format) -> None:
        self.format_string = format

    def update(self, pbar):
        context = {}
        for name, (key, transform) in self.mapping.items():
            try:
                value = getattr(pbar, key)

                if transform is None:
                    context[name] = value
                else:
                    context[name] = transform(value)
            except:  # noqa: E722
                pass  # noqa: S110

        return self.format_string % context


class SimpleProgress(Widget):

    """Returns progress as a count of the total (e.g.: "5 of 47")."""

    __slots__ = ('sep',)

    def __init__(self, sep=' of ') -> None:
        self.sep = sep

    def update(self, pbar):
        if pbar.maxval is UnknownLength:
            return '%d%s?' % (pbar.currval, self.sep)
        return '%d%s%s' % (pbar.currval, self.sep, pbar.maxval)


class Bar(WidgetHFill):

    """A progress bar which stretches to fill the line."""

    __slots__ = ('marker', 'left', 'right', 'fill', 'fill_left')

    def __init__(self, marker='#', left='|', right='|', fill=' ',
                 fill_left=True) -> None:
        """
        Creates a customizable progress bar.

        marker - string or updatable object to use as a marker
        left - string or updatable object to use as a left border
        right - string or updatable object to use as a right border
        fill - character to use for the empty part of the progress bar
        fill_left - whether to fill from the left or the right
        """
        self.marker = marker
        self.left = left
        self.right = right
        self.fill = fill
        self.fill_left = fill_left

    def update(self, pbar, width):
        """Updates the progress bar and its subcomponents."""
        left, marked, right = (
            format_updatable(i, pbar)
            for i in (self.left, self.marker, self.right)
        )

        width -= len(left) + len(right)
        # Marked must *always* have length of 1
        if pbar.maxval is not UnknownLength and pbar.maxval:
            marked *= int(pbar.currval / pbar.maxval * width)
        else:
            marked = ''

        if self.fill_left:
            return f'{left}{marked.ljust(width, self.fill)}{right}'

        return f'{left}{marked.rjust(width, self.fill)}{right}'


class ReverseBar(Bar):

    """A bar which has a marker which bounces from side to side."""

    def __init__(self, marker='#', left='|', right='|', fill=' ',
                 fill_left=False) -> None:
        """
        Creates a customizable progress bar.

        marker - string or updatable object to use as a marker
        left - string or updatable object to use as a left border
        right - string or updatable object to use as a right border
        fill - character to use for the empty part of the progress bar
        fill_left - whether to fill from the left or the right
        """
        self.marker = marker
        self.left = left
        self.right = right
        self.fill = fill
        self.fill_left = fill_left


class BouncingBar(Bar):
    def update(self, pbar, width):
        """Updates the progress bar and its subcomponents."""
        left, marker, right = (format_updatable(i, pbar) for i in
                               (self.left, self.marker, self.right))

        width -= len(left) + len(right)

        if pbar.finished:
            return f'{left}{width * marker}{right}'

        position = int(pbar.currval % (width * 2 - 1))
        if position > width:
            position = width * 2 - position
        lpad = self.fill * (position - 1)
        rpad = self.fill * (width - len(marker) - len(lpad))

        # Swap if we want to bounce the other way
        if not self.fill_left:
            rpad, lpad = lpad, rpad

        return f'{left}{lpad}{marker}{rpad}{right}'
