# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The record-taking tools answer any record with a payload, never a raise.

An agent hands ``validate_records`` and ``generate_message`` whatever
values it holds. Each must return its report, its XML or an ``{"error":
...}`` payload; an exception reaches the client only as an opaque "Error
executing tool" with the reason lost. A value is text, never markup: XML
metacharacters in a record must not add elements to the document.
``fuzz/fuzz_tools.py`` drives the same contract with Atheris; these are
its fixed and property-based cases. The string-only tools are covered in
``tests/test_properties.py``.
"""

from __future__ import annotations

import json
from xml.etree import ElementTree

import pytest

# The complete record every acmt type accepts; shared with the fixtures.
from conftest import _RECORD
from hypothesis import given
from hypothesis import strategies as st

import acmt001_mcp.server as server

#: Markup an agent might pass through from an untrusted source.
INJECTION = "</Nm><Injected>x</Injected><Nm>&amp;<!--c--><![CDATA[z]]>"

_JSON_LEAF = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(),
    st.text(max_size=20),
    st.text(alphabet="<>&\"'\x00\x01\ud800 ", max_size=5),
)
_JSON = st.recursive(
    _JSON_LEAF,
    lambda inner: st.one_of(
        st.lists(inner, max_size=3),
        st.dictionaries(st.text(max_size=8), inner, max_size=3),
    ),
    max_leaves=4,
)
_FIELDS = sorted(_RECORD)


@st.composite
def _records(draw: st.DrawFn) -> list[dict]:
    """A valid record with a few values replaced and a few fields dropped."""
    changes = draw(st.dictionaries(st.sampled_from(_FIELDS), _JSON))
    dropped = draw(st.sets(st.sampled_from(_FIELDS), max_size=3))
    merged = {**_RECORD, **changes}
    return [{k: v for k, v in merged.items() if k not in dropped}]


def _tags(xml: str) -> set[str]:
    """Every element name in ``xml``, without its namespace."""
    root = ElementTree.fromstring(xml.encode("utf-8"))
    return {element.tag.rsplit("}", 1)[-1] for element in root.iter()}


@pytest.mark.parametrize("message_type", server._MESSAGE_TYPE_VALUES)
def test_markup_in_a_value_stays_text(message_type):
    """XML metacharacters are escaped, or the record is refused."""
    record = {
        key: INJECTION if key.endswith(("name", "info", "reason")) else value
        for key, value in _RECORD.items()
    }
    out = server.generate_message(message_type, [record])
    if out.startswith("{"):
        assert set(json.loads(out)) == {"error"}
    else:
        assert "Injected" not in _tags(out)


@given(
    message_type=st.sampled_from(server._MESSAGE_TYPE_VALUES),
    records=_records(),
)
def test_generate_message_answers_any_values(message_type, records):
    """Any values get well-formed XML or an error payload."""
    out = server.generate_message(message_type, records)
    if out.startswith("{"):
        assert set(json.loads(out)) == {"error"}
    else:
        _tags(out)


@given(
    message_type=st.sampled_from(server._MESSAGE_TYPE_VALUES),
    records=_records(),
)
def test_validate_records_answers_any_values(message_type, records):
    """Any values get a consistent report."""
    report = server.validate_records(message_type, records)
    assert set(report) == {"valid", "total", "valid_count", "errors"}
    assert report["total"] == 1
    assert report["valid"] == (report["valid_count"] == 1)
