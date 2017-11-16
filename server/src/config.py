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

CONFIG_KEYS = ('name', 'gcm_api_key', 'user_id', 'created', 'modified', 'revision', 'key')

class Config(ndb.Model):
    ROOT_KEY = ndb.Key('Config', 'configs')

    # HTML formatting.
    KEYS = CONFIG_KEYS
    KEYS_WRITABLE = CONFIG_KEYS[:2]
    KEYS_READONLY = CONFIG_KEYS[2:]
    ROWS = {}
    COLUMNS = {}

    name = ndb.StringProperty(required=True, validator=Fields.validate_not_empty)
    gcm_api_key = ndb.StringProperty(default='', required=True)
    user_id = ndb.StringProperty(required=True, validator=Fields.validate_not_empty)
    created = ndb.DateTimeProperty(auto_now_add=True, required=True)
    modified = ndb.DateTimeProperty(auto_now=True, required=True)
    revision = ndb.IntegerProperty(default=0, required=True)

    @staticmethod
    def load(obj, request=None, body=None):
        logging.getLogger().debug('request=' + str(request) + ', body=' + str(body))

        j = Fields.parse_json(body)

        obj.name = Fields.extract('name', request, j)
        obj.gcm_api_key = Fields.extract('gcm_api_key', request, j)
        obj.user_id = Fields.sanitize_user_id(users.get_current_user().user_id())

        logging.getLogger().debug('obj=' + str(obj))

    @staticmethod
    def query_by_id(id):
        return Config.query(Config.name == id, ancestor=Config.ROOT_KEY).order(-Config.modified).fetch(keys_only=True)

    def get_id(self):
        return self.name

    @staticmethod
    def url_name(prefix='', suffix=''):
        return prefix + '/config/' + suffix

    def get_link(self):
        return self.url_name() + self.get_id() + '/'

    def redirect_url(self):
        return '/config/'

    @classmethod
    def get_master_db(cls, id='active'):
        keys = cls.query_by_id(id)
        if not keys:
            logging.getLogger().error('no objects found')
            return None

        if len(keys) > 1:
            logging.getLogger().error('too many objects found')
            return None

        obj = keys[0].get()
        if not obj:
            logging.getLogger().error('object not read')
            return None

        return obj

    @staticmethod
    def get_routes(base_url=''):
        return [ \
        # JSON (parent)
        ContentRoute(template=Config.url_name(base_url), handler=ConfigsHandlerJson,
            header='Accept', header_values=('application/json',),
            methods=('GET',)),
        ContentRoute(template=Config.url_name(base_url), handler=ConfigsHandlerJson,
            header='Content-Type', header_values=('application/json',),
            methods=('POST', 'PUT')),
        ContentRoute(template=Config.url_name(base_url), handler=ConfigsHandlerJson,
            methods=('DELETE')),

        # JSON (child)
        ContentRoute(template=Config.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=ConfigHandlerJson,
            header='Accept', header_values=('application/json',),
            methods=('GET',)),
        ContentRoute(template=Config.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=ConfigHandlerJson,
            header='Content-Type', header_values=('application/json',),
            methods=('POST', 'PUT')),
        ContentRoute(template=Config.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=ConfigHandlerJson,
            methods=('DELETE')),

        # HTML (parent)
        ContentRoute(template=Config.url_name(base_url), handler=ConfigsHandlerHtml,
            header='Accept', header_values=('text/html',),
            methods=('GET',)),
        ContentRoute(template=Config.url_name(base_url), handler=ConfigsHandlerHtml,
            #header='Content-Type', header_values=('application/x-www-form-urlencoded',),
            methods=('POST')),

        # HTML (child)
        ContentRoute(template=Config.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=ConfigHandlerHtml,
            header='Accept', header_values=('text/html',),
            methods=('GET',)),
        ContentRoute(template=Config.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=ConfigHandlerHtml,
            #header='Content-Type', header_values=('application/x-www-form-urlencoded',),
            methods=('POST',)),
        ]

class ConfigsHandlerJson(GenericParentHandlerJson):
    def __init__(self, request, response):
        super(ConfigsHandlerJson, self).__init__(request, response, GenericAdapter(Config))

class ConfigHandlerJson(GenericHandlerJson):
    def __init__(self, request, response):
        super(ConfigHandlerJson, self).__init__(request, response, GenericAdapter(Config))

class ConfigsHandlerHtml(GenericParentHandlerHtml):
    def __init__(self, request, response):
        super(ConfigsHandlerHtml, self).__init__(request, response, GenericAdapter(Config))

class ConfigHandlerHtml(GenericHandlerHtml):
    def __init__(self, request, response):
        super(ConfigHandlerHtml, self).__init__(request, response, GenericAdapter(Config))


Config.get_master_db()
