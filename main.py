import sys
from lexer.tokenizer import tokenize
from parser.parser import Parser
from interpreter.interpreter import Interpreter


def main():
    if len(sys.argv) < 2:
        src = sys.stdin.read()
    else:
        with open(sys.argv[1], 'r') as f:
            src = f.read()

    try:
        tokens = tokenize(src)
        ast = Parser(tokens).parse()
        engine = Interpreter()
        engine.run(ast)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    main()
