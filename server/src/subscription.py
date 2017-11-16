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
from publication import Publication

SUBSCRIPTION_KEYS = ('topic', 'dev_id', 'publication_key', 'user_id', 'created', 'modified', 'revision', 'key')

class Subscription(ndb.Model):
    ROOT_KEY = ndb.Key('Subscription', 'subscriptions')

    # HTML formatting.
    KEYS = SUBSCRIPTION_KEYS
    KEYS_WRITABLE = SUBSCRIPTION_KEYS[:2]
    KEYS_READONLY = SUBSCRIPTION_KEYS[2:]
    ROWS = {}
    COLUMNS = {}

    dev_id = ndb.StringProperty(required=True, validator=Fields.validate_dev_id)
    pub_id = ndb.StringProperty(required=True, validator=Fields.validate_not_empty)
    user_id = ndb.StringProperty(required=True, validator=Fields.validate_not_empty)
    created = ndb.DateTimeProperty(auto_now_add=True, required=True)
    modified = ndb.DateTimeProperty(auto_now=True, required=True)
    revision = ndb.IntegerProperty(default=0, required=True)

    @staticmethod
    def load(obj, request=None, body=None):
        logging.getLogger().debug('request=' + str(request) + ', body=' + str(body))

        j = Fields.parse_json(body)

        # Look up publication.
        topic = Fields.extract('topic', request, j)
        logging.getLogger().debug('topic=' + str(topic))
        if not topic:
            return

        publication_keys = Publication.query(Publication.topic == topic, ancestor=Publication.ROOT_KEY).fetch(keys_only=True)
        logging.getLogger().debug('publication_keys (' + str(len(publication_keys)) + ')=' + str(publication_keys))
        if not publication_keys:
            return

        obj.dev_id = Fields.extract('dev_id', request, j)
        obj.pub_id = publication_keys[0].urlsafe()
        obj.user_id = Fields.sanitize_user_id(users.get_current_user().user_id())

        logging.getLogger().debug('obj=' + str(obj))

    @staticmethod
    def query_by_id(id):
        return ( ndb.Key(urlsafe=id), )

    def get_id(self):
        return self.key.urlsafe()

    @staticmethod
    def url_name(prefix='', suffix=''):
        return prefix + '/subscription/' + suffix

    def get_link(self):
        return self.url_name() + self.get_id() + '/'

    def redirect_url(self):
        return '/subscription/'

    @staticmethod
    def get_routes(base_url=''):
        return [ \
        # JSON (parent)
        ContentRoute(template=Subscription.url_name(base_url), handler=SubscriptionsHandlerJson,
            header='Accept', header_values=('application/json',),
            methods=('GET',)),
        ContentRoute(template=Subscription.url_name(base_url), handler=SubscriptionsHandlerJson,
            header='Content-Type', header_values=('application/json',),
            methods=('POST', 'PUT')),
        ContentRoute(template=Subscription.url_name(base_url), handler=SubscriptionsHandlerJson,
            methods=('DELETE')),

        # JSON (child)
        ContentRoute(template=Subscription.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=SubscriptionHandlerJson,
            header='Accept', header_values=('application/json',),
            methods=('GET',)),
        ContentRoute(template=Subscription.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=SubscriptionHandlerJson,
            header='Content-Type', header_values=('application/json',),
            methods=('POST', 'PUT')),
        ContentRoute(template=Subscription.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=SubscriptionHandlerJson,
            methods=('DELETE')),

        # HTML (parent)
        ContentRoute(template=Subscription.url_name(base_url), handler=SubscriptionsHandlerHtml,
            header='Accept', header_values=('text/html',),
            methods=('GET',)),
        ContentRoute(template=Subscription.url_name(base_url), handler=SubscriptionsHandlerHtml,
            #header='Content-Type', header_values=('application/x-www-form-urlencoded',),
            methods=('POST')),

        # HTML (child)
        ContentRoute(template=Subscription.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=SubscriptionHandlerHtml,
            header='Accept', header_values=('text/html',),
            methods=('GET',)),
        ContentRoute(template=Subscription.url_name(base_url, '<id:[a-zA-Z0-9\-]+>/'), handler=SubscriptionHandlerHtml,
            #header='Content-Type', header_values=('application/x-www-form-urlencoded',),
            methods=('POST',)),
        ]

class SubscriptionsHandlerJson(GenericParentHandlerJson):
    def __init__(self, request, response):
        super(SubscriptionsHandlerJson, self).__init__(request, response, GenericAdapter(Subscription))

class SubscriptionHandlerJson(GenericHandlerJson):
    def __init__(self, request, response):
        super(SubscriptionHandlerJson, self).__init__(request, response, GenericAdapter(Subscription))

class SubscriptionsHandlerHtml(GenericParentHandlerHtml):
    def __init__(self, request, response):
        super(SubscriptionsHandlerHtml, self).__init__(request, response, GenericAdapter(Subscription))

class SubscriptionHandlerHtml(GenericHandlerHtml):
    def __init__(self, request, response):
        super(SubscriptionHandlerHtml, self).__init__(request, response, GenericAdapter(Subscription))
