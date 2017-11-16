import hashlib
import json
import logging
import re

class Fields(object):
    USER_ID_SALT = 'tvpd$wo8'

    @staticmethod
    def sanitize_user_id(value):
        value = value.strip()
        value = hashlib.sha512(Fields.USER_ID_SALT + value).hexdigest()
        return value

    @staticmethod
    def validate_not_empty(prop, value):
        if not value:
            raise TypeError('expected a non-empty string, for %s' % repr(prop))

        return value.strip()

    @staticmethod
    def validate_email(prop, value):
        result = re.match('^\s*([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,6})\s*$', value, flags=re.IGNORECASE)
        if not result:
            raise TypeError('expected an email address, got %s' % repr(value))

        return result.group(0)

    @staticmethod
    def validate_reg_id(prop, value):
        result = re.match('^\s*([a-zA-Z0-9_\-]+)\s*$', value, flags=re.IGNORECASE)
        if not result:
            raise TypeError('expected a reg_id, got %s' % repr(value))

        return result.group(0)

    @staticmethod
    def validate_dev_id(prop, value):
        result = re.match('^\s*([a-f0-9]+)\s*$', value, flags=re.IGNORECASE)
        if not result:
            raise TypeError('expected a dev_id, got %s' % repr(value))

        return result.group(0)

    @staticmethod
    def parse_json(body):
        j = None

        if body:
            try:
                j = json.loads(body)
            except ValueError:
                pass

        logging.getLogger().debug('j=' + str(j) )
        return j

    @staticmethod
    def extract(field, request, j, default=None):
        value = None

        if j:
            try:
                value = j[field]
            except KeyError:
                pass

        if not value and request:
            value = request.get(field)

        if not value:
            value = default

        return value