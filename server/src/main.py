import logging
import jinja
import urllib
import webapp2

from google.appengine.api import users
from google.appengine.ext import ndb

from config import Config
from publication import Publication
from subscription import Subscription
from device import Device
from user import User
from umessage import UMessage
from dmessage import DMessage
from pmessage import PMessage

class MainHandler(webapp2.RequestHandler):
    def get(self, *args, **kwargs):
        logging.getLogger().debug('get: args: %s, kwargs: %s' % (args, kwargs))

        template = jinja.get_template('html/home.html')
        result = template.render({})

        self.response.headers['Content-Type'] = 'text/html'
        self.response.write(result)

routes = [webapp2.Route(template='/', handler=MainHandler)]
routes.extend(Config.get_routes())
routes.extend(Publication.get_routes())
routes.extend(Subscription.get_routes())
routes.extend(Device.get_routes())
routes.extend(User.get_routes())
routes.extend(UMessage.get_routes())
routes.extend(DMessage.get_routes())
routes.extend(PMessage.get_routes())

application = webapp2.WSGIApplication(routes, debug=True)
