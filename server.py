import tornado.web
import tornado.httpclient
from tornado.gen import coroutine
from tornado.options import define, options, parse_command_line
from tornado.escape import json_encode, json_decode
from sqlalchemy import create_engine, func, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import SQLAlchemyError
import boto3

import settings
import models
from ec_generator import ECGenerator

import os
import urllib


global_settings = dict((setting.lower(), getattr(settings, setting))
                       for setting in dir(settings) if setting.isupper())


class Application(tornado.web.Application):

    def __init__(self, handlers=None, default_host='', transforms=None,
                 **settings):
        super(Application, self).__init__(handlers, default_host, transforms,
                                          **settings)
        self._db_engine = create_engine(
            self.settings.get('database_dsn'),
            pool_recycle=3600,
            echo=self.settings.get('debug')
        )


class RequestHandler(tornado.web.RequestHandler):

    def __init__(self, application, request, **kwargs):
        self._db = None
        self._http_client = None
        self._sqs = None
        super(RequestHandler, self).__init__(application, request, **kwargs)

    @property
    def sqs(self):
        if not self._sqs:
            self._sqs = boto3.resource('sqs')
        return self._sqs

    @property
    def sqs_queue(self):
        return self.sqs.get_queue_by_name(
            QueueName=os.environ.get('SQS_QUEUE_NAME')
        )

    @property
    def db(self):
        if not self._db:
            self._db = sessionmaker(
                bind=self.application._db_engine
            )()
        return self._db

    @property
    def http_client(self):
        if self._http_client is None or self._http_client._closed:
            self._http_client = tornado.httpclient.AsyncHTTPClient()
        return self._http_client

    def on_finish(self):
        if self._db:
            self._db.close()
            self._db = None
        if self._http_client:
            self._http_client.close()
            self._http_client = None


class BulkGenerateECURL(RequestHandler):

    @coroutine
    def post(self):
        ok = True
        data = self.get_argument('data', None)
        if not data:
            self.finish({'ok': False})
            return

        try:
            data = json_decode(data)
        except ValueError:
            self.finish({'ok': False})
            return

        tokens = []
        for item in data:
            if not item.get('doc_type', None) or \
                    not item.get('doc_number', None) or \
                    not item.get('period', None):
                continue
            token = models.Token(item.get('doc_type'), item.get('doc_number'),
                                 item.get('period'))
            self.db.add(token)

            tokens.append(token.token)

        try:
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            ok = False

        res = {'ok': ok}
        if ok:
            res.update({'data': tokens})
        self.finish(res)


class GenerateECURL(RequestHandler):

    def get(self, doc_type, doc_number, period):
        token = models.Token(doc_type, doc_number, period)
        self.db.add(token)

        ok = True
        try:
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            ok = False

        res = {'ok': ok}
        if ok:
            res.update({'token': token.token})
        self.finish(res)


class ViewEC(RequestHandler):

    @coroutine
    def get(self, token):
        try:
            token = self.db.query(
                models.Token.doc_type,
                models.Token.doc_number,
                models.Token.period
            ).filter(
                models.Token.token == token,
                func.now() <= func.date_add(
                    models.Token.created_at,
                    text('interval %s second' % (
                        self.settings.get('token_expiration')
                    ))
                )
            ).one()
        except NoResultFound:
            raise tornado.web.HTTPError(404)

        try:
            response = yield self.http_client.fetch(
                self.settings.get('api_url') + token.doc_type + '/' +
                token.doc_number + '/' + token.period
            )
            if response.error:
                raise tornado.httpclient.HTTPError()
        except tornado.httpclient.HTTPError:
            self.finish('')
            return
        else:
            try:
                data = json_decode(response.body)
            except ValueError:
                self.finish('')
                return

            _user_type = 'premium' if data.get('tipoAfiliado') == 'P' \
                else 'normal'
            _type = 'flujo' if data.get(
                'tipoComision'
            ).lower() == u'remuneraci\xf3n' else 'mixto'

            ec = ECGenerator(_type, _user_type)
            ec.render(data)
            res = ec.export(True, token.doc_number)
            self.set_header('Content-Type', 'application/pdf')
            self.set_header('Content-Length', len(res))
            self.finish(res)


class EmailEC(RequestHandler):

    @coroutine
    def get(self, token):
        ok = True
        try:
            token = self.db.query(
                models.Token.doc_type,
                models.Token.doc_number,
                models.Token.period
            ).filter(
                models.Token.token == token,
                func.now() <= func.date_add(
                    models.Token.created_at,
                    text('interval %s second' % (
                        self.settings.get('token_expiration')
                    ))
                )
            ).one()
        except NoResultFound:
            raise tornado.web.HTTPError(404)

        try:
            response = yield self.http_client.fetch(
                self.settings.get('email_api_url') + '?' +
                urllib.urlencode({
                    'tipoDocumento': token.doc_type,
                    'numeroDocumento': token.doc_number
                })
            )
            if response.error:
                raise tornado.httpclient.HTTPError()
        except tornado.httpclient.HTTPError:
            ok = False
        else:
            try:
                data = json_decode(response.body)
            except ValueError:
                ok = False
            else:
                self.sqs_queue.send_message(
                    MessageBody=json_encode({
                        'doc_type': token.doc_type,
                        'doc_number': token.doc_number,
                        'period': token.period,
                        'email': data.get('EMAIL')
                    })
                )

        self.finish({'ok': ok})


if __name__ == '__main__':
    define('host', default='127.0.0.1', help='host address to listen on')
    define('port', default=8888, type=int, help='port to listen on')

    parse_command_line()
    application = Application(
        (
            tornado.web.url(
                '/bulk-generate',
                BulkGenerateECURL,
                name='bulk_generate_ec_url'
            ),
            tornado.web.url(
                '/generate/(\d{2})/(.*)/(\d{6})',
                GenerateECURL,
                name='generate_ec_url'
            ),
            tornado.web.url(
                '/view/(.*)',
                ViewEC,
                name='view_ec'
            ),
            tornado.web.url(
                '/email/(.*)',
                EmailEC,
                name='email_ec'
            )
        ),
        **global_settings
    )
    application.listen(options.port, options.host, xheaders=True)

    tornado.ioloop.IOLoop.instance().start()
