""" Django settings for metro_map_saver project.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''
RECAPTCHA_SECRET_KEY = ''
RECAPTCHA_VALID_THRESHOLD = 0.5

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ADMINS = [
    ('Shannon Turner', 'hello@shannonvturner.com'),
]
MANAGERS = ADMINS

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'email_backend': 'django.core.mail.backends.smtp.EmailBackend',
            'include_html': True
        }
    },
    'loggers': {
        'map_saver.views': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
    }
}

########## EMAIL CONFIGURATION
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.webfaction.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'metromapmaker'
EMAIL_HOST_PASSWORD = ''
EMAIL_SUBJECT_PREFIX = '[metromapmaker] '
SERVER_EMAIL = 'reports@metromapmaker.com'
DEFAULT_FROM_EMAIL = 'reports@metromapmaker.com'
MAILER_LIST = ADMINS
########## END EMAIL CONFIGURATION

ALLOWED_HOSTS = [
    'metromapmaker.com',
    'www.metromapmaker.com',
    'staging.metromapmaker.com',
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'map_saver',
    'taggit',
    'citysuggester',
    'moderate',
    'summary',
    'debug_toolbar',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
]

ROOT_URLCONF = 'metro_map_saver.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'metro_map_saver.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'metromapmaker',
        'USER': 'metromapmaker',
        'PASSWORD': 'metromapmaker',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'use_unicode': True,
        },
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': 'unix:/home/sturner/memcached.sock',
    }
}

CACHE_MIDDLEWARE_SECONDS = 60 * 60 * 24 # 1 day, can override per-view
CACHE_MIDDLEWARE_KEY_PREFIX = 'metromapmaker'

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_ROOT = '/home/sturner/apps/static_metromapmaker/'
STATIC_URL = '/static/'

MEDIA_ROOT = '/home/sturner/apps/static_metromapmaker/media/'
MEDIA_URL = 'media/'
