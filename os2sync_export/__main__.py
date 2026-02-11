# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
import asyncio
from operator import itemgetter
from typing import Dict
from typing import Set
from uuid import UUID

import structlog
from fastramqpi.ra_utils.asyncio_utils import gather_with_concurrency
from fastramqpi.ra_utils.tqdm_wrapper import tqdm
from gql.client import AsyncClientSession
from more_itertools import all_unique
from more_itertools import flatten

from os2sync_export import os2mo
from os2sync_export.config import Settings
from os2sync_export.os2sync import OS2SyncClient
from os2sync_export.os2sync_models import OrgUnit

logger = structlog.stdlib.get_logger()


def log_mox_config(settings):
    """It is imperative for log-forensics to have as
    much configuration as possible logged at program start
    and end.
    """

    logger.warning("-----------------------------------------")
    logger.warning("program configuration:")
    for k, v in settings:
        logger.warning("    %s=%r", k, v)


async def read_all_org_units(
    settings: Settings, graphql_session: AsyncClientSession
) -> Dict[UUID, OrgUnit]:
    """Read all current org_units from OS2MO

    Returns a dict mapping uuids to os2sync payload for each org_unit
    """
    logger.info("read_all_org_units starting")
    # Read all relevant org_unit uuids from os2mo
    os2mo_uuids_present = await os2mo.org_unit_uuids(
        root=settings.top_unit_uuid,
        hierarchy_uuids=await os2mo.get_org_unit_hierarchy(
            settings.filter_hierarchy_names
        ),
    )

    logger.info(f"Aktive Orgenheder fundet i OS2MO {len(os2mo_uuids_present)}")

    # Create os2sync payload for all org_units:
    org_units = await asyncio.gather(
        *[
            os2mo.get_sts_orgunit(
                UUID(i), settings=settings, graphql_session=graphql_session
            )
            for i in os2mo_uuids_present
        ]
    )
    # TODO: Check that only one org_unit has parent=None

    return {ou.Uuid: ou for ou in org_units if ou}


async def read_all_user_uuids(org_uuid: str, limit: int = 1_000) -> Set[str]:
    """Return a set of all employee uuids in MO.

    :param limit: Size of pagination groups. Set to 0 to skip pagination and fetch all users in one request.
    :return: set of uuids of all employees.
    """

    start = 0
    total = 1
    all_employee_uuids = set()
    while start < total:
        res = await os2mo.os2mo_get(
            f"{{BASE}}/o/{org_uuid}/e/?limit={limit}&start={start}"
        )
        employee_list = res.json()

        batch = set(map(itemgetter("uuid"), employee_list["items"]))
        all_employee_uuids.update(batch)
        start = employee_list["offset"] + limit
        total = employee_list["total"]
    return all_employee_uuids


