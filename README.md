# NanoJS — A JavaScript Runtime Written in Python

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-90%20passing-brightgreen)](tests/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](#license)

**NanoJS** is a lightweight JavaScript runtime built from scratch in Python. It tokenizes, parses, and interprets JavaScript code — supporting variables, control flow, functions, arrays, objects, closures, arrow functions, higher-order methods, and more.

No external dependencies. No V8. Just Python.

---

## Features

### Core JavaScript
| Feature | Status |
|---|---|
| Variables (`let`, `const`, `var`) | ✅ |
| Block-scoping | ✅ |
| Arithmetic & string operations | ✅ |
| Control flow (`if`/`else`, `for`, `while`, `do...while`) | ✅ |
| `break` / `continue` | ✅ |
| Functions (declarations, expressions, recursion) | ✅ |
| Arrow functions (`x => x * x`) | ✅ |
| Closures | ✅ |
| Higher-order functions (callbacks) | ✅ |
| Rest parameters (`...args`) | ✅ |
| Default parameters | ✅ |

### Arrays
| Feature | Status |
|---|---|
| Create & index access | ✅ |
| `push`, `pop`, `shift`, `unshift` | ✅ |
| `map`, `filter`, `reduce`, `forEach` | ✅ |
| `find`, `findIndex`, `some`, `every`, `includes` | ✅ |
| `slice`, `splice`, `join`, `concat` | ✅ |
| `sort`, `reverse`, `fill` | ✅ |
| `flat`, `indexOf`, `lastIndexOf` | ✅ |
| `Array.from()`, `Array.of()` | ✅ |
| Spread operator (`...`) | ✅ |
| Array destructuring | ✅ |

### Objects
| Feature | Status |
|---|---|
| Create & property access | ✅ |
| Object methods with `this` | ✅ |
| Computed properties (`[key]: val`) | ✅ |
| `Object.keys()`, `Object.values()`, `Object.entries()` | ✅ |
| `Object.assign()` | ✅ |
| `Object.hasOwn()` | ✅ |

### Strings
| Feature | Status |
|---|---|
| `toUpperCase`, `toLowerCase` | ✅ |
| `includes`, `startsWith`, `endsWith` | ✅ |
| `split`, `slice`, `substring` | ✅ |
| `trim`, `charAt`, `concat` | ✅ |
| `replace`, `replaceAll`, `match`, `search` | ✅ |
| Template literals (concatenation) | ✅ |

### Math
| Feature | Status |
|---|---|
| `Math.PI`, `Math.E`, constants | ✅ |
| `Math.abs`, `Math.ceil`, `Math.floor`, `Math.round` | ✅ |
| `Math.max`, `Math.min`, `Math.pow`, `Math.sqrt` | ✅ |
| `Math.random`, `Math.log`, `Math.sin`, `Math.cos`, etc. | ✅ |

### Other
| Feature | Status |
|---|---|
| `console.log` (multi-arg) | ✅ |
| Ternary operator | ✅ |
| `typeof` operator | ✅ |
| Boolean operators (`&&`, `||`, `!`) | ✅ |
| Classes (basic) | ✅ |
| `try`/`catch`/`finally` | ✅ |
| `switch`/`case` | ✅ |
| `for...of`, `for...in` | ✅ |

---

## Quick Start

### Prerequisites

- **Python 3.9+** ([Download](https://www.python.org/downloads/))

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/NanoJS.git
cd NanoJS

# (Optional) Install pytest for running tests
pip install pytest
```

### Run a JavaScript File

```bash
python -m jsruntime.main script.js
```

### Interactive Mode (stdin)

```bash
echo "console.log('Hello from NanoJS!')" | python -m jsruntime.main
```

### Using the Runner Script

```bash
python runner.py
```

---

## Usage Examples

### Programmatic API

NanoJS exposes a clean Python API. You can embed JavaScript execution directly into Python code:

```python
from jsruntime import run_js, run_js_file

# Execute a JavaScript string
output = run_js("console.log(1 + 2)")
print(output)  # ['3']

# Execute a JavaScript file
output = run_js_file("script.js")
for line in output:
    print(line)
```

### CLI

```bash
# Run a file
python -m jsruntime.main examples/hello.js

# Pipe from stdin
echo "console.log('Hello, World!')" | python -m jsruntime.main
```

### Example: Arrays & Higher-Order Functions

```javascript
let numbers = [1, 2, 3, 4, 5];

let doubled = numbers.map(function(n) { return n * 2; });
console.log(doubled);  // [2, 4, 6, 8, 10]

let evens = numbers.filter(function(n) { return n % 2 === 0; });
console.log(evens);  // [2, 4]

let sum = numbers.reduce(function(acc, n) { return acc + n; }, 0);
console.log(sum);  // 15
```

### Example: Closures

```javascript
function makeCounter() {
    let count = 0;
    return function() {
        count = count + 1;
        return count;
    };
}

let counter = makeCounter();
console.log(counter());  // 1
console.log(counter());  // 2
console.log(counter());  // 3
```

### Example: Objects & Methods

```javascript
let calculator = {
    a: 10,
    b: 5,
    add: function() { return this.a + this.b; },
    subtract: function() { return this.a - this.b; }
};

console.log(calculator.add());       // 15
console.log(calculator.subtract());  // 5
```

---

## Project Structure

```
NanoJS/
├── jsruntime/                 # Core runtime package
│   ├── __init__.py            # Package exports (run_js, run_js_file)
│   ├── api.py                 # Public API
│   ├── main.py                # CLI entry point
│   ├── tokenizer/
│   │   ├── __init__.py
│   │   └── tokenizer.py       # Lexer: source → tokens
│   ├── parser/
│   │   ├── __init__.py
│   │   └── parser.py          # Parser: tokens → AST
│   ├── interpreter/
│   │   ├── __init__.py
│   │   └── interpreter.py     # Interpreter: AST → execution
│   └── runtime/
│       ├── __init__.py
│       ├── values.py           # JS value types (Object, Array, Function, etc.)
│       ├── environment.py      # Variable scoping & environments
│       ├── coercion.py         # Type coercion & conversion
│       └── signals.py          # Control flow signals (return, break, continue)
├── tests/
│   └── test_js_runtime.py     # 90+ pytest unit tests
├── runner.py                  # Quick runner for test.js
├── test.js                    # Comprehensive test script
├── README.md
└── LICENSE
```

### Architecture Pipeline

```
Source Code
    ↓
[Tokenizer]  →  Tokens (list of (type, value) tuples)
    ↓
[Parser]     →  AST (nested tuples)
    ↓
[Interpreter] →  Output (list of strings from console.log)
```

---

## Running Tests

NanoJS uses [pytest](https://docs.pytest.org/) for unit tests. All tests verify expected output values using assertion-based testing.

```bash
# Install pytest
pip install pytest

# Run all tests
python -m pytest tests/ -v

# Run with coverage report
pip install pytest-cov
python -m pytest tests/ --cov=jsruntime --cov-report=term-missing

# Run a specific test class
python -m pytest tests/ -k "TestArrays" -v
```

### Test Coverage

The test suite covers **90+ tests** organized by feature area:

| Test Class | Tests | What's Covered |
|---|---|---|
| `TestBasics` | 7 | Numbers, strings, booleans, arithmetic, comparisons |
| `TestVariables` | 4 | Variable declaration, reassignment, block scope |
| `TestControlFlow` | 6 | if/else, for, while, break, continue |
| `TestArrays` | 22 | All array methods, spread, destructuring, from/of |
| `TestObjects` | 11 | Property access, methods, keys/values/entries/assign |
| `TestFunctions` | 10 | Declarations, recursion, arrows, closures, HOFs |
| `TestCombined` | 6 | Array of objects, pipelines, nested access |
| `TestStrings` | 8 | String methods, template literals |
| `TestMath` | 5 | Constants, abs, max/min, ceil/floor/round, pow/sqrt |
| `TestEdgeCases` | 7 | Empty programs, nested blocks, typeof, booleans |

---
---

## Limitations

- **No DOM/Browser APIs** — this is a command-line runtime only.
- **No `const`/`let` enforcement** — `const` is parsed but behaves like `let`.
- **No `import`/`export`** — ES modules are not supported.
- **No async/await execution** — `async`/`await` is parsed but does not execute asynchronously.
- **Floating-point precision** — numbers use Python floats; some values may display with extra precision (e.g., `3.1400000000000001`).

---

## License

This project is open source. Choose the license that fits your needs — we recommend the [MIT License](https://opensource.org/licenses/MIT).

---

## Contributing

Contributions are welcome! Here's how to get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run the tests to make sure everything passes
4. Add tests for your new feature
5. Submit a pull request

---

*Built with Python. Inspired by JavaScript.*
