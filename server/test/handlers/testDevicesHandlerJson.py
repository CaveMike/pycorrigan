import json
import webapp2
import webtest
import unittest2 as unittest

from google.appengine.ext import testbed

from ndbjsonencoder import NdbJsonEncoder
from deploy import Deploy
from device import Device
from device import DevicesHandlerJson
from helpers import setCurrentUser
from testdata import TestData

class DevicesHandlerJsonTest(unittest.TestCase):
    def setUp(self):
        # Create a WSGI application.
        app = webapp2.WSGIApplication([('/', DevicesHandlerJson)])

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
        response = self.testapp.get('/')
        assert response.status_int == 200
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.content_type, 'application/json')

    def testDevicesHandlerPost(self):
        response = self.testapp.post('/',
            content_type='application/json', params=json.dumps(obj=self.device, cls=NdbJsonEncoder))
        assert response.status_int == 200
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.content_type, 'application/json')

    def testDevicesHandlerPost400(self):
        self.assertRaises(webtest.app.AppError, self.testapp.post, url='/')

    def testDevicesHandlerPut(self):
        self.assertRaises(webtest.app.AppError, response=self.testapp.put, url='/')

    def testDevicesHandlerDelete(self):
        response = self.testapp.delete('/')
        assert response.status_int == 200
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.content_type, 'application/json')
