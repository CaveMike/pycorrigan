import json
import webapp2
import webtest
import unittest2 as unittest

from google.appengine.ext import testbed

from ndbjsonencoder import NdbJsonEncoder
from deploy import Deploy
from device import Device
from device import DeviceHandlerJson
from helpers import setCurrentUser
from testdata import TestData

class DeviceHandlerJsonTest(unittest.TestCase):
    def setUp(self):
        # Create a WSGI application.
        app = webapp2.WSGIApplication([ \
            webapp2.Route('/<id:.*>/', DeviceHandlerJson) \
        ])

        setCurrentUser(email=Deploy.GAE_ADMIN, user_id='1234', is_admin=True)

        # Wrap the app with WebTest's TestApp.
        self.testapp = webtest.TestApp(app)
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_user_stub()
        self.testbed.init_memcache_stub()

        test = TestData.TEST_DEVICES[0]
        self.device = Device(parent=Device.ROOT_KEY, name=test['name'], reg_id=test['reg_id'], dev_id=test['dev_id'], resource=test['resource'], type=test['type'])
        self.key = self.device.put()

    def tearDown(self):
        self.testbed.deactivate()

    def testDeviceHandlerJsonGet200(self):
        headers = {
            'Accept' : 'application/json',
        }

        response = self.testapp.get(url='/' + self.device.dev_id + '/', headers=headers)
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.content_type, headers['Accept'])
        self.assertEqual(response.body, json.dumps(obj=self.device, cls=NdbJsonEncoder))

    def testDeviceHandlerJsonPost501(self):
        self.assertRaises(webtest.app.AppError, self.testapp.post,
            url='/' + self.device.dev_id + '/')

    def testDeviceHandlerJsonPut(self):
        self.device.name = 'new name'
        response = self.testapp.put(url='/' + self.device.dev_id + '/',
            content_type='application/json',
            params=json.dumps(obj=self.device, cls=NdbJsonEncoder))
        self.assertEqual(response.status_int, 200)
        self.assertTrue(response.body)

    def testDeviceHandlerJsonPutNew(self):
        # Remove default test entry.
        self.key.delete()
        self.key = None

        response = self.testapp.put(url='/' + self.device.dev_id + '/',
            content_type='application/json',
            params=json.dumps(obj=self.device, cls=NdbJsonEncoder))
        self.assertEqual(response.status_int, 200)
        self.assertTrue(response.body)

    def testDeviceHandlerJsonDelete(self):
        response = self.testapp.delete(url='/' + self.device.dev_id + '/')
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.content_type, 'application/json')

    def estDevicePublishHandlerJsonPost(self):
        p = { 'dev_id' : self.device.dev_id, 'message' : 'test' }
        response = self.testapp.post(url='/' + self.device.dev_id + '/publish/',
            content_type='application/json',
            params=json.dumps(obj=p, cls=NdbJsonEncoder))
        self.assertEqual(response.status_int, 200)
        self.assertTrue(response.body)
        self.assertTrue(False)
