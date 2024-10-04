# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from unittest.mock import ANY
from unittest.mock import MagicMock
from unittest.mock import call
from uuid import UUID
from uuid import uuid4

import pytest
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from requests import HTTPError

from os2sync_export.os2sync import ReadOnlyOS2SyncClient
from os2sync_export.os2sync import WritableOS2SyncClient
from os2sync_export.os2sync_models import OrgUnit
from os2sync_export.os2sync_models import User

uuid = uuid4()
o = OrgUnit(Name="test", Uuid=uuid, ParentOrgUnitUuid=None)
o2 = OrgUnit(
    Name="test",
    Uuid=uuid,
    ParentOrgUnitUuid=None,
    LOSShortName="Some losShortName",
    PayoutUnitUuid=uuid4(),
    ContactPlaces={uuid4()},
    SOR="SOR ID",
    Tasks={uuid4()},
)
user_uuid = uuid4()
u1 = {
    "Uuid": str(user_uuid),
    "ShortKey": None,
    "UserId": "bsg",
    "PhoneNumber": None,
    "Email": "bsg@digital-identity.dk",
    "Location": "Kontor 15",
    "Positions": [{"OrgUnitUuid": str(o.Uuid), "Name": "Udvikler"}],
    "Person": {"Name": "Brian Storm Graversen", "Cpr": None},
}
u2 = {
    "Uuid": str(uuid4()),
    "ShortKey": None,
    "UserId": "bsg",
    "PhoneNumber": None,
    "Email": "bsg@digital-identity.dk",
    "Location": "Kontor 15",
    "Positions": [{"OrgUnitUuid": str(o.Uuid), "Name": "Udvikler"}],
    "Person": {"Name": "Brian Storm Graversen", "Cpr": None},
}


def test_os2sync_upsert_org_unit_no_changes(mock_os2sync_client):
    """Test that if there are no changes to an org_unit we won't write to os2sync"""

    mock_os2sync_client.os2sync_get_org_unit = MagicMock(return_value=o)
    mock_os2sync_client.upsert_org_unit(o)
    org_unit_info = o.json()
    mock_os2sync_client.session.post.assert_called_once_with(
        f"{mock_os2sync_client.settings.os2sync_api_url}/orgUnit/", json=org_unit_info
    )


def test_os2sync_upsert_org_unit_new(mock_os2sync_client):
    """Test that if no orgUnit was found in fk-org we create it."""

    mock_os2sync_client.os2sync_get_org_unit = MagicMock(side_effect=KeyError)

    mock_os2sync_client.upsert_org_unit(o)

    mock_os2sync_client.session.post.assert_called_once_with(
        f"{mock_os2sync_client.settings.os2sync_api_url}/orgUnit/", json=o.json()
    )


def test_os2sync_upsert_org_unit_changes(mock_os2sync_client):
    """If there are changes to an orgunit it is sent to os2sync"""
    org_unit = o.copy()

    mock_os2sync_client.os2sync_get_org_unit = MagicMock(return_value=o.copy())

    org_unit.Name = "Changed name"
    mock_os2sync_client.upsert_org_unit(org_unit)
    org_unit_info = org_unit.json()

    mock_os2sync_client.session.post.assert_called_once_with(
        f"{mock_os2sync_client.settings.os2sync_api_url}/orgUnit/", json=org_unit_info
    )


def test_os2sync_upsert_org_unit_keep_fk_fields(mock_os2sync_client):
    """Test that certain fields are fetched from fk-org. If these fields are found we use their values in the payload"""

    mock_os2sync_client.os2sync_get_org_unit = MagicMock(return_value=o2)
    mock_os2sync_client.upsert_org_unit(o)
    org_unit_info = o2.json()

    mock_os2sync_client.session.post.assert_called_once_with(
        f"{mock_os2sync_client.settings.os2sync_api_url}/orgUnit/", json=org_unit_info
    )


def test_os2sync_upsert_org_unit_changes_w_fixed_fields(mock_os2sync_client):
    """Test that values from fk-org is kept even if there are changes to an orgunit"""
    new_name = "changed name"
    org_unit = OrgUnit(Name=new_name, Uuid=uuid, ParentOrgUnitUuid=None)
    fk_org = OrgUnit(
        Name="old name",
        Uuid=uuid,
        ParentOrgUnitUuid=None,
        LOSShortName="Some losShortName",
        PayoutUnitUuid=uuid4(),
        ContactPlaces={uuid4()},
        SOR="SOR ID",
        Tasks={uuid4()},
    )

    expected = OrgUnit(
        Name=new_name,
        Uuid=uuid,
        ParentOrgUnitUuid=None,
        LOSShortName=fk_org.LOSShortName,
        PayoutUnitUuid=fk_org.PayoutUnitUuid,
        ContactPlaces=fk_org.ContactPlaces,
        SOR=fk_org.SOR,
        Tasks=fk_org.Tasks,
    )
    mock_os2sync_client.os2sync_get_org_unit = MagicMock(return_value=fk_org)
    mock_os2sync_client.upsert_org_unit(org_unit)

    mock_os2sync_client.session.post.assert_called_once_with(
        f"{mock_os2sync_client.settings.os2sync_api_url}/orgUnit/", json=expected.json()
    )


