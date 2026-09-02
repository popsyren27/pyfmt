"""pyfmt - a small string formatting helper.

A placeholder-based template formatter, similar in spirit to str.format
but with a different (and sometimes nicer) syntax. Kept tiny on purpose
so it can grow piece by piece.
"""

from pyfmt.core import format

__all__ = ["format"]
