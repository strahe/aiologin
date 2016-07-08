import asyncio


class AbstractSignal:
    def __init__(self, callback, name):
        super().__init__()
        if asyncio.iscoroutine(callback) or \
                isinstance(callback, asyncio.Future):
            self.callback = [callback]
        self.name = name

    def __eq__(self, new_callback):
        if asyncio.iscoroutine(new_callback) or \
                isinstance(new_callback, asyncio.Future):
            self.callback += new_callback

    @asyncio.coroutine
    def send(self):
        for callback in self.callback:
            res = callback
            # check to see if the receivers are coroutine or futures
            if asyncio.iscoroutine(res) or isinstance(res, asyncio.Future):
                yield from res

    def add_callback(self, subscriber):
        #does this even work?
        self.callback.append(subscriber)

class LoginSignal(AbstractSignal):
    

