# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
import logging
from typing import cast
from typing import Literal
from uuid import UUID

from fastramqpi.config import Settings as _FastRAMQPISettings
from fastramqpi.ramqp.config import AMQPConnectionSettings as _AMQPConnectionSettings
from pydantic import AnyHttpUrl
from pydantic import BaseSettings

logger = logging.getLogger(__name__)


# https://git.magenta.dk/rammearkitektur/FastRAMQPI#multilayer-exchanges
class AMQPConnectionSettings(_AMQPConnectionSettings):
    upstream_exchange = "os2mo"
    exchange = "os2sync_export"
    queue_prefix = "os2sync_export"
    prefetch_count = 1


class FastRAMQPISettings(_FastRAMQPISettings):
    amqp: AMQPConnectionSettings


class Settings(BaseSettings):  # type: ignore
    fastramqpi: FastRAMQPISettings
    # common:

    municipality: str  # Called "municipality.cvr" in settings.json

    # os2sync:
    top_unit_uuid: UUID
    os2sync_api_url: AnyHttpUrl | Literal["stub"] = cast(
        AnyHttpUrl, "http://os2sync:5000/api"
    )

    sync_cpr: bool = False

    autowash: bool = False
    ca_verify_os2sync: bool = True
    ca_verify_os2mo: bool = True

    phone_scope_classes: list[UUID] = []
    landline_scope_classes: list[UUID] = []
    email_scope_classes: list[UUID] = []
    ignored_unit_levels: list[UUID] = []
    ignored_unit_types: list[UUID] = []
    templates: dict = {}

    sync_managers: bool = False
    use_contact_for_tasks: bool = False
    employee_engagement_address: list[str] = []
    uuid_from_it_systems: list[str] = []

    truncate_length: int = 200

    user_key_it_system_name: str = "Active Directory"

    filter_hierarchy_names: list[str] = []  # Title in MO
    filter_users_by_it_system: bool = False

    use_extension_field_as_job_function: bool = False

    filter_orgunit_uuid: list[UUID] = []

    enable_kle: bool = True

    class Config:
        frozen = False
        env_nested_delimiter = "__"

        env_file_encoding = "utf-8"


def get_os2sync_settings(*args, **kwargs) -> Settings:
    return Settings(*args, **kwargs)


if __name__ == "__main__":
    print(get_os2sync_settings())
