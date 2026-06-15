"""
Unit tests for the JavaScript runtime using pytest.

Tests execute JS code via run_js() and assert the console.log output
matches expected values. This validates that the tokenizer, parser,
and interpreter all work correctly together.
"""

import pytest
import sys
import os

# Ensure the project root is on sys.path so we can import jsruntime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from jsruntime import run_js


# =============================================================================
# Helpers
# =============================================================================

def run(src: str) -> list[str]:
    """Shorthand to run JS source and return output lines."""
    return run_js(src)


def assert_output(src: str, expected: list):
    """Assert that running JS source produces the expected output lines."""
    result = run(src)
    assert result == expected, f"Expected {expected!r}, got {result!r}"


# =============================================================================
# Basic Values & Arithmetic
# =============================================================================

class TestBasics:
    def test_numbers(self):
        assert_output("console.log(42)", ["42"])
        assert_output("console.log(3.14)", ["3.1400000000000001"])

    def test_strings(self):
        assert_output("console.log('hello')", ["hello"])
        assert_output('console.log("world")', ["world"])

    def test_booleans(self):
        assert_output("console.log(true)", ["true"])
        assert_output("console.log(false)", ["false"])

    def test_null_undefined(self):
        assert_output("console.log(null)", ["null"])
        assert_output("console.log(undefined)", ["undefined"])

    def test_arithmetic(self):
        assert_output("console.log(1 + 2)", ["3"])
        assert_output("console.log(10 - 3)", ["7"])
        assert_output("console.log(4 * 5)", ["20"])
        assert_output("console.log(15 / 3)", ["5"])
        assert_output("console.log(10 % 3)", ["1"])
        assert_output("console.log(2 ** 3)", ["8"])
        assert_output("console.log(1 + 2 * 3)", ["7"])

    def test_string_addition(self):
        assert_output('console.log("a" + "b")', ["ab"])
        assert_output('console.log("num: " + 42)', ["num: 42"])

    def test_comparison(self):
        assert_output("console.log(1 === 1)", ["true"])
        assert_output("console.log(1 === 2)", ["false"])
        assert_output("console.log(1 !== 2)", ["true"])
        assert_output("console.log(1 < 2)", ["true"])
        assert_output("console.log(2 <= 2)", ["true"])
        assert_output("console.log(3 > 1)", ["true"])

    def test_ternary(self):
        assert_output("console.log(true ? 'yes' : 'no')", ["yes"])
        assert_output("console.log(false ? 'yes' : 'no')", ["no"])


# =============================================================================
# Variables & Scope
# =============================================================================

class TestVariables:
    def test_let(self):
        assert_output("let x = 5; console.log(x)", ["5"])

    def test_reassign(self):
        assert_output("let x = 1; x = 2; console.log(x)", ["2"])

    def test_multiple_vars(self):
        assert_output("let a = 1; let b = 2; console.log(a + b)", ["3"])

    def test_block_scope(self):
        assert_output("""
            let x = 1;
            { let x = 2; console.log(x); }
            console.log(x);
        """, ["2", "1"])


# =============================================================================
# Control Flow
# =============================================================================

class TestControlFlow:
    def test_if(self):
        assert_output("if (true) { console.log(1); } else { console.log(2); }", ["1"])
        assert_output("if (false) { console.log(1); } else { console.log(2); }", ["2"])

    def test_if_no_else(self):
        assert_output("if (false) { console.log(1); } console.log(2);", ["2"])

    def test_for_loop(self):
        src = """
            let result = 0;
            for (let i = 1; i <= 5; i++) {
                result = result + i;
            }
            console.log(result);
        """
        assert_output(src, ["15"])  # 1+2+3+4+5

    def test_while_loop(self):
        src = """
            let i = 0;
            let r = "";
            while (i < 3) {
                r = r + "a";
                i = i + 1;
            }
            console.log(r);
        """
        assert_output(src, ["aaa"])

    def test_break(self):
        src = """
            let r = "";
            for (let i = 0; i < 10; i++) {
                if (i === 3) break;
                r = r + i;
            }
            console.log(r);
        """
        assert_output(src, ["012"])

    def test_continue(self):
        src = """
            let r = "";
            for (let i = 0; i < 5; i++) {
                if (i === 2) continue;
                r = r + i;
            }
            console.log(r);
        """
        assert_output(src, ["0134"])


# =============================================================================
# Arrays
# =============================================================================

