import os


DEBUG = False

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'templates')
KEYS_PATH = os.path.join(os.path.dirname(__file__), 'keys')

DATABASE_DSN = ''

PROFUTURO_API = 'https://profuturomovil.com.pe/serviciosexternos/'

EMAIL_FROM = 'estadodecuenta@profuturo.com.pe'
EMAIL_SUBJECT = u'%s, te enviamos tu Estado de Cuenta del periodo %s'

try:
    from local_settings import *  # noqa
except ImportError:
    pass
