import re

TOKEN_TYPES = [
    ('TEMPLATE',    r'`(?:[^`\\]|\\.)*`'),
    ('NUMBER',      r'\d+(\.\d*)?([eE][+-]?\d+)?'),
    ('STRING',      r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\''),
    ('REGEX',       r'/(?!\/)(?:[^/\\\n]|\\.)+/[gimsuy]*'),
    ('COMMENT_ML',  r'/\*[\s\S]*?\*/'),
    ('COMMENT_SL',  r'//[^\n]*'),
    ('NEWLINE',     r'\n'),
    ('WHITESPACE',  r'[ \t\r]+'),
    ('ELLIPSIS',    r'\.\.\.'),
    ('ARROW',       r'=>'),
    ('OP3',         r'===|!==|\*\*=|>>>=|<<=|>>='),
    ('OP2',
     r'[+\-*/%&|^]=|&&|\|\||[+\-]{2}|<<|>>|>>>|[<>]=|[!=]=|\*\*|\?\?'),
    ('OP',          r'[+\-*/%&|^~!<>=?:.,;(){}\[\]]'),
    ('ID',          r'[A-Za-z_$][A-Za-z0-9_$]*'),
]

MASTER_RE = re.compile(
    '|'.join(f'(?P<T{i}>{p})' for i, (_, p) in enumerate(TOKEN_TYPES)))
TOKEN_NAMES = [name for name, _ in TOKEN_TYPES]

KEYWORDS = {
    'let', 'const', 'var', 'function', 'return', 'if', 'else', 'while', 'for', 'do',
    'break', 'continue', 'new', 'this', 'typeof', 'instanceof', 'in', 'of',
    'true', 'false', 'null', 'undefined', 'class', 'extends', 'super',
    'switch', 'case', 'default', 'throw', 'try', 'catch', 'finally', 'delete',
    'void', 'import', 'export', 'async', 'await', 'yield', 'static', 'get', 'set',
}


def tokenize(src):
    tokens = []
    pos = 0
    n = len(src)
    while pos < n:
        m = MASTER_RE.match(src, pos)
        if not m:
            pos += 1
            continue
        kind = TOKEN_NAMES[next(i for i, (name, _) in enumerate(
            TOKEN_TYPES) if m.group(f'T{i}') is not None)]
        val = m.group(0)
        pos = m.end()
        if kind in ('WHITESPACE', 'COMMENT_ML', 'COMMENT_SL'):
            continue
        if kind == 'NEWLINE':
            continue
        if kind == 'ID' and val in KEYWORDS:
            tokens.append((val, val))
        elif kind == 'ID':
            tokens.append(('ID', val))
        elif kind == 'NUMBER':
            tokens.append(('NUMBER', val))
        elif kind in ('STRING', 'TEMPLATE'):
            tokens.append((kind, val))
        elif kind == 'REGEX':
            tokens.append(('REGEX', val))
        else:
            tokens.append((val, val))
    tokens.append(('EOF', ''))
    return tokens
