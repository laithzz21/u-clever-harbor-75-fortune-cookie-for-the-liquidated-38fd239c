#!/usr/bin/env python3
"""Fortune cookie for the liquidated.

Entry for the make.fun bounty "u-clever-harbor-75-fortune-cookie-for-
the-liquidated-38fd239c": a single fortune-cookie slip for a crypto
trader whose margin was just liquidated.

The program prints one fortune — exactly one line of at most 20
words, in the voice of a fortune slip — to stdout, and also writes
it to the output file named by $MAKEFUN_OUTPUT (default
``/output/entry.txt``). Stdout carries the entry text only, with no
trailing newline, so the printed bytes are exactly the fortune.

Python 3.13, standard library only. Deterministic: no network, no
clock, no randomness — the same fortune every run.
"""

import io
import os
import sys

# ---------------------------------------------------------------------------
# The fortune
# ---------------------------------------------------------------------------

MAX_WORDS = 20
MIN_WORDS = 1
# A fortune slip is short: this generous upper bound only guards against
# an accidentally concatenated or duplicated fortune, not real wording.
MAX_CHARS = 200
DEFAULT_OUTPUT = "/output/entry.txt"

# The single fortune this program delivers. Kept as one constant so the
# exact wording is visible in one place and easy to audit.
ENTRY = (
    "You will find great wealth in your future, hidden in the couch "
    "cushions where your liquidated margin went to hide."
)


# ---------------------------------------------------------------------------
# Word counting and validation
# ---------------------------------------------------------------------------

def count_words(text: str) -> int:
    """Count the whitespace-separated words in ``text``.

    Splitting on any run of whitespace means multiple spaces, tabs, or
    other spacing between words never inflates the count.
    """
    return len(text.split())


def find_control_characters(text: str) -> list[int]:
    """Return the indexes of any control characters in ``text``.

    Control characters are the C0 range (U+0000–U+001F) plus DEL
    (U+007F). A fortune slip is plain printable text, so none of these
    may appear; returning positions instead of a bare boolean makes the
    error message point at the offending character.
    """
    return [i for i, ch in enumerate(text) if ord(ch) < 0x20 or ord(ch) == 0x7F]


def check_length(text: str) -> None:
    """Reject fortunes longer than ``MAX_CHARS`` characters.

    The word-count check is the real limit; this is a backstop against
    a fortune that was accidentally duplicated or concatenated.
    """
    if len(text) > MAX_CHARS:
        raise ValueError(
            f"entry must be at most {MAX_CHARS} characters, "
            f"got {len(text)}"
        )


def check_word_count(text: str) -> None:
    """Reject fortunes that are empty or longer than ``MAX_WORDS`` words."""
    words = count_words(text)
    if words < MIN_WORDS:
        raise ValueError("entry must contain at least one word")
    if words > MAX_WORDS:
        raise ValueError(
            f"entry must be at most {MAX_WORDS} words, got {words}"
        )


def check_single_line(text: str) -> None:
    """Reject fortunes that span more than one line.

    A fortune slip carries a single short prophecy. Embedded newlines
    or carriage returns would split it, and leading or trailing
    whitespace would change the exact printed bytes.
    """
    if "\n" in text or "\r" in text:
        raise ValueError("entry must not contain a newline or carriage return")
    if text != text.strip():
        raise ValueError("entry must not start or end with whitespace")
    if "  " in text:
        raise ValueError("entry must not contain consecutive spaces")
    if len(text.splitlines()) != 1:
        raise ValueError("entry must be a single line")


def check_printable(text: str) -> None:
    """Reject fortunes containing control characters."""
    bad = find_control_characters(text)
    if bad:
        raise ValueError(
            "entry must not contain control characters "
            f"(found at positions {bad})"
        )


def check_closing_punctuation(text: str) -> None:
    """The fortune must end with a full stop.

    The closing full stop is part of the fortune-cookie voice: the
    prophecy is delivered, then the slip ends.
    """
    if not text.endswith("."):
        raise ValueError("entry must end with a full stop")


def validate(text: str) -> None:
    """Run every structural check on the fortune.

    Raises ``ValueError`` with a specific message on the first failing
    check, so a bad fortune is never printed or written.
    """
    if not text:
        raise ValueError("entry must not be empty")
    check_length(text)
    check_word_count(text)
    check_single_line(text)
    check_printable(text)
    check_closing_punctuation(text)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_output(text: str) -> str:
    """Render the exact stdout payload, verified by a round trip.

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


# ---------------------------------------------------------------------------
# Output file handling
# ---------------------------------------------------------------------------

def fallback_out_path() -> str:
    """Output fallback: an ``output`` directory next to this script."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "output", "entry.txt")


def resolve_out_path() -> str:
    """Resolve the output file path.

    ``$MAKEFUN_OUTPUT`` may point at a directory (``entry.txt`` is
    written inside it) or directly at a file (used as-is); the default
    is ``/output/entry.txt``, falling back to ``./output/entry.txt``
    next to this script when the requested location is not writable.
    """
    requested = os.environ.get("MAKEFUN_OUTPUT") or DEFAULT_OUTPUT
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


def save_entry(text: str) -> str:
    """Save the entry to its output file, falling back if needed.

    Returns the path actually written. If the primary location fails —
    whether the write itself errors or the read-back verification
    fails — retries once at the fallback location next to this script.
    """
    path = resolve_out_path()
    try:
        write_and_verify(path, text)
    except (OSError, RuntimeError):
        path = fallback_out_path()
        write_and_verify(path, text)
    return path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    """Validate the fortune, save it, and print it to stdout."""
    validate(ENTRY)
    save_entry(ENTRY)
    # Print exactly the entry text: no extra output, no trailing newline.
    sys.stdout.write(render_output(ENTRY))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
