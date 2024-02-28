# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch
from uuid import uuid4

from os2sync_export.__main__ import cleanup_duplicate_engagements


async def test_cleanup_duplicate_engagements(
    mock_settings, graphql_session, os2sync_client
):
    os2sync_client.update_users = MagicMock()
    mock_settings.os2sync_uuid_from_it_systems = ["FK-org uuid"]

    ou_1 = str(uuid4())
    user_uuid = str(uuid4())
    user_fk_org_uuid = str(uuid4())
    graphql_session.execute.return_value = {
        "data": {
            "itusers": [
                {
                    "current": {
                        "person": [{"uuid": user_uuid}],
                        "user_key": user_fk_org_uuid,
                        "itsystem": {"name": "FK-org uuid"},
                    }
                }
            ]
        }
    }
    os2sync_client.get_hierarchy = MagicMock(
        return_value=(
            "Ou part is not relevant here",
            [
                {
                    # User with duplicated engagement
                    "Uuid": user_fk_org_uuid,
                    "Positions": [
                        {"Name": "tester", "OrgUnitUuid": ou_1},
                        {"Name": "tester", "OrgUnitUuid": ou_1},
                    ],
                },
                {
                    # User with no duplicated engagement
                    "Uuid": str(uuid4()),
                    "Positions": [
                        {"Name": "Control group", "OrgUnitUuid": ou_1},
                    ],
                },
            ],
        )
    )
    with patch(
        "os2sync_export.os2mo.get_sts_user",
        return_value=[
            {
                "Uuid": user_fk_org_uuid,
                "Positions": [{"Name": "tester", "OrgUnitUuid": ou_1}],
            }
        ],
    ) as get_user_mock:
        await cleanup_duplicate_engagements(
            settings=mock_settings,
            graphql_session=graphql_session,
            os2sync_client=os2sync_client,
        )
    get_user_mock.assert_awaited_once_with(
        user_uuid, graphql_session=graphql_session, settings=mock_settings
    )
    os2sync_client.get_hierarchy.assert_called_once()
    assert os2sync_client.update_users.call_count == 2

    assert os2sync_client.update_users.call_args_list[0] == call(
        user_fk_org_uuid, {"Uuid": user_fk_org_uuid, "Positions": []}
    )
    assert os2sync_client.update_users.call_args_list[1] == call(
        user_fk_org_uuid,
        {
            "Uuid": user_fk_org_uuid,
            "Positions": [{"Name": "tester", "OrgUnitUuid": ou_1}],
        },
    )
