import re
from .coercion import js_to_string  # forward ref resolved at import time


def js_regex_to_py(pat):
    return pat


class JSUndefined:
    def __repr__(self): return 'undefined'
    def __str__(self): return 'undefined'
    def __bool__(self): return False


class JSNull:
    def __repr__(self): return 'null'
    def __str__(self): return 'null'
    def __bool__(self): return False


UNDEFINED = JSUndefined()
NULL = JSNull()


class JSObject:
    def __init__(self, props=None):
        self.props = props or {}
        self.prototype = None

    def get(self, key):
        key = str(key) if not isinstance(key, str) else key
        if key in self.props:
            v = self.props[key]
            if isinstance(v, tuple) and v[0] == '__getter__':
                return v[1](self)
            return v
        if self.prototype:
            return self.prototype.get(key)
        return UNDEFINED

    def set(self, key, val):
        self.props[str(key) if not isinstance(key, str) else key] = val

    def has(self, key):
        key = str(key) if not isinstance(key, str) else key
        return key in self.props or (self.prototype and self.prototype.has(key))

    def delete(self, key):
        key = str(key) if not isinstance(key, str) else key
        if key in self.props:
            del self.props[key]

    def keys(self):
        return [k for k in self.props.keys() if not k.startswith('__')]

    def __repr__(self):
        return js_to_string(self)


class JSArray(JSObject):
    def __init__(self, items=None):
        super().__init__()
        self.items = items if items is not None else []

    def get(self, key):
        if key == 'length':
            return float(len(self.items))
        try:
            idx = int(float(key))
            if 0 <= idx < len(self.items):
                return self.items[idx]
            return UNDEFINED
        except Exception:
            pass
        if key in self.props:
            return self.props[key]
        return UNDEFINED

    def set(self, key, val):
        try:
            idx = int(float(key))
            while len(self.items) <= idx:
                self.items.append(UNDEFINED)
            self.items[idx] = val
            return
        except Exception:
            pass
        if key == 'length':
            from .coercion import js_to_number
            n = int(js_to_number(val))
            self.items = self.items[:n]
            while len(self.items) < n:
                self.items.append(UNDEFINED)
            return
        self.props[key] = val

    def __repr__(self):
        return js_to_string(self)


class JSFunction:
    def __init__(self, name, params, body, env, is_arrow=False, is_gen=False, is_async=False):
        self.name = name or ''
        self.params = params
        self.body = body
        self.env = env
        self.is_arrow = is_arrow
        self.is_gen = is_gen
        self.is_async = is_async
        self.prototype_obj = JSObject()
        self.props = {
            'prototype': self.prototype_obj,
            'name': self.name,
            'length': float(len(params)),
        }

    def get(self, key):
        return self.props.get(key, UNDEFINED)

    def set(self, key, val):
        self.props[key] = val


class JSClass:
    def __init__(self, name, superclass, methods, env):
        self.name = name
        self.superclass = superclass
        self.methods = methods
        self.env = env
        self.static_props = {}


class JSRegex:
    def __init__(self, pattern, flags):
        self.pattern = pattern
        self.flags = flags
        self.last_index = 0
        py_flags = 0
        if 'i' in flags:
            py_flags |= re.IGNORECASE
        if 'm' in flags:
            py_flags |= re.MULTILINE
        if 's' in flags:
            py_flags |= re.DOTALL
        self.compiled = re.compile(js_regex_to_py(pattern), py_flags)
        self.global_ = 'g' in flags
