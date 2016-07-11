import asyncio
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
        raise NotImplemented()

    @abstractproperty
    def forbidden(self):
        raise NotImplemented()


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


# noinspection PyUnusedLocal
@asyncio.coroutine
def _void(*args, **kwargs):
    raise NotImplemented()


class AioLogin:
    def __init__(self, request, session_name=AIOLOGIN_KEY, disabled=False,
                 auth_by_header=_void, auth_by_session=_void,
                 forbidden=_forbidden, unauthorized=_unauthorized,
                 anonymous_user=AnonymousUser, session=get_session,
                 login_signal=[], logout_signal=[], secured_signal=[]):
        self._request = request
        self._disabled = disabled
        self._session_name = session_name

        self._anonymous_user = anonymous_user
        self._session = session

        self._auth_by_header = auth_by_header
        self._auth_by_session = auth_by_session
        self._unauthorized = unauthorized
        self._forbidden = forbidden
        self._login_signal = login_signal
        self._logout_signal = logout_signal
        self._secured_signal = secured_signal

    @asyncio.coroutine
    def send_login_signal(self):
        for callback in self._login_signal:
            if asyncio.iscoroutinefunction(callback) or \
                    isinstance(callback, asyncio.Future):
                yield from callback()
            else:
                # not sure what type of exact error to raise, but this one looks
                # good
                raise TypeError

    @asyncio.coroutine
    def send_secured_signal(self):
        for callback in self._secured_signal:
            if asyncio.iscoroutinefunction(callback) or \
                    isinstance(callback, asyncio.Future):
                yield from callback()
            else:
                # not sure what type of exact error to raise, but this one looks
                # good
                raise TypeError

    @asyncio.coroutine
    def send_logout_signal(self):
        for callback in self._logout_signal:
            if asyncio.iscoroutinefunction(callback) or \
                    isinstance(callback, asyncio.Future):
                yield from callback()
            else:
                # not sure what type of exact error to raise, but this one looks
                # good
                raise TypeError

    @asyncio.coroutine
    def login(self, user, remember):
        assert isinstance(user, AbstractUser), \
            "Expected 'AbstractUser' for {} type but received {}".format(
                user, type(user)
            )
        assert isinstance(remember, bool), \
            "Expected 'bool' type for {} but received {}".format(
                remember, type(remember)
            )
        yield from self.send_login_signal()
        session = yield from self._session(self._request)
        session['remember'] = remember
        session[self._session_name] = dict(user)

    @asyncio.coroutine
    def logout(self):
        yield from self.send_logout_signal()
        session = yield from self._session(self._request)
        session.invalidate()

    @asyncio.coroutine
    def auth_by_header(self):
        key = self._request.headers.get('AUTHORIZATION', None)
        if key is None:
            return None
        return (yield from self._auth_by_header(self._request, key))

    @asyncio.coroutine
    def auth_by_session(self):
        session = yield from self._session(self._request)
        profile = session.get(self._session_name, None)
        if profile is None:
            return None

        user = yield from self._auth_by_session(self._request, profile)
        if user is None:
            return None

        session.changed()
        return user

    @property
    def disabled(self):
        return self._disabled

    @property
    def unauthorized(self):
        return self._unauthorized

    @property
    def forbidden(self):
        return self._forbidden

    @property
    def anonymous_user(self):
        return self._anonymous_user


def setup(app, **kwargs):
    app.middlewares.append(middleware_factory(**kwargs))


def middleware_factory(**options):
    # noinspection PyUnusedLocal
    @asyncio.coroutine
    def aiologin_middleware(app, handler):
        @asyncio.coroutine
        def aiologin_handler(*args, **kwargs):
            request = kwargs['request'] if 'request' in kwargs else args[0]
            kwargs = {k: v for (k, v) in kwargs.items() if k != 'request'}

            manager = options.get('manager', AioLogin)
            request.aiologin = manager(request=request, **options)
            return (yield from handler(request=request, **kwargs))

        return aiologin_handler

    return aiologin_middleware


def secured(func):
    @asyncio.coroutine
    def wrapper(*args, **kwargs):
        request = kwargs['request'] if 'request' in kwargs else args[0]
        yield from request.aiologin.send_secured_signal()
        kwargs = {k: v for (k, v) in kwargs.items() if k != 'request'}
        if not isinstance(request, Request):
            request = args[0].request
        else:
            args = (request,) + args
        if request.aiologin.disabled:
            return (yield from func(*args, **kwargs))

        user = yield from request.aiologin.auth_by_header()
        if user is None:
            user = yield from request.aiologin.auth_by_session()
        if user is None:
            user = request.aiologin.anonymous_user()

        assert isinstance(user, AbstractUser), \
            "Expected 'user' of type AbstractUser by got {}".format(type(user))

        if not user.authenticated:
            return (yield from request.aiologin.unauthorized(*args, **kwargs))
        if user.forbidden:
            return (yield from request.aiologin.forbidden(*args, **kwargs))

        request.current_user = user
        return (yield from func(*args, **kwargs))

    return wrapper
