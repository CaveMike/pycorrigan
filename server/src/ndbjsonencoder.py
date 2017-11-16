import cgi
import datetime
import json
import logging
import re
import urllib
import os

from google.appengine.api import users
from google.appengine.ext import ndb

class NdbJsonEncoder(json.JSONEncoder):
    def default(self, o):
        # If this is a key, grab the actual model.
        if isinstance(o, ndb.Key):
            o = o.get()

        if isinstance(o, ndb.Model):
            return o.to_dict()
        elif isinstance(o, users.User):
            return o.email()
        elif isinstance(o, (datetime.datetime, datetime.date, datetime.time)):
            return str(o)
        return json.JSONEncoder.default(self, o)