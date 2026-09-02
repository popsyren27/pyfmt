"""Core template formatting logic for pyfmt.

Templates use the syntax ``{{name}}`` to reference a key. Unknown keys
are left in the output untouched so the caller can decide what to do
with them.
"""

from __future__ import annotations

from typing import Mapping

_LEFT = "{{"
_RIGHT = "}}"


def format(template: str, values: Mapping[str, object]) -> str:
    """Replace ``{{name}}`` placeholders in ``template`` with values.

    Lookup is case sensitive. If a name is not present in ``values`` the
    placeholder is left in the result so the caller can spot it.
    """
    out: list[str] = []
    i = 0
    length = len(template)

    while i < length:
        open_at = template.find(_LEFT, i)
        if open_at == -1:
            out.append(template[i:])
            break

        out.append(template[i:open_at])

        close_at = template.find(_RIGHT, open_at + len(_LEFT))
        if close_at == -1:
            # Unterminated placeholder. Keep the rest of the string as is.
            out.append(template[open_at:])
            break

        name = template[open_at + len(_LEFT) : close_at].strip()
        if name in values:
            out.append(str(values[name]))
        else:
            # Leave the placeholder visible so missing keys are obvious.
            out.append(template[open_at : close_at + len(_RIGHT)])

        i = close_at + len(_RIGHT)

    return "".join(out)
