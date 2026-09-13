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


def test_even_backslashes_before_open_brace_leave_placeholder_active():
    assert format("\\\\{{name}}", {"name": "world"}) == "\\\\world"


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


def test_type_specifier_int_accepts_int():
    assert format("{{n:d}}", {"n": 5}) == "5"


def test_type_specifier_int_rejects_str():
    with pytest.raises(TypeError):
        format("{{n:d}}", {"n": "5"})


def test_type_specifier_int_rejects_bool():
    # bool is a subclass of int in Python, but an explicit :d specifier
    # is meant to be exact, not lenient about that quirk.
    with pytest.raises(TypeError):
        format("{{n:d}}", {"n": True})


def test_type_specifier_float_accepts_float():
    assert format("{{x:f}}", {"x": 3.5}) == "3.5"


def test_type_specifier_float_rejects_int():
    # :f is exact too: an int is not treated as "close enough" to a float.
    with pytest.raises(TypeError):
        format("{{x:f}}", {"x": 3})


def test_type_specifier_string_accepts_str():
    assert format("{{s:s}}", {"s": "hi"}) == "hi"


def test_type_specifier_string_rejects_non_str():
    with pytest.raises(TypeError):
        format("{{s:s}}", {"s": 5})


def test_type_specifier_does_not_change_rendering():
    # The specifier only validates; it never reformats the value
    # (no forced decimal places, no digit grouping, etc.).
    assert format("{{x:f}}", {"x": 3.0}) == "3.0"


def test_type_specifier_not_checked_when_key_missing():
    # No value is substituted, so there's nothing to type-check against;
    # the placeholder is just left visible like any other missing key.
    assert format("{{n:d}}", {}) == "{{n:d}}"


def test_type_specifier_not_checked_when_value_is_none():
    assert format("{{n:d}}", {"n": None}) == "{{n:d}}"


def test_type_specifier_with_default_missing_key():
    assert format("{{n:d|0}}", {}) == "0"


def test_type_specifier_with_default_none_value():
    assert format("{{n:d|0}}", {"n": None}) == "0"


def test_type_specifier_with_default_and_matching_value():
    assert format("{{n:d|0}}", {"n": 7}) == "7"


def test_type_specifier_with_default_and_mismatched_value_still_raises():
    # A default doesn't excuse a present-but-wrong-typed value; only a
    # missing/None value falls through to the default.
    with pytest.raises(TypeError):
        format("{{n:d|0}}", {"n": "not a number"})


def test_type_specifier_default_is_not_itself_type_checked():
    # The default is always a literal string, regardless of the
    # declared type -- it's rendered as-is, not validated or converted.
    assert format("{{n:d|not-a-number}}", {}) == "not-a-number"


def test_type_specifier_whitespace_is_stripped():
    assert format("{{ n : d }}", {"n": 5}) == "5"


def test_unknown_type_specifier_raises_value_error():
    with pytest.raises(ValueError):
        format("{{n:z}}", {"n": 5})


def test_int_width_pads_with_spaces():
    assert format("{{n:5d}}", {"n": 5}) == "    5"


def test_int_zero_pad_pads_with_zeros():
    assert format("{{n:05d}}", {"n": 5}) == "00005"


def test_int_zero_pad_is_sign_aware():
    # The sign stays in front; zeros fill after it, not before.
    assert format("{{n:05d}}", {"n": -42}) == "-0042"


def test_int_width_is_sign_aware_with_spaces():
    assert format("{{n:5d}}", {"n": -42}) == "  -42"


def test_int_width_no_padding_needed_when_value_already_fits():
    assert format("{{n:3d}}", {"n": 12345}) == "12345"


def test_int_width_still_rejects_non_int():
    with pytest.raises(TypeError):
        format("{{n:05d}}", {"n": "5"})


def test_int_width_still_rejects_bool():
    with pytest.raises(TypeError):
        format("{{n:05d}}", {"n": True})


def test_int_width_combines_with_default():
    assert format("{{n:05d|missing}}", {}) == "missing"
    assert format("{{n:05d|missing}}", {"n": None}) == "missing"
    assert format("{{n:05d|missing}}", {"n": 7}) == "00007"


def test_plain_d_still_unpadded_after_width_support_added():
    # Bare :d is untouched by the width feature -- still plain str().
    assert format("{{n:d}}", {"n": 5}) == "5"


def test_width_not_supported_on_float_or_string():
    # Width/zero-pad is scoped to integers only; the same syntax on
    # f or s is an unrecognized specifier, not silently accepted.
    with pytest.raises(ValueError):
        format("{{x:05f}}", {"x": 3.5})
    with pytest.raises(ValueError):
        format("{{s:5s}}", {"s": "hi"})


def test_float_precision_rounds_and_pads_decimals():
    assert format("{{x:.2f}}", {"x": 3.14159}) == "3.14"
    assert format("{{x:.4f}}", {"x": 3.1}) == "3.1000"


def test_float_precision_round_to_nearest():
    assert format("{{x:.2f}}", {"x": 2.674}) == "2.67"  # rounds down


def test_float_precision_still_rejects_int():
    with pytest.raises(TypeError):
        format("{{x:.2f}}", {"x": 3})


def test_float_precision_with_pads_with_spaces():
    assert format("{{x:8.2f}}", {"x": 3.14159}) == "    3.14"


def test_float_precision_zero_pad_is_sign_aware():
    assert format("{{x:08.2f}}", {"x": -3.14159}) == "-0003.14"
    assert format("{{x:08.2f}}", {"x": 3.14159}) == "00003.14"


def test_float_precision_combines_with_default():
    assert format("{{x:.2f|missing}}", {}) == "missing"
    assert format("{{x:.2f|missing}}", {"x": None}) == "missing"
    assert format("{{x:.2f|missing}}", {"x": 3.0}) == "3.00"


def test_precision_not_supported_on_int_or_string():
    # Precision syntax is scoped to floats only.
    with pytest.raises(ValueError):
        format("{{n:.2d}}", {"n": 5})
    with pytest.raises(ValueError):
        format("{{s:.2s}}", {"s": "hi"})

def test_escaped_pipe_in_body_splits_at_real_pipe_only():
    # \| is consumed as an escape, so the first real | is the
    # name/default split. The cleaned body is "a|b|c"; split gives
    # name "a" and default "b|c".
    out = format(r"{{a\|b|c}}", {"a": "v"})
    assert out == "v"
    # With no value, the default "b|c" is used.
    assert format(r"{{a\|b|c}}", {"a": None}) == "b|c"