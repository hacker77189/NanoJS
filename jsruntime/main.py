"""
CLI entry point.

Usage:
    python -m jsruntime.main script.js
    echo "console.log(42)" | python -m jsruntime.main
"""

import sys
from .api import run_js, run_js_file


def main():
    if len(sys.argv) < 2:
        source = sys.stdin.read()
        lines = run_js(source)
    else:
        lines = run_js_file(sys.argv[1])
    for line in lines:
        print(line)


if __name__ == "__main__":
    main()
