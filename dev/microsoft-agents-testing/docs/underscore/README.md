# Underscore: Placeholder Expressions

A lightweight library for building deferred function expressions using placeholder syntax. Create concise, readable lambda-like expressions without the `lambda` keyword.

## Installation

```python
from microsoft_agents.testing.underscore import (
    _, _0, _1, _2, _3, _4, _n, _var,
    pipe,
    get_placeholder_info,
    is_placeholder,
)
```

## Quick Start

```python
from microsoft_agents.testing.underscore import _, _0, _1, _var

# Instead of: lambda x: x + 1
add_one = _ + 1
add_one(5)  # → 6

# Instead of: lambda x, y: x + y
add = _ + _
add(2, 5)  # → 7

# Instead of: lambda x: x * x
square = _0 * _0
square(5)  # → 25
```

---

## Core Concepts

### Anonymous Placeholders (`_`)

The basic `_` placeholder consumes arguments in order. Each `_` in an expression takes the next positional argument.

```python
# Single argument
double = _ * 2
double(5)  # → 10

# Multiple arguments - consumed left to right
subtract = _ - _
subtract(10, 3)  # → 7

# Three arguments
expr = (_ + _) * _
expr(1, 2, 3)  # → (1 + 2) * 3 = 9
```

### Indexed Placeholders (`_0`, `_1`, `_2`, ...)

Use indexed placeholders to refer to specific positional arguments, allowing reuse of the same argument.

```python
# Reuse the same argument
square = _0 * _0
square(5)  # → 25

# Mix different positions
expr = _0 + _1 * _0
expr(2, 3)  # → 2 + 3 * 2 = 8

# Pre-defined: _0, _1, _2, _3, _4
# For higher indices, use _n:
tenth_arg = _n(9)
```

### Named Placeholders (`_var`)

Use `_var` to create placeholders for keyword arguments.

```python
# Using bracket syntax
greet = "Hello, " + _var["name"] + "!"
greet(name="World")  # → "Hello, World!"

# Using attribute syntax
greet = "Hello, " + _var.name + "!"
greet(name="World")  # → "Hello, World!"

# Mixed with positional
expr = _0 * _var["scale"]
expr(5, scale=2)  # → 10
```

---

## Operations

### Arithmetic

```python
_ + 1      # addition
_ - 1      # subtraction
_ * 2      # multiplication
_ / 2      # division
_ // 2     # floor division
_ % 3      # modulo
_ ** 2     # power
```

### Reverse Arithmetic

When the placeholder is on the right side:

```python
10 - _     # 10 minus the argument
100 / _    # 100 divided by the argument
2 ** _     # 2 to the power of the argument
```

### Comparisons

```python
_ > 0      # greater than
_ >= 0     # greater than or equal
_ < 10     # less than
_ <= 10    # less than or equal
_ == "yes" # equality
_ != None  # inequality
```

### Unary Operators

```python
-_         # negation
+_         # positive
~_         # bitwise invert
```

### Bitwise Operators

```python
_ & mask   # AND
_ | flags  # OR
_ ^ bits   # XOR
_ << 2     # left shift
_ >> 2     # right shift
```

---

## Attribute and Item Access

### Attribute Access

Access attributes on the resolved value:

```python
get_length = _.length
get_length("hello")  # → 5 (if .length existed)

upper = _.upper
upper("hello")  # → <bound method>
```

### Item Access

Access items by index or key:

```python
# Get first element
first = _[0]
first([1, 2, 3])  # → 1

# Get by key
get_name = _["name"]
get_name({"name": "Alice"})  # → "Alice"

# Chained access
nested = _["users"][0]["name"]
nested({"users": [{"name": "Bob"}]})  # → "Bob"
```

> **Note:** `_[0]` is item access, not placeholder creation. Use `_var[0]` or `_0` for indexed placeholders.

---

## Method Calls

Chain method calls on placeholder expressions:

```python
# Call a method
upper = _.upper()
upper("hello")  # → "HELLO"

# Method with arguments
split_csv = _.split(",")
split_csv("a,b,c")  # → ["a", "b", "c"]

# Chained methods
process = _.strip().lower().split()
process("  HELLO WORLD  ")  # → ["hello", "world"]
```

