from common import *

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env()
env.read_env(os.path.join(BASE_DIR, '..', '.env'))

DEBUG = True

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS_STAGE', default=['*'])

DATABASES = {
    'default': env.db('DATABASE_URL_STAGE', default='')
}

