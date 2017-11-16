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

UMESSAGE_KEYS = ('to_user_id', 'message', 'user_id', 'created', 'modified', 'revision', 'key')

class UMessage(ndb.Model):
    ROOT_KEY = ndb.Key('UMessage', 'umessages')

    # HTML formatting.
    KEYS = UMESSAGE_KEYS
    KEYS_WRITABLE = UMESSAGE_KEYS[:2]
    KEYS_READONLY = UMESSAGE_KEYS[2:]
    ROWS = {'message' : 80}
    COLUMNS = {'message' : 5}

    to_user_id = ndb.StringProperty(required=True, validator=Fields.validate_not_empty)
    message = ndb.StringProperty(required=True)
    user_id = ndb.StringProperty(required=True, validator=Fields.validate_not_empty)
    created = ndb.DateTimeProperty(auto_now_add=True, required=True)
    modified = ndb.DateTimeProperty(auto_now=True, required=True)
    revision = ndb.IntegerProperty(default=0, required=True)

    @staticmethod
    def load(obj, request=None, body=None):
        logging.getLogger().debug('request=' + str(request) + ', body=' + str(body))

        j = Fields.parse_json(body)

        obj.to_user_id = Fields.extract('to_user_id', request, j)
        obj.message = Fields.extract('message', request, j, 'debug-message')
        obj.user_id = Fields.sanitize_user_id(users.get_current_user().user_id())

        logging.getLogger().debug('obj=' + str(obj))

    def send(self):
        data = {'from-user-id' : str(self.user_id), 'type' : 'user-message', 'context' : str(self.to_user_id), 'message' : self.message}
        logging.getLogger().debug('data=' + str(data))

        gcm.send(data=data, reg_ids=[], dev_ids=[], user_ids=[self.to_user_id])

    @staticmethod
    def query_by_id(id):
        return ( ndb.Key(urlsafe=id), )

    def get_id(self):
        return self.key.urlsafe()

    @staticmethod
    def url_name(prefix='', suffix=''):
        return prefix + '/user/<user_id:[a-f0-9]+>/message/' + suffix

    def get_link(self):
        return '/user/' + str(self.user_id) + '/message/' + str(self.key.urlsafe()) + '/'

    def redirect_url(self):
        return '/user/' + str(self.user_id) + '/'

    @staticmethod
    def get_routes(base_url=''):
        return [ \
        # JSON (parent)
        ContentRoute(template=UMessage.url_name(base_url), handler=UMessagesHandlerJson,
            header='Accept', header_values=('application/json',),
            methods=('GET',)),
        ContentRoute(template=UMessage.url_name(base_url), handler=UMessagesHandlerJson,
            header='Content-Type', header_values=('application/json',),
            methods=('POST', 'PUT')),
        ContentRoute(template=UMessage.url_name(base_url), handler=UMessagesHandlerJson,
            methods=('DELETE')),

        # JSON (child)
        ContentRoute(template=UMessage.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=UMessageHandlerJson,
            header='Accept', header_values=('application/json',),
            methods=('GET',)),
        ContentRoute(template=UMessage.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=UMessageHandlerJson,
            header='Content-Type', header_values=('application/json',),
            methods=('POST', 'PUT')),
        ContentRoute(template=UMessage.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=UMessageHandlerJson,
            methods=('DELETE')),

        # HTML (parent)
        ContentRoute(template=UMessage.url_name(base_url), handler=UMessagesHandlerHtml,
            header='Accept', header_values=('text/html',),
            methods=('GET',)),
        ContentRoute(template=UMessage.url_name(base_url), handler=UMessagesHandlerHtml,
            #header='Content-Type', header_values=('application/x-www-form-urlencoded',),
            methods=('POST')),

        # HTML (child)
        ContentRoute(template=UMessage.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=UMessageHandlerHtml,
            header='Accept', header_values=('text/html',),
            methods=('GET',)),
        ContentRoute(template=UMessage.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=UMessageHandlerHtml,
            #header='Content-Type', header_values=('application/x-www-form-urlencoded',),
            methods=('POST',)),
        ]

class UMessageAdapter(GenericAdapter):
    def create_child(self, request, body=None):
        obj = super(UMessageAdapter, self).create_child(request, body)
        if obj:
            obj.send()

        return obj

class UMessagesHandlerJson(GenericParentHandlerJson):
    def __init__(self, request, response):
        super(UMessagesHandlerJson, self).__init__(request, response, UMessageAdapter(UMessage))

class UMessageHandlerJson(GenericHandlerJson):
    def __init__(self, request, response):
        super(UMessageHandlerJson, self).__init__(request, response, UMessageAdapter(UMessage))

class UMessagesHandlerHtml(GenericParentHandlerHtml):
    def __init__(self, request, response):
        super(UMessagesHandlerHtml, self).__init__(request, response, UMessageAdapter(UMessage))

class UMessageHandlerHtml(GenericHandlerHtml):
    def __init__(self, request, response):
        super(UMessageHandlerHtml, self).__init__(request, response, UMessageAdapter(UMessage))
