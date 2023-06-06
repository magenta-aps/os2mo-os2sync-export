# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
import logging
from operator import itemgetter
from typing import Dict
from typing import Set
from uuid import UUID

from gql.client import AsyncClientSession
from more_itertools import flatten
from ra_utils.asyncio_utils import gather_with_concurrency
from ra_utils.tqdm_wrapper import tqdm
from tenacity import retry
from tenacity import retry_if_exception_type
from tenacity import stop_after_attempt

from os2sync_export import os2mo
from os2sync_export import os2sync
from os2sync_export.config import Settings
from os2sync_export.os2sync_models import OrgUnit

logger = logging.getLogger(__name__)


def log_mox_config(settings):
    """It is imperative for log-forensics to have as
    much configuration as possible logged at program start
    and end.
    """

    logger.warning("-----------------------------------------")
    logger.warning("program configuration:")
    for k, v in settings:
        logger.warning("    %s=%r", k, v)


def read_all_org_units(settings) -> Dict[UUID, OrgUnit]:
    """Read all current org_units from OS2MO

    Returns a dict mapping uuids to os2sync payload for each org_unit
    """
    logger.info("read_all_org_units starting")
    # Read all relevant org_unit uuids from os2mo
    os2mo_uuids_present = os2mo.org_unit_uuids(
        root=settings.os2sync_top_unit_uuid,
        hierarchy_uuids=os2mo.get_org_unit_hierarchy(
            settings.os2sync_filter_hierarchy_names
        ),
    )

    logger.info(f"Aktive Orgenheder fundet i OS2MO {len(os2mo_uuids_present)}")

    os2mo_uuids_present = tqdm(
        os2mo_uuids_present, desc="Reading org_units from OS2MO", unit="org_unit"
    )

    # Create os2sync payload for all org_units:
    org_units = (
        os2mo.get_sts_orgunit(i, settings=settings) for i in os2mo_uuids_present
    )
    # TODO: Check that only one org_unit has parent=None

    return {ou.Uuid: ou for ou in org_units if ou}


def read_all_user_uuids(org_uuid: str, limit: int = 1_000) -> Set[str]:
    """Return a set of all employee uuids in MO.

    :param limit: Size of pagination groups. Set to 0 to skip pagination and fetch all users in one request.
    :return: set of uuids of all employees.
    """

    start = 0
    total = 1
    all_employee_uuids = set()
    while start < total:
        employee_list = os2mo.os2mo_get(
            f"{{BASE}}/o/{org_uuid}/e/?limit={limit}&start={start}"
        ).json()

        batch = set(map(itemgetter("uuid"), employee_list["items"]))
        all_employee_uuids.update(batch)
        start = employee_list["offset"] + limit
        total = employee_list["total"]
    return all_employee_uuids


async def read_all_users(
    gql_session: AsyncClientSession, settings: Settings
) -> Dict[UUID, Dict]:
    """Read all current users from OS2MO

    Returns a dict mapping uuids to os2sync payload for each user
    """

    logger.info("read_all_users starting")

    org_uuid = os2mo.organization_uuid()

    logger.info("read_all_users getting list of users from os2mo")
    os2mo_uuids_present = read_all_user_uuids(org_uuid)

    logger.info(f"Medarbejdere fundet i OS2Mo: {len(os2mo_uuids_present)}")

    os2mo_uuids_present = tqdm(
        os2mo_uuids_present, desc="Reading users from OS2MO", unit="user"
    )

    tasks = [
        os2mo.get_sts_user(uuid, gql_session=gql_session, settings=settings)
        for uuid in os2mo_uuids_present
    ]
    all_users = await gather_with_concurrency(5, *tasks)
    res: Dict[UUID, Dict] = {}
    for u in flatten(all_users):
        if u is None:
            continue
        user_uuid = UUID(u["Uuid"])  # type: ignore
        if res.get(user_uuid):
            # This might happen if more than one user has the same uuid in an it-account
            # or one has the same uuid in an it-account as another user without any it-accounts' MO uuid
            logger.error(f"Duplicated uuid: {user_uuid}")
        else:
            res[user_uuid] = u

    return res


# Retry in case the connection to fk-org is down
@retry(
    reraise=True,
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(ConnectionError),
)
async def main(settings: Settings, gql_session):
    log_mox_config(settings)

    os2sync_client = os2sync.get_os2sync_session()
    request_uuid = os2sync.trigger_hierarchy(
        os2sync_client, os2sync_api_url=settings.os2sync_api_url
    )
    mo_org_units = read_all_org_units(settings)

    logger.info(f"Orgenheder som tjekkes i OS2Sync: {len(mo_org_units)}")

    for org_unit in tqdm(
        mo_org_units.values(), desc="Updating OrgUnits in fk-org", unit="OrgUnit"
    ):
        os2sync.upsert_org_unit(org_unit, settings.os2sync_api_url)

    existing_os2sync_org_units, existing_os2sync_users = os2sync.get_hierarchy(
        os2sync_client,
        os2sync_api_url=settings.os2sync_api_url,
        request_uuid=request_uuid,
    )

    if settings.os2sync_autowash:
        # Delete any org_unit not in os2mo
        assert (
            mo_org_units
        ), "No org_units were found in os2mo. Stopping os2sync_export to ensure we won't delete every org_unit from fk-org"
        terminated_org_units = existing_os2sync_org_units - set(mo_org_units)
        logger.info(f"Orgenheder som slettes i OS2Sync: {len(terminated_org_units)}")
        for uuid in terminated_org_units:
            os2sync.delete_orgunit(uuid)

    logger.info("sync_os2sync_orgunits done")

    logger.info("Start syncing users")
    mo_users = await read_all_users(
        gql_session=gql_session,
        settings=settings,
    )
    assert (
        mo_users
    ), "No mo-users were found. Stopping os2sync_export to ensure we won't delete every user from fk-org. Again"
    # Create or update users
    logger.info(f"Medarbejdere overført til OS2SYNC: {len(mo_users)}")
    for user in mo_users.values():
        os2sync.os2sync_post("{BASE}/user", json=user)

    # Delete any user not in os2mo
    terminated_users = existing_os2sync_users - set(mo_users)
    logger.info(f"Medarbejdere slettes i OS2Sync: {len(terminated_users)}")
    for uuid in terminated_users:
        os2sync.os2sync_delete("{BASE}/user/" + uuid)

    logger.info("sync users done")
