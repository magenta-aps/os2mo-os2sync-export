# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from uuid import uuid4

import pytest

from os2sync_export.os2sync_models import User
from os2sync_export.os2sync_models import convert_mo_to_fk_user

LANDLINE_CLASS_UUID = uuid4()


def test_os2sync_user_model_no_input():
    with pytest.raises(ValueError):
        User()


def test_convert_mo_to_fk_user(os2mo_it_user, set_settings):
    settings = set_settings(landline_scope_classes=[LANDLINE_CLASS_UUID])
    fk_user = convert_mo_to_fk_user(os2mo_it_user, settings)
    assert fk_user.Person.Name == "Bob"
    assert fk_user.Positions[0].Name == "tester"
    assert fk_user.Email == "test@example.com"
    assert fk_user.Landline == "+45 0987654321"
    assert fk_user.PhoneNumber == "1234567890"
