import unittest2 as unittest

import cookielib
import urllib
import urllib2
import requests
import json

from deploy import Deploy
from testdata import TestData

class Server(object):
    def printResponse(self, response):
        print 'req.method', response.request.method
        print 'req.url', response.request.url
        print 'req.headers', response.request.headers
        print 'req.body', response.request.body
        print 'rsp.history', response.history
        print 'rsp', response
        print 'rsp.headers', response.headers
        print 'rsp.body', response.text
        print 'cookies', requests.utils.dict_from_cookiejar(self.session.cookies)

class LocalServer(Server):
    def setUp(self):
        self.session = requests.session()
        self.loginLogout('Login')

    def tearDown(self):
        self.loginLogout('Logout')

    def loginLogout(self, action):
        values = {
            'email' : Deploy.GAE_ADMIN,
            'admin' : 'True',
            'continue' : self.ROOT_URL,
            'action' : action,
        }
        data = urllib.urlencode(values)

        url = self.ROOT_URL + '/_ah/login'+ '?' + data
        print 'url', url

        response = self.session.get(url=url)

class RemoteServer(Server):
    def setUp(self):
        self.session = requests.session()
        self.authtoken = self.getAuthToken()
        print('authtoken', str(self.authtoken))
        self.getAuthCookie()

    def tearDown(self):
        self.authtoken = None

    def getAuthToken(self):
        AUTH_URI = 'https://www.google.com/accounts/ClientLogin'
        print('AUTH_URI', str(AUTH_URI))

        """
         We use a cookie to authenticate with Google App Engine
         by registering a cookie handler here.  This will automatically store the
         cookie returned when we use urllib2 to open http://*.appspot.com/_ah/login.
        """
        cookiejar = cookielib.LWPCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))
        urllib2.install_opener(opener)

        # Get an AuthToken from Google accounts
        authreq_data = urllib.urlencode({ "Email":   Deploy.GAE_ADMIN,
                                          "Passwd":  Deploy.GAE_APP_PASSWORD,
                                          "service": "ah",
                                          "source":  Deploy.GAE_NAME,
                                          "accountType": Deploy.GAE_ACCOUNT_TYPE })
        print('authreq_data', str(authreq_data))

        auth_req = urllib2.Request(AUTH_URI, data=authreq_data)
        auth_resp = urllib2.urlopen(auth_req)
        auth_resp_body = auth_resp.read()

        # The auth response includes several fields - we're interested in the Auth field.
        auth_resp_dict = dict(x.split('=') for x in auth_resp_body.split('\n') if x)

        authtoken = auth_resp_dict['Auth']
        print('authtoken', str(authtoken))
        return authtoken

    def getAuthCookie(self):
        headers = {
            'Content-Length' : '0',
        }

        params = {
            'auth' : self.authtoken
        }

        response = self.session.post(url=self.ROOT_URL + '/_ah/login', headers=headers, params=params, allow_redirects=False)
        print 'rsp', response
        print 'headers', response.headers
        print 'body', response.text
        self.assertEqual(response.status_code, 302)

class ServerHtmlTests(object):
    def testDeviceGetHtml(self):
        headers = {
            'Accept' : 'text/html',
        }

        TARGET_URL = self.ROOT_URL + '/device/'

        response = self.session.get(url=TARGET_URL, headers=headers, allow_redirects=False)
        self.assertEqual(response.url, TARGET_URL)
        self.assertEqual(response.status_code, requests.codes.ok)
        self.assertTrue('text/html' in response.headers['Content-Type'])

    def testDevicePostHtml(self):
        headers = {
            'Content-Type' : 'application/x-www-form-urlencoded',
        }

        values = {
            'name' : TestData.TEST_DEVICES[0]['name'],
            'dev_id' : TestData.TEST_DEVICES[0]['dev_id'],
            'reg_id' : TestData.TEST_DEVICES[0]['reg_id'],
            'type' : TestData.TEST_DEVICES[0]['type'],
        }

        TARGET_URL = self.ROOT_URL + '/device/'

        response = self.session.post(url=TARGET_URL, headers=headers, data=values, allow_redirects=False)
        self.assertEqual(response.url, TARGET_URL)
        self.assertEqual(response.status_code, 302)

class ServerJsonTests(object):
    def testDevicePutJsonNew(self):
        headers = {
            'Content-Type' : 'application/json',
        }

        values = {
            'name' : TestData.TEST_DEVICES[0]['name'],
            'dev_id' : TestData.TEST_DEVICES[0]['dev_id'],
            'reg_id' : TestData.TEST_DEVICES[0]['reg_id'],
            'type' : TestData.TEST_DEVICES[0]['type'],
        }

        data = json.dumps(obj=values)
        print 'data', data

        TARGET_URL = self.ROOT_URL + '/device/' + values['dev_id'] + '/'

        response = self.session.put(url=TARGET_URL, headers=headers, data=data, allow_redirects=True)
        self.assertEqual(response.url, TARGET_URL)
        self.assertEqual(response.status_code, requests.codes.ok)

    def testDevicePostJson(self):
        headers = {
            'Content-Type' : 'application/json',
        }

        values = {
            'name' : TestData.TEST_DEVICES[0]['name'],
            'dev_id' : TestData.TEST_DEVICES[0]['dev_id'],
            'reg_id' : TestData.TEST_DEVICES[0]['reg_id'],
            'type' : TestData.TEST_DEVICES[0]['type'],
        }

        data = json.dumps(obj=values)
        print 'data', data

        TARGET_URL = self.ROOT_URL + '/device/'

        response = self.session.post(url=TARGET_URL, headers=headers, data=data, allow_redirects=False)
        self.assertEqual(response.url, TARGET_URL)
        self.assertEqual(response.status_code, requests.codes.ok)

    def testDeviceDeleteJson(self):
        TARGET_URL = self.ROOT_URL + '/device/'

        response = self.session.delete(url=TARGET_URL, allow_redirects=False)
        self.assertEqual(response.url, TARGET_URL)
        self.assertEqual(response.status_code, requests.codes.ok)

class LocalServerHtmlTests(ServerHtmlTests, LocalServer, unittest.TestCase):
    ROOT_URL = Deploy.GAE_LOCAL_URL

class LocalServerJsonTests(ServerJsonTests, LocalServer, unittest.TestCase):
    ROOT_URL = Deploy.GAE_LOCAL_URL

class LocalServerTests(LocalServerHtmlTests, LocalServerJsonTests):
    pass

class RemoteServerHtmlTests(ServerHtmlTests, RemoteServer, unittest.TestCase):
    ROOT_URL = Deploy.GAE_REMOTE_URL

class RemoteServerJsonTests(ServerJsonTests, RemoteServer, unittest.TestCase):
    ROOT_URL = Deploy.GAE_REMOTE_URL

class RemoteServerTests(RemoteServerHtmlTests, RemoteServerJsonTests):
    pass

if __name__ == '__main__':
    unittest.main()