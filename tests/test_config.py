# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from unittest.mock import patch
from uuid import uuid4

import pytest
from pydantic import ValidationError

from os2sync_export.config import get_os2sync_settings


def test_minimal_settings(set_settings):
    settings = set_settings()
    assert settings


def test_missing_settings():
    with pytest.raises(ValidationError) as excinfo:
        get_os2sync_settings()
    assert "client_secret\n  field required" in str(excinfo.value)
