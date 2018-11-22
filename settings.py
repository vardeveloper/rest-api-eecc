import os


DEBUG = False
XSRF_COOKIES = False
DATABASE_DSN = ''

EMAIL_SUBJECT = 'Estado de Cuenta - APP'
EMAIL_FROM = 'estadodecuenta@profuturo.com.pe'
EMAIL_FROM_NAME = 'Profuturo AFP'

_local_path = os.path.dirname(__file__)
STATIC_PATH = os.path.join(_local_path, 'static')
STATIC_URL_PREFIX = '/static/'
TEMPLATE_PATH = os.path.join(_local_path, 'templates')

TOKEN_EXPIRATION = 60 * 30
API_URL = 'http://apiuatw.profuturo.com.pe/serviciosexternos/srvpf/eecc/'
EMAIL_API_URL = 'http://apiuatw.profuturo.com.pe/serviciosexternos/' \
    'Home/GenClave_DatosBasico/'

try:
    from local_settings import *  # NOQA
except ImportError:
    pass
