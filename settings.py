DEBUG = False
XSRF_COOKIES = False
DATABASE_DSN = ''

EMAIL_SUBJECT = 'Estado de Cuenta - APP'
EMAIL_FROM = 'estadodecuenta@profuturo.com.pe'
EMAIL_FROM_NAME = 'Profuturo AFP'

TOKEN_EXPIRATION = 60 * 30
API_URL = 'http://apiuatw.profuturo.com.pe/serviciosexternos/srvpf/eecc/'
EMAIL_API_URL = 'http://apiuatw.profuturo.com.pe/serviciosexternos/' \
    'Home/GenClave_DatosBasico/'

try:
    from local_settings import *  # NOQA
except ImportError:
    pass
