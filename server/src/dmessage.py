import hashlib
import json
import logging
import re

from google.appengine.api import users
from google.appengine.ext import ndb

from webapp2 import RequestHandler

from contentRoute import ContentRoute
from fields import *
from gcmHelpers import gcm
from genericHandlers import GenericParentHandlerJson
from genericHandlers import GenericHandlerJson
from genericHandlers import GenericParentHandlerHtml
from genericHandlers import GenericHandlerHtml
from genericAdapter import GenericAdapter

DMESSAGE_KEYS = ('dev_id', 'message', 'user_id', 'created', 'modified', 'revision', 'key')

class DMessage(ndb.Model):
    ROOT_KEY = ndb.Key('DMessage', 'dmessages')

    # HTML formatting.
    KEYS = DMESSAGE_KEYS
    KEYS_WRITABLE = DMESSAGE_KEYS[:2]
    KEYS_READONLY = DMESSAGE_KEYS[2:]
    ROWS = {'message' : 80}
    COLUMNS = {'message' : 5}

    dev_id = ndb.StringProperty(required=True, validator=Fields.validate_dev_id)
    message = ndb.StringProperty(required=True)
    user_id = ndb.StringProperty(required=True, validator=Fields.validate_not_empty)
    created = ndb.DateTimeProperty(auto_now_add=True, required=True)
    modified = ndb.DateTimeProperty(auto_now=True, required=True)
    revision = ndb.IntegerProperty(default=0, required=True)

    @staticmethod
    def load(obj, request=None, body=None):
        logging.getLogger().debug('request=' + str(request) + ', body=' + str(body))

        j = Fields.parse_json(body)

        obj.dev_id = Fields.extract('dev_id', request, j)
        obj.message = Fields.extract('message', request, j, 'debug-message')
        obj.user_id = Fields.sanitize_user_id(users.get_current_user().user_id())

        logging.getLogger().debug('obj=' + str(obj))

    def send(self):
        data = {'from-user-id' : self.user_id, 'type' : 'device-message', 'context' : self.dev_id, 'message' : self.message}
        logging.getLogger().debug('data=' + str(data))

        gcm.send(data=data, reg_ids=[], dev_ids=[self.dev_id], user_ids=[])

    @staticmethod
    def query_by_id(id):
        return ( ndb.Key(urlsafe=id), )

    def get_id(self):
        return self.key.urlsafe()

    @staticmethod
    def url_name(prefix='', suffix=''):
        return prefix + '/device/<dev_id:[a-f0-9]+>/message/' + suffix

    def get_link(self):
        return '/device/' + str(self.dev_id) + '/message/' + str(self.key.urlsafe()) + '/'

    def redirect_url(self):
        return '/device/' + str(self.dev_id) + '/'

    @staticmethod
    def get_routes(base_url=''):
        return [ \
        # JSON (parent)
        ContentRoute(template=DMessage.url_name(base_url), handler=DMessagesHandlerJson,
            header='Accept', header_values=('application/json',),
            methods=('GET',)),
        ContentRoute(template=DMessage.url_name(base_url), handler=DMessagesHandlerJson,
            header='Content-Type', header_values=('application/json',),
            methods=('POST', 'PUT')),
        ContentRoute(template=DMessage.url_name(base_url), handler=DMessagesHandlerJson,
            methods=('DELETE')),

        # JSON (child)
        ContentRoute(template=DMessage.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=DMessageHandlerJson,
            header='Accept', header_values=('application/json',),
            methods=('GET',)),
        ContentRoute(template=DMessage.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=DMessageHandlerJson,
            header='Content-Type', header_values=('application/json',),
            methods=('POST', 'PUT')),
        ContentRoute(template=DMessage.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=DMessageHandlerJson,
            methods=('DELETE')),

        # HTML (parent)
        ContentRoute(template=DMessage.url_name(base_url), handler=DMessagesHandlerHtml,
            header='Accept', header_values=('text/html',),
            methods=('GET',)),
        ContentRoute(template=DMessage.url_name(base_url), handler=DMessagesHandlerHtml,
            #header='Content-Type', header_values=('application/x-www-form-urlencoded',),
            methods=('POST')),

        # HTML (child)
        ContentRoute(template=DMessage.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=DMessageHandlerHtml,
            header='Accept', header_values=('text/html',),
            methods=('GET',)),
        ContentRoute(template=DMessage.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=DMessageHandlerHtml,
            #header='Content-Type', header_values=('application/x-www-form-urlencoded',),
            methods=('POST',)),
        ]

class DMessageAdapter(GenericAdapter):
    def create_child(self, request, body=None):
        obj = super(DMessageAdapter, self).create_child(request, body)
        if obj:
            obj.send()

        return obj

class DMessagesHandlerJson(GenericParentHandlerJson):
    def __init__(self, request, response):
        super(DMessagesHandlerJson, self).__init__(request, response, DMessageAdapter(DMessage))

class DMessageHandlerJson(GenericHandlerJson):
    def __init__(self, request, response):
        super(DMessageHandlerJson, self).__init__(request, response, DMessageAdapter(DMessage))

class DMessagesHandlerHtml(GenericParentHandlerHtml):
    def __init__(self, request, response):
        super(DMessagesHandlerHtml, self).__init__(request, response, DMessageAdapter(DMessage))

class DMessageHandlerHtml(GenericHandlerHtml):
    def __init__(self, request, response):
        super(DMessageHandlerHtml, self).__init__(request, response, DMessageAdapter(DMessage))
