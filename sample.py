#!/usr/bin/python3

import asyncio
from urllib.parse import parse_qs

from aiohttp import web
from aiohttp_session import session_middleware, SimpleCookieStorage

import aiologin


class User(aiologin.AbstractUser):
    def __init__(self, email, password):
        self.email = email
        self.password = password

    @property
    def authenticated(self):
        return True

    @property
    def forbidden(self):
        return False

async def auth_by_header(request, key):
    if key == '1234567890':
        return User('trivigy@gmail.com', 'blueberry')
    return None

async def auth_by_session(request, profile):
    if 'email' in profile and profile['email'] == 'trivigy@gmail.com' and \
            'password' in profile and profile['password'] == 'blueberry':
        return User(profile['email'], profile['password'])
    return None

async def auth_by_form(request, email, password):
    if email == 'trivigy@gmail.com' and password == 'blueberry':
        return User(email, password)
    return None


@asyncio.coroutine
def first_message(request):
    print("practice signal for login attempt")


@asyncio.coroutine
def second_message(request):
    print("this is the second message added to the login signaler")


@asyncio.coroutine
def third_message(request):
    print("this is the logout message")


@asyncio.coroutine
def fourth_message(request):
    print("This is message prints for a generic security success")


@asyncio.coroutine
def fifth_message(request):
    print("This is message prints only when auth_by_header was successful")


@asyncio.coroutine
def sixth_message(request):
    print("This is message prints only when auth_by_session was successful")


@aiologin.secured
async def handler(request):
    return web.Response(body=b'OK')


async def login(request):
    args = parse_qs(request.query_string)
    user = await auth_by_form(request, args['email'][0], args['password'][0])
    if user is None:
        raise web.HTTPUnauthorized
    # remember is false you should add your own functionality
    await request.aiologin.login(user, remember=False)
    return web.Response()


async def logout(request):
    await request.aiologin.logout()
    return web.Response()

app = web.Application(middlewares=[
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

# noinspection PyShadowingNames
async def init(loop, app):
    srv = await loop.create_server(
        app.make_handler(), '0.0.0.0', 8080)
    return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop, app))


try:
    loop.run_forever()
except KeyboardInterrupt:
    pass


