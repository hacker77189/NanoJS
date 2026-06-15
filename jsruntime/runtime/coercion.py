import math


def js_to_string(v):
    # Import here to avoid circular import at module load time
    from .values import UNDEFINED, NULL, JSArray, JSObject, JSFunction, JSClass
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if v is UNDEFINED:
        return 'undefined'
    if v is NULL:
        return 'null'
    if isinstance(v, float):
        if v != v:
            return 'NaN'
        if v == float('inf'):
            return 'Infinity'
        if v == float('-inf'):
            return '-Infinity'
        if v == int(v) and abs(v) < 1e15:
            return str(int(v))
        return format_js_number(v)
    if isinstance(v, str):
        return v
    if isinstance(v, JSArray):
        return ','.join(js_to_string(x) for x in v.items)
    if isinstance(v, JSObject):
        return '[object Object]'
    if isinstance(v, JSFunction):
        return f'function {v.name}() {{...}}'
    if isinstance(v, JSClass):
        return f'class {v.name} {{}}'
    return str(v)


def format_js_number(v):
    s = f'{v:.17g}'
    if '.' in s and 'e' not in s:
        s = s.rstrip('0').rstrip('.')
    if s == '-0':
        return '0'
    return s


def js_to_number(v):
    from .values import UNDEFINED, NULL, JSArray, JSObject
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    if v is UNDEFINED or v is None:
        return float('nan')
    if v is NULL:
        return 0.0
    if isinstance(v, float):
        return v
    if isinstance(v, str):
        s = v.strip()
        if s == '':
            return 0.0
        if s in ('Infinity', '+Infinity'):
            return float('inf')
        if s == '-Infinity':
            return float('-inf')
        try:
            return float(s)
        except Exception:
            return float('nan')
    if isinstance(v, JSArray):
        if len(v.items) == 0:
            return 0.0
        if len(v.items) == 1:
            return js_to_number(v.items[0])
        return float('nan')
    if isinstance(v, JSObject):
        return float('nan')
    return float('nan')


def js_to_bool(v):
    from .values import UNDEFINED, NULL
    if isinstance(v, bool):
        return v
    if v is UNDEFINED or v is NULL:
        return False
    if isinstance(v, float):
        return v != 0 and v == v
    if isinstance(v, str):
        return len(v) > 0
    return True


def js_typeof(v):
    from .values import UNDEFINED, NULL, JSFunction, JSClass
    if v is UNDEFINED:
        return 'undefined'
    if v is NULL:
        return 'object'
    if isinstance(v, bool):
        return 'boolean'
    if isinstance(v, float):
        return 'number'
    if isinstance(v, str):
        return 'string'
    if isinstance(v, JSFunction):
        return 'function'
    if isinstance(v, JSClass):
        return 'function'
    return 'object'


def js_loose_equal(a, b):
    from .values import NULL, UNDEFINED, JSObject, JSArray, JSFunction
    if type(a) == type(b) or (
        isinstance(a, (JSObject, JSArray, JSFunction)) and
        isinstance(b, (JSObject, JSArray, JSFunction))
    ):
        return js_strict_equal(a, b)
    if a is NULL and b is UNDEFINED:
        return True
    if a is UNDEFINED and b is NULL:
        return True
    if isinstance(a, float) and isinstance(b, str):
        return a == js_to_number(b)
    if isinstance(a, str) and isinstance(b, float):
        return js_to_number(a) == b
    if isinstance(a, bool):
        return js_loose_equal(js_to_number(a), b)
    if isinstance(b, bool):
        return js_loose_equal(a, js_to_number(b))
    return False


def js_strict_equal(a, b):
    from .values import UNDEFINED, NULL
    if a is UNDEFINED and b is UNDEFINED:
        return True
    if a is NULL and b is NULL:
        return True
    if isinstance(a, float) and isinstance(b, float):
        if a != a or b != b:
            return False
        return a == b
    if isinstance(a, str) and isinstance(b, str):
        return a == b
    if isinstance(a, bool) and isinstance(b, bool):
        return a == b
    return a is b
