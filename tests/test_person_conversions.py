# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
import unittest

from more_itertools import one
from parameterized import parameterized
from structlog.testing import capture_logs

from os2sync_export.templates import FieldTemplateRenderError
from os2sync_export.templates import FieldTemplateSyntaxError
from os2sync_export.templates import Person
from tests.helpers import NICKNAME_TEMPLATE
from tests.helpers import MoEmployeeMixin
from tests.helpers import dummy_settings


class TestPerson(unittest.TestCase, MoEmployeeMixin):
    @parameterized.expand(
        [
            # mock CPR, os2sync_xfer_cpr, key of expected CPR value, expected log level
            ("0101013333", True, "cpr_no", "debug"),
            (None, True, "cpr_no", "warning"),
            ("0101013333", False, None, "debug"),
            (None, False, None, "debug"),
        ]
    )
    def test_transfer_cpr(self, cpr, flag, expected_key, expected_log_level):
        mo_employee = self.mock_employee(cpr=cpr)
        settings = dummy_settings
        settings.sync_cpr = flag
        person = Person(mo_employee, settings=settings)
        expected_cpr = mo_employee.get(expected_key)
        with capture_logs() as cap_log:
            self.assertDictEqual(
                person.to_json(),
                {"Name": mo_employee["name"], "Cpr": expected_cpr},
            )
            assert one(cap_log)["log_level"] == expected_log_level


class TestPersonNameTemplate(unittest.TestCase, MoEmployeeMixin):
    @parameterized.expand(
        [
            (
                {"nickname": False},  # mo employee response kwargs
                "name",  # key of expected value for `Name`
            ),
            (
                {"nickname": True},  # mo employee response kwargs
                "nickname",  # key of expected value for `Name`
            ),
        ]
    )
    def test_template(self, response_kwargs, expected_key):
        mo_employee = self.mock_employee(**response_kwargs)
        person = Person(mo_employee, settings=self._gen_settings(NICKNAME_TEMPLATE))
        self.assertEqual(person.to_json()["Name"], mo_employee[expected_key])

    def test_template_syntax_error_raises_exception(self):
        mo_employee = self.mock_employee()
        with self.assertRaises(FieldTemplateSyntaxError):
            Person(mo_employee, settings=self._gen_settings("{% invalid jinja %}"))

    @parameterized.expand(
        [
            "{{ name|dictsort }}",
            "{{ unknown_variable }}",
        ]
    )
    def test_template_render_failure_raises_exception(self, template):
        mo_employee = self.mock_employee()
        person = Person(mo_employee, settings=self._gen_settings(template))
        with self.assertRaises(FieldTemplateRenderError):
            person.to_json()

    def _gen_settings(self, template):
        settings = dummy_settings
        settings.sync_cpr = True
        settings.templates = {"person.name": template}
        return settings
