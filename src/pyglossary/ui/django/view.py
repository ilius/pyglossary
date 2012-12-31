#from django.template import Context, loader
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse, resolve
from django.template import RequestContext
from django.core.context_processors import csrf
from django.conf.urls.defaults import *
#from django.contrib.auth import authenticate, login

from ui_django import settings


import string, time, struct, zlib
from os import listdir, remove
from os.path import join
from pprint import pprint, pformat

from random import choice, randint

import logging
import logging.config
cfg = logging.config.dictConfig(settings.LOGGING)
#logging.dictConfig(settings.LOGGING)

log = logging.getLogger('pyglossary')


def toStr(s):
    if isinstance(s, str):
        return s
    elif isinstance(s, unicode):
        return s.encode('utf-8')
    else:
        return str(s)







