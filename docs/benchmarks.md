# Benchmarks

This server is a thin shell over the `acmt001` library: it validates
arguments, calls the library, and marshals a result. The library is
benchmarked in its own repository, so re-measuring schema validation here
would only measure that again. What belongs here is the shape an **agent**
experiences — which tool costs what, and how that changes with the size of
the batch it was handed.

## Running it

```sh
python benches/bench_tool_dispatch.py           # full run
python benches/bench_tool_dispatch.py --quick   # what CI runs
python benches/bench_tool_dispatch.py --json    # machine-readable
```

CI runs `--quick`. That is not a timing gate — wall-clock is not comparable
between runners, and a flaky performance gate teaches people to ignore red.
It exists so a benchmark that has stopped compiling against the current API
fails the build rather than rotting into a file that reads as verified and
is not.

## What it measures

**The dispatch floor.** `list_message_types` touches no records, so its
cost is pure shell — argument handling and return marshalling. It lands
around a microsecond, which is the price of every call before any work
happens.

**Metadata lookups.** `get_required_fields` and `get_input_schema` are what
an agent calls while working out how to build a request. Both land in the
low hundreds of microseconds.

**The two batch tools, side by side.** `validate_records` and
`generate_message` on the same growing input. Reading them together is the
point, because they do not scale alike.

## The asymmetry worth knowing

`validate_records` checks every record against the schema, so it is linear
in batch size. `generate_message`, for a single-account message type like
the default `acmt.007.001.05`, renders **only the first record** —
twenty-seven of the thirty-four templates work this way.

So an agent that validates a hundred records and then generates from them
pays for a hundred validations and receives one message. On a 2026 laptop
that is roughly 260 ms of validation against 6 ms of generation.

This is correct ISO 20022 behaviour — an Account Opening Request describes
one account — but it is a genuine trap when batching. The benchmark prints
output size beside the timings for exactly this reason: flat bytes across
growing input is what tells you the rest of the batch was not rendered.

If you need one message per account, call `generate_message` once per
record. If you want a message type that genuinely batches, `list_message_types`
marks the seven that iterate.

## Not measured

`verify_lei_online` makes a network call. Timing somebody else's DNS and
TLS handshake would say nothing about this code, so it is left out.
