import asyncio


class AbstractSignal:
    def __init__(self, name):
        super().__init__()
        self.callback = []
        self.name = name

    # def __setattr__(self, callback, value):
    #     # if asyncio.iscoroutine(callback) or \
    #     #         isinstance(callback, asyncio.Future):
    #     #     self.callback += callback
    #     print(" the = has is now trying to add a callback")
    #     if asyncio.iscoroutine(callback) or \
    #             isinstance(callback, asyncio.Future):
    #         print("callback has been added")
    #         if self.callback is None:
    #             self.callback = [callback]
    #         else:
    #             self.callback.append(callback)

    @asyncio.coroutine
    def send(self):
        for callback in self.callback:
            yield from callback()

            # check to see if the receivers are coroutine or futures
            # not sure why its not working
            if asyncio.iscoroutine(callback) or \
                    isinstance(callback, asyncio.Future):
                yield from callback()

    def add_callback(self, callback):
        # if asyncio.iscoroutine(callback) or \
        #         isinstance(callback, asyncio.Future):
        if self.callback is None:
            self.callback = [callback]
        else:
            self.callback.append(callback)


class LoginSignal(AbstractSignal):
    def init(self, name):
        super.__init__(name)
        return self


class LogoutSignal(AbstractSignal):
    def init(self, name):
        super.__init__(name)
        return self


class HomeRouteSignal(AbstractSignal):
    def init(self, name):
        super.__init__(name)
        return self

