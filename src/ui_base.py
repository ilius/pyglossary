# -*- coding: utf-8 -*-
##
## Copyright © 2012 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
## This file is part of PyGlossary project, http://sourceforge.net/projects/pyglossary/
##
## This program is a free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3, or (at your option)
## any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License along
## with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
## If not, see <http://www.gnu.org/licenses/gpl.txt>.

from glossary import *

class UIBase:
    prefSavePath = [confPath, '%s%src.py'%(srcDir,os.sep)]
    prefKeys = (
        'save', 'newline', 'auto_update',
        'auto_set_for', 'auto_set_out', 'sort', 'lower',
        'remove_tags', 'tags', 'utf8_check',
        'enable_alts',
        'wrap_out', 'wrap_err', 'wrap_edit', 'wrap_dbe',
        'color_bg_out', 'color_bg_err', 'color_bg_edit', 'color_bg_dbe',
        'color_font_out', 'color_font_err', 'color_font_edit', 'color_font_dbe',
        'matchWord', 'showRel', 'autoSaveStep', 'minRel', 'maxNum', 'includeDefs',## Reverse Options
    )




