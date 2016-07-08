import asyncio


class AbstractSignal(list):

    @asyncio.coroutine
    def _send(self, *args, **kwargs):
        for self.subscriber in self:
            res = self.subscriber
            # check to see if the receivers are corutines or futures
            if asyncio.iscoroutine(res) or isinstance(res, asyncio.Future):
                yield from res


class Signal (AbstractSignal):
    def __init__(self, app, callback, name):
        super().__init__()
        self.name = name
        self._app = app
        if asyncio.iscoroutine(callback) or isinstance(callback, asyncio.Future):
            self.callback = callback
        self.subscriber = None

    def add_receiver(self, subscriber):
        self.subscriber += subscriber

