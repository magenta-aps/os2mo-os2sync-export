# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from os2sync_export import __version__


def test_version():
    assert __version__ == "0.1.0"
