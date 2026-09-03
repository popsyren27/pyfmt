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

## Install

```
pip install -e .
```

## Test

```
python -m pytest
```
