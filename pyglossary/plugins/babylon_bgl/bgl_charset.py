# -*- coding: utf-8 -*-
#
# Copyright © 2008-2016 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# Copyright © 2011-2012 kubtek <kubtek@gmail.com>
# This file is part of PyGlossary project, http://github.com/ilius/pyglossary
# Thanks to Raul Fernandes <rgfbr@yahoo.com.br> and Karl Grill
#       for reverse engineering
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
# If not, see <http://www.gnu.org/licenses/gpl.txt>.


charsetByCode = {
    0x41: 'cp1252',  # Default, 0x41
    0x42: 'cp1252',  # Latin, 0x42
    0x43: 'cp1250',  # Eastern European, 0x43
    0x44: 'cp1251',  # Cyrillic, 0x44
    0x45: 'cp932',  # Japanese, 0x45
    0x46: 'cp950',  # Traditional Chinese, 0x46
    0x47: 'cp936',  # Simplified Chinese, 0x47
    0x48: 'cp1257',  # Baltic, 0x48
    0x49: 'cp1253',  # Greek, 0x49
    0x4A: 'cp949',  # Korean, 0x4A
    0x4B: 'cp1254',  # Turkish, 0x4B
    0x4C: 'cp1255',  # Hebrew, 0x4C
    0x4D: 'cp1256',  # Arabic, 0x4D
    0x4E: 'cp874',  # Thai, 0x4E
}
