# pyfmt

A tiny string formatting helper. Templates use `{{name}}` placeholders.

```python
from pyfmt import format

format("hello {{name}}", {"name": "world"})
# 'hello world'
```

Missing keys are left in the output untouched so you can spot them.

## Install

```
pip install -e .
```

## Test

```
python -m pytest
```
