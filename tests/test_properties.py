# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Property-based tests over the logic this server owns.

The tools are thin wrappers, but the wrapping itself has invariants an
agent relies on: every failure is an ``{"error": ...}`` payload and never
an exception, every result is JSON, the path scrubber is idempotent, and
the LEI cache hands back copies and never grows past its bound. Hypothesis
searches the input space for a counterexample instead of trusting the
handful of values the unit tests happen to use.
"""

from __future__ import annotations

import json
import string

from hypothesis import given
from hypothesis import strategies as st

import acmt001_mcp.server as server

_MESSAGE_TYPES = st.sampled_from(server._MESSAGE_TYPE_VALUES)
_TEXT = st.text(max_size=40)
_PATHY_TEXT = st.text(
    alphabet=string.ascii_letters + string.digits + "/ ._-:\n",
    max_size=80,
)


# ---------------------------------------------------------------------------
# _without_paths: a normaliser, so it must be idempotent and leave
# path-free text alone.
# ---------------------------------------------------------------------------
@given(_PATHY_TEXT)
def test_without_paths_is_idempotent(message: str) -> None:
    once = server._without_paths(message)
    assert server._without_paths(once) == once


@given(st.text(alphabet=string.ascii_letters + string.digits + " ._-:"))
def test_without_paths_leaves_path_free_text_alone(message: str) -> None:
    assert server._without_paths(message) == message


@given(
    st.lists(
        st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=8),
        min_size=2,
        max_size=5,
    )
)
def test_without_paths_keeps_only_the_basename(parts: list[str]) -> None:
    path = "/" + "/".join(parts)
    assert server._without_paths(f"schema {path} failed") == (
        f"schema {parts[-1]} failed"
    )


# ---------------------------------------------------------------------------
# Error envelopes: whatever the input, the tools answer with data.
# ---------------------------------------------------------------------------
@given(kind=_TEXT, value=_TEXT)
def test_validate_identifier_always_returns_a_json_dict(
    kind: str, value: str
) -> None:
    result = server.validate_identifier(kind, value)
    assert isinstance(result, dict)
    json.dumps(result)
    if kind.lower() in server._IDENTIFIER_KIND_VALUES:
        assert result == {
            "kind": kind.lower(),
            "value": value,
            "valid": result["valid"],
        }
        assert isinstance(result["valid"], bool)
    else:
        assert isinstance(result["error"], str) and result["error"]


@given(message_type=_TEXT)
def test_unknown_message_types_yield_error_payloads(
    message_type: str,
) -> None:
    if message_type in server._MESSAGE_TYPE_VALUES:
        return
    schema = server.get_input_schema(message_type)
    assert isinstance(schema["error"], str) and schema["error"]
    fields = server.get_required_fields(message_type)
    assert fields and all(f.startswith("error: ") for f in fields)
    report = server.validate_records(message_type, [{}])
    assert isinstance(report["error"], str) and report["error"]
    generated = json.loads(server.generate_message(message_type, [{}]))
    assert isinstance(generated["error"], str) and generated["error"]
    described = json.loads(server.describe_message_type_resource(message_type))
    assert isinstance(described["error"], str) and described["error"]


@given(
    message_type=_MESSAGE_TYPES,
    records=st.lists(
        st.dictionaries(
            st.text(alphabet=string.ascii_lowercase + "_", max_size=12),
            _TEXT,
            max_size=4,
        ),
        max_size=3,
    ),
)
def test_validate_records_report_is_consistent(
    message_type: str, records: list[dict]
) -> None:
    report = server.validate_records(message_type, records)
    json.dumps(report)
    assert report["total"] == len(records)
    assert 0 <= report["valid_count"] <= report["total"]
    assert report["valid"] == (report["errors"] == [])
    assert report["valid_count"] == report["total"] - len(
        {e["row"] for e in report["errors"]}
    )


# ---------------------------------------------------------------------------
# Catalogue: the resources are projections of the tools.
# ---------------------------------------------------------------------------
@given(message_type=_MESSAGE_TYPES)
def test_describe_resource_agrees_with_the_tools(message_type: str) -> None:
    described = json.loads(server.describe_message_type_resource(message_type))
    schema = server.get_input_schema(message_type)
    required = server.get_required_fields(message_type)
    assert described == {
        "message_type": message_type,
        "required_fields": required,
        "input_schema": schema,
    }
    assert set(required) <= set(schema["properties"])


# ---------------------------------------------------------------------------
# Prompt: a pure function of its arguments.
# ---------------------------------------------------------------------------
@given(company=_TEXT, country=_TEXT)
def test_onboarding_prompt_names_subject_and_every_tool(
    company: str, country: str
) -> None:
    text = server.onboard_corporate_account(company, country)
    header, steps = text.split("\nFollow this tool order:\n", 1)
    subject = company.strip() or "a corporate account"
    where = f" in {country.strip()}" if country.strip() else ""
    assert header == (
        f"You are onboarding {subject}{where} as an ISO 20022 acmt account."
    )
    for tool in (
        "list_message_types",
        "get_required_fields",
        "get_input_schema",
        "validate_records",
        "generate_message",
    ):
        assert tool in steps


# ---------------------------------------------------------------------------
# LEI cache: round-trips copies and never exceeds its bound.
# ---------------------------------------------------------------------------
_LEI = st.text(
    alphabet=string.ascii_uppercase + string.digits, min_size=20, max_size=20
)


@given(
    lei=_LEI, answer=st.dictionaries(st.text(max_size=8), _TEXT, max_size=4)
)
def test_lei_cache_round_trips_a_copy(lei: str, answer: dict) -> None:
    server._lei_cache.clear()
    stored = server._lei_cache_put(lei, answer)
    fetched = server._lei_cache_get(lei)
    assert stored == answer == fetched
    assert stored is not answer and fetched is not answer
    assert fetched is not stored
    answer["mutated"] = "x"
    assert server._lei_cache_get(lei) == fetched


@given(leis=st.lists(_LEI, min_size=1, max_size=300))
def test_lei_cache_never_exceeds_its_bound(leis: list[str]) -> None:
    server._lei_cache.clear()
    for lei in leis:
        server._lei_cache_put(lei, {"lei": lei})
        assert len(server._lei_cache) <= server._LEI_CACHE_MAX_ENTRIES
    assert set(server._lei_cache) <= set(leis)
    assert server._lei_cache_get(leis[-1]) == {"lei": leis[-1]}