class TestArrays:
    def test_create_and_index(self):
        src = """
            let arr = [10, 20, 30];
            console.log(arr[0]);
            console.log(arr[1]);
            console.log(arr[2]);
        """
        assert_output(src, ["10", "20", "30"])

    def test_length(self):
        assert_output("console.log([1, 2, 3].length)", ["3"])

    def test_push(self):
        assert_output("let a = [1, 2]; a.push(3); console.log(a)", ["1,2,3"])

    def test_pop(self):
        assert_output("let a = [1, 2, 3]; let p = a.pop(); console.log(p); console.log(a)", ["3", "1,2"])

    def test_unshift_shift(self):
        src = """
            let a = [2, 3];
            a.unshift(1);
            console.log(a);
            let s = a.shift();
            console.log(s);
            console.log(a);
        """
        assert_output(src, ["1,2,3", "1", "2,3"])

    def test_map(self):
        src = """
            let r = [1, 2, 3].map(function(x) { return x * 10; });
            console.log(r);
        """
        assert_output(src, ["10,20,30"])

    def test_filter(self):
        src = """
            let r = [1, 2, 3, 4, 5].filter(function(x) { return x % 2 === 0; });
            console.log(r);
        """
        assert_output(src, ["2,4"])

    def test_reduce_sum(self):
        src = """
            let r = [1, 2, 3, 4, 5].reduce(function(acc, x) { return acc + x; }, 0);
            console.log(r);
        """
        assert_output(src, ["15"])

    def test_reduce_product(self):
        src = """
            let r = [1, 2, 3, 4].reduce(function(acc, x) { return acc * x; }, 1);
            console.log(r);
        """
        assert_output(src, ["24"])

    def test_forEach(self):
        src = """
            let r = [];
            [1, 2, 3].forEach(function(x) { r.push(x * 10); });
            console.log(r);
        """
        assert_output(src, ["10,20,30"])

    def test_find(self):
        src = """
            let r = [1, 2, 3, 4].find(function(x) { return x > 2; });
            console.log(r);
        """
        assert_output(src, ["3"])

    def test_findIndex(self):
        src = """
            let r = [1, 2, 3, 4].findIndex(function(x) { return x > 2; });
            console.log(r);
        """
        assert_output(src, ["2"])

    def test_some(self):
        assert_output("console.log([1, 2, 3].some(function(x) { return x > 2; }))", ["true"])
        assert_output("console.log([1, 2, 3].some(function(x) { return x > 5; }))", ["false"])

    def test_every(self):
        assert_output("console.log([1, 2, 3].every(function(x) { return x > 0; }))", ["true"])
        assert_output("console.log([1, 2, 3].every(function(x) { return x > 1; }))", ["false"])

    def test_includes(self):
        assert_output("console.log([1, 2, 3].includes(2))", ["true"])
        assert_output("console.log([1, 2, 3].includes(5))", ["false"])

    def test_slice(self):
        assert_output("console.log([1, 2, 3, 4, 5].slice(1, 3))", ["2,3"])

    def test_join(self):
        assert_output("console.log([1, 2, 3].join('-'))", ["1-2-3"])

    def test_sort(self):
        src = """
            let a = [3, 1, 4, 1, 5];
            a.sort(function(x, y) { return x - y; });
            console.log(a);
        """
        assert_output(src, ["1,1,3,4,5"])

    def test_reverse(self):
        assert_output("let a = [1, 2, 3]; a.reverse(); console.log(a)", ["3,2,1"])

    def test_flat(self):
        src = """
            let n = [1, [2, 3], [4, [5, 6]]];
            let f = n.flat(1);
            console.log(f);
        """
        assert_output(src, ["1,2,3,4,5,6"])

    def test_array_from(self):
        assert_output("console.log(Array.from('abc'))", ["a,b,c"])

    def test_array_of(self):
        assert_output("console.log(Array.of(1, 2, 3))", ["1,2,3"])

    def test_spread(self):
        src = """
            let a = [1, 2];
            let b = [3, 4];
            let c = [...a, ...b];
            console.log(c);
        """
        assert_output(src, ["1,2,3,4"])

    def test_array_destructuring(self):
        src = """
            let [a, b, ...rest] = [1, 2, 3, 4, 5];
            console.log(a);
            console.log(b);
            console.log(rest);
        """
        assert_output(src, ["1", "2", "3,4,5"])

    def test_empty_array(self):
        assert_output("console.log([].length)", ["0"])
        assert_output("let a = []; a.push(1); console.log(a)", ["1"])


# =============================================================================
# Objects
# =============================================================================

