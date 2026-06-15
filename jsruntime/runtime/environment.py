from .signals import JSRuntimeError


class Environment:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def get(self, name):
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name)
        raise JSRuntimeError(f"ReferenceError: {name} is not defined")

    def set(self, name, val):
        if name in self.vars:
            self.vars[name] = val
            return
        if self.parent:
            try:
                self.parent.set(name, val)
                return
            except Exception:
                pass
        self.vars[name] = val

    def define(self, name, val):
        self.vars[name] = val

    def assign(self, name, val):
        if name in self.vars:
            self.vars[name] = val
            return
        if self.parent:
            self.parent.assign(name, val)
            return
        raise JSRuntimeError(f"ReferenceError: {name} is not defined")
