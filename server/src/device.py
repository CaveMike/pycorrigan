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

DEVICE_KEYS = ('name', 'resource', 'type', 'dev_id', 'reg_id', 'user_id', 'created', 'modified', 'revision', 'key')

class Device(ndb.Model):
    ROOT_KEY = ndb.Key('Device', 'devices')

    # HTML formatting.
    KEYS = DEVICE_KEYS
    KEYS_WRITABLE = DEVICE_KEYS[:5]
    KEYS_READONLY = DEVICE_KEYS[5:]
    ROWS = {}
    COLUMNS = {}

    name = ndb.StringProperty(required=True, validator=Fields.validate_not_empty)
    dev_id = ndb.StringProperty(required=True, validator=Fields.validate_dev_id)
    reg_id = ndb.StringProperty(required=True, validator=Fields.validate_reg_id)
    resource = ndb.StringProperty(required=False)
    type = ndb.StringProperty(default='ac2dm', required=True)
    user_id = ndb.StringProperty(required=False, validator=Fields.validate_not_empty)
    created = ndb.DateTimeProperty(auto_now_add=True, required=True)
    modified = ndb.DateTimeProperty(auto_now=True, required=True)
    revision = ndb.IntegerProperty(default=0, required=True)

    #staticmethod
    def load(obj, request=None, body=None):
        logging.getLogger().debug('request=' + str(request) + ', body=' + str(body))

        j = Fields.parse_json(body)

        obj.name = Fields.extract('name', request, j, users.get_current_user().nickname())
        obj.dev_id = Fields.extract('dev_id', request, j, '0123456789abcdef')
        obj.reg_id = Fields.extract('reg_id', request, j, '0123abcd')
        obj.resource = Fields.extract('resource', request, j, 'debug-resource')
        obj.type = Fields.extract('type', request, j, 'debug-type')

        obj.user_id = Fields.sanitize_user_id(users.get_current_user().user_id())

        logging.getLogger().debug('obj=' + str(obj))

    @staticmethod
    def query_by_id(id):
        return Device.query(Device.dev_id == id, ancestor=Device.ROOT_KEY).order(-Device.modified).fetch(keys_only=True)

    def get_id(self):
        return self.dev_id

    @staticmethod
    def url_name(prefix='', suffix=''):
        return prefix + '/device/' + suffix

    def get_link(self):
        return self.url_name() + self.get_id() + '/'

    def redirect_url(self):
        return '/device/'

    @staticmethod
    def get_routes(base_url=''):
        return [ \
        # JSON (parent)
        ContentRoute(template=Device.url_name(base_url), handler=DevicesHandlerJson,
            header='Accept', header_values=('application/json',),
            methods=('GET',)),
        ContentRoute(template=Device.url_name(base_url), handler=DevicesHandlerJson,
            header='Content-Type', header_values=('application/json',),
            methods=('POST', 'PUT')),
        ContentRoute(template=Device.url_name(base_url), handler=DevicesHandlerJson,
            methods=('DELETE')),

        # JSON (child)
        ContentRoute(template=Device.url_name(base_url, '<id:[a-f0-9]+>/'), handler=DeviceHandlerJson,
            header='Accept', header_values=('application/json',),
            methods=('GET',)),
        ContentRoute(template=Device.url_name(base_url, '<id:[a-f0-9]+>/'), handler=DeviceHandlerJson,
            header='Content-Type', header_values=('application/json',),
            methods=('POST', 'PUT')),
        ContentRoute(template=Device.url_name(base_url, '<id:[a-f0-9]+>/'), handler=DeviceHandlerJson,
            methods=('DELETE')),

        # HTML (parent)
        ContentRoute(template=Device.url_name(base_url), handler=DevicesHandlerHtml,
            header='Accept', header_values=('text/html',),
            methods=('GET',)),
        ContentRoute(template=Device.url_name(base_url), handler=DevicesHandlerHtml,
            #header='Content-Type', header_values=('application/x-www-form-urlencoded',),
            methods=('POST')),

        # HTML (child)
        ContentRoute(template=Device.url_name(base_url, '<id:[a-f0-9]+>/'), handler=DeviceHandlerHtml,
            header='Accept', header_values=('text/html',),
            methods=('GET',)),
        ContentRoute(template=Device.url_name(base_url, '<id:[a-f0-9]+>/'), handler=DeviceHandlerHtml,
            #header='Content-Type', header_values=('application/x-www-form-urlencoded',),
            methods=('POST',)),
        ]

class DevicesHandlerJson(GenericParentHandlerJson):
    def __init__(self, request, response):
        super(DevicesHandlerJson, self).__init__(request, response, GenericAdapter(Device))

class DeviceHandlerJson(GenericHandlerJson):
    def __init__(self, request, response):
        super(DeviceHandlerJson, self).__init__(request, response, GenericAdapter(Device))

class DevicesHandlerHtml(GenericParentHandlerHtml):
    def __init__(self, request, response):
        super(DevicesHandlerHtml, self).__init__(request, response, GenericAdapter(Device))

class DeviceHandlerHtml(GenericHandlerHtml):
    def __init__(self, request, response):
        super(DeviceHandlerHtml, self).__init__(request, response, GenericAdapter(Device))
