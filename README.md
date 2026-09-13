# pyfmt

A tiny string formatting helper. Templates use `{{name}}` placeholders.

```python
from pyfmt import format

format("hello {{name}}", {"name": "world"})
# 'hello world'
```

Missing keys are left in the output untouched so you can spot them.

You can also supply a default with `{{name|default}}`. The default is used
when the key is missing or its value is `None`:

```python
format("hello {{name|stranger}}", {})
# 'hello stranger'

format("hello {{name|stranger}}", {"name": None})
# 'hello stranger'
```

To write a literal `{{` in the output, escape it with a backslash. The
backslash is consumed:

```python
format(r"\{{not a placeholder}}", {})
# '{{not a placeholder}}'
```

```python
format(r"{{a\|b|fallback}}", {"a|b": "literal pipe in the name"})
# 'literal pipe in the name'
```

## Type specifiers

A placeholder can declare an expected type with `{{name:type}}`. This is a
validation contract, not a coercion request — the value must already be that
type, or `format()` raises `TypeError`. It can be combined with a default as
`{{name:type|default}}`; the default itself is never type-checked.

| Specifier | Type | Example | Renders |
| --- | --- | --- | --- |
| `d` | `int` (not `bool`) | `{{n:d}}` | plain `str(value)`, e.g. `5` |
| `f` | `float` | `{{x:f}}` | plain `str(value)`, e.g. `3.14159` |
| `s` | `str` | `{{s:s}}` | plain `str(value)` |

Two specifiers also accept extra formatting, applied on top of the type check:

| Specifier | Meaning | Example | Renders (value) |
| --- | --- | --- | --- |
| `Nd` | int, space-padded to width `N` | `{{n:5d}}` | `"    5"` (`5`) |
| `0Nd` | int, zero-padded to width `N`, sign-aware | `{{n:05d}}` | `"-0042"` (`-42`) |
| `.Pf` | float, rounded to `P` decimal places | `{{x:.2f}}` | `"3.14"` (`3.14159`) |
| `N.Pf` | float, space-padded to width `N`, `P` decimals | `{{x:8.2f}}` | `"    3.14"` (`3.14159`) |
| `0N.Pf` | float, zero-padded to width `N`, `P` decimals, sign-aware | `{{x:08.2f}}` | `"-0003.14"` (`-3.14159`) |

`s` never takes a width, and bare `d`/`f` without the extra syntax above are
never reformatted — they're just `str(value)`.

## Install

```
pip install -e .
```

## Test

```
python -m pytest
```