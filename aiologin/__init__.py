import asyncio
from abc import ABCMeta, abstractproperty
from collections.abc import MutableMapping

from aiohttp import web
from aiohttp.web_reqrep import Request
from aiohttp_session import get_session
from collections.abc import Sequence

AIOLOGIN_KEY = '__aiologin__'

ON_LOGIN = 1
ON_LOGOUT = 2
ON_AUTHENTICATED = 3
ON_FORBIDDEN = 4
ON_UNAUTHORIZED = 5


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
    raise web.HTTPUnauthorized()


# noinspection PyUnusedLocal
@asyncio.coroutine
def _forbidden(*args, **kwargs):
    raise web.HTTPForbidden()


# noinspection PyUnusedLocal
@asyncio.coroutine
def _void(*args, **kwargs):
    raise NotImplemented()


class AioLogin:
    def __init__(self, request, session_name=AIOLOGIN_KEY, disabled=False,
                 auth_by_form=_void, auth_by_header=_void,
                 auth_by_session=_void, forbidden=_forbidden,
                 unauthorized=_unauthorized, anonymous_user=AnonymousUser,
                 session=get_session, signals=None):

        self._request = request
        self._disabled = disabled
        self._session_name = session_name

        self._anonymous_user = anonymous_user
        self._session = session

        self._auth_by_form = auth_by_form
        self._auth_by_header = auth_by_header
        self._auth_by_session = auth_by_session
        self._unauthorized = unauthorized
        self._forbidden = forbidden

        self._on_login = []
        self._on_logout = []
        self._on_authenticated = []
        self._on_forbidden = []
        self._on_unauthorized = []

        assert isinstance(signals, (type(None), Sequence)), \
            "Excepted {!r} but received {!r}".format(Sequence, signals)

        signals = [] if signals is None else signals
        for sig in signals:
            assert isinstance(sig, Sequence), \
                "Excepted {!r} but received {!r}".format(Sequence, signals)
            is_coro = asyncio.iscoroutinefunction(sig[1])
            assert len(sig) == 2 and 1 <= sig[0] <= 7 and is_coro, \
                "Incorrectly formatted signal argument {}".format(sig)

            if sig[0] == 1:
                self._on_login.append(sig[1])
            elif sig[0] == 2:
                self._on_logout.append(sig[1])
            elif sig[0] == 3:
                self._on_authenticated.append(sig[1])
            elif sig[0] == 4:
                self._on_forbidden.append(sig[1])
            elif sig[0] == 5:
                self._on_unauthorized.append(sig[1])

    @asyncio.coroutine
    def authenticate(self, *args, remember=False, **kwargs):
        assert isinstance(remember, bool), \
            "Expected {!r} but received {!r}".format(type(bool), type(remember))
        user = yield from self._auth_by_form(self._request, *args, **kwargs)
        if user is None:
            for coro in self._on_unauthorized:
                yield from coro(self._request)
            raise web.HTTPUnauthorized
        for coro in self._on_authenticated:
            yield from coro(self._request)
        yield from self.login(user, remember=remember)

    @asyncio.coroutine
    def login(self, user, remember):
        assert isinstance(user, AbstractUser), \
            "Expected {} but received {}".format(type(AbstractUser), type(user))
        assert isinstance(remember, bool), \
            "Expected {!r} but received {!r}".format(type(bool), type(remember))
        session = yield from self._session(self._request)
        try:
            session.remember = remember
        except:
            session['_remember'] = remember
        session[self._session_name] = dict(user)
        for coro in self._on_login:
            yield from coro(self._request)

    @asyncio.coroutine
    def logout(self):
        session = yield from self._session(self._request)
        session.invalidate()
        for coro in self._on_logout:
            yield from coro(self._request)

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
        return user

    @property
    def on_login(self):
        return self._on_login

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
        kwargs = {k: v for (k, v) in kwargs.items() if k != 'request'}
        if not isinstance(request, Request):
            request = args[0].request
        elif request not in args:
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
            # noinspection PyProtectedMember
            for coro in request.aiologin._on_unauthorized:
                yield from coro(request)
            return (yield from request.aiologin.unauthorized(*args, **kwargs))
        if user.forbidden:
            # noinspection PyProtectedMember
            for coro in request.aiologin._on_forbidden:
                yield from coro(request)
            return (yield from request.aiologin.forbidden(*args, **kwargs))
        request.current_user = user
        # noinspection PyProtectedMember
        for coro in request.aiologin._on_authenticated:
            yield from coro(request)
        return (yield from func(*args, **kwargs))

    return wrapper
