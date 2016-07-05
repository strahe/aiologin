#!/usr/bin/python3

import unittest
import asyncio
from urllib.parse import parse_qs

from aiohttp import web
from aiohttp_session import session_middleware, SimpleCookieStorage

import aiologin


class User(unittest.TestCase, aiologin.AbstractUser):
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


@aiologin.secured
async def handler(request):
    # print(await request.aiologin.current_user())
    return web.Response(body=b'OK')


async def login(request):
    args = parse_qs(request.query_string)
    user = await auth_by_form(request, args['email'][0], args['password'][0])
    if user is None:
        raise web.HTTPUnauthorized
    await request.aiologin.login(user)
    return web.Response()


async def logout(request):
    await request.aiologin.logout()
    return web.Response()


# noinspection PyShadowingNames
async def init(loop):
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
    srv = await loop.create_server(
        app.make_handler(), '0.0.0.0', 8080)
    return srv


loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

if __name__ == '__main__':
    unittest.main()
