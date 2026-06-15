from ..runtime import values as _v  # late import avoids circular issue


class ReturnSignal(Exception):
    def __init__(self, val): self.val = val


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


class JSRuntimeError(Exception):
    def __init__(self, msg, js_val=None):
        super().__init__(msg)
        self._js_val = js_val  # stored lazily to avoid import cycle

    @property
    def js_val(self):
        if self._js_val is None:
            self._js_val = make_error(str(self))
        return self._js_val


class JSThrowSignal(Exception):
    def __init__(self, val): self.val = val


def make_error(msg):
    from .values import JSObject
    return JSObject({'message': msg, 'stack': msg})
