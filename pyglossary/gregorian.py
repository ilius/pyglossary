# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
# Copyright (C) 2007 Mehdi Bayazee <Bayazee@Gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux


# Gregorian calendar:
#   http://en.wikipedia.org/wiki/Gregorian_calendar

from datetime import datetime

name = 'gregorian'
desc = 'Gregorian'
origLang = 'en'

monthName = ('January', 'February', 'March', 'April', 'May', 'June',
			 'July', 'August', 'September', 'October', 'November', 'December')

monthNameAb = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
			   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')


def getMonthName(m, y=None):
	return monthName.__getitem__(m - 1)


def getMonthNameAb(m, y=None):
	return monthNameAb.__getitem__(m - 1)


def getMonthsInYear(y):
	return 12


epoch = 1721426
minMonthLen = 29
maxMonthLen = 31
avgYearLen = 365.2425  # FIXME

options = ()


def save():
	pass


def isLeap(y):
	if y < 1:
		y += 1
	return y % 4 == 0 and not (y % 100 == 0 and y % 400 != 0)


def to_jd(year, month, day):
	if year > 0:  # > 1.5x faster
		return datetime(year, month, day).toordinal() + 1721425

	# Python 2.x and 3.x:
	if month <= 2:
		tm = 0
	elif isLeap(year):
		tm = -1
	else:
		tm = -2
	# Python >= 2.5:
	# tm = 0 if month <= 2 else (-1 if isLeap(year) else -2)
	return epoch - 1 + 365*(year-1) + (year-1)//4 - (year-1)//100 + \
		(year-1)//400 + (367*month-362)//12 + tm + day


def jd_to(jd):
	ordinal = int(jd) - 1721425
	if ordinal > 0:  # > 4x faster
		dt = datetime.fromordinal(ordinal)
		return (dt.year, dt.month, dt.day)

	# wjd = floor(jd - 0.5) + 0.5
	qc, dqc = divmod(jd - epoch, 146097)  # qc ~~ quadricent
	cent, dcent = divmod(dqc, 36524)
	quad, dquad = divmod(dcent, 1461)
	yindex = dquad//365  # divmod(dquad, 365)[0]
	year = qc*400 + cent*100 + quad*4 + yindex + (cent != 4 and yindex != 4)
	yearday = jd - to_jd(year, 1, 1)
	# Python 2.x and 3.x:
	if jd < to_jd(year, 3, 1):
		leapadj = 0
	elif isLeap(year):
		leapadj = 1
	else:
		leapadj = 2
	# Python >= 2.5:
	# leapadj = 0 if jd < to_jd(year, 3, 1) else (1 if isLeap(year) else 2)
	month = ((yearday+leapadj) * 12 + 373) // 367
	day = jd - to_jd(year, month, 1) + 1
	return int(year), int(month), int(day)


def getMonthLen(y, m):
	if m == 12:
		return to_jd(y+1, 1, 1) - to_jd(y, 12, 1)
	else:
		return to_jd(y, m+1, 1) - to_jd(y, m, 1)

J0001 = to_jd(1, 1, 1)
J1970 = to_jd(1970, 1, 1)
