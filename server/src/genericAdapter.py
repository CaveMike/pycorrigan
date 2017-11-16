import logging

from google.appengine.api import users
from google.appengine.ext import ndb

class GenericAdapter(object):
    def __init__(self, cls):
        self.cls = cls

    def list_all(self, request, body=None):
        return self.cls.query(ancestor=self.cls.ROOT_KEY).order(-self.cls.modified).fetch()

    def list_one(self, id, request, body=None):
        keys = self.cls.query_by_id(id)
        if not keys:
            logging.getLogger().error('no objects found')
            return None

        if len(keys) > 1:
            logging.getLogger().error('too many objects found')
#FIXME:            return None

        obj = keys[0].get()
        if not obj:
            logging.getLogger().error('object not read')
            return None

        return obj

    def create_grandchild(self, id, request, body=None):
        # FIXME: Implement
        logging.getLogger().error('not implemented')
        return None

    def create_child(self, request, body):
        obj = self.cls(parent=self.cls.ROOT_KEY)
        self.cls.load(obj, request, body)

        keys = self.cls.query_by_id(obj.get_id())
        logging.getLogger().error('duplicate object')
#FIXME:        return None

        obj.put()
        return obj

    def update_all(self, request, body=None):
        logging.getLogger().error('not implemented')
        return None

    def update_one(self, id, request, body):
        keys = self.cls.query_by_id(id)
        if not keys:
            # TODO: Is the id lost here?
            return self.create_child(request, body)

        if len(keys) > 1:
            logging.getLogger().error('too many objects found')
#FIXME:            return None

        obj = keys[0].get()
        if not obj:
            logging.getLogger().error('object not read')
            return None

        self.cls.load(obj, request, body)

        obj.revision += 1
        obj.put()
        return ''

    def delete_all(self, request, body=None):
        keys = self.cls.query(ancestor=self.cls.ROOT_KEY).fetch(keys_only=True)
        if not keys:
            return ''

        ndb.delete_multi(keys)
        return ''

    def delete_one(self, id, request, body=None):
        keys = self.cls.query_by_id(id)
        if not keys:
            logging.getLogger().error('objects not found')
            return None

        if len(keys) > 1:
            logging.getLogger().error('too many objects found')
#FIXME:            return None

        keys[0].delete()
        return ''

    def parse_template_values(self, request):
        template_values = {}

        if users.get_current_user():
            url = users.create_logout_url('/')
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(request.uri)
            url_linktext = 'Login'

        template_values['url'] = url
        template_values['url_linktext'] = url_linktext

        template_values['keys'] = self.cls.KEYS

        template_values['writable'] = self.cls.KEYS_WRITABLE
        """
        if users.is_current_user_admin():
            template_values['writable'] = self.cls.KEYS
        else:
            template_values['writable'] = self.cls.KEYS_WRITABLE
        """

        template_values['readonly'] = self.cls.KEYS_READONLY
        template_values['rows'] = self.cls.ROWS
        template_values['columns'] = self.cls.COLUMNS

        return template_values

    def redirect_url(self):
        return self.cls.url_name()