async def read_all_users(
    graphql_session: AsyncClientSession, settings: Settings
) -> Dict[UUID, Dict]:
    """Read all current users from OS2MO

    Returns a dict mapping uuids to os2sync payload for each user
    """

    logger.info("read_all_users starting")

    org_uuid = await os2mo.organization_uuid()

    logger.info("read_all_users getting list of users from os2mo")
    os2mo_uuids_present = await read_all_user_uuids(org_uuid)

    logger.info(f"Medarbejdere fundet i OS2Mo: {len(os2mo_uuids_present)}")

    tasks = [
        os2mo.get_sts_user(uuid, graphql_session=graphql_session, settings=settings)
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


async def main(settings: Settings, graphql_session, os2sync_client):
    log_mox_config(settings)

    os2sync_client = os2sync_client or OS2SyncClient(settings=settings)
    request_uuid = await os2sync_client.trigger_hierarchy()
    mo_org_units = await read_all_org_units(settings, graphql_session)

    logger.info(f"Orgenheder som tjekkes i OS2Sync: {len(mo_org_units)}")

    for org_unit in tqdm(
        mo_org_units.values(), desc="Updating OrgUnits in fk-org", unit="OrgUnit"
    ):
        await os2sync_client.upsert_org_unit(org_unit)

    (
        existing_os2sync_org_units,
        existing_os2sync_users,
    ) = await os2sync_client.get_existing_uuids(
        request_uuid=request_uuid,
    )

    if settings.autowash:
        # Delete any org_unit not in os2mo
        assert mo_org_units, "No org_units were found in os2mo. Stopping os2sync_export to ensure we won't delete every org_unit from fk-org"
        terminated_org_units = existing_os2sync_org_units - set(mo_org_units)
        logger.info(f"Orgenheder som slettes i OS2Sync: {len(terminated_org_units)}")
        for uuid in terminated_org_units:
            await os2sync_client.delete_orgunit(uuid)

    logger.info("sync_os2sync_orgunits done")

    logger.info("Start syncing users")
    mo_users = await read_all_users(
        graphql_session=graphql_session,
        settings=settings,
    )
    assert mo_users, "No mo-users were found. Stopping os2sync_export to ensure we won't delete every user from fk-org. Again"
    # Create or update users
    logger.info(f"Medarbejdere overført til OS2SYNC: {len(mo_users)}")
    for user in mo_users.values():
        await os2sync_client.os2sync_post("{BASE}/user", json=user)

    # Delete any user not in os2mo
    terminated_users = existing_os2sync_users - set(mo_users)
    logger.info(f"Medarbejdere slettes i OS2Sync: {len(terminated_users)}")
    for uuid in terminated_users:
        await os2sync_client.delete_user(uuid)

    logger.info("sync users done")


async def cleanup_duplicate_engagements(
    settings: Settings,
    graphql_session: AsyncClientSession,
    os2sync_client: OS2SyncClient,
):
    """Delete and resync users in fk-org with multiple engagements of the same job-function (name) and same org_unit"""
    request_uuid = await os2sync_client.trigger_hierarchy()
    _, users = await os2sync_client.get_hierarchy(request_uuid=request_uuid)
    # Find users with duplicated engagements
    user_uuids = {
        UUID(item["Uuid"]) for item in users if not all_unique(item["Positions"], tuple)
    }
    logger.info(f"Found {len(user_uuids)} users with duplicated engagements.")

    logger.info("Deleting users from fk-org.")
    for user_uuid in user_uuids:
        await os2sync_client.delete_user(user_uuid)
    logger.info("Done with cleanup of duplicate engagements")
    if settings.uuid_from_it_systems:
        fk_org_uuid_map = await os2mo.fk_org_uuid_to_mo_uuid(
            graphql_session=graphql_session,
            uuids=user_uuids,
            it_system_names=settings.uuid_from_it_systems,
        )
        user_uuids = {
            fk_org_uuid_map.get(user_uuid, user_uuid) for user_uuid in user_uuids
        }
    logger.warn(
        f"""
        Users has been deleted from os2sync and must be uploaded again! Follow these steps:
        1. Connect to os2syncs database: (password is found in docker-compose.yml)
        `docker exec -it os2sync_mysql_1 mysql -u os2sync -ppassw0rD os2sync`
        2. Wait for os2sync to finish deleting the users (check the `queue_users` table)
        `SELECT COUNT(*) FROM queue_users;`
        3. Clear the `success_users` table.
        `DELETE FROM success_users;`
        4. Trigger sync of the users again:
        `docker exec -it os2sync_export bash -c "printf '{' '.join(str(u) for u in user_uuids)}' | xargs -d' ' -I % curl -X POST localhost:8000/trigger/user/%"`
        """
    )


async def cleanup_duplicates(
    settings: Settings,
    graphql_session: AsyncClientSession,
    os2sync_client: OS2SyncClient,
):
    logger.info("Starting cleanup of duplicates")
    logger.info("Reading all orgunits")
    orgunits = await read_all_org_units(
        settings=settings, graphql_session=graphql_session
    )
    logger.info("Passivating and synchronizing orgunits")
    for uuid, unit in orgunits.items():
        await os2sync_client.passivate_orgunit(uuid)
        await os2sync_client.upsert_org_unit(unit)
    logger.info("Read all users from MO")
    mo_users = await read_all_users(
        graphql_session=graphql_session,
        settings=settings,
    )
    logger.info("Passivating and synchronizing users")
    for uuid, user in mo_users.items():
        await os2sync_client.passivate_user(uuid)
        await os2sync_client.update_users(uuid, [user])

    logger.info("Cleanup Done")
