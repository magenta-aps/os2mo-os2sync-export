# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
import pytest
from pydantic import ValidationError

from os2sync_export.config import get_os2sync_settings


def test_minimal_settings(set_settings):
    settings = set_settings()
    assert settings


def test_missing_settings():
    with pytest.raises(ValidationError, match=r".*field required.*"):
        get_os2sync_settings()
