#!/usr/bin/env python3
"""Entry for make.fun bounty: fortune cookie for the liquidated (u-clever-harbor-75).

Prints one fortune-cookie message for a crypto trader just liquidated:
a single line of at most 20 words, in the voice of a fortune slip.

Python 3.13, stdlib only, deterministic: no network, clock, or randomness.
"""

import io
import os
import sys

MAX_WORDS = 20

ENTRY = (
    "You will find great wealth in your future, hidden in the couch "
    "cushions where your liquidated margin went to hide."
)


def count_words(text: str) -> int:
    """Count whitespace-separated words in ``text``."""
    return len(text.split())


def validate(text: str) -> None:
    """The entry must be one line of at most 20 words, ending in a full stop.

    Rejects empty or over-long entries, embedded newlines/carriage
    returns, leading/trailing whitespace, and control characters: a
    fortune slip carries a single short prophecy, not a paragraph.
    The closing full stop is part of the fortune-cookie voice — the
    prophecy is delivered, then the slip ends.
    """
    if not text:
        raise ValueError("entry must not be empty")
    if count_words(text) > MAX_WORDS:
        raise ValueError(
            f"entry must be at most {MAX_WORDS} words, got {count_words(text)}"
        )
    if "\n" in text or "\r" in text:
        raise ValueError("entry must not contain a newline or carriage return")
    if text != text.strip():
        raise ValueError("entry must not start or end with whitespace")
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in text):
        raise ValueError("entry must not contain control characters")
    if len(text.splitlines()) != 1:
        raise ValueError("entry must be a single line")
    if not text.endswith("."):
        raise ValueError("entry must end with a full stop")


def write_and_verify(path: str, text: str) -> None:
    """Write ``text`` to ``path``, then verify it by reading it back."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    # Verify the written file by reading it back: exact content and length.
    with open(path, "r", encoding="utf-8", newline="") as f:
        written = f.read()
    if written != text:
        raise RuntimeError("verification failed: written entry does not match")
    if len(written) != len(text):
        raise RuntimeError("verification failed: written entry length differs")


def resolve_out_path() -> str:
    """Resolve the output file path.

    ``$MAKEFUN_OUTPUT`` may point at a directory (``entry.txt`` is written
    inside it) or directly at a file (used as-is); the default is
    ``/output/entry.txt``, falling back to ``./output/entry.txt`` next to
    this script when the requested location is not writable.
    """
    requested = os.environ.get("MAKEFUN_OUTPUT") or "/output/entry.txt"
    if requested.endswith(".txt"):
        parent = os.path.dirname(requested)
        if parent:
            try:
                os.makedirs(parent, exist_ok=True)
            except OSError:
                return fallback_out_path()
        return requested
    try:
        os.makedirs(requested, exist_ok=True)
        probe = os.path.join(requested, ".write_probe")
        with open(probe, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(probe)
        return os.path.join(requested, "entry.txt")
    except OSError:
        return fallback_out_path()


def fallback_out_path() -> str:
    """Output fallback: an ``output`` directory next to this script."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "output", "entry.txt")


def render_output(text: str) -> str:
    """Render the exact stdout payload and verify it by reading it back.

    The entry is written to an in-memory buffer first and read back
    before anything reaches stdout, so a rendering fault is caught
    instead of being printed.
    """
    buffer = io.StringIO()
    buffer.write(text)
    buffer.seek(0)
    rendered = buffer.read()
    if rendered != text:
        raise RuntimeError("verification failed: rendered output does not match")
    if len(rendered) != len(text):
        raise RuntimeError("verification failed: rendered output length differs")
    return rendered


def main() -> int:
    validate(ENTRY)
    path = resolve_out_path()
    try:
        write_and_verify(path, ENTRY)
    except OSError:
        # Primary output location failed: fall back to ./output/entry.txt
        # next to this script and verify that write instead.
        path = fallback_out_path()
        write_and_verify(path, ENTRY)
    # Print exactly the entry text: no extra output, no trailing newline.
    sys.stdout.write(render_output(ENTRY))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
