# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from unittest.mock import ANY
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch
from uuid import uuid4

from os2sync_export.os2sync import OS2SyncClient
from os2sync_export.os2sync_models import OrgUnit

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


def test_os2sync_upsert_org_unit_no_changes(mock_settings):
    """Test that if there are no changes to an org_unit we won't write to os2sync"""
    session_mock = MagicMock()
    os2sync_client = OS2SyncClient(settings=mock_settings, session=session_mock)

    with patch.object(os2sync_client, "os2sync_get_org_unit", return_value=o):
        os2sync_client.upsert_org_unit(o)

    session_mock.post.assert_called_once_with(
        f"{mock_settings.os2sync_api_url}/orgUnit/", json=o.json()
    )


def test_os2sync_upsert_org_unit_new(mock_settings):
    """Test that if no orgUnit was found in fk-org we create it."""
    session_mock = MagicMock()
    os2sync_client = OS2SyncClient(settings=mock_settings, session=session_mock)

    with patch.object(os2sync_client, "os2sync_get_org_unit", side_effect=KeyError):
        os2sync_client.upsert_org_unit(o)

        session_mock.post.assert_called_once_with(
            f"{mock_settings.os2sync_api_url}/orgUnit/", json=o.json()
        )


def test_os2sync_upsert_org_unit_changes(mock_settings):
    """If there are changes to an orgunit it is sent to os2sync"""

    org_unit = o.copy()
    session_mock = MagicMock()
    os2sync_client = OS2SyncClient(settings=mock_settings, session=session_mock)

    with patch.object(os2sync_client, "os2sync_get_org_unit", return_value=o.copy()):
        org_unit.Name = "Changed name"
        os2sync_client.upsert_org_unit(org_unit)

    session_mock.post.assert_called_once_with(
        f"{mock_settings.os2sync_api_url}/orgUnit/", json=org_unit.json()
    )


def test_os2sync_upsert_org_unit_keep_fk_fields(mock_settings):
    """Test that certain fields are fetched from fk-org. If these fields are found we use their values in the payload"""

    session_mock = MagicMock()
    os2sync_client = OS2SyncClient(settings=mock_settings, session=session_mock)

    with patch.object(os2sync_client, "os2sync_get_org_unit", return_value=o2):
        os2sync_client.upsert_org_unit(o)

    session_mock.post.assert_called_once_with(
        f"{mock_settings.os2sync_api_url}/orgUnit/", json=o2.json()
    )


def test_os2sync_upsert_org_unit_changes_w_fixed_fields(mock_settings):
    """Test that values from fk-org is kept even if there are changes to an orgunit"""

    org_unit = o.copy()
    fk_org = o2.copy()
    session_mock = MagicMock()
    os2sync_client = OS2SyncClient(settings=mock_settings, session=session_mock)
    org_unit.Name = "Changed name"
    expected = o.copy()
    expected.Name = org_unit.Name
    with patch.object(os2sync_client, "os2sync_get_org_unit", return_value=fk_org):
        os2sync_client.upsert_org_unit(org_unit)

    session_mock.post.assert_called_once_with(
        f"{mock_settings.os2sync_api_url}/orgUnit/", json=expected.json()
    )


def test_os2sync_upsert_org_unit_ordered_tasks(mock_settings):
    """Test the order of 'tasks' doesn't matter."""

    task1 = uuid4()
    task2 = uuid4()
    org_unit_data = o.json()
    org_unit_data.update({"Tasks": [task1, task2]})
    current_data = o.json()
    current_data.update({"Tasks": [task2, task1]})
    org_unit = OrgUnit(**org_unit_data)
    current = OrgUnit(**current_data)
    session_mock = MagicMock()
    os2sync_client = OS2SyncClient(settings=mock_settings, session=session_mock)

    with patch.object(os2sync_client, "os2sync_get_org_unit", return_value=current):
        os2sync_client.upsert_org_unit(org_unit)

    session_mock.post.assert_called_once_with(
        f"{mock_settings.os2sync_api_url}/orgUnit/", json=org_unit.json()
    )


def test_update_orgunit_upsert(mock_settings):
    os2sync_client = OS2SyncClient(settings=mock_settings, session=MagicMock())

    with patch.object(os2sync_client, "upsert_org_unit") as mock_upsert_org_unit:
        os2sync_client.update_org_unit(o.Uuid, o)
        mock_upsert_org_unit.assert_called_with(o)


def test_update_orgunit_delete(mock_settings):
    os2sync_client = OS2SyncClient(settings=mock_settings, session=MagicMock())

    with patch.object(os2sync_client, "delete_orgunit") as mock_delete_orgunit:
        os2sync_client.update_org_unit(o.Uuid, None)
        mock_delete_orgunit.assert_called_with(o.Uuid)


def test_update_users(mock_settings):
    os2sync_client = OS2SyncClient(settings=mock_settings, session=MagicMock())

    with patch.object(os2sync_client, "os2sync_post") as mock_os2sync_post:
        os2sync_client.update_users(uuid, [u1, u2])
        mock_os2sync_post.assert_has_calls(
            [
                call(ANY, json=u1),
                call(ANY, json=u2),
            ]
        )


def test_update_users_one_overwritten_uuid_account(mock_settings):
    os2sync_client = OS2SyncClient(settings=mock_settings, session=MagicMock())

    with patch.object(os2sync_client, "os2sync_delete") as mock_os2sync_delete:
        users = [u1, u2]
        os2sync_client.update_users(user_uuid, users)
        mock_os2sync_delete.assert_not_called()


def test_update_users_deletes_overwritten_uuid_account(mock_settings):
    os2sync_client = OS2SyncClient(settings=mock_settings, session=MagicMock())

    with patch.object(os2sync_client, "os2sync_delete") as mock_os2sync_delete:
        users = [u2]
        os2sync_client.update_users(user_uuid, users)
        mock_os2sync_delete.assert_called_once_with(f"{{BASE}}/user/{user_uuid}")


def test_update_users_no_user(mock_settings):
    os2sync_client = OS2SyncClient(settings=mock_settings, session=MagicMock())

    with patch.object(os2sync_client, "os2sync_delete") as mock_os2sync_delete:
        users = [None]
        os2sync_client.update_users(user_uuid, users)
        mock_os2sync_delete.assert_called_once_with(f"{{BASE}}/user/{user_uuid}")
