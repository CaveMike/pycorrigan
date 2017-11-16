import webapp2
import webtest
import unittest2 as unittest

from google.appengine.ext import testbed

from deploy import Deploy
from device import Device
from device import DevicesHandlerHtml
from helpers import setCurrentUser
from testdata import TestData

class DevicesHandlerHtmlTest(unittest.TestCase):
    def setUp(self):
        # Create a WSGI application.
        app = webapp2.WSGIApplication(Device.get_routes(), debug=True)

        setCurrentUser(email=Deploy.GAE_ADMIN, user_id='1234', is_admin=True)

        # Wrap the app with WebTest's TestApp.
        self.testapp = webtest.TestApp(app)
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_user_stub()

        test = TestData.TEST_DEVICES[0]
        self.device = Device(parent=Device.ROOT_KEY, name=test['name'], reg_id=test['reg_id'], dev_id=test['dev_id'], resource=test['resource'], type=test['type'])
        self.key = self.device.put()

    def tearDown(self):
        self.testbed.deactivate()

    def testDevicesHandlerGet(self):
        headers = {
            'Accept' : 'text/html',
        }

        response = self.testapp.get('/device/', headers=headers)
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.content_type, 'text/html')

    def testDevicesHandlerPost(self):
        headers = {
            'Content-Type' : 'application/x-www-form-urlencoded',
        }

        params = {
            'name' : TestData.TEST_DEVICES[0]['name'],
            'dev_id' : TestData.TEST_DEVICES[0]['dev_id'],
            'reg_id' : TestData.TEST_DEVICES[0]['reg_id'],
            'type' : TestData.TEST_DEVICES[0]['type'],
        }

        response = self.testapp.post('/device/', headers=headers, params=params)
        self.assertEqual(response.status_int, 302)
        self.assertEqual(response.content_type, 'text/html')

    def testDevicesHandlerPost400(self):
        headers = {
            'Content-Type' : 'application/x-www-form-urlencoded',
        }

        self.assertRaises(webtest.app.AppError, self.testapp.post,
            '/device/', headers=headers)
