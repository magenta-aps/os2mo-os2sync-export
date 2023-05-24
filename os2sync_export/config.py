import logging
from typing import cast
from typing import Dict
from typing import List
from typing import Literal
from typing import Tuple
from uuid import UUID

from fastramqpi.config import Settings as FastRAMQPISettings  # type: ignore
from pydantic import AnyHttpUrl
from ra_utils.job_settings import JobSettings
from raclients.graph.client import GraphQLClient

logger = logging.getLogger(__name__)


class Settings(FastRAMQPISettings, JobSettings):

    # common:

    municipality: str  # Called "municipality.cvr" in settings.json

    # os2sync:
    os2sync_top_unit_uuid: UUID
    os2sync_api_url: AnyHttpUrl | Literal["stub"] = cast(
        AnyHttpUrl, "http://localhost:8081/api"
    )

    os2sync_xfer_cpr: bool = False

    os2sync_autowash: bool = False
    os2sync_ca_verify_os2sync: bool = True
    os2sync_ca_verify_os2mo: bool = True

    os2sync_phone_scope_classes: List[UUID] = []
    os2sync_landline_scope_classes: List[UUID] = []
    os2sync_email_scope_classes: List[UUID] = []
    os2sync_ignored_unit_levels: List[UUID] = []
    os2sync_ignored_unit_types: List[UUID] = []
    os2sync_templates: Dict = {}

    os2sync_sync_managers: bool = False
    os2sync_use_contact_for_tasks: bool = False
    os2sync_employee_engagement_address: List[str] = []
    os2sync_uuid_from_it_systems: List[str] = []

    os2sync_truncate_length: int = 200

    os2sync_user_key_it_system_name: str = "Active Directory"

    os2sync_filter_hierarchy_names: Tuple = tuple()  # Title in MO
    os2sync_filter_users_by_it_system: bool = False

    class Config:
        frozen = False
        env_nested_delimiter = "__"

        env_file_encoding = "utf-8"


def get_os2sync_settings(*args, **kwargs) -> Settings:
    return Settings(*args, **kwargs)


def setup_gql_client(settings: Settings) -> GraphQLClient:

    return GraphQLClient(
        url=f"{settings.mo_url}/graphql/v3",
        client_id=settings.client_id,
        client_secret=settings.client_secret,
        auth_realm=settings.auth_realm,
        auth_server=settings.auth_server,
        httpx_client_kwargs={"timeout": None},
    )


if __name__ == "__main__":
    print(get_os2sync_settings())
