import asyncio


class AbstractSignal:
    def __init__(self, name):
        super().__init__()
        self.callback = None
        self.name = name
        print("did the init")

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
        print("in the send")
        for callback in self.callback:
            print("in the for")
            yield from callback()

            # check to see if the receivers are coroutine or futures
            # not sure why its not working
            if asyncio.iscoroutine(callback) or \
                    isinstance(callback, asyncio.Future):
                yield from callback()

    def add_callback(self, callback):
        print("hit the add_callback")
        # if asyncio.iscoroutine(callback) or \
        #         isinstance(callback, asyncio.Future):
        print("sees is a coroutine and was added")
        if self.callback is None:
            self.callback = [callback]
        else:
            self.callback.append(callback)


class LoginSignal(AbstractSignal):
    def init(self, name):
        super.__init__(name)
        return self

