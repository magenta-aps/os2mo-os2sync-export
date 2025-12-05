# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastramqpi.events import Event

from os2sync_export.main import amqp_trigger_it_user
from os2sync_export.main import amqp_trigger_org_unit
from os2sync_export.os2mo import is_relevant
from os2sync_export.os2sync_models import OrgUnit


@pytest.mark.parametrize("overwritten_uuid", (True, False))
@patch(
    "os2sync_export.main.get_ituser_org_unit_and_employee_uuids",
    return_value=(None, uuid4()),
)
async def test_trigger_it_user_update(
    get_mock, overwritten_uuid, mock_settings, os2sync_client, graphql_session
):
    """Test react to it-event and update user

    Test that we perform an update user (and not a delete) on events for a user
    with one fk-org account found with uuid matching MOs
    """

    # MO persons uuid
    _, user_uuid = get_mock.return_value
    # Fk-org users for this person - same uuid as i os2mo
    fk_org_users = [{"Uuid": uuid4() if overwritten_uuid else user_uuid}]
    with patch(
        "os2sync_export.main.get_sts_user", return_value=fk_org_users
    ) as get_user_mock:
        await amqp_trigger_it_user(
            event_uuid=Event(subject=uuid4(), priority=1000),
            settings=mock_settings,
            graphql_session=graphql_session,
            graphql_client=None,
            os2sync_client=os2sync_client,
        )
    get_mock.assert_awaited_once()
    get_user_mock.assert_called_once_with(
        user_uuid, graphql_session=graphql_session, settings=mock_settings
    )
    # Test that we call update_user on events
    os2sync_client.update_users.assert_called_once_with(user_uuid, fk_org_users)
    if overwritten_uuid:
        os2sync_client.delete_user.assert_called_with(user_uuid)
    else:
        os2sync_client.delete_user.assert_not_called()


@pytest.mark.parametrize("is_relevant", (True, False))
@pytest.mark.parametrize("overwritten_uuid", (True, False))
@patch(
    "os2sync_export.main.get_ituser_org_unit_and_employee_uuids",
    return_value=(uuid4(), None),
)
async def test_trigger_it_orgunit_update(
    get_mock,
    overwritten_uuid,
    is_relevant,
    mock_settings,
    os2sync_client,
    graphql_session,
):
    """Test react to it-event and update orgunit

    Tests that changes to an orgunits it-accounts leads to the orgunit being
    updated (and not deleted) from fk-org
    """
    orgunit_uuid = get_mock.return_value[0]
    fk_org_orggunit = (
        OrgUnit(Uuid=uuid4()) if overwritten_uuid else OrgUnit(Uuid=orgunit_uuid)
    )
    with patch(
        "os2sync_export.main.get_sts_orgunit", return_value=fk_org_orggunit
    ) as get_org_unit_mock:
        with patch("os2sync_export.main.is_relevant", return_value=is_relevant):
            await amqp_trigger_it_user(
                event_uuid=Event(subject=uuid4(), priority=1000),
                settings=mock_settings,
                graphql_session=graphql_session,
                graphql_client=None,
                os2sync_client=os2sync_client,
            )

    get_mock.assert_awaited_once()

    if is_relevant:
        get_org_unit_mock.assert_called_once_with(
            orgunit_uuid, mock_settings, graphql_session=graphql_session
        )
        if overwritten_uuid:
            os2sync_client.delete_orgunit.assert_called_once_with(orgunit_uuid)
        else:
            os2sync_client.delete_orgunit.assert_not_called()
    else:
        get_org_unit_mock.assert_not_called()
        os2sync_client.delete_orgunit.assert_not_called()
    # Test that we call update_org_unit on events
    os2sync_client.update_org_unit(orgunit_uuid, fk_org_orggunit.json())
    # Ensure we won't delete the org_unit


@pytest.mark.parametrize("is_relevant", (True, False))
@pytest.mark.parametrize("overwritten_uuid", (True, False))
async def test_trigger_orgunit_update(
    overwritten_uuid, is_relevant, mock_settings, os2sync_client, graphql_session
):
    """Test react to orgunit event and update it"""
    orgunit_uuid = uuid4()
    fk_org_orggunit = (
        OrgUnit(Uuid=uuid4()) if overwritten_uuid else OrgUnit(Uuid=orgunit_uuid)
    )
    with patch(
        "os2sync_export.main.get_sts_orgunit", return_value=fk_org_orggunit
    ) as get_org_unit_mock:
        with patch("os2sync_export.main.is_relevant", return_value=is_relevant):
            await amqp_trigger_org_unit(
                event_uuid=Event(subject=orgunit_uuid, priority=1000),
                settings=mock_settings,
                graphql_session=graphql_session,
                graphql_client=None,
                os2sync_client=os2sync_client,
            )
    if is_relevant:
        get_org_unit_mock.assert_called_once_with(
            orgunit_uuid, settings=mock_settings, graphql_session=graphql_session
        )
        os2sync_client.delete_orgunit.assert_not_called()
    else:
        get_org_unit_mock.assert_not_called()
        os2sync_client.delete_orgunit.assert_called_once_with(orgunit_uuid)
    # Test that we call update_org_unit on events
    os2sync_client.update_org_unit(orgunit_uuid, fk_org_orggunit.json())