class TestObjects:
    def test_create_access(self):
        src = """
            let obj = { name: "Alice", age: 30 };
            console.log(obj.name);
            console.log(obj.age);
        """
        assert_output(src, ["Alice", "30"])

    def test_set_property(self):
        src = """
            let obj = {};
            obj.x = 10;
            obj.y = 20;
            console.log(obj.x + obj.y);
        """
        assert_output(src, ["30"])

    def test_update_property(self):
        src = """
            let obj = { val: 5 };
            obj.val = obj.val + 1;
            console.log(obj.val);
        """
        assert_output(src, ["6"])

    def test_object_method(self):
        src = """
            let calc = {
                a: 10,
                b: 5,
                add: function() { return this.a + this.b; }
            };
            console.log(calc.add());
        """
        assert_output(src, ["15"])

    def test_computed_property(self):
        src = """
            let key = "score";
            let obj = { [key]: 95 };
            console.log(obj.score);
        """
        assert_output(src, ["95"])

    def test_object_keys(self):
        src = """
            let obj = { x: 1, y: 2, z: 3 };
            console.log(Object.keys(obj));
        """
        assert_output(src, ["x,y,z"])

    def test_object_values(self):
        src = """
            let obj = { x: 10, y: 20 };
            console.log(Object.values(obj));
        """
        assert_output(src, ["10,20"])

    def test_object_entries(self):
        src = """
            let obj = { a: 1, b: 2 };
            console.log(Object.entries(obj));
        """
        assert_output(src, ["a,1,b,2"])

    def test_object_assign(self):
        src = """
            let a = { x: 1, y: 2 };
            let b = { y: 5, z: 3 };
            let m = Object.assign({}, a, b);
            console.log(m.x);
            console.log(m.y);
            console.log(m.z);
        """
        assert_output(src, ["1", "5", "3"])

    def test_object_hasOwn(self):
        src = """
            let obj = { name: "test" };
            console.log(Object.hasOwn(obj, "name"));
            console.log(Object.hasOwn(obj, "missing"));
        """
        assert_output(src, ["true", "false"])


# =============================================================================
# Functions
# =============================================================================

class TestFunctions:
    def test_declaration(self):
        assert_output("""
            function greet(name) { return "Hello, " + name + "!"; }
            console.log(greet("World"));
        """, ["Hello, World!"])

    def test_expression(self):
        assert_output("""
            let f = function(n) { return n * 2; };
            console.log(f(5));
        """, ["10"])

    def test_recursion(self):
        assert_output("""
            function fact(n) {
                if (n <= 1) return 1;
                return n * fact(n - 1);
            }
            console.log(fact(5));
        """, ["120"])

    def test_arrow_expression_body(self):
        assert_output("let sq = x => x * x; console.log(sq(4))", ["16"])

    def test_arrow_block_body(self):
        assert_output("""
            let add = (a, b) => { return a + b; };
            console.log(add(3, 7));
        """, ["10"])

    def test_closure(self):
        assert_output("""
            function makeCounter() {
                let count = 0;
                return function() {
                    count = count + 1;
                    return count;
                };
            }
            let c = makeCounter();
            console.log(c());
            console.log(c());
            console.log(c());
        """, ["1", "2", "3"])

    def test_higher_order(self):
        assert_output("""
            function apply(a, b, op) { return op(a, b); }
            console.log(apply(5, 3, function(x, y) { return x + y; }));
            console.log(apply(5, 3, function(x, y) { return x * y; }));
        """, ["8", "15"])

    def test_rest_params(self):
        assert_output("""
            function sumAll(...nums) {
                return nums.reduce(function(a, n) { return a + n; }, 0);
            }
            console.log(sumAll(1, 2, 3, 4));
        """, ["10"])

    def test_default_params(self):
        assert_output("""
            function mul(a, b) {
                if (b === undefined) b = 1;
                return a * b;
            }
            console.log(mul(5));
            console.log(mul(5, 3));
        """, ["5", "15"])

    def test_callback_in_array_method(self):
        assert_output("""
            let r = [1, 2, 3].map(function(n) { return n + 1; });
            console.log(r);
        """, ["2,3,4"])


# =============================================================================
# Combined Tests (arrays + objects + functions)
# =============================================================================

