# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from uuid import uuid4

import pytest

from os2sync_export.autogenerated_graphql_client.read_user import (
    ReadUserItusersObjectsCurrent,
)
from os2sync_export.autogenerated_graphql_client.read_user import (
    ReadUserItusersObjectsCurrentEmail,
)
from os2sync_export.autogenerated_graphql_client.read_user import (
    ReadUserItusersObjectsCurrentEmailAddressType,
)
from os2sync_export.autogenerated_graphql_client.read_user import (
    ReadUserItusersObjectsCurrentEngagement,
)
from os2sync_export.autogenerated_graphql_client.read_user import (
    ReadUserItusersObjectsCurrentEngagementJobFunction,
)
from os2sync_export.autogenerated_graphql_client.read_user import (
    ReadUserItusersObjectsCurrentEngagementOrgUnit,
)
from os2sync_export.autogenerated_graphql_client.read_user import (
    ReadUserItusersObjectsCurrentPerson,
)
from os2sync_export.autogenerated_graphql_client.read_user import (
    ReadUserItusersObjectsCurrentPhone,
)
from os2sync_export.autogenerated_graphql_client.read_user import (
    ReadUserItusersObjectsCurrentPhoneAddressType,
)
from os2sync_export.os2sync_models import User
from os2sync_export.os2sync_models import convert_mo_to_fk_user

LANDLINE_CLASS_UUID = uuid4()
USER_UUID = uuid4()


def test_os2sync_user_model_no_input():
    with pytest.raises(ValueError):
        User()


mobile_class_uuid = uuid4()
email_class_uuid = uuid4()

landline_class_uuid = LANDLINE_CLASS_UUID


def gen_os2mo_it_user() -> ReadUserItusersObjectsCurrent:
    person = ReadUserItusersObjectsCurrentPerson(
        cpr_number="1234567890", name="Bob", nickname="Bobby"
    )
    engagement = ReadUserItusersObjectsCurrentEngagement(
        org_unit=[ReadUserItusersObjectsCurrentEngagementOrgUnit(uuid=uuid4())],
        job_function=ReadUserItusersObjectsCurrentEngagementJobFunction(name="tester"),
    )
    email = ReadUserItusersObjectsCurrentEmail(
        value="test@example.com",
        address_type=ReadUserItusersObjectsCurrentEmailAddressType(
            scope="Email", uuid=email_class_uuid
        ),
        visibility=None,
    )
    mobile = ReadUserItusersObjectsCurrentPhone(
        value="1234567890",
        address_type=ReadUserItusersObjectsCurrentPhoneAddressType(
            scope="PHONE", uuid=mobile_class_uuid
        ),
        visibility=None,
    )
    landline = ReadUserItusersObjectsCurrentPhone(
        value="+45 0987654321",
        address_type=ReadUserItusersObjectsCurrentPhoneAddressType(
            scope="PHONE", uuid=landline_class_uuid
        ),
        visibility=None,
    )
    return ReadUserItusersObjectsCurrent(
        person=[person],
        user_key="BOB",
        external_id=str(USER_UUID),
        email=[email],
        phone=[mobile, landline],
        engagement=[engagement],
    )


def test_convert_mo_to_fk_user(set_settings):
    os2mo_it_user = gen_os2mo_it_user()
    settings = set_settings(landline_scope_classes=[LANDLINE_CLASS_UUID])
    fk_user = convert_mo_to_fk_user(os2mo_it_user, settings)
    assert fk_user.Uuid == USER_UUID
    assert fk_user.UserId == "BOB"
    assert fk_user.Person.Name == "Bobby"
    assert fk_user.Positions[0].Name == "tester"
    assert fk_user.Email == "test@example.com"
    assert fk_user.Landline == "+45 0987654321"
    assert fk_user.PhoneNumber == "1234567890"
