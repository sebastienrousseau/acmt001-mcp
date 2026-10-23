# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Coverage-guided fuzzing of the text-taking tools with Atheris.

Each input becomes one string. It is handed, as the value and as the
kind, to ``validate_identifier``; as the message type to
``get_required_fields``, ``get_input_schema`` and the describe resource;
as both arguments to the onboarding prompt; and, when it decodes as JSON
records (a list of objects, or one object), to ``validate_records`` and
``generate_message``. A tool must answer with its documented type -- a
result or an ``{"error": ...}`` payload -- and never raise; anything
else is a crash libFuzzer reports and minimises. The fixed and
property-based cases of the same contract are in
``tests/test_untrusted_text.py`` and ``tests/test_properties.py``.

``verify_lei_online`` is left out: it reaches the live GLEIF API, and a
fuzzer must not.

Run (Linux x86_64, Python 3.12-3.14)::

    pip install --require-hashes -r requirements/fuzz.txt
    pip install --no-deps -e .
    python fuzz/fuzz_tools.py -max_total_time=60 -max_len=16384 \\
        work-corpus/ fuzz/corpus/
"""

import contextlib
import io
import json
import sys

import atheris

with atheris.instrument_imports():
    import acmt001_mcp.server as srv

MESSAGE_TYPES = sorted(srv._MESSAGE_TYPE_VALUES)
KINDS = ("iban", "bic", "lei")


def _expect(result: object, kind: type, tool: str) -> None:
    """Raise when ``tool`` answered with anything but ``kind``."""
    if not isinstance(result, kind):
        raise TypeError(f"{tool} returned {type(result).__name__}")


def _records(text: str) -> list[dict] | None:
    """``text`` as the records argument the MCP schema admits, or None."""
    try:
        value = json.loads(text)
    except (ValueError, RecursionError):
        return None
    if isinstance(value, dict):
        value = [value]
    if isinstance(value, list) and all(isinstance(r, dict) for r in value):
        return value
    return None


def _text_tools(text: str) -> None:
    """Every tool whose arguments are plain strings."""
    for kind in (*KINDS, text):
        _expect(srv.validate_identifier(kind, text), dict, "identifier")
    _expect(srv.get_required_fields(text), list, "get_required_fields")
    _expect(srv.get_input_schema(text), dict, "get_input_schema")
    _expect(srv.describe_message_type_resource(text), str, "describe")
    _expect(srv.onboard_corporate_account(text, text), str, "prompt")


def _record_tools(message_type: str, records: list[dict]) -> None:
    """The two tools that take account records."""
    report = srv.validate_records(message_type, records)
    _expect(report, dict, "validate_records")
    _expect(srv.generate_message(message_type, records), str, "generate")


def test_one_input(data: bytes) -> None:
    """Feed one fuzzed string to every text-taking tool."""
    # Decoded directly, so libFuzzer's byte mutations of the seed corpus
    # (fuzz/corpus) stay JSON- and identifier-shaped.
    text = data.decode("utf-8", errors="replace")
    message_type = MESSAGE_TYPES[len(data) % len(MESSAGE_TYPES)]
    # The library prints validation errors to stdout; keep the log clean.
    with contextlib.redirect_stdout(io.StringIO()):
        _text_tools(text)
        records = _records(text)
        if records is not None:
            _record_tools(message_type, records)


def main() -> None:
    """Hand the target to libFuzzer."""
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
