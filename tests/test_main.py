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
async def test_trigger_it_user_update(get_mock, mock_context):
    """Test react to it-event and update user"""
    settings, graphql_session, os2sync_client = unpack_context(context=mock_context)

    user_uuid = get_mock.return_value[1]
    with patch(
        "os2sync_export.main.get_sts_user", return_value=[{"Uuid": user_uuid}]
    ) as get_user_mock:
        await amqp_trigger_it_user(mock_context, uuid4(), None)
    get_mock.assert_awaited_once()
    get_user_mock.assert_called_once_with(
        user_uuid, gql_session=graphql_session, settings=settings
    )
    os2sync_client.delete_user.assert_not_called


@pytest.mark.asyncio
@patch(
    "os2sync_export.main.get_ituser_org_unit_and_employee_uuids",
    return_value=(None, uuid4()),
)
async def test_trigger_it_user_delete_mo_uuid(get_mock, mock_context):
    """Delete fk-org user with MO uuid if a uuid is overwritten from an IT-account"""
    settings, graphql_session, os2sync_client = unpack_context(context=mock_context)
    user_uuid = get_mock.return_value[1]
    with patch(
        "os2sync_export.main.get_sts_user", return_value=[{"Uuid": uuid4()}]
    ) as get_user_mock:
        await amqp_trigger_it_user(mock_context, uuid4(), None)
    get_mock.assert_awaited_once()
    get_user_mock.assert_called_once_with(
        user_uuid, gql_session=graphql_session, settings=settings
    )
    os2sync_client.delete_user.assert_called_with(user_uuid)


@pytest.mark.asyncio
@patch(
    "os2sync_export.main.get_ituser_org_unit_and_employee_uuids",
    return_value=(uuid4(), None),
)
async def test_trigger_it_orgunit_update(get_mock, mock_context):
    """Test react to it-event and update orgunit"""
    settings, graphql_session, os2sync_client = unpack_context(context=mock_context)

    orgunit_uuid = get_mock.return_value[0]
    with patch(
        "os2sync_export.main.get_sts_orgunit", return_value=OrgUnit(Uuid=uuid4())
    ) as get_user_mock:
        await amqp_trigger_it_user(mock_context, uuid4(), None)
    get_mock.assert_awaited_once()
    get_user_mock.assert_called_once_with(orgunit_uuid, settings)
    os2sync_client.delete_orgunit.assert_not_called


@pytest.mark.asyncio
@patch(
    "os2sync_export.main.get_ituser_org_unit_and_employee_uuids",
    return_value=(uuid4(), None),
)
async def test_trigger_it_orgunit_delete_mo_uuid(get_mock, mock_context):
    """Delete fk-org org_unit with MO uuid if a uuid is overwritten from an IT-account"""
    settings, graphql_session, os2sync_client = unpack_context(context=mock_context)
    org_unit_uuid = get_mock.return_value[0]
    with patch(
        "os2sync_export.main.get_sts_orgunit", return_value=OrgUnit(Uuid=uuid4())
    ) as get_user_mock:
        await amqp_trigger_it_user(mock_context, uuid4(), None)
    get_mock.assert_awaited_once()
    get_user_mock.assert_called_once_with(org_unit_uuid, settings)
    os2sync_client.delete_orgunit.assert_called_with(org_unit_uuid)
