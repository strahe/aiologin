import asyncio
from urllib.parse import parse_qs

from aiohttp import web
from aiohttp_session import SimpleCookieStorage, session_middleware

# noinspection PyUnresolvedReferences
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
        return True


# noinspection PyUnusedLocal
async def auth_by_header(request, key):
    if key == '1234567890':
        return User('user@sample.com', 'blueberry')
    return None


# noinspection PyUnusedLocal
async def auth_by_session(request, profile):
    email, password = profile.get('email', None), profile.get('password', None)
    if email == 'user@sample.com' and password == 'blueberry':
        return User(profile['email'], profile['password'])
    return None


# noinspection PyUnusedLocal
async def auth_by_form(request):
    args = parse_qs(request.query_string)
    email, password = args.get('email', [''])[0], args.get('password', [''])[0]
    if email == 'user@sample.com' and password == 'blueberry':
        return User(email, password)
    return None


# noinspection PyUnusedLocal
@asyncio.coroutine
def func0(request):
    print("login event #1")


# noinspection PyUnusedLocal
@asyncio.coroutine
def func1(request):
    print("login event #2")


# noinspection PyUnusedLocal
@asyncio.coroutine
def func2(request):
    print("handler")


# noinspection PyUnusedLocal
@asyncio.coroutine
def func3(request):
    print("authenticated")


# noinspection PyUnusedLocal
@asyncio.coroutine
def func4(request):
    print("forbidden")


# noinspection PyUnusedLocal
@asyncio.coroutine
def func5(request):
    print("unauthorized")


# noinspection PyUnusedLocal
@aiologin.secured
async def handler(request):
    return web.Response(text="OK")


async def login(request):
    # remember is false you should add your own functionality
    await request.aiologin.authenticate(remember=False)
    return web.Response(text="logged in")


async def logout(request):
    await request.aiologin.logout()
    return web.Response(text="logged out")


app = web.Application(middlewares=[
    session_middleware(SimpleCookieStorage())
])
aiologin.setup(
    app=app,
    auth_by_form=auth_by_form,
    auth_by_header=auth_by_header,
    auth_by_session=auth_by_session,
    signals=[
        (aiologin.ON_LOGIN, func0),
        (aiologin.ON_LOGIN, func1),
        (aiologin.ON_LOGOUT, func2),
        (aiologin.ON_AUTHENTICATED, func3),
        (aiologin.ON_FORBIDDEN, func4),
        (aiologin.ON_UNAUTHORIZED, func5)
    ]
)

app.router.add_route('GET', '/', handler)
app.router.add_route('GET', '/login', login)
app.router.add_route('GET', '/logout', logout)


# noinspection PyShadowingNames
async def init(loop, app):
    print("------ Connecting to 0.0.0.0:8080 --- press CTRL+C to quit ------")
    return await loop.create_server(app.make_handler(), '0.0.0.0', 8080)


loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop, app))

try:
    loop.run_forever()
except KeyboardInterrupt:
    pass
