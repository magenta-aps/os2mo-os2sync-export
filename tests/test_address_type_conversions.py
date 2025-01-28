# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
import unittest
from uuid import UUID
from uuid import uuid4

import pytest

from os2sync_export.os2mo import addresses_to_orgunit
from os2sync_export.os2mo import pick_address


class _AddressMixin:
    def mock_address_list(self, scope, user_key, value, uuid=str(uuid4())):
        # Mock the result of
        # `os2mo_get("{BASE}/ou/" + uuid + "/details/address").json()`
        # Only contains the keys relevant for `addresses_to_orgunit`
        return [
            {
                "address_type": {
                    "uuid": uuid,
                    "scope": scope,
                    "user_key": user_key,
                },
                "name": value,
                "uuid": uuid4(),
            }
        ]


class TestContactOpenHours(unittest.TestCase, _AddressMixin):
    def test_contact_open_hours(self):
        result = {}
        mo_data = self.mock_address_list(
            "TEXT", "ContactOpenHours", "Man-fre: 11-13.30"
        )
        addresses_to_orgunit(result, mo_data)  # Mutates `result`
        self.assertDictEqual(result, {"ContactOpenHours": "Man-fre: 11-13.30"})


class TestDtrId(unittest.TestCase, _AddressMixin):
    def test_dtr_id(self):
        result = {}
        mo_data = self.mock_address_list("TEXT", "DtrId", "G123456")
        addresses_to_orgunit(result, mo_data)  # Mutates `result`
        self.assertDictEqual(result, {"DtrId": "G123456"})


@pytest.mark.parametrize(
    "addresses,classes,expected",
    [
        ([], [], None),
        # Addresses not in settings
        (
            [{"address_type": {"scope": "PUBLIC", "uuid": str(uuid4())}}],
            [uuid4()],
            None,
        ),
        # One address, is in settings, is chosen.
        (
            [
                {
                    "name": "test",
                    "visibility": {"scope": "PUBLIC"},
                    "address_type": {
                        "uuid": "8b286f2c-ba5d-48f5-bb7c-c2ef8a9e01e3",
                    },
                }
            ],
            [UUID("8b286f2c-ba5d-48f5-bb7c-c2ef8a9e01e3")],
            "test",
        ),
        # two addresses, both in settings, first is chosen.
        (
            [
                {
                    "name": "wrong",
                    "visibility": {"scope": "PUBLIC"},
                    "address_type": {
                        "uuid": "8b286f2c-ba5d-48f5-bb7c-c2ef8a9e01e3",
                    },
                },
                {
                    "name": "right",
                    "visibility": {"scope": "PUBLIC"},
                    "address_type": {
                        "uuid": "9214527f-9e8b-41bd-80c9-90cac7a8e746",
                    },
                },
            ],
            [
                UUID("9214527f-9e8b-41bd-80c9-90cac7a8e746"),
                UUID("8b286f2c-ba5d-48f5-bb7c-c2ef8a9e01e3"),
            ],
            "right",
        ),
        # two addresses, both in settings, first with scope "PUBLIC" is chosen.
        (
            [
                {
                    "name": "SECRET! Do not show!",
                    "visibility": {"scope": "SECRET"},
                    "address_type": {
                        "uuid": "8b286f2c-ba5d-48f5-bb7c-c2ef8a9e01e3",
                    },
                },
                {
                    "name": "right",
                    "visibility": {"scope": "PUBLIC"},
                    "address_type": {
                        "uuid": "9214527f-9e8b-41bd-80c9-90cac7a8e746",
                    },
                },
            ],
            [
                UUID("8b286f2c-ba5d-48f5-bb7c-c2ef8a9e01e3"),
                UUID("9214527f-9e8b-41bd-80c9-90cac7a8e746"),
            ],
            "right",
        ),
    ],
)
def test_pick_address(addresses, classes, expected):
    assert pick_address(addresses, classes) == expected
