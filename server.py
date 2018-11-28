import tornado.web
from tornado.options import define, options, parse_command_line
from jinja2 import Environment, FileSystemLoader
import pdfkit

import os


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

    def render_string(self, template, **kwargs):
        kwargs.update({'handler': self})
        return self.application._template_env.get_template(template)\
            .render(**kwargs)


class ViewEC(RequestHandler):

    def get(self):
        options = {
            'margin-top': '0in',
            'margin-bottom': '0in',
            'margin-left': '0in',
            'margin-right': '0in'
        }
        data = pdfkit.from_string(
            self.render_string('flujo-normal.html'),
            False,
            options=options
        )
        self.set_header('Content-Type', 'application/pdf')
        self.set_header('Content-Length', len(data))
        self.finish(data)


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
            )
        }
    )
    application.listen(options.port, options.host, xheaders=True)

    tornado.ioloop.IOLoop.instance().start()
