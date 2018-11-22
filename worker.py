import boto3
from botocore.vendored import requests
from botocore.exceptions import ClientError
import tornado.ioloop
from tornado.escape import json_decode
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from jinja2 import Environment, FileSystemLoader

import os

from ec_generator import ECGenerator
import settings


def work():
    pending_tasks = sqs_queue.receive_messages(
        MaxNumberOfMessages=1,
        WaitTimeSeconds=20
    )
    for task in pending_tasks:
        try:
            body = json_decode(task.body)
        except ValueError:
            pass
        else:
            email = body.get('email')

            response = requests.get(
                settings.API_URL + body.get('doc_type') + '/' +
                body.get('doc_number') + '/' + body.get('period')
            )
            if response.status_code != 200:
                continue
            data = response.json()
            _user_type = 'premium' if data.get('tipoAfiliado') == 'P' \
                else 'normal'
            _type = 'flujo' if data.get(
                'tipoComision'
            ).lower() == u'remuneraci\xf3n' else 'mixto'

            ec = ECGenerator(_type, _user_type)
            ec.render(data)
            res = ec.export(True, body.get('doc_number'))

        try:
            task.delete()
        except ClientError:
            pass

        msg = MIMEMultipart()
        msg['From'] = '%s <%s>' % (
            settings.EMAIL_FROM_NAME,
            settings.EMAIL_FROM
        )
        msg['To'] = email
        msg['Subject'] = settings.EMAIL_SUBJECT
        msg.attach(MIMEText(
            _template_env.get_template(
                'mail_%s.html' % _user_type
            ).render(),
            'html',
            'utf-8'
        ))

        part = MIMEApplication(res, Name='estadodecuenta.pdf')
        part['Content-Disposition'] = 'attachment; filename=estadodecuenta.pdf'
        part['Content-Type'] = 'application/pdf'
        msg.attach(part)

        ses.send_raw_email(Source=msg['From'], Destinations=[msg['To']],
                           RawMessage={'Data': msg.as_string()})


if __name__ == '__main__':
    _template_env = Environment(
        loader=FileSystemLoader(
            os.path.join(os.path.dirname(__file__), 'templates')
        ),
        auto_reload=settings.DEBUG,
        extensions=['jinja2.ext.do']
    )
    sqs = boto3.resource('sqs')
    sqs_queue = sqs.get_queue_by_name(
        QueueName=os.environ.get('SQS_QUEUE_NAME')
    )
    ses = boto3.client('ses')
    scheduler = tornado.ioloop.PeriodicCallback(work, 700)
    scheduler.start()
    tornado.ioloop.IOLoop.instance().start()
