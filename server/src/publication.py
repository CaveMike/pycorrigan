import hashlib
import json
import logging
import re

from google.appengine.api import users
from google.appengine.ext import ndb

from webapp2 import RequestHandler

from contentRoute import ContentRoute
from fields import *
from genericHandlers import GenericParentHandlerJson
from genericHandlers import GenericHandlerJson
from genericHandlers import GenericParentHandlerHtml
from genericHandlers import GenericHandlerHtml
from genericAdapter import GenericAdapter

PUBLICATION_KEYS = ('topic', 'description', 'user_id', 'created', 'modified', 'revision', 'key')

class Publication(ndb.Model):
    ROOT_KEY = ndb.Key('Publication', 'publications')

    # HTML formatting.
    KEYS = PUBLICATION_KEYS
    KEYS_WRITABLE = PUBLICATION_KEYS[:2]
    KEYS_READONLY = PUBLICATION_KEYS[2:]
    ROWS = {}
    COLUMNS = {}

    topic = ndb.StringProperty(required=True, validator=Fields.validate_not_empty)
    description = ndb.StringProperty(required=True, validator=Fields.validate_not_empty)
    user_id = ndb.StringProperty(required=True, validator=Fields.validate_not_empty)
    created = ndb.DateTimeProperty(auto_now_add=True, required=True)
    modified = ndb.DateTimeProperty(auto_now=True, required=True)
    revision = ndb.IntegerProperty(default=0, required=True)

    @staticmethod
    def load(obj, request=None, body=None):
        logging.getLogger().debug('request=' + str(request) + ', body=' + str(body))

        j = Fields.parse_json(body)

        obj.topic = Fields.extract('topic', request, j, 'debug-topic')
        obj.description = Fields.extract('description', request, j, 'debug-description')
        obj.user_id = Fields.sanitize_user_id(users.get_current_user().user_id())

        logging.getLogger().debug('obj=' + str(obj))

    @staticmethod
    def query_by_id(id):
        return ( ndb.Key(urlsafe=id), )

    def get_id(self):
        return self.key.urlsafe()

    @staticmethod
    def url_name(prefix='', suffix=''):
        return prefix + '/publication/' + suffix

    def get_link(self):
        return self.url_name() + self.get_id() + '/'

    def redirect_url(self):
        return '/publication/'

    @staticmethod
    def get_routes(base_url=''):
        return [ \
        # JSON (parent)
        ContentRoute(template=Publication.url_name(base_url), handler=PublicationsHandlerJson,
            header='Accept', header_values=('application/json',),
            methods=('GET',)),
        ContentRoute(template=Publication.url_name(base_url), handler=PublicationsHandlerJson,
            header='Content-Type', header_values=('application/json',),
            methods=('POST', 'PUT')),
        ContentRoute(template=Publication.url_name(base_url), handler=PublicationsHandlerJson,
            methods=('DELETE')),

        # JSON (child)
        ContentRoute(template=Publication.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=PublicationHandlerJson,
            header='Accept', header_values=('application/json',),
            methods=('GET',)),
        ContentRoute(template=Publication.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=PublicationHandlerJson,
            header='Content-Type', header_values=('application/json',),
            methods=('POST', 'PUT')),
        ContentRoute(template=Publication.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=PublicationHandlerJson,
            methods=('DELETE')),

        # HTML (parent)
        ContentRoute(template=Publication.url_name(base_url), handler=PublicationsHandlerHtml,
            header='Accept', header_values=('text/html',),
            methods=('GET',)),
        ContentRoute(template=Publication.url_name(base_url), handler=PublicationsHandlerHtml,
            #header='Content-Type', header_values=('application/x-www-form-urlencoded',),
            methods=('POST')),

        # HTML (child)
        ContentRoute(template=Publication.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=PublicationHandlerHtml,
            header='Accept', header_values=('text/html',),
            methods=('GET',)),
        ContentRoute(template=Publication.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=PublicationHandlerHtml,
            #header='Content-Type', header_values=('application/x-www-form-urlencoded',),
            methods=('POST',)),
        ]

class PublicationsHandlerJson(GenericParentHandlerJson):
    def __init__(self, request, response):
        super(PublicationsHandlerJson, self).__init__(request, response, GenericAdapter(Publication))

class PublicationHandlerJson(GenericHandlerJson):
    def __init__(self, request, response):
        super(PublicationHandlerJson, self).__init__(request, response, GenericAdapter(Publication))

class PublicationsHandlerHtml(GenericParentHandlerHtml):
    def __init__(self, request, response):
        super(PublicationsHandlerHtml, self).__init__(request, response, GenericAdapter(Publication))

class PublicationHandlerHtml(GenericHandlerHtml):
    def __init__(self, request, response):
        super(PublicationHandlerHtml, self).__init__(request, response, GenericAdapter(Publication))
