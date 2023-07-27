# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from typing import Callable
from unittest.mock import ANY
from unittest.mock import AsyncMock
from unittest.mock import call
from unittest.mock import patch
from uuid import UUID
from uuid import uuid4

import pytest

from os2sync_export.config import Settings
from os2sync_export.os2mo import get_sts_user
from os2sync_export.os2mo import group_accounts

mo_uuid = str(uuid4())
engagement_uuid1 = str(uuid4())
engagement_uuid2 = str(uuid4())
fk_org_uuid_1 = str(uuid4())
fk_org_user_key_1 = "AndersA"
fk_org_uuid_2 = str(uuid4())
fk_org_user_key_2 = "AAnd"
fk_org_uuid_3 = str(uuid4())

query_response = [
    {
        "uuid": str(uuid4()),
        "user_key": fk_org_uuid_2,
        "engagement_uuid": engagement_uuid2,
        "itsystem": {"name": "FK-ORG UUID"},
    },
    {
        "uuid": str(uuid4()),
        "user_key": fk_org_user_key_1,
        "engagement_uuid": engagement_uuid1,
        "itsystem": {"name": "FK-ORG USERNAME"},
    },
    {
        "uuid": str(uuid4()),
        "user_key": fk_org_uuid_3,
        "engagement_uuid": None,
        "itsystem": {"name": "FK-ORG UUID"},
    },
    {
        "uuid": str(uuid4()),
        "user_key": fk_org_uuid_1,
        "engagement_uuid": engagement_uuid1,
        "itsystem": {"name": "FK-ORG UUID"},
    },
    {
        "uuid": str(uuid4()),
        "user_key": fk_org_user_key_2,
        "engagement_uuid": engagement_uuid2,
        "itsystem": {"name": "FK-ORG USERNAME"},
    },
]


def test_group_by_engagement_noop():
    groups = group_accounts(query_response, [], None)
    assert len(groups) == 3
    for g in groups:
        assert g.get("uuid") is None
        assert g.get("user_key") is None


def test_group_by_engagement():
    groups = group_accounts(query_response, ["FK-ORG UUID"], "FK-ORG USERNAME")
    assert len(groups) == 3

    for g in [
        {"engagement_uuid": None, "user_key": None, "uuid": fk_org_uuid_3},
        {
            "engagement_uuid": engagement_uuid1,
            "user_key": fk_org_user_key_1,
            "uuid": fk_org_uuid_1,
        },
        {
            "engagement_uuid": engagement_uuid2,
            "user_key": fk_org_user_key_2,
            "uuid": fk_org_uuid_2,
        },
    ]:
        assert g in groups


@pytest.mark.asyncio
@patch("os2sync_export.os2mo.create_os2sync_user")
async def test_get_sts_user(
    create_os2sync_user_mock, set_settings: Callable[..., Settings]
):
    gql_mock = AsyncMock()
    gql_mock.execute.return_value = {
        "employees": [{"objects": [{"itusers": query_response}]}]
    }
    settings = set_settings(
        os2sync_uuid_from_it_systems=["FK-ORG UUID"],
        os2sync_user_key_it_system_name="FK-ORG USERNAME",
    )
    await get_sts_user(mo_uuid=mo_uuid, gql_session=gql_mock, settings=settings)

    assert len(create_os2sync_user_mock.call_args_list) == 3
    for c in [
        call(
            settings=settings,
            gql_session=ANY,
            employee_uuid=UUID(mo_uuid),
            fk_org_uuid=UUID(fk_org_uuid_1),
            user_key=fk_org_user_key_1,
            engagement_uuid=engagement_uuid1,
        ),
        call(
            settings=settings,
            gql_session=ANY,
            employee_uuid=UUID(mo_uuid),
            fk_org_uuid=UUID(fk_org_uuid_2),
            user_key=fk_org_user_key_2,
            engagement_uuid=engagement_uuid2,
        ),
        call(
            settings=settings,
            gql_session=ANY,
            employee_uuid=UUID(mo_uuid),
            fk_org_uuid=UUID(fk_org_uuid_3),
            user_key=None,
            engagement_uuid=None,
        ),
    ]:
        assert c in create_os2sync_user_mock.call_args_list


@pytest.mark.asyncio
@patch("os2sync_export.os2mo.get_sts_user_raw")
async def test_get_sts_user_no_it_accounts(
    get_sts_user_raw_mock, mock_settings: Settings
):
    """Test that users without it-accounts creates one fk-org account"""
    gql_mock = AsyncMock()
    gql_mock.execute.return_value = {"employees": [{"objects": [{"itusers": []}]}]}

    await get_sts_user(mo_uuid=mo_uuid, gql_session=gql_mock, settings=mock_settings)
    get_sts_user_raw_mock.assert_called_once_with(
        mo_uuid,
        settings=mock_settings,
        fk_org_uuid=None,
        user_key=None,
        engagement_uuid=None,
    )
