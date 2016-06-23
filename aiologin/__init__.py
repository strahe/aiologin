from abc import ABCMeta, abstractproperty
from collections.abc import MutableMapping
from aiohttp import web

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
async def _unauthorized(request):
    return web.Response(status=401, body=b'Unauthorized')


# noinspection PyUnusedLocal
async def _forbidden(request):
    return web.Response(status=403, body=b'Forbidden')


class AioLogin:
    def __init__(self, request, default_user, key=AIOLOGIN_KEY, disabled=False,
                 forbidden=_forbidden, unauthorized=_unauthorized,
                 anonymous_user=AnonymousUser):
        self._request = request
        self._key = key
        self._disabled = disabled

        self._default_user = default_user
        self._anonymous_user = anonymous_user

        self._unauthorized = unauthorized
        self._forbidden = forbidden

    async def login(self, user):
        assert isinstance(user, AbstractUser), \
            "Expected 'AbstractUser' type but received {}".format(type(user))
        session = await get_session(self._request)
        session[self._key] = dict(user)

    async def logout(self):
        session = await get_session(self._request)
        del session[self._key]

    async def current_user(self):
        session = await get_session(self._request)
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
    app.middlewares.append(aiologin_middleware_factory(
        default_user=default_user, **kwargs
    ))


def aiologin_middleware_factory(**kwargs):
    # noinspection PyUnusedLocal
    async def aiologin_middleware(app, handler):
        async def aiologin_handler(request):
            request.aiologin = AioLogin(request, **kwargs)
            return await handler(request)

        return aiologin_handler

    return aiologin_middleware


def secured(func):
    async def wrapper(request):
        cur_usr = await request.aiologin.current_user()
        if request.aiologin.disabled:
            return await func(request)
        if not cur_usr.authenticated:
            return await request.aiologin.unauthorized(request)
        if cur_usr.forbidden:
            return await request.aiologin.forbidden(request)
        return await func(request)

    return wrapper
