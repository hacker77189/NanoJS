// ============================================================
// JavaScript Runtime Test Suite
// Covers: Arrays, Objects, Functions, and mixed features
// ============================================================

console.log("=== ARRAY TESTS ===");

// --- Basic Array Operations ---
let arr = [1, 2, 3, 4, 5];
console.log("Array:", arr);
console.log("Length:", arr.length);
console.log("First:", arr[0]);
console.log("Last:", arr[arr.length - 1]);

// push / pop
arr.push(6);
console.log("After push:", arr);
let popped = arr.pop();
console.log("Popped:", popped);
console.log("After pop:", arr);

// unshift / shift
arr.unshift(0);
console.log("After unshift:", arr);
let shifted = arr.shift();
console.log("Shifted:", shifted);
console.log("After shift:", arr);

// --- Array Iteration ---
let doubled = arr.map(function(x) { return x * 2; });
console.log("Doubled:", doubled);

let evens = arr.filter(function(x) { return x % 2 === 0; });
console.log("Evens:", evens);

let sum = arr.reduce(function(acc, x) { return acc + x; }, 0);
console.log("Sum:", sum);

let product = arr.reduce(function(acc, x) { return acc * x; }, 1);
console.log("Product:", product);

// forEach
let forEachResult = [];
arr.forEach(function(x) { forEachResult.push(x * 10); });
console.log("forEach *10:", forEachResult);

// --- Searching Arrays ---
let found = arr.find(function(x) { return x > 3; });
console.log("Find >3:", found);

let foundIdx = arr.findIndex(function(x) { return x > 3; });
console.log("FindIndex >3:", foundIdx);

let hasEven = arr.some(function(x) { return x % 2 === 0; });
console.log("Has even:", hasEven);

let allPositive = arr.every(function(x) { return x > 0; });
console.log("All positive:", allPositive);

let includesThree = arr.includes(3);
console.log("Includes 3:", includesThree);

// --- Array Slicing ---
let sliced = arr.slice(1, 3);
console.log("Slice(1,3):", sliced);

let joined = arr.join("-");
console.log("Join: '" + joined + "'");

// --- Sort & Reverse ---
let unsorted = [3, 1, 4, 1, 5, 9, 2, 6];
unsorted.sort(function(a, b) { return a - b; });
console.log("Sorted:", unsorted);

unsorted.reverse();
console.log("Reversed:", unsorted);

// --- Flat ---
let nested = [1, [2, 3], [4, [5, 6]]];
console.log("Nested:", nested);
let flat1 = nested.flat(1);
console.log("Flat(1):", flat1);

// --- Spread Operator ---
let a1 = [1, 2, 3];
let a2 = [4, 5, 6];
let combined = [...a1, ...a2];
console.log("Spread combined:", combined);

let [first, second, ...rest] = combined;
console.log("Destructured first:", first);
console.log("Destructured second:", second);
console.log("Destructured rest:", rest);

// Array.from & Array.of
let fromStr = Array.from("hello");
console.log("Array.from('hello'):", fromStr);

let ofArr = Array.of(1, 2, 3);
console.log("Array.of(1,2,3):", ofArr);

// === OBJECT TESTS ===
console.log("");
console.log("=== OBJECT TESTS ===");

// --- Basic Object ---
let person = {
    name: "Alice",
    age: 30,
    city: "New York"
};
console.log("Person:", person);
console.log("Name:", person.name);
console.log("Age:", person.age);

// Add property
person.job = "Engineer";
console.log("After job:", person);

// Update property
person.age = 31;
console.log("After age++:", person);

// --- Computed Properties ---
let key = "score";
let computed = {
    [key]: 95,
    grade: "A"
};
console.log("Computed:", computed);
console.log("Score:", computed[key]);

// --- Object Methods ---
let calculator = {
    a: 10,
    b: 5,
    add: function() { return this.a + this.b; },
    subtract: function() { return this.a - this.b; }
};
console.log("Calc add:", calculator.add());
console.log("Calc sub:", calculator.subtract());

// --- Object.keys/values/entries ---
let keys = Object.keys(person);
console.log("Keys:", keys);

let values = Object.values(person);
console.log("Values:", values);

