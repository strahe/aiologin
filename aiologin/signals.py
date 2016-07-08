import asyncio


class AbstractSignal:
    def __init__(self, name):
        super().__init__()
        self.name = name

    def __eq__(self, callback):
        # if asyncio.iscoroutine(callback) or \
        #         isinstance(callback, asyncio.Future):
        #     self.callback += callback
        if asyncio.iscoroutine(callback) or \
                isinstance(callback, asyncio.Future):
            if self.callback is None:
                self.callback = [callback]
            else:
                self.callback.append(callback)

    @asyncio.coroutine
    def send(self):
        for callback in self.callback:
            res = callback
            # check to see if the receivers are coroutine or futures
            if asyncio.iscoroutine(res) or isinstance(res, asyncio.Future):
                yield from res

    def add_callback(self, callback):
        if asyncio.iscoroutine(callback) or \
                isinstance(callback, asyncio.Future):
            if self.callback is None:
                 self.callback = [callback]
            else:
                self.callback.append(callback)


class LoginSignal(AbstractSignal):
    print("loginSignal class made")


class LogoutSignal(AbstractSignal):
    print("loginSignal class made")
