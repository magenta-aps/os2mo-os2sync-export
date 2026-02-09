# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from unittest.mock import AsyncMock
from uuid import UUID
from uuid import uuid4

from os2sync_export.__main__ import cleanup_duplicate_engagements


async def test_cleanup_duplicate_engagements(
    mock_settings, graphql_session, os2sync_client
):
    os2sync_client.update_users = AsyncMock()
    os2sync_client.delete_user = AsyncMock()
    mock_settings.uuid_from_it_systems = ["FK-org uuid"]

    ou_1 = str(uuid4())
    user_fk_org_uuid = str(uuid4())
    os2sync_client.get_hierarchy = AsyncMock(
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
    await cleanup_duplicate_engagements(
        settings=mock_settings,
        graphql_session=graphql_session,
        os2sync_client=os2sync_client,
    )
    os2sync_client.get_hierarchy.assert_called_once()
    os2sync_client.delete_user.assert_called_with(UUID(user_fk_org_uuid))
