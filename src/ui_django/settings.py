# -*- coding: utf-8 -*-
# Django settings for pyglossary project.

import os, string
from os.path import dirname
from os.path import join

DJ_ROOT_DIR = dirname(__file__)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': join(DJ_ROOT_DIR, 'pyglossary.sqlite'),
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Asia/Tehran'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'fa-ir'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '=v0luzu#yy7^^#!$d&umx5n)i8c7y_#&_e7fq2dq6p!(e_c#n('


# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'pyglossary.urls'


TEMPLATE_DIRS = (
    join(DJ_ROOT_DIR, 'templates')
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    #'pyglossary',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)


SESSION_ENGINE = 'django.contrib.sessions.backends.db'

IMAGES_DIR = join(DJ_ROOT_DIR, 'static', 'img')
JS_DIR = join(DJ_ROOT_DIR, 'static', 'img')


LOGGING = {
    'version': 1,
    'formatters': {
        'file': {
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s'
        },
        'console': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'console'
        },
        'request': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'formatter': 'file',
            'filename': '/var/log/pyglossary/request',
            'maxBytes': 1024,
            'backupCount': 10,
        },
        'file_debug': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'formatter': 'file',
            'filename': '/var/log/pyglossary/debug',
            'maxBytes': 1024,
            'backupCount': 10,
        },
        'file_error': {
            'level':'ERROR',
            'class':'logging.handlers.RotatingFileHandler',
            'formatter': 'file',
            'filename': '/var/log/pyglossary/error',
            'maxBytes': 1024,
            'backupCount': 10,
        },
    },
    'loggers': {
        'django': {
            'handlers':[],
            'propagate': True,
            'level':'INFO',
        },
        'django.request': {
            'handlers': ['request'],
            'level': 'ERROR',
            'propagate': False,
        },
        'pyglossary': {
            'handlers': ['file_debug', 'file_error'],
            'level': 'DEBUG',
            'filters': []
        },
    }
}


