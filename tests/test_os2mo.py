# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
import unittest
from unittest.mock import ANY
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch
from uuid import UUID
from uuid import uuid4

import pytest
from freezegun import freeze_time
from hypothesis import given
from hypothesis import strategies as st
from parameterized import parameterized
from pydantic import ValidationError

from os2sync_export.os2mo import check_terminated_accounts
from os2sync_export.os2mo import get_address_org_unit_and_employee_uuids
from os2sync_export.os2mo import get_engagement_employee_uuid
from os2sync_export.os2mo import get_ituser_org_unit_and_employee_uuids
from os2sync_export.os2mo import get_kle_org_unit_uuid
from os2sync_export.os2mo import get_manager_org_unit_uuid
from os2sync_export.os2mo import get_org_unit_hierarchy
from os2sync_export.os2mo import get_work_address
from os2sync_export.os2mo import is_ignored
from os2sync_export.os2mo import is_terminated
from os2sync_export.os2mo import kle_to_orgunit
from os2sync_export.os2mo import manager_to_orgunit
from os2sync_export.os2mo import org_unit_uuids
from os2sync_export.os2mo import overwrite_position_uuids
from os2sync_export.os2mo import overwrite_unit_uuids
from os2sync_export.os2mo import partition_kle
from os2sync_export.os2sync_models import OrgUnit
from tests.helpers import dummy_settings
from tests.helpers import MockOs2moGet


