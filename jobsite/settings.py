import os
import re
import sys
from pathlib import Path
from django.template import base

MAX_PROMOTED_JOBS = 5

# 250MB-ish
DATA_UPLOAD_MAX_MEMORY_SIZE = 259715200

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Fixes issue with request.is_secure() for unicorn
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = (sys.argv[1] == 'runserver')

ALLOWED_HOSTS = ['.railway.app', '.wechatjobs.com']

CSRF_TRUSTED_ORIGINS = ['https://*.railway.app', 'https://*.wechatjobs.com']

AUTH_USER_MODEL ='jobsboard.SiteUser'

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000


INSTALLED_APPS = [
    'jobsboard',
    'django_countries',
    "phonenumber_field",
    'django_drf_filepond',
    'hitcount',
    'tz_detect',
    'captcha',

    'django.contrib.postgres',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.forms',
    'django.contrib.sitemaps',

    'storages',
    'django_cleanup.apps.CleanupConfig',
    'jobsite.apps.MainAppConfig',
    'csp'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'tz_detect.middleware.TimezoneMiddleware',
    'jobsite.middleware.custom_middleware.InterceptRequestMiddleware',
    'csp.middleware.CSPMiddleware'
]

ROOT_URLCONF = 'jobsite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'jobsite.wsgi.application'

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'railway',
        'USER': 'postgres',
        'PASSWORD': os.getenv('PGPASSWORD'),
        'HOST': 'postgres.railway.internal',
        'PORT': '5432',
        # This connection incurs extra egress costs
        # Must be used to interact with the Shell
        # 'HOST': 'monorail.proxy.rlwy.net',
        # 'PORT': 12477
    }
}



LOGIN_REDIRECT_URL = '/'

# Displays correct error message when account inactive
# But doesn't log them out if they become inactive
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.AllowAllUsersModelBackend',
]



# Static and media file configuration
# STATIC_URL = f'{AWS_S3_URL_PROTOCOL}://{AWS_S3_CUSTOM_DOMAIN}/static/'
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

MEDIA_URL = 'https://candidate-docs-1.s3.amazonaws.com/media/'
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# STATIC_ROOT = BASE_DIR / 'staticfiles'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
# STATIC_ROOT = os.path.join(BASE_DIR, 'static')
# STATIC_URL = 'https://candidate-docs-1.s3.amazonaws.com/static/'




# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True



# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# This isn't working!
DATE_FORMAT = 'D, jS M y, g:i a'
SHORT_DATE_FORMAT = 'jS M y, P'

# for django-countries
COUNTRIES_FIRST = ['US', 'GB', 'CN', 'AU', 'CA', 'NZ', 'IE', 'ZA']
# Need to add the cloudfront distribution
COUNTRIES_FLAG_URL = 'https://d3or71lek9ixz.cloudfront.net/flags/{code}.gif'


EMAIL_BACKEND = 'django_ses.SESBackend'


DJANGO_DRF_FILEPOND_UPLOAD_TMP = os.path.join(BASE_DIR, 'filepond-temp-uploads')
DJANGO_DRF_FILEPOND_STORAGES_BACKEND = 'storages.backends.s3boto3.S3Boto3Storage'


# CELERY_BROKER_URL = "redis://localhost:6379"
# CELERY_RESULT_BACKEND = "redis://localhost:6379"

# Can't get this to work with videos!!
STORAGES = {
    "default": {
        # "BACKEND": "storages.backends.s3.S3Storage",
        "BACKEND": 'storages.backends.s3boto3.S3Boto3Storage',
        "OPTIONS": {
            'access_key': os.getenv('AWS_ACCESS_KEY_ID'),
            'secret_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
            'bucket_name': 'wechatjobs-media',
            'endpoint_url': 'https://s3.ap-east-1.amazonaws.com',
            'region_name': 'ap-east-1',
            'file_overwrite': False,
            'default_acl': 'private',
            'gzip': True,
            'querystring_auth': False
        #   'custom_domain': 'wechatjobs.com'
        },
    },
    "staticfiles": {
        # "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
        "OPTIONS": {
            'access_key': os.getenv('AWS_ACCESS_KEY_ID'),
            'secret_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
            'bucket_name': 'wechatjobs-static',
            'endpoint_url': 'https://s3.ap-east-1.amazonaws.com',
            'region_name': 'ap-east-1',
            'file_overwrite': False,
            'default_acl': 'private',
            'gzip': True,
            'querystring_auth': False,
            # 'custom_domain': 'wechatjobs.com'
            'custom_domain': 'd3or71lek9ixz.cloudfront.net',
        },
    },
}




base.tag_re = re.compile(base.tag_re.pattern, re.DOTALL)


CSRF_COOKIE_SECURE = True

SESSION_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = 15768000

SECURE_HSTS_INCLUDE_SUBDOMAINS = True

SECURE_HSTS_PRELOAD = True

SECURE_SSL_REDIRECT = True


# from csp.constants import SELF, UNSAFE_INLINE, NONE

# CONTENT_SECURITY_POLICY = {
#     "EXCLUDE_URL_PREFIXES": ["/admin"],
#     "DIRECTIVES": {
#         "default-src": [SELF, '*.wechatjobs.com'],
#         "script-src": [SELF, UNSAFE_INLINE, '*.i.posthog.com'],
#         'object-src': [NONE],
#         'connect-src': ['*.i.posthog.com'],
#         "img-src": [SELF, "data:", 'https://s3.ap-east-1.amazonaws.com'],
#         'style-src': [SELF, UNSAFE_INLINE, 'https://fonts.googleapis.com'],
#         'font-src': [SELF, 'https://fonts.googleapis.com', 'https://fonts.gstatic.com']
#     },
# }
