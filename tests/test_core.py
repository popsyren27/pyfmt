"""Tests for pyfmt.core.format."""

import pytest

from pyfmt import format


def test_simple_replacement():
    assert format("hello {{name}}", {"name": "world"}) == "hello world"


def test_multiple_placeholders():
    out = format("{{a}} and {{b}}", {"a": "x", "b": "y"})
    assert out == "x and y"


def test_missing_key_is_left_alone():
    out = format("hi {{name}}", {})
    assert out == "hi {{name}}"


def test_no_placeholders():
    assert format("plain text", {"x": 1}) == "plain text"


def test_repeated_key():
    out = format("{{x}} {{x}}", {"x": "ok"})
    assert out == "ok ok"


def test_whitespace_inside_placeholder_is_ignored():
    assert format("{{  name  }}", {"name": "z"}) == "z"


def test_unterminated_placeholder_is_preserved():
    out = format("hi {{name", {"name": "x"})
    assert out == "hi {{name"


def test_value_is_coerced_to_string():
    assert format("count: {{n}}", {"n": 42}) == "count: 42"


def test_value_can_be_none():
    assert format("{{x}}", {"x": None}) == "None"
