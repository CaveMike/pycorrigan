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

USER_KEYS = ('name', 'description', 'groups', 'email', 'user_id', 'created', 'modified', 'revision', 'key')

class User(ndb.Model):
    ROOT_KEY = ndb.Key('User', 'users')

    # HTML formatting.
    KEYS = USER_KEYS
    KEYS_WRITABLE = USER_KEYS[:3]
    KEYS_READONLY = USER_KEYS[3:]
    ROWS = {'description' : 80}
    COLUMNS = {}

    name = ndb.StringProperty(required=True, validator=Fields.validate_not_empty)
    description = ndb.StringProperty(default='', required=True)
    groups = ndb.StringProperty(default='', required=True)
    email = ndb.StringProperty(required=True, validator=Fields.validate_email)
    user_id = ndb.StringProperty(required=True, validator=Fields.validate_not_empty)
    created = ndb.DateTimeProperty(auto_now_add=True, required=True)
    modified = ndb.DateTimeProperty(auto_now=True, required=True)
    revision = ndb.IntegerProperty(default=0, required=True)

    @staticmethod
    def load(obj, request=None, body=None):
        logging.getLogger().debug('request=' + str(request) + ', body=' + str(body))

        j = Fields.parse_json(body)

        obj.name = Fields.extract('name', request, j, users.get_current_user().nickname())
        obj.description = Fields.extract('description', request, j, 'debug-description')
        obj.groups = Fields.extract('groups', request, j, 'debug-groups')

        obj.email = users.get_current_user().email()
        obj.user_id = Fields.sanitize_user_id(users.get_current_user().user_id())

        logging.getLogger().debug('obj=' + str(obj))

    @staticmethod
    def query_by_id(id):
        return User.query(User.user_id == id, ancestor=User.ROOT_KEY).order(-User.modified).fetch(keys_only=True)

    def get_id(self):
        return self.user_id

    @staticmethod
    def url_name(prefix='', suffix=''):
        return prefix + '/user/' + suffix

    def get_link(self):
        return self.url_name() + self.get_id() + '/'

    def redirect_url(self):
        return '/user/'

    @staticmethod
    def get_routes(base_url=''):
        return [ \
        # JSON (parent)
        ContentRoute(template=User.url_name(base_url), handler=UsersHandlerJson,
            header='Accept', header_values=('application/json',),
            methods=('GET',)),
        ContentRoute(template=User.url_name(base_url), handler=UsersHandlerJson,
            header='Content-Type', header_values=('application/json',),
            methods=('POST', 'PUT')),
        ContentRoute(template=User.url_name(base_url), handler=UsersHandlerJson,
            methods=('DELETE')),

        # JSON (child)
        ContentRoute(template=User.url_name(base_url, '<id:[a-f0-9]+>/'), handler=UserHandlerJson,
            header='Accept', header_values=('application/json',),
            methods=('GET',)),
        ContentRoute(template=User.url_name(base_url, '<id:[a-f0-9]+>/'), handler=UserHandlerJson,
            header='Content-Type', header_values=('application/json',),
            methods=('POST', 'PUT')),
        ContentRoute(template=User.url_name(base_url, '<id:[a-f0-9]+>/'), handler=UserHandlerJson,
            methods=('DELETE')),

        # HTML (parent)
        ContentRoute(template=User.url_name(base_url), handler=UsersHandlerHtml,
            header='Accept', header_values=('text/html',),
            methods=('GET',)),
        ContentRoute(template=User.url_name(base_url), handler=UsersHandlerHtml,
            #header='Content-Type', header_values=('application/x-www-form-urlencoded',),
            methods=('POST')),

        # HTML (child)
        ContentRoute(template=User.url_name(base_url, '<id:[a-f0-9]+>/'), handler=UserHandlerHtml,
            header='Accept', header_values=('text/html',),
            methods=('GET',)),
        ContentRoute(template=User.url_name(base_url, '<id:[a-f0-9]+>/'), handler=UserHandlerHtml,
            #header='Content-Type', header_values=('application/x-www-form-urlencoded',),
            methods=('POST',)),
        ]

class UsersHandlerJson(GenericParentHandlerJson):
    def __init__(self, request, response):
        super(UsersHandlerJson, self).__init__(request, response, GenericAdapter(User))

class UserHandlerJson(GenericHandlerJson):
    def __init__(self, request, response):
        super(UserHandlerJson, self).__init__(request, response, GenericAdapter(User))

class UsersHandlerHtml(GenericParentHandlerHtml):
    def __init__(self, request, response):
        super(UsersHandlerHtml, self).__init__(request, response, GenericAdapter(User))

class UserHandlerHtml(GenericHandlerHtml):
    def __init__(self, request, response):
        super(UserHandlerHtml, self).__init__(request, response, GenericAdapter(User))
