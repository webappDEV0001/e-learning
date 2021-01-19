import os
import environ

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env()
env.read_env(os.path.join(BASE_DIR, '..', '.env'))

DEBUG = env.bool('DEBUG', default=False)

SECRET_KEY = env('SECRET_KEY', default='CHANGE_ME_IMPORTANT_!!!')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS_LOCAL', default=['*'])

SITE_ID = 1

DATE_FORMAT = '%Y-%m-%d'

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

REST_FRAMEWORK = {
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S'
}

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'users',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'crispy_forms',
    'rest_framework',
    'question',
    'exam',
    'subscription',
    'elearning',
    'presentations',
    'coupon',
    'sites',
    # 'import_export',
    'django.contrib.sitemaps',
]

# IMPORT_EXPORT_USE_TRANSACTIONS = False

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'users.middleware.TimezoneMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'users.context_processors.common',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

#Email Settings
EMAIL_HOST = 'mail.privateemail.com'
EMAIL_HOST_USER = 'noreply@4actuaries.com'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = 'df4tg3FF8fsfq0'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

MEDIA_URL = env('MEDIA_URL', default='/media/')
MEDIA_ROOT = os.path.join(BASE_DIR, '..', 'media')

STATIC_URL = env('STATIC_URL', default='/static/')
STATIC_ROOT = os.path.join(BASE_DIR, '..', 'dist')
STATICFILES_DIRS = [os.path.join(BASE_DIR, '..', 'assets')]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
TEMP_DIR = os.path.join(STATICFILES_DIRS[0], 'temp')
#### Authentication

AUTH_USER_MODEL = 'users.User'

LOGIN_REDIRECT_URL = '/list'

# ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_ADAPTER = 'users.adapter.MyAccountAdapter'
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION=True
ACCOUNT_EMAIL_SUBJECT_PREFIX = "Hello, "


ACCOUNT_FORMS = {
    "login": "users.forms.LoginForm",
    "signup": "users.forms.SignUpForm",
    "change_password": "users.forms.ChangePasswordForm"
}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)


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


#### Crispy Forms

CRISPY_TEMPLATE_PACK = 'bootstrap4'

RECAPTCHA_PRIVATE_KEY = "6LdtPcYUAAAAAM0CcFMRffccvEA0bS8u2mFcaSgq"
RECAPTCHA_PUBLIC_KEY = "6LdtPcYUAAAAAKj3Xhg6_Knz0tsm-f2BB-yGgTub"
RECAPTCHA_VERIFICATION_URL = 'https://www.google.com/recaptcha/api/siteverify'

# STRIPE CREDENTTIALS
STRIPE_PUBLISHABLE_KEY = 'pk_test_51I9phNIpmmNn1DpcqFdIHZH0s55ZkabNmj2sylsyjhJ0PeFFlBNxmWVvM2MbDasa7WG6hij6Z7Sgf0YnJeSWKqMC002v8ZmhFn'
STRIPE_SECRET_KEY = "sk_test_51I9phNIpmmNn1DpcBtceT4CZz9RqDxZ42mIVyUm4BpuXzDGSwBUfi6M6E91gV1w4qr3JQTClaGjjodOTbyZa3IyQ00lbeyWKuz" #Test Key
STRIPE_ENDPOINT_SECRET = "whsec_0ZYlRV2kumPsQGCbiYPqTQsgAu8OL0sg"
STRIPE_PRODUCT_ID = "price_1I9rE0IpmmNn1Dpc9RrTt36O"

# STRIPE ACCESS FOR READ AND WRITE
SOCIALACCOUNT_PROVIDERS = {
    'stripe': {
        'SCOPE': ['read_write'],
    }
}
