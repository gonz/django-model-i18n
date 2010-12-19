# -*- coding: utf-8 -*-
from os.path import abspath, dirname, join
import sys

LANGUAGES = (
  ('en', 'English'),
  ('es', 'Español'),
  ('fr', 'Français'),
)
LANGUAGE_CODE = 'en'

### model_i18n settings ###
MODEL_I18N_CONF = 'i18n_conf'
MODEL_I18N_MASTER_LANGUAGE = LANGUAGE_CODE

PROJECT_DIR = dirname(abspath(__file__))
sys.path.append(join(PROJECT_DIR, 'apps'))
sys.path.append(join(PROJECT_DIR, '..'))

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'model_i18n',
    'app',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.request',
)

MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/admin_media/'

ROOT_URLCONF = 'test_project.urls'

SECRET_KEY = '+h78sko_^A,k,sm77^s(CRGsL&^5laxR()/)&1&sw(290nm'

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = '%s/test_project.db' % PROJECT_DIR

DEBUG = True

try:
    from local_settings import *
except ImportError:
    pass
