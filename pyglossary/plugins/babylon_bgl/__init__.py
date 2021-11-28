# -*- coding: utf-8 -*-
#
# Copyright © 2008-2020 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

from formats_common import *
from .bgl_reader import BglReader as Reader
from .bgl_reader import optionsProp

enable = True
lname = "babylon_bgl"
format = "BabylonBgl"
description = "Babylon (.BGL)"
extensions = (".bgl",)
extensionCreate = ""
singleFile = True
kind = "binary"
wiki = ""
website = None
# progressbar = DEFAULT_YES

# FIXME: document type of read/write options
# (that would be specified in command line)