def test_os2sync_upsert_org_unit_ordered_tasks(mock_os2sync_client):
    """Test the order of 'tasks' doesn't matter."""
    task1 = uuid4()
    task2 = uuid4()
    org_unit_data = o.json()
    org_unit_data.update({"Tasks": [task1, task2]})
    current_data = o.json()
    current_data.update({"Tasks": [task2, task1]})
    org_unit = OrgUnit(**org_unit_data)
    current = OrgUnit(**current_data)

    mock_os2sync_client.os2sync_get_org_unit = MagicMock(return_value=current)
    mock_os2sync_client.upsert_org_unit(org_unit)
    org_unit_info = org_unit.json()

    mock_os2sync_client.session.post.assert_called_once_with(
        f"{mock_os2sync_client.settings.os2sync_api_url}/orgUnit/", json=org_unit_info
    )


def test_update_orgunit_upsert(mock_os2sync_client):
    mock_os2sync_client.upsert_org_unit = MagicMock()
    mock_os2sync_client.update_org_unit(o.Uuid, o)
    mock_os2sync_client.upsert_org_unit.assert_called_with(o)


def test_update_orgunit_delete(mock_os2sync_client):
    mock_os2sync_client.delete_orgunit = MagicMock()
    mock_os2sync_client.update_org_unit(o.Uuid, None)
    mock_os2sync_client.delete_orgunit.assert_called_with(o.Uuid)


def test_update_users(mock_os2sync_client):
    mock_os2sync_client.os2sync_post = MagicMock()
    mock_os2sync_client.update_users(uuid, [u1, u2])
    mock_os2sync_client.os2sync_post.assert_has_calls(
        [
            call(ANY, json=u1),
            call(ANY, json=u2),
        ]
    )


def test_update_users_one_overwritten_uuid_account(mock_os2sync_client):
    mock_os2sync_client.os2sync_delete = MagicMock()
    users = [u1, u2]
    mock_os2sync_client.update_users(user_uuid, users)
    mock_os2sync_client.os2sync_delete.assert_not_called()


def test_update_users_overwritten_uuid_account(mock_os2sync_client):
    mock_os2sync_client.os2sync_delete = MagicMock()
    users = [u2]
    mock_os2sync_client.update_users(user_uuid, users)
    # Deleting overwritten uuid accounts happens on it-account events in main.py
    mock_os2sync_client.os2sync_delete.assert_not_called()


def test_update_users_no_user(mock_os2sync_client):
    mock_os2sync_client.os2sync_delete = MagicMock()
    users = []
    mock_os2sync_client.update_users(user_uuid, users)
    mock_os2sync_client.os2sync_delete.assert_called_once_with(
        f"{{BASE}}/user/{user_uuid}"
    )


@pytest.mark.parametrize(
    "input_org_units",
    ([], [{"Uuid": str(uuid4())}], [{"Uuid": str(uuid4())}, {"Uuid": str(uuid4())}]),
)
@pytest.mark.parametrize(
    "input_users",
    ([], [{"Uuid": str(uuid4())}], [{"Uuid": str(uuid4())}, {"Uuid": str(uuid4())}]),
)
def test_get_hierarchy(input_org_units, input_users, mock_os2sync_client):
    """Test that org_unit and user uuids are returned correctly"""
    # Arrange
    expected_org_units = {UUID(o["Uuid"]) for o in input_org_units}
    expected_users = {UUID(o["Uuid"]) for o in input_users}

    response = MagicMock()
    response.json.return_value = {
        "Result": {"OUs": input_org_units, "Users": input_users}
    }

    mock_os2sync_client.session.get.return_value = response

    request_uuid = uuid4()
    # Act
    org_units, users = mock_os2sync_client.get_hierarchy(request_uuid=request_uuid)
    assert org_units == input_org_units
    assert users == input_users

    org_units, users = mock_os2sync_client.get_existing_uuids(request_uuid=request_uuid)
    mock_os2sync_client.session.get.assert_called_with(
        f"{mock_os2sync_client.settings.os2sync_api_url}/hierarchy/{request_uuid}"
    )

    # Assert
    assert org_units == expected_org_units
    assert users == expected_users


