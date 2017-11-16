#!/usr/bin/env python

# From:
#  http://stackoverflow.com/questions/101742/how-do-you-access-an-authenticated-google-app-engine-service-from-a-non-web-py

import cookielib
import json
import os
import urllib
import urllib2

from deploy import Deploy

def get_auth_token():
    AUTH_URI = 'https://www.google.com/accounts/ClientLogin'
    #print('AUTH_URI', str(AUTH_URI))

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
    #print('authreq_data', str(authreq_data))

    auth_req = urllib2.Request(AUTH_URI, data=authreq_data)
    auth_resp = urllib2.urlopen(auth_req)
    auth_resp_body = auth_resp.read()

    # The auth response includes several fields - we're interested in the Auth field.
    auth_resp_dict = dict(x.split("=") for x in auth_resp_body.split("\n") if x)

    authtoken = auth_resp_dict["Auth"]
    #print('authtoken', str(authtoken))
    return authtoken

def get_json(uri, authtoken):
    print('uri', str(uri))

    serv_args = {}
    serv_args['continue'] = uri
    serv_args['auth']     = authtoken
    #print('serv_args', str(serv_args))

    headers = {
        'Accept' : 'application/json',
    }
    #print('headers', str(headers))

    serv_uri = Deploy.GAE_REMOTE_URL + "/_ah/login?%s" % (urllib.urlencode(serv_args))
    #print('serv_uri', str(serv_uri))

    serv_req = urllib2.Request(serv_uri, headers=headers)
    serv_resp = urllib2.urlopen(serv_req)
    serv_resp_body = serv_resp.read()
    #print('serv_resp_body', str(serv_resp_body))

    # serv_resp_body should contain the contents of TARGET_URI as we will have been
    # redirected to that page automatically.

    try:
        j = json.loads(serv_resp_body)

        for i in range(len(j)):
            r = j[i]
            print('[' + str(i) + ']')
            for k in r:
                print('  ' + str(k) + ': ' + str(r[k]))
    except ValueError:
        pass

    print('')

if __name__ == "__main__":
    authtoken = get_auth_token()

    get_json(Deploy.GAE_REMOTE_URL + '/user/', authtoken)
    get_json(Deploy.GAE_REMOTE_URL + '/device/', authtoken)
    get_json(Deploy.GAE_REMOTE_URL + '/publication/', authtoken)
    get_json(Deploy.GAE_REMOTE_URL + '/subscription/', authtoken)