class TestsMOAd(unittest.TestCase):
    def test_is_ignored(self):
        settings = dummy_settings
        il1, il2, iu1, iu2 = [uuid4() for u in range(4)]
        settings.os2sync_ignored_unit_levels = [il1, il2]
        settings.os2sync_ignored_unit_types = [iu1, iu2]
        unit = {
            "org_unit_level": {"uuid": str(uuid4())},
            "org_unit_type": {"uuid": str(uuid4())},
        }
        self.assertFalse(is_ignored(unit, settings))
        unit = {
            "org_unit_level": {"uuid": str(uuid4())},
            "org_unit_type": {"uuid": str(iu2)},
        }
        self.assertTrue(is_ignored(unit, settings))
        unit = {
            "org_unit_level": {"uuid": str(il1)},
            "org_unit_type": {"uuid": str(uuid4())},
        }
        self.assertTrue(is_ignored(unit, settings))

    @parameterized.expand(
        [
            ({"os2mo_has_kle": True}, ["2", "4", "6"], []),
            (
                {"os2mo_has_kle": True, "os2sync_use_contact_for_tasks": True},
                ["2", "4"],
                ["6"],
            ),
        ]
    )
    def test_kle_to_orgunit(
        self, testsettings, expected_tasks, expected_contactfortasks
    ):
        kles = [
            {
                "uuid": 1,
                "kle_aspect": [{"name": "Udførende"}],
                "kle_number": {"uuid": "2"},
            },
            {
                "uuid": 3,
                "kle_aspect": [{"name": "Udførende"}],
                "kle_number": {"uuid": "4"},
            },
            {
                "uuid": 5,
                "kle_aspect": [{"name": "Ansvarlig"}],
                "kle_number": {"uuid": "6"},
            },
        ]
        settings = dummy_settings
        settings.os2sync_use_contact_for_tasks = (
            True if testsettings.get("os2sync_use_contact_for_tasks") else False
        )

        tasks, contact_for_tasks = partition_kle(
            kles, settings.os2sync_use_contact_for_tasks
        )
        self.assertListEqual(expected_tasks, tasks)
        self.assertListEqual(expected_contactfortasks, contact_for_tasks)
        org_unit = {}
        kle_to_orgunit(
            org_unit, kles, use_contact_for_tasks=settings.os2sync_use_contact_for_tasks
        )
        self.assertListEqual(expected_tasks, org_unit.get("Tasks"))
        self.assertListEqual(
            expected_contactfortasks, org_unit.get("ContactForTasks", [])
        )

    @parameterized.expand(
        [
            (["Henvendelsessted", "Adresse"], "Henvendelsesstednavn"),
            (["Adresse", "Henvendelsessted"], "Adressenavn"),
            ([], None),
        ]
    )
    def test_get_work_address(self, work_address_names, expected):
        addresses = [
            {
                "name": "Henvendelsesstednavn",
                "address_type": {"name": "Henvendelsessted"},
            },
            {"name": "Adressenavn", "address_type": {"name": "Adresse"}},
            {"name": "Adressenavn2", "address_type": {"name": "Adresse"}},
        ]
        positions = [{"is_primary": True, "OrgUnitUuid": "Some_unit_uuid"}]
        with patch(
            "os2sync_export.os2mo.os2mo_get", return_value=MockOs2moGet(addresses)
        ):
            work_address = get_work_address(positions, work_address_names)
            self.assertEqual(work_address, expected)

    @parameterized.expand(
        [
            # No (relevant) it systems - no change
            ([], [], {"Uuid": "old_uuid", "ParentOrgUnitUuid": "old_parent_uuid"}),
            (
                [{"itsystem": {"name": "irrelevant it system"}, "user_key": "dummy"}],
                [{"itsystem": {"name": "irrelevant it system"}, "user_key": "dummy"}],
                {"Uuid": "old_uuid", "ParentOrgUnitUuid": "old_parent_uuid"},
            ),
            # Overwrite both uuid and parent uuid
            (
                [{"itsystem": {"name": "FK-org uuid"}, "user_key": "fk-unit_uuid"}],
                [{"itsystem": {"name": "FK-org uuid"}, "user_key": "parent_uuid"}],
                {"Uuid": "fk-unit_uuid", "ParentOrgUnitUuid": "parent_uuid"},
            ),
            (
                [{"itsystem": {"name": "AD ObjectGUID"}, "user_key": "fk-unit_uuid"}],
                [{"itsystem": {"name": "AD ObjectGUID"}, "user_key": "parent_uuid"}],
                {"Uuid": "fk-unit_uuid", "ParentOrgUnitUuid": "parent_uuid"},
            ),
            # Two it-systems - use first from the given list (fk-org first, AD second)
            (
                [
                    {"itsystem": {"name": "FK-org uuid"}, "user_key": "right_uuid"},
                    {"itsystem": {"name": "AD ObjectGUID"}, "user_key": "wrong_uuid"},
                ],
                [],
                {"Uuid": "right_uuid", "ParentOrgUnitUuid": "old_parent_uuid"},
            ),
            (
                [],
                [
                    {
                        "itsystem": {"name": "FK-org uuid"},
                        "user_key": "right_parent_uuid",
                    },
                    {
                        "itsystem": {"name": "AD ObjectGUID"},
                        "user_key": "wrong_parent_uuid",
                    },
                ],
                {"Uuid": "old_uuid", "ParentOrgUnitUuid": "right_parent_uuid"},
            ),
        ]
    )
    def test_overwrite_unit_uuids(self, it_system, parent_it_system, expected):
        test_org = {"Uuid": "old_uuid", "ParentOrgUnitUuid": "old_parent_uuid"}
        with patch(
            "os2sync_export.os2mo.os2mo_get",
            side_effect=[MockOs2moGet(it_system), MockOs2moGet(parent_it_system)],
        ):
            overwrite_unit_uuids(test_org, ["FK-org uuid", "AD ObjectGUID"])
        assert test_org == expected

    @parameterized.expand(
        [
            # No (relevant) it systems - no change
            (
                [],
                {"Uuid": "old_uuid", "Positions": [{"OrgUnitUuid": "mo_unit_uuid"}]},
            ),
            # Person has a position in a unit with a mapped uuid:
            (
                [
                    {
                        "itsystem": {"name": "AD ObjectGUID"},
                        "user_key": "new_uuid",
                    },
                ],
                {"Uuid": "old_uuid", "Positions": [{"OrgUnitUuid": "new_uuid"}]},
            ),
        ]
    )
    def test_overwrite_position_uuids(self, position_it_systems, expected):
        test_user = {
            "Uuid": "old_uuid",
            "Positions": [{"OrgUnitUuid": "mo_unit_uuid"}],
        }
        with patch(
            "os2sync_export.os2mo.os2mo_get",
            side_effect=[MockOs2moGet(position_it_systems)],
        ):
            overwrite_position_uuids(test_user, ["FK-org uuid", "AD ObjectGUID"])
        assert test_user == expected


