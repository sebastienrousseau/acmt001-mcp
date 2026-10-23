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


"""generate_message answers every invalid record with an error payload."""

import json

import pytest

server = pytest.importorskip("acmt001_mcp.server")


def test_year_out_of_range_is_an_error(sample_record):
    """A year the XSD date types cannot hold is an error payload, not a raise.

    The schema check raises OverflowError for it (found by fuzz/fuzz_tools.py).
    """
    record = dict(
        sample_record, creation_date_time="222222222026-01-15T10:30:00"
    )
    payload = json.loads(server.generate_message("acmt.007.001.05", [record]))
    assert "year overflow" in payload["error"]
