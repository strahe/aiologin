from abc import ABCMeta, abstractmethod
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

    @abstractmethod
    def is_authenticated(self):
        return

    @abstractmethod
    def is_forbidden(self):
        return

        # @abstractmethod
        # def get_id(self):
        #     return


class AnonymousUser(AbstractUser):
    def is_authenticated(self):
        return False

    def is_forbidden(self):
        return False

        # def get_id(self):
        #     return None


class AioLogin:
    def __init__(self, request, key=AIOLOGIN_KEY, disabled=False,
                 forbidden=_forbidden, unauthorized=_unauthorized):
        self._request = request
        self._key = key
        self._disabled = disabled

        self.forbidden = forbidden
        self.unauthorized = unauthorized

    async def login(self, user):
        assert isinstance(user, AbstractUser), \
            "Expected 'AbstractUser' base type but received {!r}".format(
                type(user))
        session = await get_session(self._request)
        session[self._key] = dict(user)

    async def logout(self):
        session = await get_session(self._request)
        del session[self._key]

    @property
    def disabled(self):
        return self._disabled


def setup(app, **kwargs):
    app.middlewares.append(aiologin_middleware_factory(**kwargs))


def aiologin_middleware_factory(**kwargs):
    # noinspection PyUnusedLocal
    async def aiologin_middleware(app, handler):
        async def aiologin_handler(request):
            request.aiologin = AioLogin(request, **kwargs)
            return await handler(request)

        return aiologin_handler

    return aiologin_middleware


def secured(func):
    async def wrapper(**kwargs):
        request = kwargs['request']
        session = await get_session(request)
        user = session.get(AIOLOGIN_KEY, AnonymousUser())

        if request.aiologin.disabled:
            return await func(request)

        if not user.is_authenticated():
            return await request.aiologin.unauthorized(request)

        if not user.is_forbidden():
            return await request.aiologin.forbidden(request)

        return await func(request)

    return wrapper


# noinspection PyUnusedLocal
async def _unauthorized(request):
    web.Response(status=401)


# noinspection PyUnusedLocal
async def _forbidden(request):
    web.Response(status=403)