class TestCombined:
    def test_array_of_objects_map(self):
        assert_output("""
            let users = [
                { name: "Alice", age: 25 },
                { name: "Bob", age: 30 }
            ];
            let names = users.map(function(u) { return u.name; });
            console.log(names);
        """, ["Alice,Bob"])

    def test_array_of_objects_filter(self):
        assert_output("""
            let users = [
                { name: "Alice", age: 25 },
                { name: "Bob", age: 30 },
                { name: "Charlie", age: 35 }
            ];
            let adults = users.filter(function(u) { return u.age >= 30; });
            console.log(adults.length);
        """, ["2"])

    def test_array_of_objects_reduce(self):
        assert_output("""
            let users = [
                { age: 25 },
                { age: 30 },
                { age: 35 }
            ];
            let total = users.reduce(function(acc, u) { return acc + u.age; }, 0);
            console.log(total);
        """, ["90"])

    def test_function_returning_object(self):
        assert_output("""
            function makeUser(name, age) {
                return { name: name, age: age, isAdult: age >= 18 };
            }
            let u = makeUser("Diana", 28);
            console.log(u.name);
            console.log(u.isAdult);
        """, ["Diana", "true"])

    def test_nested_member_access(self):
        assert_output("""
            let data = { coords: { x: 10, y: 20 } };
            console.log(data.coords.x);
            console.log(data.coords.y);
        """, ["10", "20"])

    def test_function_pipeline(self):
        assert_output("""
            let ops = [
                function(x) { return x + 1; },
                function(x) { return x * 2; },
                function(x) { return x * x; }
            ];
            let r = 5;
            for (let i = 0; i < ops.length; i++) {
                r = ops[i](r);
            }
            console.log(r);
        """, ["144"])  # 5 -> +1 = 6 -> *2 = 12 -> ^2 = 144


# =============================================================================
# Strings
# =============================================================================

class TestStrings:
    def test_upper_lower(self):
        assert_output("console.log('Hello'.toUpperCase())", ["HELLO"])
        assert_output("console.log('Hello'.toLowerCase())", ["hello"])

    def test_includes(self):
        assert_output("console.log('Hello World'.includes('World'))", ["true"])
        assert_output("console.log('Hello World'.includes('Foo'))", ["false"])

    def test_split(self):
        src = """
            let parts = "a,b,c".split(",");
            console.log(parts);
        """
        assert_output(src, ["a,b,c"])

    def test_slice(self):
        assert_output("console.log('JavaScript'.slice(0, 4))", ["Java"])
        assert_output("console.log('JavaScript'.slice(4))", ["Script"])

    def test_trim(self):
        assert_output("console.log('  hi  '.trim())", ["hi"])

    def test_charAt(self):
        assert_output("console.log('abc'.charAt(1))", ["b"])

    def test_concat(self):
        assert_output("console.log('a'.concat('b', 'c'))", ["abc"])

    def test_template_literal(self):
        src = """
            let name = "World";
            console.log("Hello, " + name + "!");
        """
        assert_output(src, ["Hello, World!"])


# =============================================================================
# Math
# =============================================================================

class TestMath:
    def test_constants(self):
        assert_output("console.log(Math.PI)", ["3.1415926535897931"])

    def test_abs(self):
        assert_output("console.log(Math.abs(-5))", ["5"])
        assert_output("console.log(Math.abs(5))", ["5"])

    def test_max_min(self):
        assert_output("console.log(Math.max(3, 7, 2))", ["7"])
        assert_output("console.log(Math.min(3, 7, 2))", ["2"])

    def test_ceil_floor_round(self):
        assert_output("console.log(Math.ceil(3.2))", ["4"])
        assert_output("console.log(Math.floor(3.8))", ["3"])
        assert_output("console.log(Math.round(3.5))", ["4"])

    def test_pow_sqrt(self):
        assert_output("console.log(Math.pow(2, 3))", ["8"])
        assert_output("console.log(Math.sqrt(9))", ["3"])


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    def test_empty_program(self):
        assert_output("", [])

    def test_multiple_console_log(self):
        assert_output("""
            console.log(1);
            console.log(2);
            console.log(3);
        """, ["1", "2", "3"])

    def test_console_log_multiple_args(self):
        assert_output('console.log("a", "b", "c")', ["a b c"])

    def test_nested_blocks(self):
        assert_output("""
            let x = 1;
            {
                let x = 2;
                {
                    let x = 3;
                    console.log(x);
                }
                console.log(x);
            }
            console.log(x);
        """, ["3", "2", "1"])

    def test_boolean_operators(self):
        assert_output("console.log(true && true)", ["true"])
        assert_output("console.log(true && false)", ["false"])
        assert_output("console.log(false || true)", ["true"])
        assert_output("console.log(false || false)", ["false"])
        assert_output("console.log(!true)", ["false"])
        assert_output("console.log(!false)", ["true"])

    def test_typeof(self):
        assert_output("console.log(typeof 42)", ["number"])
        assert_output('console.log(typeof "hi")', ["string"])
        assert_output("console.log(typeof true)", ["boolean"])
        assert_output("console.log(typeof undefined)", ["undefined"])
        assert_output("console.log(typeof null)", ["object"])

    def test_comma_operator(self):
        assert_output("console.log((1, 2, 3))", ["3"])

    def test_nested_array(self):
        assert_output("console.log([[1, 2], [3, 4]])", ["1,2,3,4"])
