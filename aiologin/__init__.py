import asyncio
import types
from abc import ABCMeta, abstractproperty
from collections.abc import MutableMapping

from aiohttp import web
from aiohttp.web_reqrep import Request
from aiohttp_session import get_session

AIOLOGIN_KEY = '__aiologin__'


class AbstractUser(MutableMapping, metaclass=ABCMeta):
    def __iter__(self):
        return self.__dict__.__iter__()

    def __len__(self):
        return len(self.__dict__)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __delitem__(self, key):
        delattr(self, key)

    @abstractproperty
    def authenticated(self):
        return

    @abstractproperty
    def forbidden(self):
        return


class AnonymousUser(AbstractUser):
    @property
    def authenticated(self):
        return False

    @property
    def forbidden(self):
        return False


# noinspection PyUnusedLocal
@asyncio.coroutine
def _unauthorized(*args, **kwargs):
    return web.Response(status=401, body=b'Unauthorized')


# noinspection PyUnusedLocal
@asyncio.coroutine
def _forbidden(*args, **kwargs):
    return web.Response(status=403, body=b'Forbidden')


class AioLogin:
    def __init__(self, request, default_user, key=AIOLOGIN_KEY, disabled=False,
                 forbidden=_forbidden, unauthorized=_unauthorized,
                 anonymous_user=AnonymousUser, session=get_session):
        self._request = request
        self._disabled = disabled
        self._key = key

        self._default_user = default_user
        self._anonymous_user = anonymous_user

        self._session = session
        self._unauthorized = unauthorized
        self._forbidden = forbidden

    @asyncio.coroutine
    def login(self, user):
        assert isinstance(user, AbstractUser), \
            "Expected 'AbstractUser' type but received {}".format(type(user))
        session = yield from self._session(self._request)
        session[self._key] = dict(user)

    @asyncio.coroutine
    def logout(self):
        session = yield from self._session(self._request)
        del session[self._key]

    @asyncio.coroutine
    def current_user(self):
        session = yield from self._session(self._request)
        user_info = session.get(AIOLOGIN_KEY, None)
        if user_info is None:
            user = self.anonymous_user()
        else:
            user = self.default_user(**user_info)

        return user

    @property
    def disabled(self):
        return self._disabled

    @property
    def default_user(self):
        return self._default_user

    @property
    def anonymous_user(self):
        return self._anonymous_user

    @property
    def unauthorized(self):
        return self._unauthorized

    @property
    def forbidden(self):
        return self._forbidden


def setup(app, default_user, **kwargs):
    app.middlewares.append(middleware_factory(
        default_user=default_user, **kwargs
    ))


def middleware_factory(**options):
    # noinspection PyUnusedLocal
    @asyncio.coroutine
    def aiologin_middleware(app, handler):
        @asyncio.coroutine
        def aiologin_handler(*args, **kwargs):
            request = kwargs['request'] if 'request' in kwargs else args[0]
            kwargs = {k: v for (k, v) in kwargs.items() if k != 'request'}

            request.aiologin = AioLogin(request=request, **options)
            return (yield from handler(request=request, **kwargs))

        return aiologin_handler

    return aiologin_middleware


def secured(func):
    @asyncio.coroutine
    def wrapper(*args, **kwargs):
        request = kwargs['request'] if 'request' in kwargs else args[0]
        kwargs = {k: v for (k, v) in kwargs.items() if k != 'request'}
        if not isinstance(request, Request):
            request = args[0].request

        cur_usr = yield from request.aiologin.current_user()
        if request.aiologin.disabled:
            return (yield from func(*args, **kwargs))
        if not cur_usr.authenticated:
            return (yield from request.aiologin.unauthorized(*args, **kwargs))
        if cur_usr.forbidden:
            return (yield from request.aiologin.forbidden(*args, **kwargs))
        return (yield from func(*args, **kwargs))

    return wrapper
