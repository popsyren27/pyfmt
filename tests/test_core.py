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


def test_none_value_falls_through_to_default_or_placeholder():
    # None is treated as missing: use the default if there is one,
    # otherwise leave the placeholder visible.
    assert format("{{x}}", {"x": None}) == "{{x}}"
    assert format("{{x|fallback}}", {"x": None}) == "fallback"


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


def test_default_can_be_empty():
    # {{x|}} parses with default="" and renders as nothing, but only when
    # the key is actually missing or None.
    assert format("{{x|}}", {}) == ""
    assert format("{{x|}}", {"x": None}) == ""
    assert format("{{x|}}", {"x": "real"}) == "real"


def test_default_only_uses_first_pipe_as_separator():
    # Any pipes after the first are part of the default literal.
    assert format("{{x|a|b|c}}", {}) == "a|b|c"
    assert format("{{x|a|b|c}}", {"x": None}) == "a|b|c"


def test_escaped_open_brace_renders_literally():
    # \{{ is consumed as an escape; the braces appear as literal text
    # and the value at "name" is NOT used.
    assert format("\\{{name}}", {"name": "world"}) == "{{name}}"


def test_escaped_open_brace_does_not_look_up_key():
    assert format("\\{{name}}", {}) == "{{name}}"


def test_escaped_close_brace_renders_literally():
    # A lone \} has no matching {{, so it's just a literal }.
    assert format("hi \\}", {}) == "hi }"


def test_trailing_backslash_is_literal():
    # A backslash with nothing to escape is left as-is.
    assert format("path\\", {}) == "path\\"


def test_escaped_close_brace_inside_placeholder_does_not_close():
    # \} inside a placeholder body must not terminate the placeholder,
    # and the body is cleaned so the name is the literal "a}".
    out = format(r"{{a\}}}", {"a}": "v"})
    assert out == "v"


def test_escaped_close_brace_in_placeholder_body_renders():
    # \} inside the body does not close the placeholder; the real }} does.
    # Body raw is "a\}}y"; cleaned body is "a}}y" (the escaped \} becomes
    # a literal }).
    out = format(r"x{{a\}}y}}", {"a}}y": "ok"})
    assert out == "xok"


def test_placeholder_with_escaped_close_then_text():
    # \} inside the body is literal; the real }} later closes the
    # placeholder and the text after stays outside. Cleaned body is
    # "a}}rest".
    out = format(r"{{a\}}rest}}tail", {"a}}rest": "v"})
    assert out == "vtail"


def test_escaped_open_brace_in_body_is_literal():
    # \{ inside a placeholder body becomes a literal {. The body is
    # cleaned, so the name is "a{b" and the value at that key is used.
    out = format(r"{{a\{b}}", {"a{b": "v"})
    assert out == "v"


def test_escaped_pipe_in_body_splits_at_real_pipe_only():
    # \| is consumed as an escape, so the first real | is the
    # name/default split. The cleaned body is "a|b|c"; split gives
    # name "a" and default "b|c".
    out = format(r"{{a\|b|c}}", {"a": "v"})
    assert out == "v"
    # With no value, the default "b|c" is used.
    assert format(r"{{a\|b|c}}", {"a": None}) == "b|c"