let entries = Object.entries(person);
console.log("Entries:", entries);

// --- Object.assign ---
let defaults = { x: 1, y: 2 };
let overrides = { y: 5, z: 3 };
let merged = Object.assign({}, defaults, overrides);
console.log("Merged:", merged);

// --- Object.hasOwn ---
console.log("Has 'name':", Object.hasOwn(person, "name"));
console.log("Has 'foo':", Object.hasOwn(person, "foo"));

// === FUNCTION TESTS ===
console.log("");
console.log("=== FUNCTION TESTS ===");

// --- Function Declaration ---
function greet(name) {
    return "Hello, " + name + "!";
}
console.log("Greet:", greet("World"));

// --- Function Expression ---
let factorial = function(n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
};
console.log("Factorial 5:", factorial(5));

// --- Arrow Functions ---
let square = x => x * x;
console.log("Square 4:", square(4));

let add = (a, b) => a + b;
console.log("Add 3 + 7:", add(3, 7));

let greetArrow = name => {
    let msg = "Hi there, " + name;
    return msg;
};
console.log("Arrow greet:", greetArrow("Bob"));

// --- Closures ---
function makeCounter() {
    let count = 0;
    return function() {
        count = count + 1;
        return count;
    };
}
let counter = makeCounter();
console.log("Counter 1:", counter());
console.log("Counter 2:", counter());
console.log("Counter 3:", counter());

// --- Higher-Order Functions ---
function applyOperation(a, b, operation) {
    return operation(a, b);
}
console.log("Apply add 5+3:", applyOperation(5, 3, function(x, y) { return x + y; }));
console.log("Apply mul 5*3:", applyOperation(5, 3, function(x, y) { return x * y; }));

// --- Default Parameters ---
function multiply(a, b) {
    if (b === undefined) {
        b = 1;
    }
    return a * b;
}
console.log("Multiply 5:", multiply(5));
console.log("Multiply 5,3:", multiply(5, 3));

// --- Rest Parameters ---
function sumAll(...nums) {
    return nums.reduce(function(acc, n) { return acc + n; }, 0);
}
console.log("SumAll 1,2,3,4:", sumAll(1, 2, 3, 4));

// === COMBINED TESTS ===
console.log("");
console.log("=== COMBINED TESTS ===");

// Array of objects
let users = [
    { name: "Alice", age: 25 },
    { name: "Bob", age: 30 },
    { name: "Charlie", age: 35 }
];
console.log("Users:", users);

let names = users.map(function(u) { return u.name; });
console.log("User names:", names);

let adults = users.filter(function(u) { return u.age >= 30; });
console.log("Adults (>=30):", adults);

let totalAge = users.reduce(function(acc, u) { return acc + u.age; }, 0);
console.log("Total age:", totalAge);

// Functions returning objects
function createUser(name, age) {
    return {
        name: name,
        age: age,
        isAdult: age >= 18
    };
}
let newUser = createUser("Diana", 28);
console.log("Created user:", newUser);

// Nested member access
let data = {
    title: "Test",
    coords: { x: 10, y: 20, z: 30 }
};
console.log("Nested x:", data.coords.x);
console.log("Nested y:", data.coords.y);

// Mix: array of functions
let operations = [
    function(x) { return x + 1; },
    function(x) { return x * 2; },
    function(x) { return x * x; }
];
let result = 5;
for (let i = 0; i < operations.length; i++) {
    result = operations[i](result);
}
console.log("Pipeline 5 -> +1 -> *2 -> ^2:", result);

// String operations (bonus)
let str = "JavaScript Runtime";
console.log("Uppercase:", str.toUpperCase());
console.log("Lowercase:", str.toLowerCase());
console.log("Includes 'Script':", str.includes("Script"));
console.log("Split by space:", str.split(" "));
console.log("Slice(0,4):", str.slice(0, 4));

// Math (bonus)
console.log("PI:", Math.PI);
console.log("Abs(-5):", Math.abs(-5));
console.log("Max(3,7,2):", Math.max(3, 7, 2));
console.log("Min(3,7,2):", Math.min(3, 7, 2));

console.log("");
console.log("All tests completed!");
