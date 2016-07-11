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


def test_app_setup(loop):
    print("in the init method")
    app = web.Application(loop=loop, middlewares=[
        session_middleware(SimpleCookieStorage())
    ])
    aiologin.setup(
        app=app,
        auth_by_header=auth_by_header,
        auth_by_session=auth_by_session,
        login_signal=[first_message, second_message],
        logout_signal=[third_message],
        secured_signal=[fourth_message],
        auth_by_header_signal=[fifth_message],
        auth_by_session_signal=[sixth_message]
    )
    app.router.add_route('GET', '/', handler)
    app.router.add_route('GET', '/login', login)
    app.router.add_route('GET', '/logout', logout)
    print("init is done, loop has been created with all the routes")
    return app


def test_app_setup_bad(loop):
    app = web.Application(loop=loop, middlewares=[
        session_middleware(SimpleCookieStorage())
    ])
    aiologin.setup(
        app=app,
        auth_by_header=auth_by_header,
        auth_by_session=auth_by_session,
        login_signal=[bad_message, bad_message],
        logout_signal=[bad_message],
        secured_signal=[bad_message],
        auth_by_header_signal=[bad_message],
        auth_by_session_signal=[bad_message]
    )
    app.router.add_route('GET', '/', handler)
    app.router.add_route('GET', '/login', login)
    app.router.add_route('GET', '/logout', logout)
    return app

@asyncio.coroutine
def first_message(request):
    print("signal_login: success")


@asyncio.coroutine
def second_message(request):
    print("two messages in one signaler: success")


def bad_message(request):
    # this should not print
    print("non_coroutine_message :fail")
@asyncio.coroutine
def third_message(request):
    print("signal_logout: success")


@asyncio.coroutine
def fourth_message(request):
    print("signal_secured: success")


@asyncio.coroutine
def fifth_message(request):
    print("signal_auth_by_header: success")


@asyncio.coroutine
def sixth_message(request):
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
            print("if you get a deprecated warning on using Response."
                       "Prepared, that's because the use of web_utils is not "
                       "100% correct by one of the modules we use that in turn "
                       "are importing web_utils ")
            url = "/"
            resp = await self.client.request("GET", url)
            self.assertEqual(resp.status, 401)
            text = await resp.text()
            self.assertEqual(text, "Unauthorized")
            resp.close()
            print("test successful")
        self.loop.run_until_complete(test_home_route_no_login())

        async def test_login_bad():
            print("\n"+"2: testing a bad login attempt")
            url = "/login?email=BadTest@BadUser.com&password=bad"
            resp = await self.client.request("GET", url)
            self.assertEqual(resp.status, 401)
            resp.close()
            text = await resp.text()
            self.assertEqual(text, "401: Unauthorized")
            print("test successful")
        self.loop.run_until_complete(test_login_bad())

        async def test_login_good():
            print("\n" + "3: testing a good login attempt")
            url = "/login?email=Test@User.com&password=foobar"
            resp = await self.client.request("GET", url)
            self.assertEqual(resp.status, 200)
            # the cookie is stored for a home route test later
            self.client.session.cookies.update(resp.cookies)
            resp.close()
            print("test successful")
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
            resp.close()
            print("test successful")
            # this should replace the logged in cookie to the logout cookie
            self.client.session.cookies.update(resp.cookies)
        self.loop.run_until_complete(test_logout())

        async def test_login_home_route_after_logout():
            print("\n" + "6: testing access after logging out")
            url = "/"
            resp = await self.client.request("GET", url)
            self.assertEqual(resp.status, 401)
            text = await resp.text()
            self.assertEqual(text, "Unauthorized")
            print("test successful")
        self.loop.run_until_complete(test_login_home_route_after_logout())


class TestBadSignal(AioHTTPTestCase):
    def get_app(self, loop):
        app = test_app_setup_bad(loop=loop)
        return app

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_bad_signal(self):
        async def test_bad_signal():
            print("\n" + "7: testing what happens when a callback is added to a"
                         " signal that wasn't a coroutine")
            url = "/"
            try:
                resp = await self.client.request("GET", url)
                print("non_coroutine_message: success")
                print("test successful")
                resp.close()
            except TypeError:
                print("non_coroutine_message: fail")


        self.loop.run_until_complete(test_bad_signal())

if __name__ == '__main__':
    unittest.main()