@patch("os2sync_export.os2mo.organization_uuid", return_value="root_uuid")
@given(st.tuples(st.uuids()))
def test_org_unit_uuids(root_mock, hierarchy_uuids):
    session_mock = MagicMock()
    with patch("os2sync_export.os2mo.os2mo_get") as session_mock:
        session_mock.return_value = MockOs2moGet({"items": [{"uuid": "test"}]})
        org_unit_uuids(hierarchy_uuids=hierarchy_uuids)

    session_mock.assert_called_once_with(
        "{BASE}/o/root_uuid/ou/",
        limit=999999,
        hierarchy_uuids=tuple(str(u) for u in hierarchy_uuids),
    )


@patch("os2sync_export.os2mo.organization_uuid", return_value="root_uuid")
def test_get_org_unit_hierarchy(root_mock):
    with patch(
        "os2sync_export.os2mo.os2mo_get",
        return_value=MockOs2moGet(
            {
                "uuid": "403eb28f-e21e-bdd6-3612-33771b098a12",
                "user_key": "org_unit_hierarchy",
                "description": "",
                "data": {
                    "total": 2,
                    "offset": 0,
                    "items": [
                        {
                            "uuid": "8c30ab5a-8c3a-566c-bf12-790bdd7a9fef",
                            "name": "Skjult organisation",
                            "user_key": "hide",
                            "example": None,
                            "scope": "TEXT",
                            "owner": None,
                        },
                        {
                            "uuid": "f805eb80-fdfe-8f24-9367-68ea955b9b9b",
                            "name": "Linjeorganisation",
                            "user_key": "linjeorg",
                            "example": None,
                            "scope": "TEXT",
                            "owner": None,
                        },
                    ],
                },
                "path": "/o/3b866d97-0b1f-48e0-8078-686d96f430b3/f/org_unit_hierarchy/",
            }
        ),
    ):
        hierarchy_uuids = get_org_unit_hierarchy("Linjeorganisation")
    assert hierarchy_uuids == (UUID("f805eb80-fdfe-8f24-9367-68ea955b9b9b"),)


def test_manager_to_orgunit():
    manager_uuid = uuid4()
    person = {"uuid": manager_uuid}
    with patch("os2sync_export.os2mo.os2mo_get") as session_mock:
        session_mock.return_value = MockOs2moGet([{"person": person}])
        manager_uuid = manager_to_orgunit("org_unit_uuid")
    assert manager_uuid == manager_uuid


def test_manager_to_orgunit_no_manager():
    with patch("os2sync_export.os2mo.os2mo_get") as session_mock:
        session_mock.return_value = MockOs2moGet([])
        manager_uuid = manager_to_orgunit("org_unit_uuid")
    assert manager_uuid is None


def test_manager_to_orgunit_vacant():
    person = None
    with patch("os2sync_export.os2mo.os2mo_get") as session_mock:
        session_mock.return_value = MockOs2moGet([{"person": person}])
        manager_uuid = manager_to_orgunit("org_unit_uuid")
    assert manager_uuid is None


def test_manager_to_orgunit_multiple_managers():
    with patch("os2sync_export.os2mo.os2mo_get") as session_mock:
        person_uuids = [uuid4(), uuid4()]
        managers = [{"person": {"uuid": uuid}} for uuid in person_uuids]
        session_mock.return_value = MockOs2moGet(managers)
        manager_uuid = manager_to_orgunit("org_unit_uuid")
    assert manager_uuid in person_uuids


