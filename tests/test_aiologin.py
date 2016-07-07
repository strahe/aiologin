#!/usr/bin/python3
import unittest
from aiohttp.test_utils import TestClient, AioHTTPTestCase, loop_context
from aiohttp import request
import asyncio
from urllib.parse import parse_qs

from aiohttp import web
from aiohttp_session import session_middleware, SimpleCookieStorage

import aiologin

print("test being run")


class User(aiologin.AbstractUser):

    # User classes should have attributes to be identified with, in this case
    # we use email and password attributes
    def __init__(self, email, password):

        self.email = email
        self.password = password

    # the properties of authenticated and forbidden must be overridden from the
    # parent class or else an exception will be thrown when the class is used
    @property
    def authenticated(self):
        return True

    @property
    def forbidden(self):
        return False
    print("User class made")


# by default these methods are NUll, but you should override these methods and
# pass them to the aiologin class. These two methods have sample forms of
# authorization, but you should have create your own in your own version.
async def auth_by_header(request, key):
    print("inside the auth_by_header method")
    if key == '1234567890':
        return User('Test@User.com', 'foobar')
    return None

async def auth_by_session(request, profile):
    print("inside the auth_by_session method")
    if 'email' in profile and profile['email'] == 'Test@User.com' and \
            'password' in profile and profile['password'] == 'foobar':
        return User(profile['email'], profile['password'])
    return None

# this method is not required by the aiologin class, however you might want to
# use a method like this to authenticate your user
async def auth_by_form(request, email, password):
    print("inside the auth_by_forum method")
    if email == 'Test@User.com' and password == 'foobar':
        return User(email, password)
    return None


@aiologin.secured
async def handler(request):
    print("inside the handler method which is the handler for the '/' route")
    return web.Response(body=b'OK')


async def login(request):
    print("inside the login method which is the handler for the '/login' route")
    args = parse_qs(request.query_string)
    user = await auth_by_form(request, args['email'][0], args['password'][0])
    if user is None:
        raise web.HTTPUnauthorized
    # remember is false by default, but can be set at your discretion
    await request.aiologin.login(user, remember=False)
    return web.Response()


async def logout(request):
    print(
        "inside the logout method which is the handler for the '/logout' route")
    await request.aiologin.logout()
    return web.Response()


# noinspection PyShadowingNames
def test_app_setup():
    print("in the init method")
    app = web.Application(middlewares=[
        session_middleware(SimpleCookieStorage())
    ])
    aiologin.setup(
        app=app,
        auth_by_header=auth_by_header,
        auth_by_session=auth_by_session
    )
    app.router.add_route('GET', '/', handler)
    app.router.add_route('GET', '/login', login)
    app.router.add_route('GET', '/logout', logout)
    print("init is done, loop has been created with all the routes")
    return app

# noinspection PyShadowingNames
async def init_loop(loop, app):
    srv = await loop.create_server(
        app.make_handler(), '0.0.0.0', 8080)
    return srv

app = test_app_setup()
loop = asyncio.get_event_loop()
loop.run_until_complete(init_loop(loop, app))

# try:
#     print("run forever loop is about to start, so the init is done")
#     print("")
#     loop.run_forever()
# except KeyboardInterrupt:
#     pass


from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp import web

class MyAppTestCase(AioHTTPTestCase):

    def get_app(self, loop):
        """
        override the get_app method to return
        your application.
        """
        web.Application(loop=loop)
        self.app = test_app_setup()
        # it's important to use the loop passed here.
        return web.Application(loop=loop)

    # the unittest_run_loop decorator can be used in tandem with
    # the AioHTTPTestCase to simplify running
    # tests that are asynchronous
    # @unittest_run_loop
    # async def test_example(self):
    #     request = await self.client.request("GET", "/")
    #     assert request.status == 200
    #     text = await request.text()
    #     assert "Hello, world" in text

    # a vanilla example
    def test_example(self):
        async def test_get_route():
            url = "localhost:8080" + "/"
            resp = await self.client.request("GET", url, loop=loop)
            assert resp.status == 401
            text = await resp.text()
            assert "Unauthorized" in text

        self.loop.run_until_complete(test_get_route())
