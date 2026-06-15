from ..tokenizer.tokenizer import tokenize, KEYWORDS


class ParseError(Exception):
    pass


def parse_js_string(s):
    if s.startswith('"') or s.startswith("'"):
        inner = s[1:-1]
        return (inner.replace('\\"', '"').replace("\\'", "'")
                     .replace('\\n', '\n').replace('\\t', '\t')
                     .replace('\\r', '\r').replace('\\\\', '\\')
                     .replace('\\0', '\0'))
    return s[1:-1]


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self, offset=0):
        i = self.pos + offset
        if i < len(self.tokens):
            return self.tokens[i]
        return ('EOF', '')

    def consume(self, expected=None):
        tok = self.tokens[self.pos]
        if expected and tok[0] != expected and tok[1] != expected:
            raise ParseError(f"Expected {expected!r}, got {tok!r}")
        self.pos += 1
        return tok

    def match(self, *vals):
        tok = self.peek()
        if tok[0] in vals or tok[1] in vals:
            self.pos += 1
            return tok
        return None

    def check(self, *vals):
        tok = self.peek()
        return tok[0] in vals or tok[1] in vals

    def consume_prop_name(self):
        """Consume a property name after '.' — accepts IDs or any keyword."""
        tok = self.peek()
        if tok[0] == 'ID':
            self.pos += 1
            return tok[1]
        # Keywords (tok[0] == tok[1]) are also valid property names
        if tok[0] == tok[1] and tok[0] in KEYWORDS:
            self.pos += 1
            return tok[1]
        raise ParseError(f"Expected property name, got {tok!r}")

    def parse(self):
        stmts = []
        while not self.check('EOF'):
            stmts.append(self.parse_stmt())
        return ('Program', stmts)

    def parse_stmt(self):
        t = self.peek()
        if t[1] in ('let', 'const', 'var'):
            return self.parse_var_decl()
        if t[1] == 'function':
            return self.parse_func_decl()
        if t[1] == 'class':
            return self.parse_class_decl()
        if t[1] == 'return':
            return self.parse_return()
        if t[1] == 'if':
            return self.parse_if()
        if t[1] == 'while':
            return self.parse_while()
        if t[1] == 'for':
            return self.parse_for()
        if t[1] == 'do':
            return self.parse_do_while()
        if t[1] == 'break':
            self.consume()
            self.match(';')
            return ('Break',)
        if t[1] == 'continue':
            self.consume()
            self.match(';')
            return ('Continue',)
        if t[1] == 'throw':
            self.consume()
            e = self.parse_expr()
            self.match(';')
            return ('Throw', e)
        if t[1] == 'try':
            return self.parse_try()
        if t[1] == 'switch':
            return self.parse_switch()
        if t[1] == '{':
            return self.parse_block()
        if t[1] == ';':
            self.consume()
            return ('Empty',)
        stmt = ('ExprStmt', self.parse_expr())
        self.match(';')
        return stmt

    def parse_block(self):
        self.consume('{')
        stmts = []
        while not self.check('}') and not self.check('EOF'):
            stmts.append(self.parse_stmt())
        self.consume('}')
        return ('Block', stmts)

    def parse_var_decl(self):
        kind = self.consume()[1]
        decls = []
        while True:
            name = self.parse_destructure_target()
            init = None
            if self.match('='):
                init = self.parse_assign_expr()
            decls.append((name, init))
            if not self.match(','):
                break
        self.match(';')
        return ('VarDecl', kind, decls)

    def parse_destructure_target(self):
        if self.check('['):
            return self.parse_array_destructure()
        if self.check('{'):
            return self.parse_object_destructure()
        return ('ID', self.consume('ID')[1])

    def parse_array_destructure(self):
        self.consume('[')
        elems = []
        while not self.check(']'):
            if self.check(','):
                elems.append(None)
                self.consume()
                continue
            if self.match('...'):
                name = self.consume('ID')[1]
                elems.append(('Rest', name))
                break
            target = self.parse_destructure_target()
            default = None
            if self.match('='):
                default = self.parse_assign_expr()
            elems.append(('Elem', target, default))
            if not self.match(','):
                break
        self.consume(']')
        return ('ArrayDestruct', elems)

    def parse_object_destructure(self):
        self.consume('{')
        props = []
        while not self.check('}'):
            if self.match('...'):
                name = self.consume('ID')[1]
                props.append(('RestProp', name))
                break
            key = self.consume('ID')[1]
            if self.match(':'):
                target = self.parse_destructure_target()
            else:
                target = ('ID', key)
            default = None
            if self.match('='):
                default = self.parse_assign_expr()
            props.append(('Prop', key, target, default))
            if not self.match(','):
                break
        self.consume('}')
        return ('ObjectDestruct', props)

    def parse_func_decl(self):
        self.consume('function')
        is_gen = bool(self.match('*'))
        name = None
        if self.check('ID'):
            name = self.consume()[1]
        params = self.parse_params()
        body = self.parse_block()
        return ('FuncDecl', name, params, body, is_gen)

    def parse_params(self):
        self.consume('(')
        params = []
        while not self.check(')'):
            if self.match('...'):
                name = self.consume('ID')[1]
                params.append(('Rest', name))
                break
            target = self.parse_destructure_target()
            default = None
            if self.match('='):
                default = self.parse_assign_expr()
            params.append(('Param', target, default))
            if not self.match(','):
                break
        self.consume(')')
        return params

    def parse_class_decl(self):
        self.consume('class')
        name = self.consume('ID')[1]
        superclass = None
        if self.match('extends'):
            superclass = self.consume('ID')[1]
        self.consume('{')
        methods = []
        while not self.check('}'):
            is_static = bool(self.match('static'))
            is_async = bool(self.match('async'))
            is_get = False
            is_set = False
            if self.check('ID') and self.peek()[1] in ('get', 'set'):
                peek2 = self.peek(1)
                if peek2[0] == 'ID' or peek2[1] in ('constructor', '*'):
                    gs = self.consume()[1]
                    is_get = gs == 'get'
                    is_set = gs == 'set'
            is_gen = bool(self.match('*'))
            mname = self.peek()[1] if self.check('ID') else self.consume()[1]
            if self.check('ID'):
                mname = self.consume()[1]
            params = self.parse_params()
            body = self.parse_block()
            methods.append(('Method', mname, params, body,
                           is_static, is_get, is_set, is_async))
        self.consume('}')
        return ('ClassDecl', name, superclass, methods)

    def parse_return(self):
        self.consume('return')
        if self.check(';') or self.check('EOF') or self.check('}'):
            self.match(';')
            return ('Return', None)
        val = self.parse_expr()
        self.match(';')
        return ('Return', val)

    def parse_if(self):
        self.consume('if')
        self.consume('(')
        cond = self.parse_expr()
        self.consume(')')
        then = self.parse_stmt()
        alt = None
        if self.match('else'):
            alt = self.parse_stmt()
        return ('If', cond, then, alt)

    def parse_while(self):
        self.consume('while')
        self.consume('(')
        cond = self.parse_expr()
        self.consume(')')
        body = self.parse_stmt()
        return ('While', cond, body)

    def parse_do_while(self):
        self.consume('do')
        body = self.parse_stmt()
        self.consume('while')
        self.consume('(')
        cond = self.parse_expr()
        self.consume(')')
        self.match(';')
        return ('DoWhile', body, cond)

    def parse_for(self):
        self.consume('for')
        self.consume('(')
        init_node = None
        if self.check('EOF') or self.check(';'):
            init_node = None
            self.match(';')
        else:
            if self.peek()[1] in ('let', 'const', 'var'):
                kind = self.consume()[1]
                target = self.parse_destructure_target()
                if self.check('of'):
                    self.consume('of')
                    iterable = self.parse_expr()
                    self.consume(')')
                    body = self.parse_stmt()
                    return ('ForOf', kind, target, iterable, body)
                if self.check('in'):
                    self.consume('in')
                    obj = self.parse_expr()
                    self.consume(')')
                    body = self.parse_stmt()
                    return ('ForIn', kind, target, obj, body)
                init_val = None
                if self.match('='):
                    init_val = self.parse_assign_expr()
                decls = [(target, init_val)]
                while self.match(','):
                    t2 = self.parse_destructure_target()
                    v2 = None
                    if self.match('='):
                        v2 = self.parse_assign_expr()
                    decls.append((t2, v2))
                init_node = ('VarDecl', kind, decls)
                self.consume(';')
            else:
                if not self.check(';'):
                    init_node = ('ExprStmt', self.parse_expr())
                self.consume(';')
        cond_node = None
        if not self.check(';'):
            cond_node = self.parse_expr()
        self.consume(';')
        update_node = None
        if not self.check(')'):
            update_node = self.parse_expr()
        self.consume(')')
        body = self.parse_stmt()
        return ('For', init_node, cond_node, update_node, body)

    def parse_try(self):
        self.consume('try')
        body = self.parse_block()
        catch_clause = None
        finally_clause = None
        if self.match('catch'):
            param = None
            if self.match('('):
                param = self.consume('ID')[1]
                self.consume(')')
            catch_body = self.parse_block()
            catch_clause = (param, catch_body)
        if self.match('finally'):
            finally_clause = self.parse_block()
        return ('Try', body, catch_clause, finally_clause)

    def parse_switch(self):
        self.consume('switch')
        self.consume('(')
        disc = self.parse_expr()
        self.consume(')')
        self.consume('{')
        cases = []
        while not self.check('}'):
            if self.match('case'):
                val = self.parse_expr()
                self.consume(':')
                stmts = []
                while not self.check('case') and not self.check('default') and not self.check('}'):
                    stmts.append(self.parse_stmt())
                cases.append(('Case', val, stmts))
            elif self.match('default'):
                self.consume(':')
                stmts = []
                while not self.check('case') and not self.check('default') and not self.check('}'):
                    stmts.append(self.parse_stmt())
                cases.append(('Default', stmts))
        self.consume('}')
        return ('Switch', disc, cases)

    def parse_expr(self):
        return self.parse_comma()

    def parse_comma(self):
        left = self.parse_assign_expr()
        while self.match(','):
            right = self.parse_assign_expr()
            left = ('Comma', left, right)
        return left

    ASSIGN_OPS = {'=', '+=', '-=', '*=', '/=', '%=', '**=',
                  '&&=', '||=', '??=', '<<=', '>>=', '>>>=', '&=', '|=', '^='}

    def parse_assign_expr(self):
        left = self.parse_ternary()
        op = self.peek()
        if op[1] in self.ASSIGN_OPS:
            self.consume()
            right = self.parse_assign_expr()
            return ('Assign', op[1], left, right)
        return left

    def parse_ternary(self):
        cond = self.parse_nullcoalesce()
        if self.match('?'):
            then = self.parse_assign_expr()
            self.consume(':')
            alt = self.parse_assign_expr()
            return ('Ternary', cond, then, alt)
        return cond

    def parse_nullcoalesce(self):
        left = self.parse_or()
        while self.check('??'):
            self.consume()
            right = self.parse_or()
            left = ('BinOp', '??', left, right)
        return left

    def parse_or(self):
        left = self.parse_and()
        while self.check('||'):
            self.consume()
            right = self.parse_and()
            left = ('BinOp', '||', left, right)
        return left

    def parse_and(self):
        left = self.parse_bitor()
        while self.check('&&'):
            self.consume()
            right = self.parse_bitor()
            left = ('BinOp', '&&', left, right)
        return left

    def parse_bitor(self):
        left = self.parse_bitxor()
        while self.peek()[1] == '|' and self.peek(1)[1] != '|' and self.peek(1)[1] != '=':
            self.consume()
            right = self.parse_bitxor()
            left = ('BinOp', '|', left, right)
        return left

    def parse_bitxor(self):
        left = self.parse_bitand()
        while self.peek()[1] == '^' and self.peek(1)[1] != '=':
            self.consume()
            right = self.parse_bitand()
            left = ('BinOp', '^', left, right)
        return left

    def parse_bitand(self):
        left = self.parse_equality()
        while self.peek()[1] == '&' and self.peek(1)[1] not in ('&', '='):
            self.consume()
            right = self.parse_equality()
            left = ('BinOp', '&', left, right)
        return left

    def parse_equality(self):
        left = self.parse_relational()
        while self.peek()[1] in ('===', '!==', '==', '!='):
            op = self.consume()[1]
            right = self.parse_relational()
            left = ('BinOp', op, left, right)
        return left

    def parse_relational(self):
        left = self.parse_shift()
        while self.peek()[1] in ('<', '>', '<=', '>=', 'instanceof', 'in'):
            op = self.consume()[1]
            right = self.parse_shift()
            left = ('BinOp', op, left, right)
        return left

    def parse_shift(self):
        left = self.parse_additive()
        while self.peek()[1] in ('<<', '>>', '>>>'):
            op = self.consume()[1]
            right = self.parse_additive()
            left = ('BinOp', op, left, right)
        return left

    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.peek()[1] in ('+', '-') and self.peek(1)[1] != '=':
            op = self.consume()[1]
            right = self.parse_multiplicative()
            left = ('BinOp', op, left, right)
        return left

    def parse_multiplicative(self):
        left = self.parse_exponent()
        while self.peek()[1] in ('*', '/', '%') and self.peek(1)[1] not in ('*', '=', '/'):
            op = self.consume()[1]
            right = self.parse_exponent()
            left = ('BinOp', op, left, right)
        return left

    def parse_exponent(self):
        left = self.parse_unary()
        if self.peek()[1] == '**' and self.peek(1)[1] != '=':
            self.consume()
            right = self.parse_exponent()
            return ('BinOp', '**', left, right)
        return left

    def parse_unary(self):
        t = self.peek()
        if t[1] in ('+', '-', '!', '~'):
            op = self.consume()[1]
            return ('Unary', op, self.parse_unary())
        if t[1] == 'typeof':
            self.consume()
            return ('Typeof', self.parse_unary())
        if t[1] == 'void':
            self.consume()
            return ('Void', self.parse_unary())
        if t[1] == 'delete':
            self.consume()
            return ('Delete', self.parse_unary())
        if t[1] == '++':
            self.consume()
            return ('PreOp', '++', self.parse_unary())
        if t[1] == '--':
            self.consume()
            return ('PreOp', '--', self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self):
        expr = self.parse_call_expr()
        while self.peek()[1] in ('++', '--'):
            op = self.consume()[1]
            expr = ('PostOp', op, expr)
        return expr

    def parse_call_expr(self):
        expr = self.parse_new_expr()
        while True:
            if self.match('.'):
                prop = self.consume_prop_name()
                expr = ('Member', expr, prop)
            elif self.check('['):
                self.consume('[')
                idx = self.parse_expr()
                self.consume(']')
                expr = ('Index', expr, idx)
            elif self.check('('):
                args = self.parse_args()
                expr = ('Call', expr, args)
            elif self.match('?.'):
                if self.check('('):
                    args = self.parse_args()
                    expr = ('OptCall', expr, args)
                elif self.check('['):
                    self.consume('[')
                    idx = self.parse_expr()
                    self.consume(']')
                    expr = ('OptIndex', expr, idx)
                else:
                    prop = self.consume_prop_name()
                    expr = ('OptMember', expr, prop)
            else:
                break
        return expr

    def parse_new_expr(self):
        if self.match('new'):
            callee = self.parse_new_expr()
            args = []
            if self.check('('):
                args = self.parse_args()
            return ('New', callee, args)
        return self.parse_primary()

    def parse_args(self):
        self.consume('(')
        args = []
        while not self.check(')'):
            if self.match('...'):
                args.append(('Spread', self.parse_assign_expr()))
            else:
                args.append(self.parse_assign_expr())
            if not self.match(','):
                break
        self.consume(')')
        return args

    def parse_primary(self):
        t = self.peek()

        if t[1] == 'async' and self.peek(1)[1] == 'function':
            self.consume()
            return self.parse_func_expr(is_async=True)
        if t[1] == 'async' and self.peek(1)[0] == 'ID':
            self.consume()
            param_name = self.consume('ID')[1]
            self.consume('=>')
            if self.check('{'):
                body = self.parse_block()
            else:
                body = ('Return', self.parse_assign_expr())
            return ('Arrow', [('Param', ('ID', param_name), None)], body, True)
        if t[1] == 'function':
            return self.parse_func_expr()
        if t[1] == 'class':
            return self.parse_class_expr()

        if t[0] == 'NUMBER':
            self.consume()
            return ('Num', float(t[1]))
        if t[0] == 'STRING':
            self.consume()
            return ('Str', parse_js_string(t[1]))
        if t[0] == 'TEMPLATE':
            self.consume()
            return self.parse_template(t[1])
        if t[0] == 'REGEX':
            self.consume()
            return ('Regex', t[1])
        if t[1] == 'true':
            self.consume()
            return ('Bool', True)
        if t[1] == 'false':
            self.consume()
            return ('Bool', False)
        if t[1] == 'null':
            self.consume()
            return ('Null',)
        if t[1] == 'undefined':
            self.consume()
            return ('Undefined',)
        if t[1] == 'this':
            self.consume()
            return ('This',)
        if t[1] == 'super':
            self.consume()
            return ('Super',)

        if t[0] == 'ID':
            if self.peek(1)[1] == '=>':
                name = self.consume()[1]
                self.consume('=>')
                if self.check('{'):
                    body = self.parse_block()
                else:
                    body = ('Return', self.parse_assign_expr())
                return ('Arrow', [('Param', ('ID', name), None)], body, False)
            return ('ID', self.consume()[1])

        if t[1] == '(':
            saved = self.pos
            try:
                params = self.parse_params()
                if self.check('=>'):
                    self.consume('=>')
                    if self.check('{'):
                        body = self.parse_block()
                    else:
                        body = ('Return', self.parse_assign_expr())
                    return ('Arrow', params, body, False)
                else:
                    self.pos = saved
            except Exception:
                self.pos = saved
            self.consume('(')
            expr = self.parse_expr()
            self.consume(')')
            return expr

        if t[1] == '[':
            return self.parse_array_literal()
        if t[1] == '{':
            return self.parse_object_literal()
        if t[1] == '...':
            self.consume()
            return ('Spread', self.parse_assign_expr())

        raise ParseError(f"Unexpected token {t!r}")

    def parse_func_expr(self, is_async=False):
        self.consume('function')
        is_gen = bool(self.match('*'))
        name = None
        if self.check('ID'):
            name = self.consume()[1]
        params = self.parse_params()
        body = self.parse_block()
        return ('FuncExpr', name, params, body, is_gen, is_async)

    def parse_class_expr(self):
        self.consume('class')
        name = None
        if self.check('ID'):
            name = self.consume()[1]
        superclass = None
        if self.match('extends'):
            superclass = self.consume('ID')[1]
        self.consume('{')
        methods = []
        while not self.check('}'):
            is_static = bool(self.match('static'))
            is_async = bool(self.match('async'))
            is_get = False
            is_set = False
            if self.check('ID') and self.peek()[1] in ('get', 'set'):
                peek2 = self.peek(1)
                if peek2[0] == 'ID' or peek2[1] in ('constructor',):
                    gs = self.consume()[1]
                    is_get = gs == 'get'
                    is_set = gs == 'set'
            is_gen = bool(self.match('*'))
            mname = self.consume('ID')[1] if self.check(
                'ID') else self.consume()[1]
            params = self.parse_params()
            body = self.parse_block()
            methods.append(('Method', mname, params, body,
                           is_static, is_get, is_set, is_async))
        self.consume('}')
        return ('ClassExpr', name, superclass, methods)

    def parse_array_literal(self):
        self.consume('[')
        elems = []
        while not self.check(']'):
            if self.check(','):
                elems.append(None)
                self.consume()
                continue
            if self.match('...'):
                elems.append(('Spread', self.parse_assign_expr()))
            else:
                elems.append(self.parse_assign_expr())
            if not self.match(','):
                break
        self.consume(']')
        return ('Array', elems)

    def parse_object_literal(self):
        self.consume('{')
        props = []
        while not self.check('}'):
            if self.match('...'):
                props.append(('SpreadProp', self.parse_assign_expr()))
                if not self.match(','):
                    break
                continue
            if self.match('['):
                key = self.parse_assign_expr()
                self.consume(']')
                self.consume(':')
                val = self.parse_assign_expr()
                props.append(('Computed', key, val))
            else:
                t = self.peek()
                if (t[0] == 'ID' or t[0] == 'STRING') and self.peek(1)[1] == '(':
                    name = self.consume()[1]
                    params = self.parse_params()
                    body = self.parse_block()
                    props.append(('Method', name, params, body))
                elif t[0] == 'ID' and self.peek(1)[1] == ':':
                    key = self.consume()[1]
                    self.consume(':')
                    val = self.parse_assign_expr()
                    props.append(('Pair', key, val))
                elif t[0] == 'ID':
                    name = self.consume()[1]
                    props.append(('Shorthand', name))
                elif t[0] == 'STRING':
                    key = parse_js_string(self.consume()[1])
                    self.consume(':')
                    val = self.parse_assign_expr()
                    props.append(('Pair', key, val))
                elif t[0] == 'NUMBER':
                    key = self.consume()[1]
                    self.consume(':')
                    val = self.parse_assign_expr()
                    props.append(('Pair', key, val))
                else:
                    kw = self.consume()[1]
                    if kw in ('get', 'set'):
                        name = self.consume('ID')[1]
                        params = self.parse_params()
                        body = self.parse_block()
                        props.append(('Accessor', kw, name, params, body))
                    else:
                        props.append(('Pair', kw, self.parse_assign_expr()))
            if not self.match(','):
                break
        self.consume('}')
        return ('Object', props)

    def parse_template(self, raw):
        content = raw[1:-1]
        parts = []
        i = 0
        buf = ''
        while i < len(content):
            if content[i] == '$' and i+1 < len(content) and content[i+1] == '{':
                parts.append(('Str', buf))
                buf = ''
                depth = 1
                i += 2
                expr_src = ''
                while i < len(content) and depth > 0:
                    if content[i] == '{':
                        depth += 1
                    elif content[i] == '}':
                        depth -= 1
                    if depth > 0:
                        expr_src += content[i]
                    i += 1
                subtokens = tokenize(expr_src)
                subparser = Parser(subtokens)
                parts.append(subparser.parse_assign_expr())
            elif content[i] == '\\' and i+1 < len(content):
                esc = content[i+1]
                escapes = {'n': '\n', 't': '\t',
                           'r': '\r', '\\': '\\', '`': '`'}
                buf += escapes.get(esc, esc)
                i += 2
            else:
                buf += content[i]
                i += 1
        parts.append(('Str', buf))
        return ('Template', parts)
