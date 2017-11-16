#!/usr/bin/env python
import getpass

from google.appengine.ext.remote_api import remote_api_stub

from deploy import Deploy

remote_api_stub.ConfigureRemoteApi(None, '/_ah/remote_api', lambda: (Deploy.GAE_ADMIN, Deploy.GAE_APP_PASSWORD), Deploy.GAE_REMOTE_SERVER)
#remote_api_stub.ConfigureRemoteApi(None, '/_ah/remote_api', lambda: (raw_input('Admin User: '), getpass.getpass('App Password: ')), Deploy.GAE_REMOTE_SERVER)
