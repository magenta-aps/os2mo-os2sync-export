# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from unittest.mock import patch
from uuid import uuid4

import pytest

from os2sync_export.main import amqp_trigger_it_user
from os2sync_export.main import unpack_context
from os2sync_export.os2sync_models import OrgUnit


@pytest.mark.asyncio
@patch(
    "os2sync_export.main.get_ituser_org_unit_and_employee_uuids",
    return_value=(None, uuid4()),
)
@patch(
    "os2sync_export.main.is_relevant",
    return_value=True,
)
async def test_trigger_it_user_update(
    is_relevant_mock, get_mock, mock_context, mock_settings
):
    """Test react to it-event and update user

    Test that we perform an update user (and not a delete) on events for a user
    with one fk-org account found with uuid matching MOs
    """
    mock_context["user_context"]["settings"] = mock_settings
    settings, _, os2sync_client = unpack_context(context=mock_context)
    # MO persons uuid
    user_uuid = get_mock.return_value[1]
    # Fk-org users for this person - same uuid as i os2mo
    fk_org_users = [{"Uuid": user_uuid}]
    with patch(
        "os2sync_export.main.get_sts_user", return_value=fk_org_users
    ) as get_user_mock:
        await amqp_trigger_it_user(mock_context, uuid4(), None)
    get_mock.assert_awaited_once()
    get_user_mock.assert_called_once_with(user_uuid, gql_session=_, settings=settings)
    # Test that we call update_user on events
    os2sync_client.update_users.assert_called_once_with(user_uuid, fk_org_users)
    # Ensure we won't delete the user
    os2sync_client.delete_user.assert_not_called()


@pytest.mark.asyncio
@patch(
    "os2sync_export.main.get_ituser_org_unit_and_employee_uuids",
    return_value=(None, uuid4()),
)
@patch(
    "os2sync_export.main.is_relevant",
    return_value=True,
)
async def test_trigger_it_user_delete_mo_uuid(
    is_relevant_mock, get_mock, mock_context, mock_settings
):
    """Delete fk-org user with MO uuid if a uuid is overwritten from an IT-account

    Tests that if the found it-account(s) has different uuids to MOs
    the account with MOs uuid is deleted
    """
    mock_context["user_context"]["settings"] = mock_settings
    settings, _, os2sync_client = unpack_context(context=mock_context)
    # MO persons uuid
    user_uuid = get_mock.return_value[1]
    # Fk-org users for this person with uuids different from os2mo
    fk_org_users = [{"Uuid": uuid4()}, {"Uuid": uuid4()}]
    with patch(
        "os2sync_export.main.get_sts_user", return_value=fk_org_users
    ) as get_user_mock:
        await amqp_trigger_it_user(mock_context, uuid4(), None)
    get_mock.assert_awaited_once()
    get_user_mock.assert_called_once_with(user_uuid, gql_session=_, settings=settings)
    # Test that we call update_user on events
    os2sync_client.update_users.assert_called_once_with(user_uuid, fk_org_users)
    # Ensure that we delete the fk-org user with MO uuid as the fk-org accounts have different uuids
    os2sync_client.delete_user.assert_called_with(user_uuid)


@pytest.mark.asyncio
@patch(
    "os2sync_export.main.get_ituser_org_unit_and_employee_uuids",
    return_value=(uuid4(), None),
)
@patch(
    "os2sync_export.main.is_relevant",
    return_value=True,
)
async def test_trigger_it_orgunit_update(
    is_relevant_mock, get_mock, mock_context, mock_settings
):
    """Test react to it-event and update orgunit

    Tests that changes to an orgunits it-accounts leads to the orgunit being
    updated (and not deleted) from fk-org
    """
    mock_context["user_context"]["settings"] = mock_settings
    settings, _, os2sync_client = unpack_context(context=mock_context)

    orgunit_uuid = get_mock.return_value[0]
    fk_org_orggunit = OrgUnit(Uuid=orgunit_uuid)
    with patch(
        "os2sync_export.main.get_sts_orgunit", return_value=fk_org_orggunit
    ) as get_user_mock:
        await amqp_trigger_it_user(mock_context, uuid4(), None)
    get_mock.assert_awaited_once()
    get_user_mock.assert_called_once_with(orgunit_uuid, settings)
    # Test that we call update_org_unit on events
    os2sync_client.update_org_unit(orgunit_uuid, fk_org_orggunit.json())
    # Ensure we won't delete the org_unit
    os2sync_client.delete_orgunit.assert_not_called()


@pytest.mark.asyncio
@patch(
    "os2sync_export.main.get_ituser_org_unit_and_employee_uuids",
    return_value=(uuid4(), None),
)
@patch(
    "os2sync_export.main.is_relevant",
    return_value=True,
)
async def test_trigger_it_orgunit_delete_mo_uuid(
    is_relevant_mock, get_mock, mock_context, mock_settings
):
    """Delete fk-org org_unit with MO uuid if a uuid is overwritten from an IT-account

    Tests that if the found it-account(s) has different uuids to MOs
    the account with MOs uuid is deleted
    """
    mock_context["user_context"]["settings"] = mock_settings
    settings, _, os2sync_client = unpack_context(context=mock_context)
    org_unit_uuid = get_mock.return_value[0]
    with patch(
        "os2sync_export.main.get_sts_orgunit", return_value=OrgUnit(Uuid=uuid4())
    ) as get_user_mock:
        await amqp_trigger_it_user(mock_context, uuid4(), None)
    get_mock.assert_awaited_once()
    # Test that we call update_org_unit on events
    get_user_mock.assert_called_once_with(org_unit_uuid, settings)
    # Ensure that we delete the fk-org org_unit with MO uuid as the unit has a different uuid in fk-org
    os2sync_client.delete_orgunit.assert_called_with(org_unit_uuid)
