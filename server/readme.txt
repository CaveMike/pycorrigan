Pre-requisites:
  - Google App Engine account and app.
  - Google Cloud Message API key.
  - (Optional) Create an app account for your Google App Engine admin account.

Technologies, links, acronymns:
  GAE:
    Google AppEngine
    https://cloud.google.com/appengine/docs/python/

  GCM:
    Google Cloud Messaging (GCM) for use as a C2DM client.
    https://developer.android.com/google/gcm/index.html

  requests:
    Higher-level HTTP library.
    http://docs.python-requests.org/en/latest/

  webapp2:
    Python WSGI-compliant web-framework
    https://webapp-improved.appspot.com/

  jinja2:
    Python templating language.
    http://jinja.pocoo.org/docs/dev/

  unittest2:
    Unit-test runner
    https://pypi.python.org/pypi/unittest2

  webtest:
    Tests WSGI-compliant handlers.
    http://webtest.readthedocs.org/en/latest/

  testbed:
    Simulate AppEngine for testing.
    https://cloud.google.com/appengine/docs/python/tools/localunittesting

  nose:
    Python unit-test runner.
    https://nose.readthedocs.org/en/latest/

  nose-gae:
    nose plugin for GAE.
    https://github.com/sadovnychyi/NoseGAE

  HTTP requests:
    HTTP library.  Used for testing.
    http://docs.python-requests.org/en/latest/

Tools:

Running an app instance on local machine:
  bin/localrun.sh: Run app instance on local machine.
  bin/localshell.py: Connect to app running on local machine.

Running an app instance on appspot:
  bin/remotedeploy.sh: Deploy to app to appspot.
  bin/remoteshell.py: Connect to app running on appspot.
  bin/remotedump.py: Dump objects on remote server using Python and urllib2.

Initialize database:
  bin/fill.sh: Initialize database using CURL.

Both local and remote:
  test/curl/test.sh: Test API using CURL.

Testing:
  To select specific tests with nose, use the following format:
    nosetests-2.7 [options] path-to-py/class/test-member

  For example by file:
    nosetests-2.7 [options] test/localserver/testServer.py
  For example by class:
    nosetests-2.7 [options] test/localserver/testServer.py:LocalServerHtmlTests
  For example by test:
    nosetests-2.7 [options] test/localserver/testServer.py:LocalServerHtmlTests.testDeviceGetHtml

  You can specify one or more patterns:
    nosetests-2.7 [options] test/localserver/testServer.py:LocalServerHtmlTests test/localserver/testServer.py:LocalServerJsonTests

  Simulated Server:
    Requires nose GAE plug-in
    Cannot have local server running.
    Example:
      nosetests-2.7 --with-path=./src --with-path=./cfg --with-gae --gae-application=./src/ --without-sandbox -v test/server/testServer.py:LocalServerTests
  Local Server:
    Requires a real server running locally on localhost:8080
    Example:
      nosetests-2.7 --with-path=./src --with-path=./cfg --without-sandbox -v test/server/testServer.py:LocalServerTests
  Remote Server:
    Requires a real server running on appspot.com
    Example:
      nosetests-2.7 --with-path=./src --with-path=./cfg --without-sandbox -v test/server/testServer.py:RemoteServerTests

  Handlers:
    Performs functional tests on each individual request handlers.
    Uses WebTest to stub out the majority of the web-server.
    Requires the web-server to be WSIG-compliant.
    Does not require the web-server to be started.
    Uses the GAE testbed which stubs out GAE sub-systems (e.g. datastore, user, memcache, etc.)
    Cannot have local server running.
    Example:
      nosetests-2.7 --with-path=./src --with-path=./cfg --with-gae --gae-application=./src/ --without-sandbox -v test/handlers/

Class Diagram:

Device: A NDB model implementation of a device.  This allows a Device to be read and written to an NDB store.
JsonDeviceAdapter: An adapter between JSON and a Device object.  This implements the 8 primitives that a JSON Handler needs to create, update, delete, and list one or more Device objects.

GenericHandlerJson and GenericParentHandlerJson: These handlers can interface to any object that implments a corresponding JSON Adapter (with the 8 primitives).  GenericHandlerJson interfaces to a single object while GenericParentHandlerJson interfaces to a collection of objects.
DeviceHandlerJson and DevicesHandlerJson: These are specializations of GenericHandlerJson and GenericParentHandlerJson.
MainHandler: This dispatches to DeviceHandlerJson and DevicesHandlerJson based on the URL.

                                                     ndb.Model
                                                        o
                                                        |
                                                        |
                                                      Device
                                                        ^
                                                        |
                                                        |
                                                  GenericAdapter
                                                        ^
                        /------------------------------/ \------------------------------------\
                        |           |                                         |               |
                       /             \                                        |               |
 GenericParentHandlerJson           GenericHandlerJson        GenericParentHandlerHtml      GenericHandlerHtml
   o                                        o                                 |               |
   |                                        |                                 |               |
   |                                        |                                 |               |
 DevicesHandlerJson                 DeviceHandlerJson         DevicesHandlerHtml             DeviceHandlerHtml
            |                                |                      |                                |
            | /devices/                      | /devices/id/         | /devices/                      | /devices/id/
            |                                |                      |                                |
            |                                \--------\    /--------/                                |
            \---------------------------------------\ |    | /---------------------------------------/
                                                    | |    | |
                                                    MainHandler
                                                        |
                                                        |
                                                        o
                                             webapp2.RequestHandler


URL mapping:

USER:
read one:
  GET /user/<user_id>/
    Accept: application/json
read all:
  GET /user/
    Accept: application/json

publish:
  POST /user/<key>/message/
    body

DEVICE:
read one:
  GET /device/<dev_id>/
    Accept: application/json
read all:
  GET /device/
    Accept: application/json

create:
  POST /device/
    Content-Type: application/json
    name = if specified otherwise from GAE
    email = from GAE
    user_id = from GAE
    dev_id
    reg_id
    type = ac2dm

update:
  PUT /device/<dev_id>/
    Content-Type: application/json
    name = if specified otherwise from GAE
    dev_id
    reg_id
    type

delete:
  DELETE /device/<dev_id>/
delete all:
  DELETE /device/

publish:
  POST /device/<key>/message/
    body


PUBLICATION:
read one:
  GET /publication/<key>/
    Accept: application/json
read all:
  GET /publication/
    Accept: application/json

create:
  POST /publication/
    Content-Type: application/json
    topic
    description

update:
  PUT /publication/<key>/
    Content-Type: application/json
    topic
    description

delete:
  DELETE /publication/<key>/
delete all:
  DELETE /publication/

publish:
  POST /publication/<key>/message/
    body

SUBSCRIPTION:
read one:
  GET /subscription/<key>/
    Accept: application/json
read all:
  GET /subscription/
    Accept: application/json

create:
  POST /subscription/
    Content-Type: application/json
    publication_key
    dev_id

delete:
  DELETE /subscription/<key>/
delete all:
  DELETE /subscription/



TODO:
  put objects in a hierarchy inside ndb.
  move subscription under publication
  create fields.py with validators, regexes, etc.
  create user object if not present when creating device object?
  support broadcast for all user and devices?
  look up sender info in gcm send?