@patch("os2sync_export.main.is_relevant", return_value=True)
@patch("os2sync_export.main.amqp_trigger_employee")
@patch(
    "os2sync_export.main.get_sts_orgunit",
    return_value=OrgUnit(Uuid=uuid4(), Name="test", ParentOrgUnitUuid=None),
)
async def test_trigger_orgunit_employees_update(
    is_relevant_mock,
    trigger_employee_mock,
    find_employee_mock,
    mock_settings,
    os2sync_client,
    graphql_session,
):
    """Test react to orgunit event and all employees"""
    employee_uuids = {uuid4(), uuid4()}
    with patch("os2sync_export.main.find_employees", return_value=employee_uuids):
        await amqp_trigger_org_unit(
            event_uuid=Event(subject=uuid4(), priority=1000),
            settings=mock_settings,
            graphql_session=graphql_session,
            graphql_client=None,
            os2sync_client=os2sync_client,
        )
    assert trigger_employee_mock.call_args_list == [
        call(
            event_uuid=Event(subject=u, priority=1000),
            settings=mock_settings,
            graphql_session=graphql_session,
            graphql_client=None,
            os2sync_client=os2sync_client,
        )
        for u in employee_uuids
    ]


async def test_is_relevant(set_settings):
    unit_uuid = uuid4()
    top_unit_uuid = uuid4()
    line_org = "linjeorganisation"
    mock_settings = set_settings(
        top_unit_uuid=top_unit_uuid, filter_hierarchy_names=[line_org]
    )
    graphql_session = AsyncMock()
    graphql_session.execute.side_effect = [
        {
            "org_units": {
                "objects": [
                    {
                        "current": {
                            "ancestors": [{"uuid": str(top_unit_uuid)}],
                            "org_unit_hierarchy_model": {"name": line_org},
                            "itusers": [],
                        }
                    }
                ]
            }
        }
    ]
    assert await is_relevant(
        graphql_session=graphql_session, unit_uuid=unit_uuid, settings=mock_settings
    )


async def test_is_not_below_top_unit(mock_settings):
    graphql_session = AsyncMock()
    unit_uuid = uuid4()
    graphql_session.execute.side_effect = [
        {
            "org_units": {
                "objects": [{"current": {"ancestors": [{"uuid": str(uuid4())}]}}]
            }
        }
    ]
    assert not await is_relevant(
        graphql_session=graphql_session, unit_uuid=unit_uuid, settings=mock_settings
    )


async def test_is_relevant_wrong_hierarchy(set_settings):
    unit_uuid = uuid4()
    top_unit_uuid = uuid4()
    line_org = "linjeorganisation"
    mock_settings = set_settings(
        top_unit_uuid=top_unit_uuid, filter_hierarchy_names=[line_org]
    )
    graphql_session = AsyncMock()
    graphql_session.execute.side_effect = [
        {
            "org_units": {
                "objects": [
                    {
                        "current": {
                            "ancestors": [{"uuid": str(top_unit_uuid)}],
                            "org_unit_hierarchy_model": {"name": "hidden"},
                            "itusers": [],
                        }
                    }
                ]
            }
        }
    ]
    assert not await is_relevant(
        graphql_session=graphql_session, unit_uuid=unit_uuid, settings=mock_settings
    )


async def test_is_relevant_has_it_account(set_settings):
    unit_uuid = uuid4()
    top_unit_uuid = uuid4()
    line_org = "linjeorganisation"
    it_system_name = "FK-org uuid"
    mock_settings = set_settings(
        top_unit_uuid=top_unit_uuid,
        filter_hierarchy_names=[line_org],
        uuid_from_it_systems=[it_system_name],
    )
    graphql_session = AsyncMock()
    graphql_session.execute.side_effect = [
        {
            "org_units": {
                "objects": [
                    {
                        "current": {
                            "ancestors": [{"uuid": str(top_unit_uuid)}],
                            "org_unit_hierarchy_model": {"name": "hidden"},
                            "itusers": [{"itsystem": {"name": it_system_name}}],
                        }
                    }
                ]
            }
        }
    ]
    assert await is_relevant(
        graphql_session=graphql_session, unit_uuid=unit_uuid, settings=mock_settings
    )


async def test_amqp_trigger_it_user_no_old_accounts(set_settings):
    mock_settings = set_settings(uuid_from_it_systems=["FK-org uuid"])
    os2sync_client_mock = MagicMock()
    with patch(
        "os2sync_export.main.check_terminated_accounts",
        return_value=(set(), set()),
    ):
        await amqp_trigger_it_user(
            Event(subject=uuid4(), priority=1000),
            mock_settings,
            AsyncMock(),
            AsyncMock(),
            os2sync_client_mock,
        )

    os2sync_client_mock.delete_orgunit.assert_not_called()
    os2sync_client_mock.delete_user.assert_not_called()


@patch("os2sync_export.main.is_relevant")
@patch(
    "os2sync_export.main.get_ituser_org_unit_and_employee_uuids",
    return_value=("Irellevant orgunit", None),
)
async def test_amqp_trigger_it_user_deletes_old_accounts(
    relevant_mock, get_ituser_mock, set_settings
):
    old_user_uuids = {uuid4(), uuid4()}
    old_org_unit_uuids = {uuid4(), uuid4()}
    mock_settings = set_settings(uuid_from_it_systems=["FK-org uuid"])
    os2sync_client_mock = MagicMock()
    with patch(
        "os2sync_export.main.check_terminated_accounts",
        return_value=(old_user_uuids, old_org_unit_uuids),
    ):
        await amqp_trigger_it_user(
            Event(subject=uuid4(), priority=1000),
            mock_settings,
            AsyncMock(),
            AsyncMock(),
            os2sync_client_mock,
        )

    for uuid in old_org_unit_uuids:
        assert call(uuid) in os2sync_client_mock.delete_orgunit.call_args_list
    for uuid in old_user_uuids:
        assert call(uuid) in os2sync_client_mock.delete_user.call_args_list
