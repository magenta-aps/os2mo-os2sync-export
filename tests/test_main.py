# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from unittest.mock import MagicMock
from unittest.mock import patch
from uuid import uuid4

import pytest


@pytest.mark.asyncio
@patch("ramqp.mo.MORouter")
@patch("fastapi.APIRouter")
@patch("os2sync_export.os2mo.get_sts_orgunit", return_value=None)
async def test_update_single_orgunit(
    mock_router, mock_ramqp, get_sts_orgunit_mock, mock_settings
):
    with patch(
        "os2sync_export.config.get_os2sync_settings", return_value=mock_settings
    ):
        from os2sync_export.main import update_single_orgunit

        uuid = uuid4()
        os2sync_client = MagicMock(delete_orgunit=MagicMock())
        await update_single_orgunit(uuid, mock_settings, os2sync_client)
        os2sync_client.delete_orgunit.assert_called_once_with(uuid)
