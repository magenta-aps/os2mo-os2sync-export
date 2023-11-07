# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
import logging
from typing import Dict
from uuid import UUID

import sentry_sdk
from fastapi import APIRouter
from fastapi import BackgroundTasks
from fastapi import FastAPI
from fastramqpi.main import FastRAMQPI  # type: ignore
from gql import gql
from gql.client import AsyncClientSession
from more_itertools import one
from ramqp.depends import Context
from ramqp.depends import RateLimit
from ramqp.mo import MORouter
from ramqp.mo import PayloadUUID

from os2sync_export.__main__ import main
from os2sync_export.config import get_os2sync_settings
from os2sync_export.config import Settings
from os2sync_export.os2mo import get_address_org_unit_and_employee_uuids
from os2sync_export.os2mo import get_engagement_employee_uuid
from os2sync_export.os2mo import get_ituser_org_unit_and_employee_uuids
from os2sync_export.os2mo import get_kle_org_unit_uuid
from os2sync_export.os2mo import get_manager_org_unit_uuid
from os2sync_export.os2mo import get_sts_orgunit
from os2sync_export.os2mo import get_sts_user
from os2sync_export.os2sync import OS2SyncClient

logger = logging.getLogger(__name__)

fastapi_router = APIRouter()
amqp_router = MORouter()


def unpack_context(context) -> tuple[Settings, AsyncClientSession, OS2SyncClient]:
    """Returns the relevant objects from the context dictionary"""
    settings: Settings = context["user_context"]["settings"]
    graphql_session: AsyncClientSession = context["graphql_session"]
    os2sync_client: OS2SyncClient = context["user_context"]["os2sync_client"]
    return settings, graphql_session, os2sync_client


@fastapi_router.get("/")
async def index() -> Dict[str, str]:
    return {"name": "os2sync_export"}


@fastapi_router.post("/trigger", status_code=202)
async def trigger_all(
    context: Context, background_tasks: BackgroundTasks
) -> Dict[str, str]:
    settings, graphql_session, os2sync_client = unpack_context(context=context)

    background_tasks.add_task(
        main,
        settings=settings,
        gql_session=graphql_session,
        os2sync_client=os2sync_client,
    )
    return {"triggered": "OK"}


@amqp_router.register("person")
async def amqp_trigger_employee(
    context: Context, uuid: PayloadUUID, _: RateLimit
) -> None:
    settings, graphql_session, os2sync_client = unpack_context(context=context)

    try:
        sts_users = await get_sts_user(
            str(uuid),
            gql_session=graphql_session,
            settings=settings,
        )
        logger.debug(sts_users)
    except ValueError:
        os2sync_client.delete_user(uuid)
        logger.info(f"No fk-org user was found for {uuid=}. Deleting from fk-org")
    else:
        os2sync_client.update_users(uuid, sts_users)


@amqp_router.register("org_unit")
async def amqp_trigger_org_unit(context: Context, uuid: PayloadUUID, _: RateLimit):
    settings, graphql_session, os2sync_client = unpack_context(context=context)

    sts_org_unit = None
    if await is_below_top_unit(
        graphql_session,
        uuid,
        settings.os2sync_top_unit_uuid,
    ):
        try:
            sts_org_unit = get_sts_orgunit(str(uuid), settings=settings)
        except ValueError:
            logger.info(f"Event registered but no org_unit was found with {uuid=}")
            os2sync_client.delete_orgunit(uuid)
    if sts_org_unit is None:
        os2sync_client.delete_orgunit(uuid)
        return

    os2sync_client.upsert_org_unit(sts_org_unit)
    logger.info(f"Synced org_unit to fk-org: {uuid=}")


