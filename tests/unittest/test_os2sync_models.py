# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
import pytest

from os2sync_export.os2sync_models import User
from os2sync_export.os2sync_models import convert_mo_to_fk_user


def test_os2sync_user_model_no_input():
    with pytest.raises(ValueError):
        User()


def test_convert_mo_to_fk_user(os2mo_it_user):
    fk_user = convert_mo_to_fk_user(os2mo_it_user)
    assert fk_user.Person.Name == "Bob"
    assert fk_user.Positions[0].Name == "tester"