---

## Partial Application

If you provide fewer arguments than required, you get back a new placeholder with those arguments bound:

```python
add = _ + _
add2 = add(2)      # Partial: first arg is 2
add2(5)            # → 7

# Works with indexed placeholders
expr = _0 + _1 + _2
partial = expr(1, 2)  # Waiting for third arg
partial(3)            # → 6
```

---

## Composition with `pipe`

Chain multiple transformations in a pipeline:

```python
from microsoft_agents.testing.underscore import pipe

# Process value through multiple steps
process = pipe(
    _ + 1,       # add 1
    _ * 2,       # multiply by 2
    str          # convert to string
)

process(5)  # → (5 + 1) * 2 = 12 → "12"
```

---

## Introspection

Analyze placeholder expressions to understand their requirements:

### Check if something is a placeholder

```python
from microsoft_agents.testing.underscore import is_placeholder

is_placeholder(_ + 1)    # → True
is_placeholder(42)       # → False
```

### Get placeholder information

```python
from microsoft_agents.testing.underscore import get_placeholder_info

expr = _0 + _1 * _var["scale"] + _
info = get_placeholder_info(expr)

info.anonymous_count       # → 1 (one bare _)
info.indexed               # → {0, 1}
info.named                 # → {'scale'}
info.total_positional_needed  # → 2
```

### Convenience functions

```python
from microsoft_agents.testing.underscore import (
    get_anonymous_count,
    get_indexed_placeholders,
    get_named_placeholders,
    get_required_args,
)

expr = _0 + _1 * _var["x"]

get_anonymous_count(expr)      # → 0
get_indexed_placeholders(expr) # → {0, 1}
get_named_placeholders(expr)   # → {'x'}

pos, named = get_required_args(expr)
# pos = 2, named = {'x'}
```

---

## Examples

### Filtering and Mapping

```python
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Filter even numbers
evens = list(filter(_ % 2 == 0, numbers))
# → [2, 4, 6, 8, 10]

# Double all numbers
doubled = list(map(_ * 2, numbers))
# → [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]

# Sorting by a key
users = [{"name": "Bob", "age": 30}, {"name": "Alice", "age": 25}]
sorted_users = sorted(users, key=_["age"])
```

### String Processing

```python
# Clean and normalize
normalize = _.strip().lower()
normalize("  HELLO  ")  # → "hello"

# Check prefix
is_admin = _.startswith("admin_")
is_admin("admin_user")  # → True
```

### Complex Expressions

```python
# Temperature conversion: Fahrenheit to Celsius
f_to_c = (_ - 32) * 5 / 9
f_to_c(98.6)  # → 37.0

# Quadratic formula component
discriminant = _1 ** 2 - 4 * _0 * _2
discriminant(1, 5, 6)  # → 25 - 24 = 1
```

---

## API Reference

### Placeholders

| Symbol | Description |
|--------|-------------|
| `_` | Anonymous placeholder, consumes next positional arg |
| `_0`, `_1`, ... `_4` | Indexed placeholders for specific positions |
| `_n(i)` | Create indexed placeholder for position `i` |
| `_var[i]` | Create indexed placeholder (same as `_n(i)`) |
| `_var["name"]` | Create named placeholder for keyword arg |
| `_var.name` | Create named placeholder (attribute syntax) |

### Functions

| Function | Description |
|----------|-------------|
| `pipe(*funcs)` | Compose functions left-to-right |
| `is_placeholder(value)` | Check if value is an Underscore |
| `get_placeholder_info(expr)` | Get full placeholder analysis |
| `get_anonymous_count(expr)` | Count anonymous placeholders |
| `get_indexed_placeholders(expr)` | Get set of indexed positions |
| `get_named_placeholders(expr)` | Get set of named placeholder names |
| `get_required_args(expr)` | Get `(positional_count, named_set)` tuple |

### Classes

| Class | Description |
|-------|-------------|
| `Underscore` | The placeholder class |
| `PlaceholderInfo` | Result of `get_placeholder_info()` |