# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from unittest.mock import patch
from uuid import uuid4

from os2sync_export.os2mo import get_sts_orgunit

top_level_uuid = str(uuid4())
other_top_level_uuid = str(uuid4())


class MockUnitWParent:
    def json(self):
        return {"uuid": uuid4(), "parent": {"uuid": other_top_level_uuid}}


@patch("os2sync_export.os2mo.os2mo_get", return_value=MockUnitWParent())
@patch("os2sync_export.os2mo.is_ignored", return_value=False)
async def test_get_sts_orgunit_not_under_top_level(
    mock_os2mo_get, ignored_mock, mock_settings
):
    res = await get_sts_orgunit(uuid4(), settings=mock_settings, graphql_session=None)
    assert res is None
