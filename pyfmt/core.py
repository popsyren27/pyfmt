r"""Core template formatting logic for pyfmt.

Templates use the syntax ``{{name}}`` to reference a key. Unknown keys
are left in the output untouched so the caller can decide what to do
with them. The form ``{{name|default}}`` substitutes the literal
``default`` when the key is missing or its value is ``None``.

A placeholder may also carry an explicit type specifier,
``{{name:type}}``, where ``type`` is one of ``d`` (int), ``f`` (float),
or ``s`` (str). This is a validation contract, not a coercion request:
the value is still rendered with plain ``str()`` exactly as before, but
if the value's actual type doesn't match the specifier, ``format()``
raises ``TypeError`` rather than silently stringifying it. ``bool`` is
never accepted for ``d`` even though it is technically an ``int``
subclass. A type specifier combines with a default as
``{{name:type|default}}``; the default itself is never type-checked,
since it's always a literal string.

The ``d`` specifier alone additionally accepts a width, and an
optional zero-pad flag, in front of it: ``{{n:5d}}`` right-aligns to a
width of 5 with spaces, ``{{n:05d}}`` zero-pads to width 5 instead
(sign-aware, so ``-42`` renders as ``-0042``). This is the one place
this module *does* reformat rather than just validate -- it's asked
for explicitly by the width syntax, and only applies to ``d``; ``f``
and ``s`` don't take a width.

A backslash before a brace or pipe (``\{``, ``\}``, ``\|``) escapes the
following character so it is treated as a literal. The backslash
itself is consumed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterator, Mapping, Union

_LEFT = "{{"
_RIGHT = "}}"
# Cached so the hot loop doesn't pay len() on every iteration.
_LEFT_LEN = len(_LEFT)
_RIGHT_LEN = len(_RIGHT)

# Recognized {{name:type}} specifiers and the label used in error messages.
_TYPE_LABELS = {"d": "int", "f": "float", "s": "str"}
# {{n:d}}, {{n:5d}}, {{n:05d}} -- optional zero-pad flag, optional width,
# then the literal "d". Only "d" gets width/zero-pad; "f" and "s" don't.
_INT_FORMAT_RE = re.compile(r"^0?\d*d$")


@dataclass(frozen=True)
class TextSegment:
    text: str


@dataclass(frozen=True)
class PlaceholderSegment:
    name: str
    raw: str  # The original "{{...}}" text from the template, with original whitespace.
    default: str | None = None  # The literal after the pipe, if any.
    type: str | None = None  # "d" / "f" / "s" from a {{name:type}} spec, if any.


Segment = Union[TextSegment, PlaceholderSegment]


def _scan(template: str) -> Iterator[Segment]:
    r"""Walk ``template`` and yield text and placeholder segments in order.

    A placeholder segment carries the parsed ``name`` and the ``raw`` text
    (with the original whitespace inside the braces) so callers can do
    whatever they want with either representation. The body is cleaned
    of ``\{``, ``\}`` and ``\|`` escapes before the name and default
    are extracted, so callers see the interpreted form.
    """
    i = 0
    length = len(template)

    while i < length:
        open_at = template.find(_LEFT, i)
        if open_at == -1:
            yield TextSegment(template[i:])
            return

        if open_at > i:
            # If the {{ is preceded by a backslash, the backslash is
            # consumed and the {{ becomes literal text. Yield the prefix
            # without the backslash, then a literal {{, and skip past
            # both before resuming the scan.
            if _is_escaped(template, open_at):
                yield TextSegment(_clean_text(template[i : open_at - 1]) + "{{")
                i = open_at + _LEFT_LEN
                continue

            yield TextSegment(_clean_text(template[i:open_at]))

        # Find the matching }} by scanning forward, treating \}
        # pairs as escaped literals that don't close the placeholder.
        close_at = _find_closing(template, open_at + _LEFT_LEN)
        if close_at == -1:
            # Unterminated placeholder. Keep the rest of the string as is
            # rather than dropping it, otherwise the user gets a confusing
            # truncated result with no hint about what went wrong.
            yield TextSegment(template[open_at:])
            return

        raw = template[open_at : close_at + _RIGHT_LEN]
        inner = template[open_at + _LEFT_LEN : close_at]
        # Clean the body: \|, \{, and \} become literal pipe/brace and
        # the backslash is consumed. The result is what the name (and
        # default, after splitting) refer to.
        cleaned = _clean_body(inner).strip()

        if "|" in cleaned:
            name_part, _, default = cleaned.partition("|")
            name_part = name_part.strip()
            default = default.strip()
        else:
            name_part = cleaned
            default = None

        # An explicit type specifier, if any, is attached to the name with
        # a colon: {{name:type}} or {{name:type|default}}. Only the first
        # colon is significant, so a name that legitimately needs one
        # should avoid this form or expect a ValueError here.
        if ":" in name_part:
            name, _, type_spec = name_part.partition(":")
            name = name.strip()
            type_spec = type_spec.strip()
            if type_spec not in ("f", "s") and not _INT_FORMAT_RE.fullmatch(type_spec):
                raise ValueError(
                    f"unknown type specifier {type_spec!r} in placeholder "
                    f"{{{{{name_part}}}}}; expected d/f/s, optionally with "
                    f"a width and zero-pad flag on d (e.g. 05d)"
                )
        else:
            name = name_part
            type_spec = None

        yield PlaceholderSegment(name=name, raw=raw, default=default, type=type_spec)

        i = close_at + _RIGHT_LEN


def _clean_body(body: str) -> str:
    r"""Process escape sequences in a placeholder body.

    Recognized escapes: ``\{`` -> ``{``, ``\}`` -> ``}``, ``\|`` -> ``|``.
    The backslash is consumed; a trailing backslash with nothing to escape
    is left as-is so the user can spot it.
    """
    out: list[str] = []
    i = 0
    length = len(body)
    while i < length:
        ch = body[i]
        if ch == "\\" and i + 1 < length and body[i + 1] in "{}|":
            out.append(body[i + 1])
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _is_escaped(text: str, index: int) -> bool:
    """Return whether the character at ``index`` has an odd slash prefix."""
    slash_count = 0
    index -= 1
    while index >= 0 and text[index] == "\\":
        slash_count += 1
        index -= 1
    return slash_count % 2 == 1


def _clean_text(text: str) -> str:
    """Remove escapes before braces in ordinary text, respecting parity."""
    out: list[str] = []
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text) and text[i + 1] in "{}":
            if _is_escaped(text, i + 1):
                out.append(text[i + 1])
                i += 2
                continue
        out.append(text[i])
        i += 1
    return "".join(out)


def _find_closing(template: str, start: int) -> int:
    """Return the index of the first ``}}`` at or after ``start`` that is
    not preceded by a backslash. Returns -1 if none is found.
    """
    i = start
    length = len(template)
    while i <= length - _RIGHT_LEN:
        if template[i] == "}" and _is_escaped(template, i):
            i += 1
            continue
        if template[i : i + _RIGHT_LEN] == _RIGHT:
            return i
        i += 1
    return -1


def _matches_type(value: object, type_spec: str) -> bool:
    """Return whether ``value`` satisfies a ``{{name:type}}`` specifier.

    ``type_spec`` may be a bare letter (``"d"``, ``"f"``, ``"s"``) or,
    for ints, carry a width/zero-pad prefix (``"5d"``, ``"05d"``) --
    only the trailing letter matters for the type check itself.

    This is an exact check, not a coercion: ``bool`` does not satisfy
    ``"d"`` even though ``bool`` is technically an ``int`` subclass, and
    an ``int`` does not satisfy ``"f"``. If it did, ``{{x:d}}`` would
    silently accept ``True`` and print ``"True"``, which defeats the
    point of asking for an explicit type.
    """
    kind = type_spec[-1]
    if kind == "d":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "f":
        return isinstance(value, float)
    return isinstance(value, str)  # kind == "s"


def format(template: str, values: Mapping[str, object]) -> str:
    r"""Replace ``{{name}}`` placeholders in ``template`` with values.

    Lookup is case sensitive. If a name is not present in ``values`` the
    placeholder is left in the result so the caller can spot it.

    A placeholder may use the form ``{{name|default}}``; when the key is
    missing from ``values`` or its value is ``None``, ``default`` is
    inserted as a literal string.

    A placeholder may also declare an expected type with
    ``{{name:type}}`` (``type`` is ``d``, ``f``, or ``s`` for int, float,
    or str), optionally combined with a default as
    ``{{name:type|default}}``. This does not change how the value is
    rendered -- it's still just ``str(value)`` -- but raises
    ``TypeError`` if the value's actual type doesn't match.

    ``d`` alone also accepts a width and an optional zero-pad flag in
    front of it, e.g. ``{{n:5d}}`` (space-padded to width 5) or
    ``{{n:05d}}`` (zero-padded, sign-aware). This is the one case where
    the value *is* reformatted rather than just validated.

    A backslash before a brace or pipe (``\{``, ``\}``, ``\|``) escapes
    the following character so it is treated as a literal. The backslash
    itself is consumed.
    """
    parts: list[str] = []

    for segment in _scan(template):
        if isinstance(segment, PlaceholderSegment):
            if segment.name in values and values[segment.name] is not None:
                value = values[segment.name]
                if segment.type is not None:
                    if not _matches_type(value, segment.type):
                        raise TypeError(
                            f"{{{{{segment.name}:{segment.type}}}}} expects "
                            f"{_TYPE_LABELS[segment.type[-1]]}, got "
                            f"{type(value).__name__}"
                        )
                    if segment.type not in ("d", "f", "s"):
                        # A d-with-width spec like "05d" -- the one case
                        # this module actually reformats the value.
                        parts.append(("{:" + segment.type + "}").format(value))
                    else:
                        parts.append(str(value))
                else:
                    parts.append(str(value))
            elif segment.default is not None:
                parts.append(segment.default)
            else:
                # Leave the placeholder visible so missing keys are obvious.
                parts.append(segment.raw)
        else:
            # Drop any backslashes that are escaping braces at the text
            # level. These are backslashes preceding a { or } that the
            # scanner didn't handle (e.g. a lone \}).
            parts.append(_clean_text(segment.text))

    return "".join(parts)