#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""What an agent waits for when it calls these tools.

A server like this one is a thin shell over `acmt001`: it validates
arguments, calls the library, and marshals a result. The library is
benchmarked in its own repository, so re-measuring schema validation here
would just measure that again. What belongs here is the shape an *agent*
experiences -- which tool costs what, and how that changes with the size
of the batch it was handed.

Three things are measured.

* **The dispatch floor.** `list_message_types` touches no records at all.
  Whatever it costs is pure shell: argument handling and return
  marshalling. An agent pays this on every call it makes, however small.

* **Metadata lookups.** `get_required_fields` and `get_input_schema` are
  what an agent calls while working out how to build a request. They are
  called often and interactively, so their cost is felt directly.

* **The two batch tools across sizes.** `validate_records` and
  `generate_message` on the same growing input. Reading them side by side
  is the point, because they do not scale alike and the difference is
  easy to misread as one of them being fast.

The asymmetry is the finding. `validate_records` checks every record
against the schema, so it is linear in batch size and dominates. For a
single-account message type like the default `acmt.007.001.05`,
`generate_message` renders **only the first record** -- twenty-seven of
the thirty-four templates work this way -- so its cost is nearly flat and
the extra records are silently dropped. An agent that validates a hundred
records and then generates from them pays for a hundred validations and
receives one message. That is correct ISO 20022 behaviour and a genuine
trap, so the table prints output size beside the timing: flat bytes is
what tells you the rest of the batch was not rendered.

`verify_lei_online` is deliberately not measured. It makes a network
call, and timing somebody else's DNS and TLS handshake tells you nothing
about this code.

Run::

    python benches/bench_tool_dispatch.py
    python benches/bench_tool_dispatch.py --json
    python benches/bench_tool_dispatch.py --quick     # what CI runs

Nothing here asserts a threshold: wall-clock is not comparable between
machines, and a flaky performance gate teaches people to ignore red. CI
runs ``--quick`` so a benchmark that has stopped compiling against the
current API fails the build instead of rotting into a file that reads as
verified and is not.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from functools import partial
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import acmt001_mcp.server as server  # noqa: E402

#: The server's default message type: one account per message.
MESSAGE_TYPE = "acmt.007.001.05"

#: One complete, valid account-opening record. Kept complete on purpose:
#: a record missing fields fails validation early and would measure the
#: rejection path rather than the working one.
_RECORD = {
    "msg_id": "ACMT-MSG-0001",
    "creation_date_time": "2026-01-15T10:30:00",
    "process_id": "ACMT-PRC-0001",
    "account_id": "GB29NWBK60161331926819",
    "account_id_other": "VRTL-0001-0001",
    "account_currency": "EUR",
    "account_name": "Treasury Operating Account",
    "account_type_cd": "CACC",
    "account_servicer_bic": "NWBKGB2LXXX",
    "account_owner_name": "Acme Embedded Finance Ltd",
    "account_owner_country": "GB",
    "account_owner_lei": "5493001KJTIIGC8Y1R12",
    "org_full_legal_name": "Acme Embedded Finance Limited",
    "org_country_of_operation": "GB",
    "org_address_country": "GB",
    "org_address_town": "London",
    "org_id_lei": "5493001KJTIIGC8Y1R12",
    "org_id_other": "ACME-ORG-001",
    "status_cd": "RECE",
    "reason_cd": "RR04",
}


def build(count: int) -> list[dict]:
    """``count`` distinct valid records."""
    return [
        dict(
            _RECORD,
            msg_id=f"ACMT-MSG-{i:05d}",
            account_id_other=f"VRTL-{i:04d}-0001",
        )
        for i in range(count)
    ]


def _best(call, repeats: int) -> float:
    """Best-of timing after one untimed warm-up.

    The warm-up matters more than usual here: the first `generate_message`
    in a process compiles the XSD, which costs two orders of magnitude
    more than every call after it. Timing that once and calling it the
    tool's cost would be wrong in both directions -- far too slow for a
    long-lived server, and far too fast for a one-shot process.
    """
    call()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        call()
        samples.append(time.perf_counter() - start)
    return min(samples)


def measure(count: int, repeats: int) -> dict:
    """Both batch tools on the same ``count``-record input."""
    records = build(count)
    validate = _best(
        partial(server.validate_records, MESSAGE_TYPE, records), repeats
    )
    generate = _best(
        partial(server.generate_message, MESSAGE_TYPE, records), repeats
    )
    rendered = server.generate_message(MESSAGE_TYPE, records)
    return {
        "records": count,
        "validate_ms": validate * 1e3,
        "validate_us_per_record": validate * 1e6 / count,
        "generate_ms": generate * 1e3,
        "generated_bytes": len(rendered),
    }


def run(quick: bool) -> dict:
    sizes = [1, 10] if quick else [1, 10, 50, 100]
    repeats = 2 if quick else 5
    reps = 200 if quick else 2000
    floor = {
        "list_message_types": _best(server.list_message_types, reps) * 1e6,
        "get_required_fields": _best(
            partial(server.get_required_fields, MESSAGE_TYPE), reps // 4
        )
        * 1e6,
        "get_input_schema": _best(
            partial(server.get_input_schema, MESSAGE_TYPE), reps // 4
        )
        * 1e6,
    }
    return {
        "message_type": MESSAGE_TYPE,
        "dispatch_us": floor,
        "sizes": [measure(n, repeats) for n in sizes],
    }


def render(results: dict) -> None:
    print("  Per-call cost of the tools an agent uses to orient itself:\n")
    for name, micros in results["dispatch_us"].items():
        print(f"    {name:<22}{micros:>10.1f} us")
    print(
        "\n  list_message_types touches no records, so its cost is the "
        "dispatch floor:\n  what every call pays before doing any work."
    )

    print(f"\n  Batch tools, {results['message_type']}:\n")
    print(
        f"    {'records':>8}{'validate ms':>14}{'us/record':>12}"
        f"{'generate ms':>14}{'output bytes':>15}"
    )
    for row in results["sizes"]:
        print(
            f"    {row['records']:>8}{row['validate_ms']:>14.2f}"
            f"{row['validate_us_per_record']:>12.1f}"
            f"{row['generate_ms']:>14.2f}{row['generated_bytes']:>15,}"
        )

    rows = results["sizes"]
    first, last = rows[0], rows[-1]
    if last["generated_bytes"] == first["generated_bytes"]:
        ratio = (
            last["validate_ms"] / last["generate_ms"]
            if last["generate_ms"]
            else 0.0
        )
        print(
            f"\n  Output size is FLAT while the batch grows: this message "
            f"type describes one account,\n  so generate_message renders "
            f"the first record and ignores the rest. At "
            f"{last['records']} records\n  validation costs "
            f"{ratio:.0f}x what generation does -- an agent pays for "
            f"{last['records']} validations\n  and receives one message. "
            f"That is correct for acmt, and worth knowing before you "
            f"batch."
        )
    else:
        print(
            "\n  Output grows with the batch: this message type iterates "
            "records."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "--quick", action="store_true", help="small sizes, as CI runs"
    )
    args = parser.parse_args()

    results = run(quick=args.quick)
    if args.json:
        json.dump(results, sys.stdout, indent=1)
        print()
    else:
        render(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