def test_get_hierarchy_retry(mock_settings, mock_os2sync_client):
    """Test that we retry on http-errors"""

    mock_os2sync_client.session.get.side_effect = [HTTPError, HTTPError, MagicMock()]
    # TODO: overwrite wait-time to avoid waiting 10 seconds during tests
    mock_os2sync_client.get_existing_uuids(uuid4())

    assert mock_os2sync_client.session.get.call_count == 3


def test_update_users_delete_uuid_from_it_user(mock_settings):
    """Test that when calling update user the user is deleted with the correct uuid if there are no engagements"""
    uuid = uuid4()
    client = WritableOS2SyncClient(mock_settings, None)
    users = [{"Uuid": uuid, "Positions": []}]
    client.delete_user = MagicMock()

    client.update_users(uuid=uuid4(), users=users)

    client.delete_user.assert_called_once_with(uuid)


def test_update_user(mock_settings):
    client = WritableOS2SyncClient(mock_settings, None)
    client.session = MagicMock()
    user = User(
        **{
            "Uuid": uuid4(),
            "UserId": "BG",
            "Person": {"Name": "Brian"},
            "Positions": [{"OrgUnitUuid": uuid4(), "Name": "Open Source Developer"}],
        }
    )
    client.update_user(user=user)
    client.session.post.assert_called_once_with(
        "http://os2sync:5000/api/user", json=jsonable_encoder(user)
    )


def test_user_no_positions():
    with pytest.raises(ValidationError):
        User(
            **{
                "Uuid": uuid4(),
                "UserId": "BG",
                "Person": {"Name": "Brian"},
                "Positions": [],
            }
        )


@pytest.mark.parametrize("dry_run", (True, False))
def test_dry_run_delete_orgunit(dry_run, mock_settings):
    org_unit_uuid = uuid4()
    session = MagicMock()
    client = (
        ReadOnlyOS2SyncClient(mock_settings, session)
        if dry_run
        else WritableOS2SyncClient(mock_settings, session)
    )
    client.delete_orgunit(uuid=org_unit_uuid)

    if dry_run:
        session.delete.assert_not_called()
    else:
        session.delete.assert_called_once_with(
            f"{mock_settings.os2sync_api_url}/orgUnit/{org_unit_uuid}"
        )


@pytest.mark.parametrize("dry_run", (True, False))
def test_dry_run_update_orgunit(dry_run, mock_settings):
    org_unit_uuid = uuid4()
    client = (
        ReadOnlyOS2SyncClient(mock_settings, MagicMock())
        if dry_run
        else WritableOS2SyncClient(mock_settings, MagicMock())
    )
    # Fake an orgunit wasn't found in fk-org
    client.os2sync_get_org_unit = MagicMock(side_effect=KeyError)
    client.session.post = MagicMock()
    orgunit = OrgUnit(Uuid=org_unit_uuid, Name="test")
    client.update_org_unit(org_unit_uuid, orgunit)

    if dry_run:
        client.session.post.assert_not_called()
    else:
        client.session.post.assert_called_once_with(
            f"{mock_settings.os2sync_api_url}/orgUnit/", json=jsonable_encoder(orgunit)
        )


@pytest.mark.parametrize("dry_run", (True, False))
def test_dry_run_delete_user(dry_run, mock_settings):
    user_uuid = uuid4()
    session = MagicMock()

    client = (
        ReadOnlyOS2SyncClient(mock_settings, session)
        if dry_run
        else WritableOS2SyncClient(mock_settings, session)
    )
    client.delete_user(uuid=user_uuid)

    if dry_run:
        client.session.delete.assert_not_called()
    else:
        client.session.delete.assert_called_once_with(
            f"{mock_settings.os2sync_api_url}/user/{user_uuid}"
        )


@pytest.mark.parametrize("dry_run", (True, False))
def test_dry_run_update_user(dry_run, mock_settings):
    user_uuid = uuid4()
    client = (
        ReadOnlyOS2SyncClient(mock_settings)
        if dry_run
        else WritableOS2SyncClient(mock_settings)
    )
    client.session.post = MagicMock()
    user = User(
        Uuid=user_uuid,
        Name="test",
        UserId="test",
        Person={"Name": "Brian"},
        Positions=[{"Name": "Developer", "OrgUnitUuid": uuid4()}],
    )
    client.update_user(user)

    if dry_run:
        client.session.post.assert_not_called()
    else:
        client.session.post.assert_called_once_with(
            f"{mock_settings.os2sync_api_url}/user", json=jsonable_encoder(user)
        )