@amqp_router.register("address")
async def amqp_trigger_address(context: Context, uuid: PayloadUUID, _: RateLimit):
    settings, graphql_session, os2sync_client = unpack_context(context=context)
    try:
        ou_uuid, e_uuid = await get_address_org_unit_and_employee_uuids(
            graphql_session, uuid
        )
    except ValueError:
        logger.debug(f"No address found {uuid=}")
        return

    if ou_uuid and is_below_top_unit(
        graphql_session,
        uuid,
        settings.os2sync_top_unit_uuid,
    ):
        try:
            sts_org_unit = get_sts_orgunit(str(ou_uuid), settings)
        except ValueError:
            logger.info("Related org_unit not found")
            return
        os2sync_client.update_org_unit(ou_uuid, sts_org_unit)
        logger.info(f"Synced org_unit to fk-org: {ou_uuid}")
        return

    if e_uuid:
        sts_users = await get_sts_user(
            e_uuid, gql_session=graphql_session, settings=settings
        )
        os2sync_client.update_users(e_uuid, sts_users)
        return

    logger.warn(
        f"Unable to update address, could not find org_unit or employee for: {uuid}"
    )


async def is_below_top_unit(
    gql_session: AsyncClientSession,
    unit_uuid: UUID,
    top_unit_uuid: UUID,
) -> bool:
    """Checks whether an organisation unit is below the top unit.

    This check is necessary because fk-org only supports one top level unit.
    """
    query = """
    query QueryAncestors($uuids: [UUID!]) {
        org_units(uuids: $uuids) {
            current {
            ancestors {
                uuid
            }
            }
        }
    }
     """
    res = await gql_session.execute(
        gql(query), variable_values={"uuids": str(unit_uuid)}
    )
    if not res["org_units"]:
        logger.warn("No unit found")
        return False
    ancestors = one(res["org_units"])["current"]["ancestors"]
    if ancestors is None:
        return False
    else:
        return top_unit_uuid in {UUID(a["uuid"]) for a in ancestors}


@amqp_router.register("ituser")
async def amqp_trigger_it_user(context: Context, uuid: PayloadUUID, _: RateLimit):
    settings, graphql_session, os2sync_client = unpack_context(context=context)

    try:
        ou_uuid, e_uuid = await get_ituser_org_unit_and_employee_uuids(
            graphql_session, uuid
        )
    except ValueError:
        logger.debug(f"Event registered but no it-user found with {uuid=}")
        return

    if ou_uuid and await is_below_top_unit(
        graphql_session, ou_uuid, settings.os2sync_top_unit_uuid
    ):
        try:
            sts_org_unit = get_sts_orgunit(str(ou_uuid), settings)
        except ValueError:
            logger.info("Related org_unit not found")
            return
        os2sync_client.update_org_unit(ou_uuid, sts_org_unit)
        logger.info(f"Synced org_unit to fk-org: {ou_uuid}")

        # If the uuid is overwritten from an it-account we need to ensure no org_unit exists with the old uuid.
        if sts_org_unit and str(ou_uuid) != str(sts_org_unit.Uuid):
            logger.info(
                f"Delete org_unit with {ou_uuid=} from fk-org to as the uuid was overwritten by an it-account"
            )
            os2sync_client.delete_orgunit(ou_uuid)
        return

    if e_uuid:
        sts_users = await get_sts_user(
            e_uuid, gql_session=graphql_session, settings=settings
        )
        os2sync_client.update_users(e_uuid, sts_users)

        # If the users uuid is overwritten from an it-account we need to ensure no user exists with the old uuid.
        if not any(str(e_uuid) == str(user["Uuid"]) for user in sts_users if user):
            logger.info(
                f"Delete user with {e_uuid=} from fk-org to as the uuid was overwritten by an it-account"
            )
            os2sync_client.delete_user(e_uuid)
        return

    logger.warn(f"Unable to update ituser, could not find owners for: {uuid}")


