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


def test_empty_template():
    assert format("", {"x": 1}) == ""


def test_placeholder_at_start():
    assert format("{{x}}!", {"x": "hi"}) == "hi!"


def test_placeholder_at_end():
    assert format("hi {{x}}", {"x": "there"}) == "hi there"


def test_placeholder_on_both_sides():
    assert format("a{{x}}b{{y}}c", {"x": "1", "y": "2"}) == "a1b2c"


def test_placeholder_only_template():
    assert format("{{x}}", {"x": "solo"}) == "solo"


def test_placeholder_no_separator():
    assert format("{{a}}{{b}}", {"a": "1", "b": "2"}) == "12"


def test_lookup_is_case_sensitive():
    out = format("{{Name}} vs {{name}}", {"name": "lower"})
    assert out == "{{Name}} vs lower"


def test_tab_and_newline_whitespace_is_stripped():
    assert format("{{\tname\n}}", {"name": "ok"}) == "ok"


def test_missing_key_does_not_affect_others():
    out = format("{{a}}-{{missing}}-{{b}}", {"a": "x", "b": "y"})
    assert out == "x-{{missing}}-y"


def test_value_is_float():
    assert format("{{x}}", {"x": 3.5}) == "3.5"


def test_value_is_bool():
    assert format("{{x}}", {"x": True}) == "True"


def test_value_containing_braces_is_inserted_literally():
    out = format("code: {{x}}", {"x": "{{not a placeholder}}"})
    # The substituted value is a string; it does not get re-scanned.
    assert out == "code: {{not a placeholder}}"


def test_unterminated_placeholder_with_trailing_text():
    out = format("hi {{name and more", {"name": "x"})
    assert out == "hi {{name and more"


def test_empty_placeholder_name_substitutes_when_empty_key_present():
    # {{}} strips to "". If the values dict has an "" key, it matches.
    out = format("a{{}}b", {"": "x"})
    assert out == "axb"


def test_values_supports_mapping_protocol():
    # Anything that behaves like a Mapping should work, not just dict.
    class M:
        def __init__(self, data):
            self._data = data

        def __getitem__(self, key):
            return self._data[key]

        def __contains__(self, key):
            return key in self._data

    assert format("{{x}}", M({"x": "ok"})) == "ok"


def test_default_used_when_key_missing():
    assert format("{{name|anon}}", {}) == "anon"


def test_default_used_when_value_is_none():
    assert format("{{name|anon}}", {"name": None}) == "anon"


def test_value_used_when_present_and_not_none():
    assert format("{{name|anon}}", {"name": "world"}) == "world"


def test_default_with_empty_string_value():
    # Only None triggers the default; an empty string is a real value.
    assert format("{{x|fallback}}", {"x": ""}) == ""


def test_default_can_contain_braces_literal():
    # Defaults are not re-scanned for placeholders.
    assert format("{{x|{{y}}}}", {}) == "{{y}}"


def test_default_with_whitespace_is_stripped():
    assert format("{{name |  anon  }}", {"name": None}) == "anon"


def test_default_only_placeholder():
    # {{|hello}} strips the name to ""; empty name with no key -> default.
    assert format("{{|hello}}", {}) == "hello"


def test_default_does_not_apply_to_other_placeholders():
    out = format("{{a|foo}}-{{missing}}-{{b|bar}}", {"a": "x"})
    assert out == "x-{{missing}}-bar"


def test_default_with_int_value_in_values():
    assert format("{{n|0}}", {}) == "0"
    assert format("{{n|0}}", {"n": None}) == "0"
    assert format("{{n|0}}", {"n": 7}) == "7"