def test_orgunit_model():
    sts_org_unit = {"Uuid": uuid4(), "Name": "Test", "ParentOrgUnitUuid": uuid4()}
    assert OrgUnit(**sts_org_unit)


def test_orgunit_model_invalid_key():
    sts_org_unit = {
        "Uuid": uuid4(),
        "Name": "Test",
        "ParentOrgUnitUuid": uuid4(),
        "managerUuid": uuid4(),
    }
    with pytest.raises(ValidationError):
        OrgUnit(**sts_org_unit)


async def test_get_address_org_unit_and_employee_uuids():
    addr_uuid_mock = uuid4()
    ou_uuid_mock = uuid4()
    e_uuid_mock = uuid4()

    graphql_session_mock = AsyncMock()
    graphql_session_mock.execute.return_value = {
        "addresses": [
            {
                "objects": [
                    {
                        "org_unit_uuid": str(ou_uuid_mock),
                        "employee_uuid": str(e_uuid_mock),
                    },
                    {
                        "org_unit_uuid": str(ou_uuid_mock),
                        "employee_uuid": str(e_uuid_mock),
                    },
                ]
            }
        ]
    }

    result_ou_uuid, result_e_uuid = await get_address_org_unit_and_employee_uuids(
        graphql_session_mock, addr_uuid_mock
    )

    graphql_session_mock.execute.assert_called_with(
        ANY,
        variable_values={
            "uuids": str(addr_uuid_mock),
        },
    )
    assert UUID(result_ou_uuid) == ou_uuid_mock
    assert UUID(result_e_uuid) == e_uuid_mock


async def test_get_ituser_org_unit_and_employee_uuids():
    ituser_uuid_mock = uuid4()
    ou_uuid_mock = uuid4()
    e_uuid_mock = uuid4()

    graphql_session_mock = MagicMock()
    graphql_session_mock.execute = AsyncMock(
        return_value={
            "itusers": [
                {
                    "objects": [
                        {
                            "org_unit_uuid": str(ou_uuid_mock),
                            "employee_uuid": str(e_uuid_mock),
                        },
                        {
                            "org_unit_uuid": str(ou_uuid_mock),
                            "employee_uuid": str(e_uuid_mock),
                        },
                    ]
                }
            ]
        }
    )

    result_ou_uuid, result_e_uuid = await get_ituser_org_unit_and_employee_uuids(
        graphql_session_mock, ituser_uuid_mock
    )

    graphql_session_mock.execute.assert_called_with(
        ANY,
        variable_values={
            "uuids": str(ituser_uuid_mock),
        },
    )
    assert UUID(result_ou_uuid) == ou_uuid_mock
    assert UUID(result_e_uuid) == e_uuid_mock


async def test_get_manager_org_unit_uuid():
    manager_uuid_mock = uuid4()
    ou_uuid_mock = uuid4()

    graphql_session_mock = AsyncMock()
    graphql_session_mock.execute.return_value = {
        "managers": [
            {
                "objects": [
                    {
                        "org_unit_uuid": str(ou_uuid_mock),
                    },
                    {
                        "org_unit_uuid": str(ou_uuid_mock),
                    },
                ]
            }
        ]
    }

    result_ou_uuid = await get_manager_org_unit_uuid(
        graphql_session_mock, manager_uuid_mock
    )

    graphql_session_mock.execute.assert_called_with(
        ANY,
        variable_values={
            "uuids": str(manager_uuid_mock),
        },
    )
    assert UUID(result_ou_uuid) == ou_uuid_mock


async def test_get_manager_org_unit_uuid_not_found():
    manager_uuid_mock = uuid4()
    graphql_session_mock = AsyncMock()
    graphql_session_mock.execute.return_value = {"managers": []}

    with pytest.raises(ValueError):
        _ = await get_manager_org_unit_uuid(graphql_session_mock, manager_uuid_mock)

        graphql_session_mock.execute.assert_called_with(
            ANY,
            variable_values={
                "uuids": str(manager_uuid_mock),
            },
        )


