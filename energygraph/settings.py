# Copyright (c) 2010, Cullen Jennings. All rights reserved.

import os
import sys
import urlparse

import djcelery
from datetime import timedelta
from celery.schedules import crontab

DEBUG = False
# TODO turn off debug
DEBUG = True

try:
    if 'DJANGO_DEBUG' in  os.environ:
        if os.environ['DJANGO_DEBUG'] == "TRUE" :
            DEBUG = True
except Exception:
    print "Unexpected error checking DJANGO_DEBUG environment variable"

TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Cullen Jennings', 'c.jennings@ieee.org'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'hero',                      # Or path to database file if using sqlite3.
        'USER': 'fluffy',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': 'localhost',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

PROJECT_PATH = os.path.dirname(os.path.realpath(__file__))

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Denver'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/{{ docs_version }}/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [ '.fluffyhome.com', '127.0.0.1' ]

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(PROJECT_PATH, 'staticfiles/static')

STATIC_DIR =  os.path.join(PROJECT_PATH, 'staticfiles')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
#STATIC_URL = 'http://s3.amazonaws.com/fluffyhome'
#STATIC_URL = 'http://fluffyhome.s3-website-us-east-1.amazonaws.com/static/'
STATIC_URL = '/static/'

ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(PROJECT_PATH, 'static'), #'energygraph/static/',
    #'static/',
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

#STATICFILES_STORAGE = 'myproject.storage.S3Storage'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
#STATICFILES_STORAGE  = 'storages.backends.s3boto.S3BotoStorage'
#DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

#AWS_ACCESS_KEY_ID = ""
#AWS_SECRET_ACCESS_KEY = ""
AWS_STORAGE_BUCKET_NAME = "fluffyhome"

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'CHANGE-THIS-lsk232djflljkjhykjh7ojk23467rkj8j'
if 'DJANGO_SECRET_KEY' in os.environ:
    SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')


# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
)

MIDDLEWARE_CLASSES = (
    #'google.appengine.ext.appstats.recording.AppStatsDjangoMiddleware',
    #'django.middleware.common.CommonMiddleware',
    #'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'django.middleware.doc.XViewMiddleware',

    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',

)

ROOT_URLCONF = 'energygraph.urls'

# Python dotted path to the WSGI application used by Django's runserver.
# WSGI_APPLICATION = 'energygraph.wsgi.application'

TEMPLATE_DIRS = (
    'templates',
    'energygraph/templates',
    #'templates',
    "/Users/fluffy/src/fluffyhome/energygraph/templates",
    "/home/fluffy/src/fluffyhome/energygraph/templates",
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    #'django.contrib.admindocs',

    # stuff for Celery
    #'kombu.transport.django',
   'djcelery',
   'djcelery.transport',

    # for the S3 storage stuff
    #'storages',
    'django.contrib.staticfiles',

    'energygraph.store',

    'south'
)

# APPEND_SLASH=False

import secrets

if secrets.key != None :
    SECRET_KEY = secrets.key

if secrets.dbPasswd != None :
    DATABASES[ 'default' ][ 'PASSWORD' ] = secrets.dbPasswd
    
#Register database schemes in URLs.
urlparse.uses_netloc.append('postgres')
urlparse.uses_netloc.append('mysql')

try:
    # Check to make sure DATABASES is set in settings.py file.
    # If not default to {}

    if 'DATABASES' not in locals():
        DATABASES = {}

    if 'DATABASE_URL' in os.environ:
        url = urlparse.urlparse(os.environ['DATABASE_URL'])

        # Ensure default database exists.
        DATABASES['default'] = DATABASES.get('default', {})

        # Update with environment configuration.
        DATABASES['default'].update({
            'NAME': url.path[1:],
            'USER': url.username,
            'PASSWORD': url.password,
            'HOST': url.hostname,
            'PORT': url.port,
        })
        if url.scheme == 'postgres':
            DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql_psycopg2'

        if url.scheme == 'mysql':
            DATABASES['default']['ENGINE'] = 'django.db.backends.mysql'
except Exception:
    print 'Unexpected error:', sys.exc_info()


LOGGING = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
            },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/tmp/energygraph.log',
            'formatter': 'simple'
            },
        },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
            },
        'django.request': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
            },
        'django.db.backends': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
            },
        'energygraph': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
            },
        }
    }

if DEBUG:
    # make all loggers use the console.
    for logger in LOGGING['loggers']:
        LOGGING['loggers'][logger]['handlers'] = ['console','file']
        LOGGING['loggers'][logger]['propagate'] = False
    LOGGING['loggers']['django.db.backends']['handlers'] = ['file']


LOGIN_URL = "/accounts/login/"


# Stuff for Celery
BROKER_URL = 'redis://localhost:6379/0'
#BROKER_BACKEND = 'django'
#CELERYD_CONCURRENCY = 1
from store.tasks import *

djcelery.setup_loader()

CELERYBEAT_SCHEDULE = {
    #    "my-store-doTask-shedule": {
    #    "task": "energygraph.store.tasks.doTask",
    #    "schedule": crontab(minute="*/5"), #execute every 5 minute 
    #    "args": ( 42, 66 ),
    #},

    # "my-store-update-hourly-shedule": {
    #    "task": "energygraph.store.tasks.updateHourly",
    #    "schedule": crontab(minute="*/2"), #execute every 2 minute 
    #                                       #"args": ( 42, 66 ),
    #},
}

