from common import *

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env()
env.read_env(os.path.join(BASE_DIR, '..', '.env'))

DEBUG = True

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS_LOCAL', default=['*'])

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'elearning',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '',
    }
}
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'elearning',
#         'USER': 'postgres',
#         'PASSWORD': 'silver@123',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }