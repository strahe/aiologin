import asyncio
import unittest
from urllib.parse import parse_qs

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase
from aiohttp_session import session_middleware, SimpleCookieStorage

import aiologin


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


# by default these methods are NUll, but you should override these methods and
# pass them to the aiologin class. These two methods have sample forms of
# authorization, but you should have create your own in your own version.
async def auth_by_header(request, key):
    if key == '1234567890':
        return User('Test@User.com', 'foobar')
    return None


async def auth_by_session(request, profile):
    if 'email' in profile and profile['email'] == 'Test@User.com' and \
                    'password' in profile and profile['password'] == 'foobar':
        return User(profile['email'], profile['password'])
    return None


# this method is not required by the aiologin class, however it is a good idea
# to use a method like this to authenticate a user
async def auth_by_form(request, email, password):
    if email == 'Test@User.com' and password == 'foobar':
        return User(email, password)
    return None


@aiologin.secured
async def handler(request):
    return web.Response(body=b'OK')


async def login(request):
    args = parse_qs(request.query_string)
    user = await auth_by_form(request, args['email'][0], args['password'][0])
    if user is None:
        raise web.HTTPUnauthorized
    # remember is false by default, but can be set at your discretion
    await request.aiologin.login(user, remember=False)
    return web.Response()


async def logout(request):
    await request.aiologin.logout()
    return web.Response()


def test_app_setup(loop):
    app = web.Application(loop=loop, middlewares=[
        session_middleware(SimpleCookieStorage())
    ])
    aiologin.setup(
        app=app,
        auth_by_header=auth_by_header,
        auth_by_session=auth_by_session,
    )
    # print(app.middlewares)
    aiologin.on_login.append(login_message)
    aiologin.on_login.append(second_message)
    aiologin.on_logout.append(logout_message)
    aiologin.on_secured.append(secured_message)
    aiologin.on_auth_by_header.append(auth_by_header_message)
    aiologin.on_auth_by_session.append(auth_by_session_message)
    aiologin.on_forbidden.append(forbidden_message)
    aiologin.on_unauthenticated.append(unauth_message)
    app.router.add_route('GET', '/', handler)
    app.router.add_route('GET', '/login', login)
    app.router.add_route('GET', '/logout', logout)
    return app


def test_app_setup_bad(loop):
    app = web.Application(loop=loop, middlewares=[
        session_middleware(SimpleCookieStorage())
    ])
    aiologin.setup(
        app=app,
        auth_by_header=auth_by_header,
        auth_by_session=auth_by_session,
    )
    print('app1', id(aiologin))
    app.router.add_route('GET', '/', handler)
    app.router.add_route('GET', '/login', login)
    app.router.add_route('GET', '/logout', logout)
    return app


@asyncio.coroutine
def login_message():
    print("signal_login: success")


@asyncio.coroutine
def second_message():
    print("two messages in one signaler: success")


def bad_message():
    # this should not print
    print("non_coroutine_message :fail")


@asyncio.coroutine
def logout_message():
    print("signal_logout: success")


@asyncio.coroutine
def secured_message():
    print("signal_secured: success")


@asyncio.coroutine
def auth_by_header_message():
    print("signal_auth_by_header: success")

@asyncio.coroutine
def unauth_message():
    print("unauthorized message: success")

@asyncio.coroutine
def forbidden_message():
    print("forbidden_message: success")


@asyncio.coroutine
def auth_by_session_message():
    print("signal_auth_by_session: success")


class TestAioLogin(AioHTTPTestCase):

    def get_app(self, loop):
        app = test_app_setup(loop=loop)
        return app

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_routes(self):
        async def test_home_route_no_login():
            print("\n"+"1: testing access without logging in")
            print("if you get a deprecated warning on using Response.Prepared, "
                  "that's because the use of web_utils is not 100% correct by "
                  "one of the modules we use that in turn is importing "
                  "web_utils ")
            url = "/"
            resp = await self.client.request("GET", url)
            self.assertEqual(resp.status, 401)
            print("test successful")
            resp.close()
        self.loop.run_until_complete(test_home_route_no_login())

        async def test_login_bad():
            print("\n"+"2: testing a bad login attempt")
            url = "/login?email=BadTest@BadUser.com&password=bad"
            resp = await self.client.request("GET", url)
            self.assertEqual(resp.status, 401)
            text = await resp.text()
            self.assertEqual(text, "401: Unauthorized")
            print("test successful")
            resp.close()
        self.loop.run_until_complete(test_login_bad())

        async def test_login_good():
            print("\n" + "3: testing a good login attempt")
            url = "/login?email=Test@User.com&password=foobar"
            resp = await self.client.request("GET", url)
            self.assertEqual(resp.status, 200)
            # the cookie is stored for a home route test later
            self.client.session.cookies.update(resp.cookies)
            print("test successful")
            resp.close()
        self.loop.run_until_complete(test_login_good())

        async def test_home_route_with_login():
            print("\n"+"4: testing the home route after a good login")
            url = "/"
            resp = await self.client.request("GET", url)
            self.assertEqual(resp.status, 200)
            text = await resp.text()
            self.assertEqual(text, "OK")
            print("test successful")
        self.loop.run_until_complete(test_home_route_with_login())

        async def test_logout():
            print("\n"+"5: testing a logout attempt")
            url = "/logout"
            resp = await self.client.request("GET", url)
            self.assertEqual(resp.status, 200)
            print("test successful")
            # this should replace the logged in cookie to the logout cookie
            self.client.session.cookies.update(resp.cookies)
            resp.close()
        self.loop.run_until_complete(test_logout())

        async def test_login_home_route_after_logout():
            print("\n" + "6: testing access after logging out")
            url = "/"
            resp = await self.client.request("GET", url)
            self.assertEqual(resp.status, 401)
            print("test successful")
            resp.close()
        self.loop.run_until_complete(test_login_home_route_after_logout())



# class TestBadSignal(AioHTTPTestCase):
#     def get_app(self, loop):
#         app = test_app_setup_bad(loop=loop)
#         print('app2', id(app))
#         return app
#
#     def setUp(self):
#         super().setUp()
#
#     def tearDown(self):
#         super().tearDown()
#
#     def test_bad_signal(self):
#         async def test_bad_signal():
#             print("\n" + "7: testing what happens when a callback is added to a"
#                          " signal that wasn't a coroutine")
#             url = "/"
#             try:
#                 resp = await self.client.request("GET", url)
#                 print("non_coroutine_message: success")
#                 print("test successful")
#                 resp.close()
#             except TypeError:
#                 print("non_coroutine_message: fail")
#
#         self.loop.run_until_complete(test_bad_signal())

if __name__ == '__main__':
    unittest.main()