async def test_get_engagement_employee_uuid():
    engagement_uuid_mock = uuid4()
    e_uuid_mock = uuid4()

    graphql_session_mock = MagicMock()
    graphql_session_mock.execute = AsyncMock(
        return_value={
            "engagements": [
                {
                    "objects": [
                        {
                            "employee_uuid": str(e_uuid_mock),
                        },
                        {
                            "employee_uuid": str(e_uuid_mock),
                        },
                    ]
                }
            ]
        }
    )

    result_e_uuid = await get_engagement_employee_uuid(
        graphql_session_mock, engagement_uuid_mock
    )

    graphql_session_mock.execute.assert_called_with(
        ANY,
        variable_values={
            "uuids": str(engagement_uuid_mock),
        },
    )
    assert UUID(result_e_uuid) == e_uuid_mock


async def test_get_kle_org_unit_uuid():
    kle_uuid_mock = uuid4()
    ou_uuid_mock = uuid4()

    graphql_session_mock = MagicMock()
    graphql_session_mock.execute = AsyncMock(
        return_value={
            "kles": [
                {
                    "objects": [
                        {
                            "org_unit_uuid": str(ou_uuid_mock),
                        },
                        {
                            "org_unit_uuid": str(ou_uuid_mock),
                        },
                    ]
                }
            ]
        }
    )

    result_ou_uuid = await get_kle_org_unit_uuid(graphql_session_mock, kle_uuid_mock)

    graphql_session_mock.execute.assert_called_with(
        ANY,
        variable_values={
            "uuids": str(kle_uuid_mock),
        },
    )
    assert UUID(result_ou_uuid) == ou_uuid_mock


@freeze_time("2024-05-17T00:00:00+02:00")
def test_is_terminated():
    # Still active
    assert not is_terminated(None)
    # Still active but terminated from next day
    assert not is_terminated("2024-05-18T00:00:00+02:00")
    # Terminated days before
    assert is_terminated("2024-05-01T00:00:00+02:00")
    # Terminated one hour ago in another timezone
    assert is_terminated("2024-05-17T00:00:00+03:00")
    # Terminated right now
    assert is_terminated("2024-05-17T00:00:00+02:00")


@freeze_time("2024-05-17T00:00:00+02:00")
async def test_check_terminated_it_user():
    fk_org_uuid = uuid4()
    graphql_session_mock = MagicMock()
    graphql_session_mock.execute = AsyncMock(
        return_value={
            "itusers": [
                {
                    "objects": [
                        {
                            "uuid": "b49d1206-6721-4e9f-a44a-4b8d3e726ce5",
                            "user_key": "New Active fk-org uuid",
                            "engagement_uuid": "830cee7d-d7ec-4d09-9ed4-edb2fd741e9b",
                            "itsystem": {"name": "Omada - AD GUID"},
                            "validity": {"to": None},
                            "employee_uuid": "a719ee4c-811c-45e5-b077-7fb7117b9d4a",
                            "org_unit_uuid": None,
                        },
                        {
                            "uuid": "b49d1206-6721-4e9f-a44a-4b8d3e726ce5",
                            "user_key": str(fk_org_uuid),
                            "engagement_uuid": "830cee7d-d7ec-4d09-9ed4-edb2fd741e9b",
                            "itsystem": {"name": "Omada - AD GUID"},
                            "validity": {"to": "2024-05-01T00:00:00+02:00"},
                            "employee_uuid": "a719ee4c-811c-45e5-b077-7fb7117b9d4a",
                            "org_unit_uuid": None,
                        },
                    ]
                },
            ]
        }
    )
    os2sync_uuid_from_it_systems = ["Omada - AD GUID"]
    deleted_users, deleted_org_units = await check_terminated_accounts(
        graphql_session=graphql_session_mock,
        uuid=uuid4(),
        os2sync_uuid_from_it_systems=os2sync_uuid_from_it_systems,
    )
    assert deleted_users == {fk_org_uuid}
    assert deleted_org_units == set()


