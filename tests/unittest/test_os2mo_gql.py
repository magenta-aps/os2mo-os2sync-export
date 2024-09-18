# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from unittest.mock import patch
from uuid import UUID
from uuid import uuid4

import pytest

from os2sync_export.autogenerated_graphql_client.read_user_i_t_accounts import (
    ReadUserITAccountsEmployees,
)
from os2sync_export.autogenerated_graphql_client.read_user_i_t_accounts import (
    ReadUserITAccountsEmployeesObjectsCurrentItusers,
)
from os2sync_export.autogenerated_graphql_client.read_user_i_t_accounts import (
    ReadUserITAccountsEmployeesObjectsCurrentItusersEngagement,
)
from os2sync_export.autogenerated_graphql_client.read_user_i_t_accounts import (
    ReadUserITAccountsEmployeesObjectsCurrentItusersPerson,
)
from os2sync_export.os2mo_gql import convert_to_os2sync
from os2sync_export.os2mo_gql import sync_mo_user_to_fk_org


@patch("os2sync_export.os2mo_gql.ensure_mo_fk_org_user_exists")
async def test_sync_mo_user_to_fk_no_users(
    update_mock, graphql_client, mock_settings, os2sync_client
):
    graphql_client.read_user_i_t_accounts.return_value = ReadUserITAccountsEmployees(
        **{"objects": [{"current": None}]}
    )
    await sync_mo_user_to_fk_org(
        graphql_client=graphql_client,
        uuid=uuid4(),
        settings=mock_settings,
        os2sync_client=os2sync_client,
    )
    update_mock.assert_not_called()


async def test_sync_mo_user_to_fk_one_it_user(
    graphql_client, mock_settings, os2sync_client
):
    it_users = ReadUserITAccountsEmployees(
        **{
            "objects": [
                {
                    "current": {
                        "itusers": [
                            {
                                "uuid": uuid4(),
                                "user_key": str(uuid4()),
                                "external_id": str(uuid4()),
                                "phone": [
                                    {
                                        "address_type": {
                                            "uuid": uuid4(),
                                            "scope": "PHONE",
                                        },
                                        "visibility": {"user_key": "PUBLIC"},
                                        "value": "11223344",
                                    }
                                ],
                                "email": [
                                    {
                                        "address_type": {
                                            "uuid": uuid4(),
                                            "scope": "EMAIL",
                                        },
                                        "visibility": {"user_key": "PUBLIC"},
                                        "value": "bsg@digital-identity.dk",
                                    }
                                ],
                                "person": [
                                    {
                                        "name": "Brian Storm Graversen",
                                        "nickname": "",
                                        "cpr_number": 1234567890,
                                    }
                                ],
                                "engagement": [
                                    {
                                        "org_unit": [{"uuid": uuid4()}],
                                        "job_function": {
                                            "name": "open source developer"
                                        },
                                    }
                                ],
                            }
                        ],
                        "fk_org_uuids": [],
                    }
                }
            ]
        }
    )
    graphql_client.read_user_i_t_accounts.return_value = it_users
    await sync_mo_user_to_fk_org(
        graphql_client=graphql_client,
        uuid=uuid4(),
        settings=mock_settings,
        os2sync_client=os2sync_client,
    )
    os2sync_client.delete_user.assert_not_called()
    os2sync_client.update_user.assert_called_once_with(
        convert_to_os2sync(mock_settings, it_users.objects[0].current.itusers[0])
    )


async def test_sync_mo_user_to_fk_delete_user(
    graphql_client, mock_settings, os2sync_client
):
    it_users = ReadUserITAccountsEmployees(
        **{
            "objects": [
                {
                    "current": {
                        "itusers": [],
                        "fk_org_uuids": [
                            {
                                "user_key": str(uuid4()),
                                "external_id": str(uuid4()),
                            }
                        ],
                    }
                }
            ]
        }
    )
    graphql_client.read_user_i_t_accounts.return_value = it_users
    await sync_mo_user_to_fk_org(
        graphql_client=graphql_client,
        uuid=uuid4(),
        settings=mock_settings,
        os2sync_client=os2sync_client,
    )
    os2sync_client.update_user.assert_not_called()
    os2sync_client.delete_user.assert_called_once_with(
        UUID(it_users.objects[0].current.fk_org_uuids[0].external_id)
    )


BASE_ITUSER_RESPONSE = ReadUserITAccountsEmployeesObjectsCurrentItusers(
    uuid=uuid4(),
    user_key="test",
    external_id=str(uuid4()),
    email=[],
    phone=[],
    person=[],
    engagement=[
        ReadUserITAccountsEmployeesObjectsCurrentItusersEngagement(
            **{"job_function": {"name": "tester"}, "org_unit": [{"uuid": uuid4()}]}  # type: ignore
        )
    ],
)


def test_convert_to_os2sync(mock_settings):
    mo_it_user = BASE_ITUSER_RESPONSE.copy()
    mo_it_user.person = [
        ReadUserITAccountsEmployeesObjectsCurrentItusersPerson(
            name="Brian", nickname=""
        )
    ]
    os2sync_user = convert_to_os2sync(mock_settings, mo_it_user)
    assert os2sync_user.Person.Name == "Brian"


def test_convert_to_os2sync_nickname(mock_settings):
    mo_it_user = BASE_ITUSER_RESPONSE.copy()
    mo_it_user.person = [
        ReadUserITAccountsEmployeesObjectsCurrentItusersPerson(
            name="Brian", nickname="STORMEN"
        )
    ]
    os2sync_user = convert_to_os2sync(mock_settings, mo_it_user)
    assert os2sync_user.Person.Name == "STORMEN"


@pytest.mark.parametrize("sync_cpr", [True, False])
def test_convert_to_os2sync_cpr(sync_cpr, set_settings):
    settings = set_settings(sync_cpr=sync_cpr)
    mo_it_user = BASE_ITUSER_RESPONSE.copy()
    mo_it_user.person = [
        ReadUserITAccountsEmployeesObjectsCurrentItusersPerson(
            name="Brian", nickname="STORMEN", cpr_number="1234567890"
        )
    ]
    os2sync_user = convert_to_os2sync(settings, mo_it_user)
    if sync_cpr:
        assert os2sync_user.Person.Cpr == "1234567890"
    else:
        assert os2sync_user.Person.Cpr is None
