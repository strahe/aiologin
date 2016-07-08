#!/usr/bin/python3

import asyncio
from urllib.parse import parse_qs

from aiohttp import web
from aiohttp_session import session_middleware, SimpleCookieStorage
import aiologin
import aiologin.signals

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
def message():
    print("practice signal for logout attempt")


@asyncio.coroutine
def second_message():
    print("this is the second message added")

def bad_message():
    print("this should throw an exception if added, but for now it just prints"
          "a warning ")

login_signal = aiologin.signals.LoginSignal('login')
login_signal.add_callback(message)
login_signal.add_callback(second_message)
login_signal.add_callback(bad_message)


@aiologin.secured
async def handler(request):
    # print(await request.aiologin.current_user())
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
    await login_signal.send()
    await request.aiologin.logout()
    return web.Response()

app = web.Application(middlewares=[
    session_middleware(SimpleCookieStorage())
    ])
aiologin.setup(
    app=app, auth_by_header=auth_by_header, auth_by_session=auth_by_session
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