@freeze_time("2024-05-17T00:00:00+02:00")
async def test_check_terminated_it_user_org_unit():
    fk_org_uuid = uuid4()
    graphql_session_mock = MagicMock()
    graphql_session_mock.execute = AsyncMock(
        return_value={
            "itusers": [
                {
                    "objects": [
                        {
                            "uuid": "b49d1206-6721-4e9f-a44a-4b8d3e726ce5",
                            "user_key": "New Active fk-org uuid",
                            "engagement_uuid": "830cee7d-d7ec-4d09-9ed4-edb2fd741e9b",
                            "itsystem": {"name": "FK-org UUID"},
                            "validity": {"to": None},
                            "employee_uuid": None,
                            "org_unit_uuid": "a719ee4c-811c-45e5-b077-7fb7117b9d4a",
                        },
                        {
                            "uuid": "b49d1206-6721-4e9f-a44a-4b8d3e726ce5",
                            "user_key": str(fk_org_uuid),
                            "engagement_uuid": "830cee7d-d7ec-4d09-9ed4-edb2fd741e9b",
                            "itsystem": {"name": "FK-org UUID"},
                            "validity": {"to": "2024-05-01T00:00:00+02:00"},
                            "employee_uuid": None,
                            "org_unit_uuid": "a719ee4c-811c-45e5-b077-7fb7117b9d4a",
                        },
                    ]
                },
            ]
        }
    )
    os2sync_uuid_from_it_systems = ["Omada - AD GUID", "FK-org UUID"]
    deleted_users, deleted_org_units = await check_terminated_accounts(
        graphql_session=graphql_session_mock,
        uuid=uuid4(),
        os2sync_uuid_from_it_systems=os2sync_uuid_from_it_systems,
    )
    assert deleted_users == set()
    assert deleted_org_units == {fk_org_uuid}


@freeze_time("2024-05-17T00:00:00+02:00")
async def test_check_terminated_it_user_still_active():
    """What if an it-user was edited in some way which gave the old registration an end date?
    Could there still be an active acount then?
    Lets make sure we won't delete fk-org accounts that are still active"""
    fk_org_uuid = uuid4()
    graphql_session_mock = MagicMock()
    graphql_session_mock.execute = AsyncMock(
        return_value={
            "itusers": [
                {
                    "objects": [
                        {
                            "uuid": "b49d1206-6721-4e9f-a44a-4b8d3e726ce5",
                            "user_key": str(fk_org_uuid),
                            "engagement_uuid": "830cee7d-d7ec-4d09-9ed4-edb2fd741e9b",
                            "itsystem": {"name": "Omada - AD GUID"},
                            "validity": {"to": None},
                            "employee_uuid": "a719ee4c-811c-45e5-b077-7fb7117b9d4a",
                            "org_unit_uuid": None,
                        },
                        {
                            "uuid": "b49d1206-6721-4e9f-a44a-4b8d3e726ce5",
                            "user_key": str(fk_org_uuid),
                            "engagement_uuid": None,
                            "itsystem": {"name": "Omada - AD GUID"},
                            "validity": {"to": "2024-05-01T00:00:00+02:00"},
                            "employee_uuid": "a719ee4c-811c-45e5-b077-7fb7117b9d4a",
                            "org_unit_uuid": None,
                        },
                    ]
                },
            ]
        }
    )
    os2sync_uuid_from_it_systems = ["Omada - AD GUID"]
    deleted_users, deleted_org_units = await check_terminated_accounts(
        graphql_session=graphql_session_mock,
        uuid=uuid4(),
        os2sync_uuid_from_it_systems=os2sync_uuid_from_it_systems,
    )
    assert deleted_users == set()
    assert deleted_org_units == set()
