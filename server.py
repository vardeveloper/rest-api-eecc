import tornado.web
from tornado.options import define, options, parse_command_line
import tornado.httpclient
from tornado.escape import json_decode
from tornado.gen import coroutine
from jinja2 import Environment, FileSystemLoader
import pdfkit
from PyPDF2 import PdfFileReader, PdfFileWriter
from jose import jwt, ExpiredSignatureError

import os
import functools
from cStringIO import StringIO
from datetime import datetime


def authenticated(method):

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        _token = self.get_argument('token', None)
        if not _token:
            raise tornado.web.HTTPError(404)
        try:
            self._token = jwt.decode(_token, self.public_key,
                                     algorithms=['RS256'])
        except ExpiredSignatureError:
            raise tornado.web.HTTPError(404)
        return method(self, *args, **kwargs)
    return wrapper


class Application(tornado.web.Application):

    def __init__(self, handlers=None, default_host='', transforms=None,
                 **settings):
        super(Application, self).__init__(handlers, default_host, transforms,
                                          **settings)
        self._template_env = Environment(
            loader=FileSystemLoader(self.settings.get('template_path')),
            auto_reload=self.settings.get('debug'),
            extensions=['jinja2.ext.do']
        )


class RequestHandler(tornado.web.RequestHandler):

    _token = None
    _http_client = None

    @property
    def public_key(self):
        _file = os.path.join(self.settings.get('keys_path'), 'public.pem')
        with open(_file, 'rb+') as f:
            return f.read()

    @property
    def http_client(self):
        if self._http_client is None or self._http_client._closed:
            self._http_client = tornado.httpclient.AsyncHTTPClient()
        return self._http_client

    def render_string(self, template, **kwargs):
        kwargs.update({'handler': self})
        return self.application._template_env.get_template(template)\
            .render(**kwargs)

    def get_param(self, container, group_type):
        return list(filter(
            lambda x: x.get('grupoMensaje', '') == group_type,
            container.get('mensajes')
        ))[0].get('mensajes')


class ViewEC(RequestHandler):

    # @authenticated
    @coroutine
    def get(self):
        _doc_type = self.get_argument('doc_type')
        _doc_number = self.get_argument('doc_number')
        _period = self.get_argument('period')
        try:
            datetime.strptime(
                _period,
                '%Y%m'
            )
        except ValueError:
            raise tornado.web.HTTPError(400)

        try:
            req = yield self.http_client.fetch(
                self.settings.get('profuturo_api') +
                _doc_type + '/' + _doc_number + '/' +
                # self._token.get('tipoDocumento') + '/' +
                # self._token.get('user_name') + '/' +
                _period
            )
            if req.error:
                raise tornado.httpclient.HTTPError(500)
            data = json_decode(req.body)
        except (tornado.httpclient.HTTPError, ValueError):
            self.finish('')
            return

        _type = None
        _user_type = None
        if data.get('tipoComision').lower() == u'remuneraci\xf3n':
            _type = 'flujo'
        else:
            _type = 'mixto'

        if data.get('tipoAfiliado').lower() == 'p':
            _user_type = 'premium'
        else:
            _user_type = 'normal'

        _input = StringIO(
            pdfkit.from_string(
                self.render_string(
                    '%s-%s.html' % (_type, _user_type),
                    data=data
                ),
                False,
                options={
                    'page-size': 'A4',
                    'margin-top': '0in',
                    'margin-bottom': '0in',
                    'margin-left': '0in',
                    'margin-right': '0in',
                    'no-outline': None
                }
            )
        )
        _input_reader = PdfFileReader(_input)
        _output_writer = PdfFileWriter()
        _output_writer.appendPagesFromReader(_input_reader)
        # _output_writer.encrypt(self._token.get('user_name'))
        _output = StringIO()
        _output_writer.write(_output)
        _output.seek(0)
        _data = _output.read()
        _input.close()
        _output.close()

        self.set_header('Content-Type', 'application/pdf')
        self.set_header('Content-Length', len(_data))
        self.finish(_data)


class EmailEC(tornado.web.RequestHandler):

    def get(self):
        self.finish('email')


if __name__ == '__main__':
    define('host', default='127.0.0.1', help='host address to listen on')
    define('port', default=8888, type=int, help='port to listen on')

    parse_command_line()
    application = Application(
        (
            tornado.web.url(
                '/view',
                ViewEC,
                name='api_view'
            ),
            tornado.web.url(
                '/email',
                EmailEC,
                name='api_email'
            )
        ),
        **{
            'debug': False,
            'template_path': os.path.join(
                os.path.dirname(__file__),
                'templates'
            ),
            'keys_path': os.path.join(
                os.path.dirname(__file__),
                'keys'
            ),
            'profuturo_api': 'http://apiuatw.profuturo.com.pe/' \
            'serviciosexternos/srvpf/eecc/'
        }
    )
    application.listen(options.port, options.host, xheaders=True)

    tornado.ioloop.IOLoop.instance().start()
