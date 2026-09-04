r"""Core template formatting logic for pyfmt.

Templates use the syntax ``{{name}}`` to reference a key. Unknown keys
are left in the output untouched so the caller can decide what to do
with them. The form ``{{name|default}}`` substitutes the literal
``default`` when the key is missing or its value is ``None``.

A backslash before a brace or pipe (``\{``, ``\}``, ``\|``) escapes the
following character so it is treated as a literal. The backslash
itself is consumed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Mapping, Union

_LEFT = "{{"
_RIGHT = "}}"
# Cached so the hot loop doesn't pay len() on every iteration.
_LEFT_LEN = len(_LEFT)
_RIGHT_LEN = len(_RIGHT)


@dataclass(frozen=True)
class TextSegment:
    text: str


@dataclass(frozen=True)
class PlaceholderSegment:
    name: str
    raw: str  # The original "{{...}}" text from the template, with original whitespace.
    default: str | None = None  # The literal after the pipe, if any.


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
            if template[open_at - 1] == "\\":
                yield TextSegment(template[i : open_at - 1] + "{{")
                i = open_at + _LEFT_LEN
                continue

            yield TextSegment(template[i:open_at])

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
            name, _, default = cleaned.partition("|")
            name = name.strip()
            default = default.strip()
        else:
            name = cleaned
            default = None

        yield PlaceholderSegment(name=name, raw=raw, default=default)

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


def _find_closing(template: str, start: int) -> int:
    """Return the index of the first ``}}`` at or after ``start`` that is
    not preceded by a backslash. Returns -1 if none is found.
    """
    i = start
    length = len(template)
    while i <= length - _RIGHT_LEN:
        if i > 0 and template[i - 1] == "\\" and template[i] == "}":
            i += 1
            continue
        if template[i : i + _RIGHT_LEN] == _RIGHT:
            return i
        i += 1
    return -1


def format(template: str, values: Mapping[str, object]) -> str:
    r"""Replace ``{{name}}`` placeholders in ``template`` with values.

    Lookup is case sensitive. If a name is not present in ``values`` the
    placeholder is left in the result so the caller can spot it.

    A placeholder may use the form ``{{name|default}}``; when the key is
    missing from ``values`` or its value is ``None``, ``default`` is
    inserted as a literal string.

    A backslash before a brace or pipe (``\{``, ``\}``, ``\|``) escapes
    the following character so it is treated as a literal. The backslash
    itself is consumed.
    """
    parts: list[str] = []

    for segment in _scan(template):
        if isinstance(segment, PlaceholderSegment):
            if segment.name in values and values[segment.name] is not None:
                parts.append(str(values[segment.name]))
            elif segment.default is not None:
                parts.append(segment.default)
            else:
                # Leave the placeholder visible so missing keys are obvious.
                parts.append(segment.raw)
        else:
            # Drop any backslashes that are escaping braces at the text
            # level. These are backslashes preceding a { or } that the
            # scanner didn't handle (e.g. a lone \}).
            text = segment.text.replace("\\}", "}").replace("\\{", "{")
            parts.append(text)

    return "".join(parts)