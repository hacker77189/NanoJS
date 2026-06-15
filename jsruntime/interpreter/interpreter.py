import sys
import math
import random
import re
import functools
from datetime import datetime

from ..runtime.values import (
    JSObject, JSArray, JSFunction, JSClass, JSRegex,
    UNDEFINED, NULL,
)
from ..runtime.coercion import (
    js_to_string, js_to_number, js_to_bool,
    js_typeof, js_strict_equal, js_loose_equal, format_js_number,
)
from ..runtime.environment import Environment
from ..runtime.signals import (
    ReturnSignal, BreakSignal, ContinueSignal,
    JSRuntimeError, JSThrowSignal, make_error,
)


class Interpreter:
    def __init__(self):
        self.output_lines = []
        self.global_env = Environment()
        self._setup_globals()
        self._this_stack = [self.global_env.vars]

    def _setup_globals(self):
        e = self.global_env
        e.define('undefined', UNDEFINED)
        e.define('null', NULL)
        e.define('NaN', float('nan'))
        e.define('Infinity', float('inf'))
        e.define('console', self._make_console())
        e.define('Math', self._make_math())
        e.define('Date', self._make_date_class())
        e.define('Array', self._make_array_class())
        e.define('Object', self._make_object_class())
        e.define('String', self._make_string_class())
        e.define('Number', self._make_number_class())
        e.define('Boolean', self._make_boolean_class())
        e.define('JSON', self._make_json())
        e.define('parseInt', self._builtin_parseInt())
        e.define('parseFloat', self._builtin_parseFloat())
        e.define('isNaN', self._builtin_isNaN())
        e.define('isFinite', self._builtin_isFinite())
        e.define('TypeError', self._make_error_class('TypeError'))
        e.define('RangeError', self._make_error_class('RangeError'))
        e.define('Error', self._make_error_class('Error'))
        e.define('Promise', self._make_promise())
        e.define('setTimeout', self._make_setTimeout())
        e.define('clearTimeout', JSFunction('clearTimeout', [], None, e))
        e.define('Symbol', self._make_symbol())

    def _make_console(self):
        interp = self

        def _log(*args):
            parts = []
            for a in args:
                parts.append(js_to_string(a))
            interp.output_lines.append(' '.join(parts))

        def _error(*args):
            pass
        obj = JSObject()
        obj.set('log', self._native('log', _log))
        obj.set('error', self._native('error', _error))
        obj.set('warn', self._native('warn', _error))
        obj.set('info', self._native('info', _log))
        return obj

    def _native(self, name, fn):
        f = JSFunction(name, [], None, self.global_env)
        f._native = fn
        return f

    def _make_math(self):
        obj = JSObject()
        obj.set('PI', math.pi)
        obj.set('E', math.e)
        obj.set('LN2', math.log(2))
        obj.set('LN10', math.log(10))
        obj.set('LOG2E', math.log2(math.e))
        obj.set('LOG10E', math.log10(math.e))
        obj.set('SQRT2', math.sqrt(2))
        obj.set('abs', self._native(
            'abs', lambda x: float(abs(js_to_number(x)))))
        obj.set('ceil', self._native(
            'ceil', lambda x: float(math.ceil(js_to_number(x)))))
        obj.set('floor', self._native(
            'floor', lambda x: float(math.floor(js_to_number(x)))))
        obj.set('round', self._native(
            'round', lambda x: float(round(js_to_number(x)))))
        obj.set('sqrt', self._native(
            'sqrt', lambda x: float(math.sqrt(js_to_number(x)))))
        obj.set('cbrt', self._native('cbrt', lambda x: float(math.cbrt(
            js_to_number(x)) if hasattr(math, 'cbrt') else js_to_number(x)**(1/3))))
        obj.set('pow', self._native('pow', lambda x,
                y: float(js_to_number(x)**js_to_number(y))))
        obj.set('max', self._native('max', lambda *args: float(max((js_to_number(a)
                for a in args), default=float('-inf')))))
        obj.set('min', self._native(
            'min', lambda *args: float(min((js_to_number(a) for a in args), default=float('inf')))))
        obj.set('random', self._native('random', lambda: random.random()))
        obj.set('log', self._native(
            'log', lambda x: float(math.log(js_to_number(x)))))
        obj.set('log2', self._native(
            'log2', lambda x: float(math.log2(js_to_number(x)))))
        obj.set('log10', self._native(
            'log10', lambda x: float(math.log10(js_to_number(x)))))
        obj.set('sin', self._native(
            'sin', lambda x: float(math.sin(js_to_number(x)))))
        obj.set('cos', self._native(
            'cos', lambda x: float(math.cos(js_to_number(x)))))
        obj.set('tan', self._native(
            'tan', lambda x: float(math.tan(js_to_number(x)))))
        obj.set('atan', self._native(
            'atan', lambda x: float(math.atan(js_to_number(x)))))
        obj.set('atan2', self._native('atan2', lambda y, x: float(
            math.atan2(js_to_number(y), js_to_number(x)))))
        obj.set('sign', self._native('sign', lambda x: float(
            0 if js_to_number(x) == 0 else (1 if js_to_number(x) > 0 else -1))))
        obj.set('trunc', self._native(
            'trunc', lambda x: float(math.trunc(js_to_number(x)))))
        obj.set('hypot', self._native(
            'hypot', lambda *args: float(math.hypot(*(js_to_number(a) for a in args)))))
        return obj

    def _make_date_class(self):
        interp = self

        class DateConstructor:
            pass
        f = self._native('Date', None)
        f._is_constructor = True

        def _construct(*args):
            obj = JSObject()
            if not args:
                dt = datetime.now()
            elif len(args) == 1:
                ms = js_to_number(args[0])
                dt = datetime.fromtimestamp(ms/1000)
            else:
                nums = [int(js_to_number(a)) for a in args]
                dt = datetime(*nums)
            obj._dt = dt
            obj.set('getFullYear', interp._native(
                'getFullYear', lambda: float(dt.year)))
            obj.set('getMonth', interp._native(
                'getMonth', lambda: float(dt.month-1)))
            obj.set('getDate', interp._native(
                'getDate', lambda: float(dt.day)))
            obj.set('getDay', interp._native(
                'getDay', lambda: float(dt.weekday())))
            obj.set('getHours', interp._native(
                'getHours', lambda: float(dt.hour)))
            obj.set('getMinutes', interp._native(
                'getMinutes', lambda: float(dt.minute)))
            obj.set('getSeconds', interp._native(
                'getSeconds', lambda: float(dt.second)))
            obj.set('getTime', interp._native(
                'getTime', lambda: float(int(dt.timestamp()*1000))))
            obj.set('toISOString', interp._native('toISOString',
                    lambda: dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')))
            obj.set('toLocaleDateString', interp._native(
                'toLocaleDateString', lambda: dt.strftime('%m/%d/%Y')))
            obj.set('toString', interp._native('toString', lambda: str(dt)))
            return obj
        f._construct = _construct
        f._native = lambda *a: _construct(*a)
        return f

    def _make_array_class(self):
        interp = self
        f = self._native('Array', None)
        f._is_constructor = True

        def _construct(*args):
            if len(args) == 1 and isinstance(args[0], float):
                return JSArray([UNDEFINED]*int(args[0]))
            return JSArray(list(args))
        f._construct = _construct
        f._native = lambda *a: _construct(*a)
        # static methods
        f.set('isArray', interp._native(
            'isArray', lambda x: isinstance(x, JSArray)))
        f.set('from', interp._native('from', lambda x,
              *rest: interp._array_from(x, *rest)))
        f.set('of', interp._native('of', lambda *args: JSArray(list(args))))
        return f

    def _array_from(self, x, *rest):
        map_fn = rest[0] if rest else None
        if isinstance(x, JSArray):
            items = list(x.items)
        elif isinstance(x, str):
            items = list(x)
        elif isinstance(x, JSObject) and not isinstance(x, JSArray):
            length = js_to_number(x.get('length'))
            items = [x.get(str(i)) for i in range(int(length))]
        else:
            items = []
        if map_fn:
            items = [self._call(map_fn, [it, float(i)])
                     for i, it in enumerate(items)]
        return JSArray(items)

    def _make_object_class(self):
        interp = self
        f = self._native('Object', None)
        f._is_constructor = True

        def _construct(*args):
            if not args or args[0] is NULL or args[0] is UNDEFINED:
                return JSObject()
            if isinstance(args[0], JSObject):
                return args[0]
            return JSObject()
        f._construct = _construct
        f._native = lambda *a: _construct(*a)
        f.set('keys', interp._native('keys', lambda o: JSArray(
            [k for k in (o.keys() if isinstance(o, JSObject) else [])])))
        f.set('values', interp._native('values', lambda o: JSArray(
            [o.get(k) for k in (o.keys() if isinstance(o, JSObject) else [])])))
        f.set('entries', interp._native('entries', lambda o: JSArray(
            [JSArray([k, o.get(k)]) for k in (o.keys() if isinstance(o, JSObject) else [])])))
        f.set('assign', interp._native('assign', lambda target,
              *sources: interp._object_assign(target, *sources)))
        f.set('freeze', interp._native('freeze', lambda o: o))
        f.set('create', interp._native(
            'create', lambda proto, *_: interp._object_create(proto)))
        f.set('defineProperty', interp._native('defineProperty',
              lambda o, k, desc: interp._define_property(o, k, desc)))
        f.set('getOwnPropertyNames', interp._native('getOwnPropertyNames',
              lambda o: JSArray(o.keys() if isinstance(o, JSObject) else [])))
        f.set('hasOwn', interp._native('hasOwn', lambda o, k: str(
            k) in (o.props if isinstance(o, JSObject) else {})))
        return f

    def _object_assign(self, target, *sources):
        for src in sources:
            if isinstance(src, JSObject):
                for k in src.keys():
                    target.set(k, src.get(k))
        return target

    def _object_create(self, proto):
        obj = JSObject()
        if isinstance(proto, JSObject):
            obj.prototype = proto
        return obj

    def _define_property(self, obj, key, desc):
        if isinstance(desc, JSObject):
            val = desc.get('value')
            if val is not UNDEFINED:
                obj.set(key, val)
        return obj

    def _make_string_class(self):
        interp = self
        f = self._native('String', lambda x=UNDEFINED: js_to_string(
            x) if x is not UNDEFINED else '')
        f._is_constructor = True
        f._construct = lambda *args: JSObject(
            {'_val': js_to_string(args[0]) if args else ''})
        f.set('fromCharCode', interp._native('fromCharCode',
              lambda *codes: ''.join(chr(int(js_to_number(c))) for c in codes)))
        return f

    def _make_number_class(self):
        f = self._native('Number', lambda x=UNDEFINED: js_to_number(
            x) if x is not UNDEFINED else 0.0)
        f._is_constructor = True
        f._construct = lambda *args: JSObject(
            {'_val': js_to_number(args[0]) if args else 0.0})
        f.set('isInteger', self._native('isInteger',
              lambda x: isinstance(x, float) and x == int(x) and x == x))
        f.set('isFinite', self._native('isFinite', lambda x: isinstance(
            x, float) and not math.isinf(x) and x == x))
        f.set('isNaN', self._native(
            'isNaN', lambda x: isinstance(x, float) and x != x))
        f.set('parseInt', self._builtin_parseInt())
        f.set('parseFloat', self._builtin_parseFloat())
        f.set('MAX_SAFE_INTEGER', float(2**53 - 1))
        f.set('MIN_SAFE_INTEGER', float(-(2**53 - 1)))
        f.set('MAX_VALUE', float('1.7976931348623157e+308'))
        f.set('POSITIVE_INFINITY', float('inf'))
        f.set('NEGATIVE_INFINITY', float('-inf'))
        f.set('NaN', float('nan'))
        return f

    def _make_boolean_class(self):
        f = self._native('Boolean', lambda x=UNDEFINED: js_to_bool(
            x) if x is not UNDEFINED else False)
        f._is_constructor = True
        f._construct = lambda *args: JSObject(
            {'_val': js_to_bool(args[0]) if args else False})
        return f

    def _make_json(self):
        interp = self
        obj = JSObject()
        obj.set('stringify', self._native('stringify',
                lambda v, *_: interp._json_stringify(v)))
        obj.set('parse', self._native(
            'parse', lambda s, *_: interp._json_parse(s)))
        return obj

    def _json_stringify(self, v, indent=None):
        import json

        def convert(x):
            if x is UNDEFINED or isinstance(x, JSFunction):
                return None
            if x is NULL:
                return None
            if isinstance(x, bool):
                return x
            if isinstance(x, float):
                if x != x or math.isinf(x):
                    return None
                return int(x) if x == int(x) else x
            if isinstance(x, str):
                return x
            if isinstance(x, JSArray):
                return [convert(i) for i in x.items]
            if isinstance(x, JSObject):
                return {k: convert(v) for k, v in x.props.items() if not k.startswith('__')}
            return None
        return json.dumps(convert(v), separators=(',', ':'))

    def _json_parse(self, s):
        import json

        def convert(x):
            if x is None:
                return NULL
            if isinstance(x, bool):
                return x
            if isinstance(x, (int, float)):
                return float(x)
            if isinstance(x, str):
                return x
            if isinstance(x, list):
                return JSArray([convert(i) for i in x])
            if isinstance(x, dict):
                obj = JSObject()
                for k, v in x.items():
                    obj.set(k, convert(v))
                return obj
            return UNDEFINED
        try:
            return convert(json.loads(s))
        except:
            raise JSThrowSignal(make_error('SyntaxError: Unexpected token'))

    def _builtin_parseInt(self):
        def _impl(s=UNDEFINED, radix=UNDEFINED):
            s = js_to_string(s).strip()
            r = int(js_to_number(radix)
                    ) if radix is not UNDEFINED and radix is not NULL else 10
            if r == 0:
                r = 10
            neg = False
            if s.startswith('-'):
                neg = True
                s = s[1:]
            elif s.startswith('+'):
                s = s[1:]
            if r == 16 and (s.startswith('0x') or s.startswith('0X')):
                s = s[2:]
            acc = ''
            digits = '0123456789abcdefghijklmnopqrstuvwxyz'[:r]
            for ch in s:
                if ch.lower() in digits:
                    acc += ch
                else:
                    break
            if not acc:
                return float('nan')
            result = int(acc, r)
            return float(-result if neg else result)
        return self._native('parseInt', _impl)

    def _builtin_parseFloat(self):
        def _impl(s=UNDEFINED):
            s = js_to_string(s).strip()
            try:
                m = re.match(r'^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?', s)
                if m:
                    return float(m.group(0))
                return float('nan')
            except:
                return float('nan')
        return self._native('parseFloat', _impl)

    def _builtin_isNaN(self):
        return self._native('isNaN', lambda x: float(js_to_number(x)) != float(js_to_number(x)))

    def _builtin_isFinite(self):
        return self._native('isFinite', lambda x: not math.isinf(js_to_number(x)) and js_to_number(x) == js_to_number(x))

    def _make_error_class(self, name):
        interp = self
        f = self._native(name, None)
        f._is_constructor = True

        def _construct(*args):
            msg = js_to_string(args[0]) if args else ''
            obj = JSObject({'message': msg, 'name': name,
                           'stack': f'{name}: {msg}'})
            return obj
        f._construct = _construct
        f._native = lambda *a: _construct(*a)
        return f

    def _make_promise(self):
        interp = self
        f = self._native('Promise', None)
        f._is_constructor = True

        def _construct(executor=UNDEFINED):
            obj = JSObject()
            obj.set('then', interp._native('then', lambda *a: obj))
            obj.set('catch', interp._native('catch', lambda *a: obj))
            obj.set('finally', interp._native('finally', lambda *a: obj))
            if isinstance(executor, JSFunction):
                try:
                    res = interp._native('resolve', lambda v=UNDEFINED: v)
                    rej = interp._native('reject', lambda v=UNDEFINED: v)
                    interp._call(executor, [res, rej])
                except:
                    pass
            return obj
        f._construct = _construct
        f._native = lambda *a: _construct(*a)
        f.set('resolve', interp._native('resolve', lambda v=UNDEFINED: v))
        f.set('reject', interp._native('reject', lambda v=UNDEFINED: v))
        f.set('all', interp._native('all', lambda arr=UNDEFINED: arr))
        return f

    def _make_setTimeout(self):
        return self._native('setTimeout', lambda fn=UNDEFINED, ms=UNDEFINED: 0.0)

    def _make_symbol(self):
        counter = [0]
        f = self._native(
            'Symbol', lambda desc=UNDEFINED: f'Symbol({js_to_string(desc)})')
        f.set('iterator', 'Symbol(Symbol.iterator)')
        f.set('toPrimitive', 'Symbol(Symbol.toPrimitive)')
        return f

    # ── EXECUTION ──

    def run(self, ast):
        env = self.global_env
        # hoist function declarations
        self._hoist(ast, env)
        try:
            self._exec(ast, env)
        except ReturnSignal:
            pass
        except JSThrowSignal as e:
            msg = js_to_string(e.val) if isinstance(
                e.val, JSObject) else js_to_string(e.val)
            print(f'Uncaught: {msg}', file=sys.stderr)
        except JSRuntimeError as e:
            print(f'RuntimeError: {e}', file=sys.stderr)

    def _hoist(self, node, env):
        if not node:
            return
        kind = node[0]
        if kind == 'Program':
            for stmt in node[1]:
                self._hoist(stmt, env)
        elif kind == 'FuncDecl':
            _, name, params, body, is_gen = node
            if name:
                fn = JSFunction(name, params, body, env, is_gen=is_gen)
                env.define(name, fn)
        elif kind == 'Block':
            for stmt in node[1]:
                self._hoist(stmt, env)
        elif kind == 'ClassDecl':
            pass  # hoisted as undefined in JS, but we'll handle it in exec

    def _exec(self, node, env):
        if node is None:
            return
        kind = node[0]
        if kind == 'Program':
            for stmt in node[1]:
                self._exec(stmt, env)
        elif kind == 'Block':
            block_env = Environment(env)
            for stmt in node[1]:
                self._exec(stmt, block_env)
        elif kind == 'Empty':
            pass
        elif kind == 'VarDecl':
            _, kw, decls = node
            for (target, init) in decls:
                val = self._eval(init, env) if init else UNDEFINED
                self._bind_target(target, val, env)
        elif kind == 'FuncDecl':
            _, name, params, body, is_gen = node
            if name and name in env.vars:
                pass  # already hoisted
            elif name:
                fn = JSFunction(name, params, body, env, is_gen=is_gen)
                env.define(name, fn)
        elif kind == 'ClassDecl':
            _, name, superclass, methods = node
            cls = self._make_class(name, superclass, methods, env)
            env.define(name, cls)
        elif kind == 'ExprStmt':
            self._eval(node[1], env)
        elif kind == 'Return':
            val = self._eval(node[1], env) if node[1] else UNDEFINED
            raise ReturnSignal(val)
        elif kind == 'Break':
            raise BreakSignal()
        elif kind == 'Continue':
            raise ContinueSignal()
        elif kind == 'Throw':
            val = self._eval(node[1], env)
            raise JSThrowSignal(val)
        elif kind == 'If':
            _, cond, then, alt = node
            if js_to_bool(self._eval(cond, env)):
                self._exec(then, env)
            elif alt:
                self._exec(alt, env)
        elif kind == 'While':
            _, cond, body = node
            while js_to_bool(self._eval(cond, env)):
                try:
                    self._exec(body, env)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
        elif kind == 'DoWhile':
            _, body, cond = node
            while True:
                try:
                    self._exec(body, env)
                except BreakSignal:
                    break
                except ContinueSignal:
                    pass
                if not js_to_bool(self._eval(cond, env)):
                    break
        elif kind == 'For':
            _, init, cond, update, body = node
            for_env = Environment(env)
            if init:
                self._exec(init, for_env)
            while True:
                if cond and not js_to_bool(self._eval(cond, for_env)):
                    break
                try:
                    self._exec(body, for_env)
                except BreakSignal:
                    break
                except ContinueSignal:
                    pass
                if update:
                    self._eval(update, for_env)
        elif kind == 'ForOf':
            _, kw, target, iterable_node, body = node
            iterable = self._eval(iterable_node, env)
            items = self._get_iterable(iterable)
            for item in items:
                for_env = Environment(env)
                self._bind_target(target, item, for_env)
                try:
                    self._exec(body, for_env)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
        elif kind == 'ForIn':
            _, kw, target, obj_node, body = node
            obj = self._eval(obj_node, env)
            keys = obj.keys() if isinstance(obj, JSObject) else []
            for k in keys:
                for_env = Environment(env)
                self._bind_target(target, k, for_env)
                try:
                    self._exec(body, for_env)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
        elif kind == 'Try':
            _, body, catch_clause, finally_clause = node
            try:
                self._exec(body, env)
            except (JSThrowSignal, JSRuntimeError) as e:
                if catch_clause:
                    param, catch_body = catch_clause
                    catch_env = Environment(env)
                    val = e.val if isinstance(e, JSThrowSignal) else e.js_val
                    if param:
                        catch_env.define(param, val)
                    try:
                        self._exec(catch_body, catch_env)
                    except ReturnSignal:
                        if finally_clause:
                            self._exec(finally_clause, env)
                        raise
                else:
                    if finally_clause:
                        self._exec(finally_clause, env)
                    raise
            finally:
                if finally_clause:
                    self._exec(finally_clause, env)
        elif kind == 'Switch':
            _, disc, cases = node
            val = self._eval(disc, env)
            matched = False
            switch_env = Environment(env)
            try:
                for case in cases:
                    if case[0] == 'Default':
                        continue
                    cv = self._eval(case[1], switch_env)
                    if js_strict_equal(val, cv):
                        matched = True
                    if matched:
                        try:
                            for stmt in case[2]:
                                self._exec(stmt, switch_env)
                        except BreakSignal:
                            return
                if not matched:
                    for case in cases:
                        if case[0] == 'Default':
                            try:
                                for stmt in case[1]:
                                    self._exec(stmt, switch_env)
                            except BreakSignal:
                                return
            except BreakSignal:
                pass
        else:
            self._eval(node, env)

    def _bind_target(self, target, val, env):
        if target is None:
            return
        kind = target[0]
        if kind == 'ID':
            env.define(target[1], val)
        elif kind == 'ArrayDestruct':
            items = self._get_iterable(
                val) if val is not UNDEFINED and val is not NULL else []
            for i, elem in enumerate(target[1]):
                if elem is None:
                    continue
                if elem[0] == 'Rest':
                    env.define(elem[1], JSArray(items[i:]))
                    break
                item_val = items[i] if i < len(items) else UNDEFINED
                actual_val = item_val if item_val is not UNDEFINED else (
                    self._eval(elem[2], env) if elem[2] else UNDEFINED)
                self._bind_target(elem[1], actual_val, env)
        elif kind == 'ObjectDestruct':
            used = set()
            for prop in target[1]:
                if prop[0] == 'RestProp':
                    rest_obj = JSObject()
                    if isinstance(val, JSObject):
                        for k in val.keys():
                            if k not in used:
                                rest_obj.set(k, val.get(k))
                    env.define(prop[1], rest_obj)
                else:
                    _, key, ptarget, default = prop
                    pval = val.get(key) if isinstance(
                        val, JSObject) else UNDEFINED
                    if pval is UNDEFINED and default:
                        pval = self._eval(default, env)
                    used.add(key)
                    self._bind_target(ptarget, pval, env)

    def _get_iterable(self, val):
        if isinstance(val, JSArray):
            return list(val.items)
        if isinstance(val, str):
            return list(val)
        if isinstance(val, JSObject):
            return []
        return []

    def _eval(self, node, env):
        if node is None:
            return UNDEFINED
        kind = node[0]

        if kind == 'Num':
            return node[1]
        if kind == 'Str':
            return node[1]
        if kind == 'Bool':
            return node[1]
        if kind == 'Null':
            return NULL
        if kind == 'Undefined':
            return UNDEFINED

        if kind == 'ID':
            try:
                return env.get(node[1])
            except JSRuntimeError:
                return UNDEFINED

        if kind == 'This':
            return self._this_stack[-1] if self._this_stack else UNDEFINED

        if kind == 'Regex':
            raw = node[1]
            m = re.match(r'/(.*)/(.*)', raw)
            if m:
                return JSRegex(m.group(1), m.group(2))
            return JSRegex(raw, '')

        if kind == 'Template':
            parts = []
            for p in node[1]:
                parts.append(js_to_string(self._eval(p, env)))
            return ''.join(parts)

        if kind == 'Array':
            items = []
            for elem in node[1]:
                if elem is None:
                    items.append(UNDEFINED)
                elif elem[0] == 'Spread':
                    spread = self._eval(elem[1], env)
                    items.extend(self._get_iterable(spread))
                else:
                    items.append(self._eval(elem, env))
            return JSArray(items)

        if kind == 'Object':
            obj = JSObject()
            for prop in node[1]:
                if prop[0] == 'Pair':
                    obj.set(prop[1], self._eval(prop[2], env))
                elif prop[0] == 'Shorthand':
                    obj.set(prop[1], env.get(prop[1]))
                elif prop[0] == 'Computed':
                    k = js_to_string(self._eval(prop[1], env))
                    obj.set(k, self._eval(prop[2], env))
                elif prop[0] == 'Method':
                    name, params, body = prop[1], prop[2], prop[3]
                    fn = JSFunction(name, params, body, env)
                    obj.set(name, fn)
                elif prop[0] == 'SpreadProp':
                    src = self._eval(prop[1], env)
                    if isinstance(src, JSObject):
                        for k in src.keys():
                            obj.set(k, src.get(k))
                elif prop[0] == 'Accessor':
                    # get/set - simplified
                    pass
            return obj

        if kind in ('FuncExpr', 'FuncDecl'):
            _, name, params, body, is_gen = node[:5]
            is_async = node[5] if len(node) > 5 else False
            fn = JSFunction(name, params, body, env,
                            is_gen=is_gen, is_async=is_async)
            if name:
                fn_env = Environment(env)
                fn_env.define(name, fn)
                fn.env = fn_env
            return fn

        if kind == 'Arrow':
            _, params, body, is_async = node
            fn = JSFunction(None, params, body, env,
                            is_arrow=True, is_async=is_async)
            return fn

        if kind == 'ClassExpr':
            _, name, superclass, methods = node
            return self._make_class(name, superclass, methods, env)

        if kind == 'Member':
            obj = self._eval(node[1], env)
            return self._get_member(obj, node[2], env)

        if kind == 'Index':
            obj = self._eval(node[1], env)
            idx = self._eval(node[2], env)
            return self._get_index(obj, idx, env)

        if kind in ('OptMember', 'OptIndex', 'OptCall'):
            obj = self._eval(node[1], env)
            if obj is NULL or obj is UNDEFINED:
                return UNDEFINED
            if kind == 'OptMember':
                return self._get_member(obj, node[2], env)
            elif kind == 'OptIndex':
                idx = self._eval(node[2], env)
                return self._get_index(obj, idx, env)
            else:
                args = self._eval_args(node[2], env)
                return self._call(obj, args)

        if kind == 'Call':
            _, callee_node, arg_nodes = node
            args = self._eval_args(arg_nodes, env)

            # get callee and this
            if callee_node[0] == 'Member':
                this_val = self._eval(callee_node[1], env)
                method = self._get_member(this_val, callee_node[2], env)
                return self._call_method(method, this_val, args, env)
            elif callee_node[0] == 'Index':
                this_val = self._eval(callee_node[1], env)
                prop = self._eval(callee_node[2], env)
                method = self._get_index(this_val, prop, env)
                return self._call_method(method, this_val, args, env)
            else:
                fn = self._eval(callee_node, env)
                return self._call(fn, args, env=env)

        if kind == 'New':
            _, callee_node, arg_nodes = node
            args = self._eval_args(arg_nodes, env)
            cls = self._eval(callee_node, env)
            return self._construct(cls, args)

        if kind == 'Assign':
            _, op, target, rhs_node = node
            if op == '=':
                val = self._eval(rhs_node, env)
                self._assign(target, val, env)
                return val
            else:
                cur = self._eval(target, env)
                rhs = self._eval(rhs_node, env)
                base_op = op[:-1]
                val = self._apply_op(base_op, cur, rhs)
                self._assign(target, val, env)
                return val

        if kind == 'BinOp':
            _, op, left_node, right_node = node
            if op == '&&':
                l = self._eval(left_node, env)
                return l if not js_to_bool(l) else self._eval(right_node, env)
            if op == '||':
                l = self._eval(left_node, env)
                return l if js_to_bool(l) else self._eval(right_node, env)
            if op == '??':
                l = self._eval(left_node, env)
                return l if (l is not NULL and l is not UNDEFINED) else self._eval(right_node, env)
            l = self._eval(left_node, env)
            r = self._eval(right_node, env)
            return self._apply_op(op, l, r)

        if kind == 'Unary':
            _, op, operand = node
            v = self._eval(operand, env)
            if op == '-':
                return -js_to_number(v)
            if op == '+':
                return js_to_number(v)
            if op == '!':
                return not js_to_bool(v)
            if op == '~':
                return float(~int(js_to_number(v)))
            return UNDEFINED

        if kind == 'Typeof':
            if node[1][0] == 'ID':
                try:
                    v = env.get(node[1][1])
                except:
                    return 'undefined'
            else:
                v = self._eval(node[1], env)
            return js_typeof(v)

        if kind == 'Void':
            self._eval(node[1], env)
            return UNDEFINED

        if kind == 'Delete':
            target = node[1]
            if target[0] == 'Member':
                obj = self._eval(target[1], env)
                if isinstance(obj, JSObject):
                    obj.delete(target[2])
            elif target[0] == 'Index':
                obj = self._eval(target[1], env)
                idx = js_to_string(self._eval(target[2], env))
                if isinstance(obj, JSObject):
                    obj.delete(idx)
            return True

        if kind == 'PreOp':
            _, op, target = node
            cur = js_to_number(self._eval(target, env))
            val = cur + 1 if op == '++' else cur - 1
            self._assign(target, val, env)
            return val

        if kind == 'PostOp':
            _, op, target = node
            cur = js_to_number(self._eval(target, env))
            val = cur + 1 if op == '++' else cur - 1
            self._assign(target, val, env)
            return cur

        if kind == 'Ternary':
            _, cond, then, alt = node
            return self._eval(then if js_to_bool(self._eval(cond, env)) else alt, env)

        if kind == 'Comma':
            self._eval(node[1], env)
            return self._eval(node[2], env)

        if kind == 'Spread':
            return self._eval(node[1], env)

        if kind == 'Super':
            return self._this_stack[-1] if self._this_stack else UNDEFINED

        raise JSRuntimeError(f"Unknown node: {kind}")

    def _eval_args(self, arg_nodes, env):
        args = []
        for a in arg_nodes:
            if isinstance(a, tuple) and a[0] == 'Spread':
                spread = self._eval(a[1], env)
                args.extend(self._get_iterable(spread))
            else:
                args.append(self._eval(a, env))
        return args

    def _assign(self, target, val, env):
        kind = target[0]
        if kind == 'ID':
            try:
                env.assign(target[1], val)
            except:
                env.define(target[1], val)
        elif kind == 'Member':
            obj = self._eval(target[1], env)
            self._set_member(obj, target[2], val)
        elif kind == 'Index':
            obj = self._eval(target[1], env)
            idx = self._eval(target[2], env)
            self._set_index(obj, idx, val)
        elif kind in ('ArrayDestruct', 'ObjectDestruct'):
            self._bind_target(target, val, env)

    def _get_member(self, obj, prop, env=None):
        if isinstance(obj, str):
            return self._string_method(obj, prop)
        if isinstance(obj, float):
            return self._number_method(obj, prop)
        if isinstance(obj, bool):
            return UNDEFINED
        if isinstance(obj, JSArray):
            return self._array_method(obj, prop)
        if isinstance(obj, JSObject):
            return obj.get(prop)
        if isinstance(obj, JSFunction):
            return obj.get(prop)
        if isinstance(obj, JSClass):
            return obj.static_props.get(prop, UNDEFINED)
        if isinstance(obj, JSRegex):
            return obj.props.get(prop, UNDEFINED) if hasattr(obj, 'props') else UNDEFINED
        return UNDEFINED

    def _get_index(self, obj, idx, env=None):
        key = js_to_string(idx) if not isinstance(idx, str) else idx
        if isinstance(obj, str):
            try:
                i = int(float(key))
                if 0 <= i < len(obj):
                    return obj[i]
            except:
                pass
            return self._string_method(obj, key)
        if isinstance(obj, JSArray):
            try:
                i = int(float(key))
                if 0 <= i < len(obj.items):
                    return obj.items[i]
            except:
                pass
            return self._array_method(obj, key)
        if isinstance(obj, JSObject):
            return obj.get(key)
        return UNDEFINED

    def _set_member(self, obj, prop, val):
        if isinstance(obj, (JSObject, JSArray, JSFunction)):
            obj.set(prop, val)

    def _set_index(self, obj, idx, val):
        key = js_to_string(idx) if not isinstance(idx, str) else idx
        if isinstance(obj, (JSObject, JSArray)):
            obj.set(key, val)

    def _call(self, fn, args, this_val=None, env=None):
        if isinstance(fn, JSFunction):
            if hasattr(fn, '_native'):
                try:
                    return fn._native(*args) or UNDEFINED
                except TypeError as e:
                    return UNDEFINED
            return self._call_js_func(fn, args, this_val)
        if isinstance(fn, JSClass):
            return self._construct(fn, args)
        raise JSRuntimeError(
            f'TypeError: {js_to_string(fn)} is not a function')

    def _call_method(self, method, this_val, args, env=None):
        if isinstance(method, JSFunction):
            if hasattr(method, '_native'):
                try:
                    r = method._native(*args)
                    return UNDEFINED if r is None else r
                except TypeError:
                    return UNDEFINED
            return self._call_js_func(method, args, this_val)
        raise JSRuntimeError(
            f'TypeError: {js_to_string(method)} is not a function')

    def _call_js_func(self, fn, args, this_val=None):
        fn_env = Environment(fn.env)
        # bind params
        for i, param in enumerate(fn.params):
            if param[0] == 'Rest':
                fn_env.define(param[1], JSArray(args[i:]))
            elif param[0] == 'Param':
                target, default = param[1], param[2]
                val = args[i] if i < len(args) else UNDEFINED
                if val is UNDEFINED and default is not None:
                    val = self._eval(default, fn.env)
                self._bind_target(target, val, fn_env)
        fn_env.define('arguments', JSArray(args))
        if not fn.is_arrow:
            self._this_stack.append(
                this_val if this_val is not None else self.global_env.vars)
        try:
            self._exec(fn.body, fn_env)
            return UNDEFINED
        except ReturnSignal as r:
            return r.val
        finally:
            if not fn.is_arrow:
                self._this_stack.pop()

    def _construct(self, cls, args):
        if isinstance(cls, JSFunction):
            if hasattr(cls, '_construct'):
                return cls._construct(*args)
            if hasattr(cls, '_native') and cls._native is None:
                return UNDEFINED
            obj = JSObject()
            obj.prototype = cls.prototype_obj
            self._this_stack.append(obj)
            try:
                self._call_js_func(cls, args, obj)
            except ReturnSignal as r:
                if isinstance(r.val, JSObject):
                    self._this_stack.pop()
                    return r.val
            finally:
                if self._this_stack and self._this_stack[-1] is obj:
                    self._this_stack.pop()
            return obj
        if isinstance(cls, JSClass):
            return self._instantiate_class(cls, args)
        raise JSRuntimeError(
            f'TypeError: {js_to_string(cls)} is not a constructor')

    def _make_class(self, name, superclass_name, methods, env):
        superclass = None
        if superclass_name:
            try:
                superclass = env.get(superclass_name)
            except:
                pass
        cls = JSClass(name, superclass, methods, env)
        for method in methods:
            mname, params, body, is_static = method[1], method[2], method[3], method[4]
            if is_static:
                fn = JSFunction(mname, params, body, env)
                cls.static_props[mname] = fn
        return cls

    def _instantiate_class(self, cls, args):
        obj = JSObject()
        if cls.superclass and isinstance(cls.superclass, JSClass):
            obj.prototype = self._instantiate_class(cls.superclass, [])
        constructor = None
        for method in cls.methods:
            if method[1] == 'constructor':
                constructor = JSFunction(
                    'constructor', method[2], method[3], cls.env)
        if constructor:
            self._this_stack.append(obj)
            try:
                fn_env = Environment(cls.env)
                for i, param in enumerate(constructor.params):
                    if param[0] == 'Rest':
                        fn_env.define(param[1], JSArray(args[i:]))
                    elif param[0] == 'Param':
                        target, default = param[1], param[2]
                        val = args[i] if i < len(args) else UNDEFINED
                        if val is UNDEFINED and default is not None:
                            val = self._eval(default, cls.env)
                        self._bind_target(target, val, fn_env)
                fn_env.define('arguments', JSArray(args))
                self._exec(constructor.body, fn_env)
            except ReturnSignal:
                pass
            finally:
                if self._this_stack and self._this_stack[-1] is obj:
                    self._this_stack.pop()
        # bind methods
        for method in cls.methods:
            mname, params, body, is_static = method[1], method[2], method[3], method[4]
            if not is_static and mname != 'constructor':
                fn = JSFunction(mname, params, body, cls.env)
                obj.set(mname, fn)
        return obj

    def _apply_op(self, op, l, r):
        if op == '+':
            if isinstance(l, str) or isinstance(r, str):
                return js_to_string(l) + js_to_string(r)
            if isinstance(l, (JSObject, JSArray)) or isinstance(r, (JSObject, JSArray)):
                ls = js_to_string(l)
                rs = js_to_string(r)
                try:
                    return js_to_number(ls) + js_to_number(rs)
                except:
                    return ls + rs
            return js_to_number(l) + js_to_number(r)
        if op == '-':
            return js_to_number(l) - js_to_number(r)
        if op == '*':
            return js_to_number(l) * js_to_number(r)
        if op == '/':
            d = js_to_number(r)
            n = js_to_number(l)
            if d == 0:
                return float('inf') if n > 0 else (float('-inf') if n < 0 else float('nan'))
            return n / d
        if op == '%':
            d = js_to_number(r)
            n = js_to_number(l)
            if d == 0:
                return float('nan')
            result = math.fmod(n, d)
            return result
        if op == '**':
            return js_to_number(l) ** js_to_number(r)
        if op == '===':
            return js_strict_equal(l, r)
        if op == '!==':
            return not js_strict_equal(l, r)
        if op == '==':
            return js_loose_equal(l, r)
        if op == '!=':
            return not js_loose_equal(l, r)
        if op == '<':
            return js_to_number(l) < js_to_number(r) if not (isinstance(l, str) and isinstance(r, str)) else l < r
        if op == '>':
            return js_to_number(l) > js_to_number(r) if not (isinstance(l, str) and isinstance(r, str)) else l > r
        if op == '<=':
            return js_to_number(l) <= js_to_number(r) if not (isinstance(l, str) and isinstance(r, str)) else l <= r
        if op == '>=':
            return js_to_number(l) >= js_to_number(r) if not (isinstance(l, str) and isinstance(r, str)) else l >= r
        if op == '|':
            return float(int(js_to_number(l)) | int(js_to_number(r)))
        if op == '&':
            return float(int(js_to_number(l)) & int(js_to_number(r)))
        if op == '^':
            return float(int(js_to_number(l)) ^ int(js_to_number(r)))
        if op == '<<':
            return float(int(js_to_number(l)) << (int(js_to_number(r)) & 31))
        if op == '>>':
            return float(int(js_to_number(l)) >> (int(js_to_number(r)) & 31))
        if op == '>>>':
            v = int(js_to_number(l)) & 0xFFFFFFFF
            return float(v >> (int(js_to_number(r)) & 31))
        if op == 'instanceof':
            if isinstance(r, JSFunction) and hasattr(r, 'prototype_obj'):
                return r.prototype_obj is getattr(l, 'prototype', None)
            return False
        if op == 'in':
            if isinstance(r, JSObject):
                return r.has(js_to_string(l))
            return False
        return UNDEFINED

    # ── STRING METHODS ──

    def _string_method(self, s, prop):
        interp = self
        if prop == 'length':
            return float(len(s))
        if prop == 'split':
            def _split(sep=UNDEFINED, limit=UNDEFINED):
                if sep is UNDEFINED:
                    return JSArray([s])
                if isinstance(sep, JSRegex):
                    parts = sep.compiled.split(s)
                else:
                    sep_s = js_to_string(sep)
                    parts = s.split(sep_s) if sep_s != '' else list(s)
                lim = int(js_to_number(limit)
                          ) if limit is not UNDEFINED else len(parts)+1
                return JSArray(parts[:lim])
            return interp._native('split', _split)
        if prop == 'join':
            return interp._native('join', lambda sep=',': js_to_string(sep).join(s))
        if prop == 'trim':
            return interp._native('trim', lambda: s.strip())
        if prop == 'trimStart' or prop == 'trimLeft':
            return interp._native(prop, lambda: s.lstrip())
        if prop == 'trimEnd' or prop == 'trimRight':
            return interp._native(prop, lambda: s.rstrip())
        if prop == 'toUpperCase' or prop == 'toLocaleUpperCase':
            return interp._native(prop, lambda: s.upper())
        if prop == 'toLowerCase' or prop == 'toLocaleLowerCase':
            return interp._native(prop, lambda: s.lower())
        if prop == 'includes':
            return interp._native('includes', lambda sub, pos=0.0: js_to_string(sub) in s[int(js_to_number(pos)):])
        if prop == 'startsWith':
            return interp._native('startsWith', lambda sub, pos=0.0: s[int(js_to_number(pos)):].startswith(js_to_string(sub)))
        if prop == 'endsWith':
            return interp._native('endsWith', lambda sub, end=UNDEFINED: s[:int(js_to_number(end)) if end is not UNDEFINED else len(s)].endswith(js_to_string(sub)))
        if prop == 'indexOf':
            return interp._native('indexOf', lambda sub, pos=0.0: float(s.find(js_to_string(sub), int(js_to_number(pos)))))
        if prop == 'lastIndexOf':
            return interp._native('lastIndexOf', lambda sub, pos=UNDEFINED: float(s.rfind(js_to_string(sub), 0, int(js_to_number(pos))+1 if pos is not UNDEFINED else len(s))))
        if prop == 'slice':
            def _slice(start=UNDEFINED, end=UNDEFINED):
                st = int(js_to_number(start)) if start is not UNDEFINED else 0
                if st < 0:
                    st = max(0, len(s) + st)
                if end is UNDEFINED:
                    return s[st:]
                en = int(js_to_number(end))
                if en < 0:
                    en = max(0, len(s) + en)
                return s[st:en]
            return interp._native('slice', _slice)
        if prop == 'substring':
            def _substring(start=0.0, end=UNDEFINED):
                st = max(0, int(js_to_number(start)))
                en = len(s) if end is UNDEFINED else max(
                    0, int(js_to_number(end)))
                if st > en:
                    st, en = en, st
                return s[st:en]
            return interp._native('substring', _substring)
        if prop == 'substr':
            def _substr(start=0.0, length=UNDEFINED):
                st = int(js_to_number(start))
                if st < 0:
                    st = max(0, len(s) + st)
                if length is UNDEFINED:
                    return s[st:]
                ln = max(0, int(js_to_number(length)))
                return s[st:st+ln]
            return interp._native('substr', _substr)
        if prop == 'replace':
            def _replace(pattern, replacement):
                if isinstance(pattern, JSRegex):
                    if isinstance(replacement, JSFunction):
                        def repl_fn(m):
                            groups = [m.group(0)] + list(m.groups())
                            return js_to_string(interp._call(replacement, [js_to_string(g) if g else '' for g in groups]))
                        if pattern.global_:
                            return pattern.compiled.sub(repl_fn, s)
                        return pattern.compiled.sub(repl_fn, s, count=1)
                    repl = js_to_string(replacement)
                    repl = repl.replace('$&', r'\g<0>')
                    if pattern.global_:
                        return pattern.compiled.sub(repl, s)
                    return pattern.compiled.sub(repl, s, count=1)
                pat = js_to_string(pattern)
                if isinstance(replacement, JSFunction):
                    idx = s.find(pat)
                    if idx == -1:
                        return s
                    rep = js_to_string(interp._call(
                        replacement, [pat, float(idx), s]))
                    return s[:idx] + rep + s[idx+len(pat):]
                return s.replace(pat, js_to_string(replacement), 1)
            return interp._native('replace', _replace)
        if prop == 'replaceAll':
            def _replaceAll(pattern, replacement):
                pat = js_to_string(pattern)
                if isinstance(replacement, JSFunction):
                    result = ''
                    start = 0
                    while True:
                        idx = s.find(pat, start)
                        if idx == -1:
                            result += s[start:]
                            break
                        rep = js_to_string(interp._call(
                            replacement, [pat, float(idx), s]))
                        result += s[start:idx] + rep
                        start = idx + len(pat)
                    return result
                return s.replace(pat, js_to_string(replacement))
            return interp._native('replaceAll', _replaceAll)
        if prop == 'repeat':
            return interp._native('repeat', lambda n: s * int(js_to_number(n)))
        if prop == 'padStart':
            def _padStart(length, fill=' '):
                ln = int(js_to_number(length))
                f = js_to_string(fill) if fill is not UNDEFINED else ' '
                if len(s) >= ln:
                    return s
                pad_needed = ln - len(s)
                pad = (f * (pad_needed // len(f) + 1))[:pad_needed]
                return pad + s
            return interp._native('padStart', _padStart)
        if prop == 'padEnd':
            def _padEnd(length, fill=' '):
                ln = int(js_to_number(length))
                f = js_to_string(fill) if fill is not UNDEFINED else ' '
                if len(s) >= ln:
                    return s
                pad_needed = ln - len(s)
                pad = (f * (pad_needed // len(f) + 1))[:pad_needed]
                return s + pad
            return interp._native('padEnd', _padEnd)
        if prop == 'charAt':
            return interp._native('charAt', lambda i=0.0: s[int(js_to_number(i))] if 0 <= int(js_to_number(i)) < len(s) else '')
        if prop == 'charCodeAt':
            return interp._native('charCodeAt', lambda i=0.0: float(ord(s[int(js_to_number(i))])) if 0 <= int(js_to_number(i)) < len(s) else float('nan'))
        if prop == 'codePointAt':
            return interp._native('codePointAt', lambda i=0.0: float(ord(s[int(js_to_number(i))])) if 0 <= int(js_to_number(i)) < len(s) else UNDEFINED)
        if prop == 'at':
            def _at(i=0.0):
                idx = int(js_to_number(i))
                if idx < 0:
                    idx = len(s) + idx
                return s[idx] if 0 <= idx < len(s) else UNDEFINED
            return interp._native('at', _at)
        if prop == 'concat':
            return interp._native('concat', lambda *args: s + ''.join(js_to_string(a) for a in args))
        if prop == 'match':
            def _match(pattern):
                if isinstance(pattern, JSRegex):
                    if pattern.global_:
                        matches = pattern.compiled.findall(s)
                        if not matches:
                            return NULL
                        return JSArray([m if isinstance(m, str) else m[0] for m in matches])
                    m = pattern.compiled.search(s)
                    if not m:
                        return NULL
                    arr = JSArray([m.group(0)] + list(m.groups()))
                    arr.set('index', float(m.start()))
                    return arr
                pat = js_to_string(pattern)
                idx = s.find(pat)
                if idx == -1:
                    return NULL
                arr = JSArray([pat])
                arr.set('index', float(idx))
                return arr
            return interp._native('match', _match)
        if prop == 'search':
            def _search(pattern):
                if isinstance(pattern, JSRegex):
                    m = pattern.compiled.search(s)
                    return float(m.start()) if m else -1.0
                return float(s.find(js_to_string(pattern)))
            return interp._native('search', _search)
        if prop == 'toString' or prop == 'valueOf':
            return interp._native(prop, lambda: s)
        if prop == 'normalize':
            return interp._native('normalize', lambda form='NFC': s)
        # try numeric index
        try:
            idx = int(float(prop))
            if 0 <= idx < len(s):
                return s[idx]
        except:
            pass
        return UNDEFINED

    def _number_method(self, n, prop):
        interp = self
        if prop == 'toString':
            def _toStr(radix=10.0):
                r = int(js_to_number(radix))
                if r == 10:
                    return js_to_string(n)
                if n == int(n):
                    formats = {2: 'b', 8: 'o', 16: 'x'}
                    fmt = formats.get(r, 'd')
                    return format(int(n), fmt)
                return js_to_string(n)
            return interp._native('toString', _toStr)
        if prop == 'toFixed':
            def _toFixed(digits=0.0):
                d = int(js_to_number(digits))
                return f'{n:.{d}f}'
            return interp._native('toFixed', _toFixed)
        if prop == 'toPrecision':
            def _toPrecision(prec=UNDEFINED):
                if prec is UNDEFINED:
                    return js_to_string(n)
                p = int(js_to_number(prec))
                return f'{n:.{p}g}'
            return interp._native('toPrecision', _toPrecision)
        if prop == 'valueOf':
            return interp._native('valueOf', lambda: n)
        return UNDEFINED

    # ── ARRAY METHODS ──

    def _array_method(self, arr, prop):
        interp = self
        if prop == 'length':
            return float(len(arr.items))
        if prop == 'push':
            def _push(*args):
                arr.items.extend(args)
                return float(len(arr.items))
            return interp._native('push', _push)
        if prop == 'pop':
            return interp._native('pop', lambda: arr.items.pop() if arr.items else UNDEFINED)
        if prop == 'shift':
            return interp._native('shift', lambda: arr.items.pop(0) if arr.items else UNDEFINED)
        if prop == 'unshift':
            def _unshift(*args):
                arr.items = list(args) + arr.items
                return float(len(arr.items))
            return interp._native('unshift', _unshift)
        if prop == 'splice':
            def _splice(start=0.0, deleteCount=UNDEFINED, *insertItems):
                st = int(js_to_number(start))
                if st < 0:
                    st = max(0, len(arr.items) + st)
                dc = int(js_to_number(deleteCount)) if deleteCount is not UNDEFINED else len(arr.items) - st
                removed = arr.items[st:st+dc]
                arr.items = arr.items[:st] + list(insertItems) + arr.items[st+dc:]
                return JSArray(removed)
            return interp._native('splice', _splice)
        if prop == 'slice':
            def _slice(start=0.0, end=UNDEFINED):
                st = int(js_to_number(start))
                if st < 0:
                    st = max(0, len(arr.items) + st)
                if end is UNDEFINED:
                    return JSArray(arr.items[st:])
                en = int(js_to_number(end))
                if en < 0:
                    en = max(0, len(arr.items) + en)
                return JSArray(arr.items[st:en])
            return interp._native('slice', _slice)
        if prop == 'concat':
            def _concat(*args):
                result = list(arr.items)
                for a in args:
                    if isinstance(a, JSArray):
                        result.extend(a.items)
                    else:
                        result.append(a)
                return JSArray(result)
            return interp._native('concat', _concat)
        if prop == 'join':
            def _join(sep=','):
                return js_to_string(sep).join(js_to_string(x) for x in arr.items)
            return interp._native('join', _join)
        if prop == 'indexOf':
            def _indexOf(searchElement, fromIndex=0.0):
                f = int(js_to_number(fromIndex))
                if f < 0:
                    f = max(0, len(arr.items) + f)
                for i in range(f, len(arr.items)):
                    if js_strict_equal(arr.items[i], searchElement):
                        return float(i)
                return -1.0
            return interp._native('indexOf', _indexOf)
        if prop == 'lastIndexOf':
            def _lastIndexOf(searchElement, fromIndex=UNDEFINED):
                f = len(arr.items) - 1 if fromIndex is UNDEFINED else int(js_to_number(fromIndex))
                for i in range(f, -1, -1):
                    if js_strict_equal(arr.items[i], searchElement):
                        return float(i)
                return -1.0
            return interp._native('lastIndexOf', _lastIndexOf)
        if prop == 'includes':
            def _includes(searchElement, fromIndex=0.0):
                f = int(js_to_number(fromIndex))
                if f < 0:
                    f = max(0, len(arr.items) + f)
                for i in range(f, len(arr.items)):
                    if js_strict_equal(arr.items[i], searchElement):
                        return True
                return False
            return interp._native('includes', _includes)
        if prop == 'forEach':
            def _forEach(fn):
                for i, item in enumerate(arr.items):
                    interp._call(fn, [item, float(i), arr])
                return UNDEFINED
            return interp._native('forEach', _forEach)
        if prop == 'map':
            def _map(fn):
                result = []
                for i, item in enumerate(arr.items):
                    result.append(interp._call(fn, [item, float(i), arr]))
                return JSArray(result)
            return interp._native('map', _map)
        if prop == 'filter':
            def _filter(fn):
                result = []
                for i, item in enumerate(arr.items):
                    if js_to_bool(interp._call(fn, [item, float(i), arr])):
                        result.append(item)
                return JSArray(result)
            return interp._native('filter', _filter)
        if prop == 'reduce':
            def _reduce(fn, initialValue=UNDEFINED):
                if initialValue is UNDEFINED:
                    if not arr.items:
                        raise JSRuntimeError('TypeError: reduce of empty array with no initial value')
                    acc = arr.items[0]
                    for i in range(1, len(arr.items)):
                        acc = interp._call(fn, [acc, arr.items[i], float(i), arr])
                else:
                    acc = initialValue
                    for i, item in enumerate(arr.items):
                        acc = interp._call(fn, [acc, item, float(i), arr])
                return acc
            return interp._native('reduce', _reduce)
        if prop == 'reduceRight':
            def _reduceRight(fn, initialValue=UNDEFINED):
                rev = list(reversed(arr.items))
                if initialValue is UNDEFINED:
                    if not rev:
                        raise JSRuntimeError('TypeError: reduceRight of empty array with no initial value')
                    acc = rev[0]
                    for i in range(1, len(rev)):
                        acc = interp._call(fn, [acc, rev[i], float(len(rev) - 1 - i), arr])
                else:
                    acc = initialValue
                    for i, item in enumerate(rev):
                        acc = interp._call(fn, [acc, item, float(len(rev) - 1 - i), arr])
                return acc
            return interp._native('reduceRight', _reduceRight)
        if prop == 'find':
            def _find(fn):
                for i, item in enumerate(arr.items):
                    if js_to_bool(interp._call(fn, [item, float(i), arr])):
                        return item
                return UNDEFINED
            return interp._native('find', _find)
        if prop == 'findIndex':
            def _findIndex(fn):
                for i, item in enumerate(arr.items):
                    if js_to_bool(interp._call(fn, [item, float(i), arr])):
                        return float(i)
                return -1.0
            return interp._native('findIndex', _findIndex)
        if prop == 'some':
            def _some(fn):
                for i, item in enumerate(arr.items):
                    if js_to_bool(interp._call(fn, [item, float(i), arr])):
                        return True
                return False
            return interp._native('some', _some)
        if prop == 'every':
            def _every(fn):
                for i, item in enumerate(arr.items):
                    if not js_to_bool(interp._call(fn, [item, float(i), arr])):
                        return False
                return True
            return interp._native('every', _every)
        if prop == 'sort':
            def _sort(compareFn=UNDEFINED):
                if compareFn is UNDEFINED:
                    arr.items.sort(key=lambda x: js_to_string(x).lower() if isinstance(x, str) else js_to_string(x))
                else:
                    def py_cmp(a, b):
                        r = js_to_number(interp._call(compareFn, [a, b]))
                        if r < 0:
                            return -1
                        if r > 0:
                            return 1
                        return 0
                    arr.items.sort(key=functools.cmp_to_key(py_cmp))
                return arr
            return interp._native('sort', _sort)
        if prop == 'reverse':
            def _reverse():
                arr.items.reverse()
                return arr
            return interp._native('reverse', _reverse)
        if prop == 'toString':
            return interp._native('toString', lambda: js_to_string(arr))
        if prop == 'fill':
            def _fill(value, start=0.0, end=UNDEFINED):
                st = int(js_to_number(start))
                if st < 0:
                    st = max(0, len(arr.items) + st)
                en = len(arr.items) if end is UNDEFINED else int(js_to_number(end))
                if en < 0:
                    en = max(0, len(arr.items) + en)
                for i in range(st, en):
                    arr.items[i] = value
                return arr
            return interp._native('fill', _fill)
        if prop == 'flat':
            def _flat(depth=1.0):
                d = int(js_to_number(depth))

                def do_flat(items, depth):
                    result = []
                    for item in items:
                        if depth > 0 and isinstance(item, JSArray):
                            result.extend(do_flat(item.items, depth - 1))
                        else:
                            result.append(item)
                    return result
                return JSArray(do_flat(arr.items, d))
            return interp._native('flat', _flat)
        # try numeric index for strings
        try:
            idx = int(float(prop))
            if 0 <= idx < len(arr.items):
                return arr.items[idx]
        except:
            pass
        return UNDEFINED
