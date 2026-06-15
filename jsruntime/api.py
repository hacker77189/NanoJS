"""
Public API for the JS runtime.

Usage from another file:
    from jsruntime import run_js, run_js_file

    output = run_js("console.log(1 + 2)")
    # returns: ["3"]

    output = run_js_file("script.js")
"""

import sys
from .tokenizer.tokenizer import tokenize
from .parser.parser import Parser, ParseError
from .interpreter.interpreter import Interpreter


def run_js(source: str) -> list[str]:
    """
    Execute a JavaScript source string.
    Returns a list of strings printed via console.log.
    Raises SyntaxError (Python) on parse failure.
    """
    tokens = tokenize(source)
    parser = Parser(tokens)
    try:
        ast = parser.parse()
    except ParseError as e:
        raise SyntaxError(str(e)) from e

    interp = Interpreter()
    interp.run(ast)
    return interp.output_lines


def run_js_file(path: str) -> list[str]:
    """
    Execute a JavaScript file at the given path.
    Returns a list of strings printed via console.log.
    """
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    return run_js(source)
