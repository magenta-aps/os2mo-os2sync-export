# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from uuid import uuid4

from os2sync_export.config import get_os2sync_settings


# Create dummy settings ignoring any settings.json file.
# with patch("os2sync_export.config.load_settings", return_value={}):
dummy_settings = get_os2sync_settings(
    amqp={"url": "amqp://guest:guest@msg_broker"},
    municipality="1234",
    os2sync_top_unit_uuid="269a0339-0c8b-472d-9514-aef952a2b4df",
    client_id="os2sync_exporter",
    client_secret="94923cbb-ca38-4c82-96ca-b96957b6be4e",
)

NICKNAME_TEMPLATE = "{% if nickname -%}{{ nickname }}{%- else %}{{ name }}{%- endif %}"


class MockOs2moGet:
    """Class which allows patching to have a json() method"""

    def __init__(self, return_value):
        self.return_value = return_value

    def json(self):
        return self.return_value


class MoEmployeeMixin:
    def mock_employee(self, cpr="0101012222", nickname=False):
        # Mock the result of `os2mo_get("{BASE}/e/" + uuid + "/").json()`
        # Only contains the keys relevant for testing
        return {
            # Name
            "name": "Test Testesen",
            "givenname": "Test",
            "surname": "Testesen",
            # Nickname
            "nickname": "Kalde Navn" if nickname else "",
            "nickname_givenname": "Kalde" if nickname else "",
            "nickname_surname": "Navn" if nickname else "",
            # Other fields
            "cpr_no": cpr,
            "user_key": "testtestesen",
            "uuid": "mock-uuid",
        }

    def mock_employee_response(self, **kwargs):
        mo_employee = self.mock_employee(**kwargs)

        class MockResponse:
            def json(self):
                return mo_employee

        return MockResponse()


dummy_positions = [{"org_unit": {"uuid": uuid4()}}]


async def mock_engagements_to_user(user, *args, **kwargs):
    user["Positions"] = dummy_positions