@amqp_router.register("manager")
async def amqp_trigger_manager(context: Context, uuid: PayloadUUID, _: RateLimit):
    settings, graphql_session, os2sync_client = unpack_context(context=context)

    try:
        ou_uuid = await get_manager_org_unit_uuid(graphql_session, uuid)
    except ValueError:
        logger.debug(f"Event registered but no manager found with {uuid=}")
        return

    if ou_uuid and await is_below_top_unit(
        graphql_session,
        ou_uuid,
        settings.os2sync_top_unit_uuid,
    ):
        try:
            sts_org_unit = get_sts_orgunit(str(ou_uuid), settings)
        except ValueError:
            logger.info("Related org_unit not found")
            return
        os2sync_client.update_org_unit(ou_uuid, sts_org_unit)
        logger.info(f"Synced org_unit to fk-org: {ou_uuid}")
        return

    logger.warn(f"Unable to update manager, could not find owners for: {uuid}")


@amqp_router.register("engagement")
async def amqp_trigger_engagement(context: Context, uuid: PayloadUUID, _: RateLimit):
    settings, graphql_session, os2sync_client = unpack_context(context=context)

    try:
        e_uuid = await get_engagement_employee_uuid(graphql_session, uuid)
    except ValueError:
        logger.debug(f"Event registered but no engagement found with {uuid=}")
        return

    if e_uuid:
        sts_users = await get_sts_user(
            e_uuid, gql_session=graphql_session, settings=settings
        )
        os2sync_client.update_users(e_uuid, sts_users)
        return

    logger.warn(f"Unable to update ituser, could not find owners for: {uuid}")


@amqp_router.register("kle")
async def amqp_trigger_kle(context: Context, uuid: PayloadUUID, _: RateLimit):
    settings, graphql_session, os2sync_client = unpack_context(context=context)

    ou_uuid = await get_kle_org_unit_uuid(graphql_session, uuid)
    if ou_uuid and await is_below_top_unit(
        graphql_session,
        ou_uuid,
        settings.os2sync_top_unit_uuid,
    ):
        try:
            sts_org_unit = get_sts_orgunit(str(ou_uuid), settings)
        except ValueError:
            logger.info("Related org_unit not found")
            return
        os2sync_client.update_org_unit(ou_uuid, sts_org_unit)
        logger.info(f"Synced org_unit to fk-org: {ou_uuid}")
        return

    logger.warn(f"Unable to update ituser, could not find owners for ituser: {uuid}")


@fastapi_router.post("/trigger/user/{uuid}")
async def trigger_user(
    context: Context,
    uuid: UUID,
) -> str:
    settings, graphql_session, os2sync_client = unpack_context(context=context)

    sts_users = await get_sts_user(
        str(uuid),
        gql_session=graphql_session,
        settings=settings,
    )
    os2sync_client.update_users(uuid, sts_users)
    logger.info(f"Synced user to fk-org: {uuid}")

    return "OK"


@fastapi_router.post("/trigger/orgunit/{uuid}", status_code=200)
async def trigger_orgunit(
    context: Context,
    uuid: UUID,
) -> str:
    settings, _, os2sync_client = unpack_context(context=context)
    try:
        sts_org_unit = get_sts_orgunit(str(uuid), settings=settings)
    except ValueError:
        logger.info("Org_unit not found")
        return "Org_unit not found"
    os2sync_client.update_org_unit(uuid, sts_org_unit)
    logger.info(f"Synced org_unit to fk-org: {uuid}")
    return "OK"


def create_fastramqpi(**kwargs) -> FastRAMQPI:
    settings: Settings = get_os2sync_settings(**kwargs)
    settings.start_logging_based_on_settings()
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn)

    fastramqpi = FastRAMQPI(application_name="os2sync-export", settings=settings)

    amqpsystem = fastramqpi.get_amqpsystem()
    amqpsystem.router.registry.update(amqp_router.registry)
    fastramqpi.add_context(
        settings=settings, os2sync_client=OS2SyncClient(settings=settings)
    )

    app = fastramqpi.get_app()
    app.include_router(fastapi_router)

    return fastramqpi


def create_app(**kwargs) -> FastAPI:
    fastramqpi = create_fastramqpi(**kwargs)
    return fastramqpi.get_app()
