# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
import logging
from typing import Any
from typing import Dict
from uuid import UUID

import sentry_sdk
from fastapi import APIRouter
from fastapi import BackgroundTasks
from fastapi import FastAPI
from fastapi import Request
from fastramqpi.main import FastRAMQPI  # type: ignore
from gql.client import AsyncClientSession
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
    request: Request, background_tasks: BackgroundTasks
) -> Dict[str, str]:
    context: dict[str, Any] = request.app.state.context
    background_tasks.add_task(
        main,
        settings=context["user_context"]["settings"],
        gql_session=context["graphql_session"],
        os2sync_client=context["user_context"]["os2sync_client"],
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
    except ValueError:
        logger.info(f"Event registered but person was found with {uuid=}")
        os2sync_client.delete_user(uuid)

    os2sync_client.update_users(uuid, sts_users)
    logger.info(f"Synced user to fk-org: {uuid=}")


@amqp_router.register("org_unit")
async def amqp_trigger_org_unit(context: Context, uuid: PayloadUUID, _: RateLimit):
    settings, _, os2sync_client = unpack_context(context=context)

    sts_org_unit = None
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

    if ou_uuid:
        sts_org_unit = get_sts_orgunit(ou_uuid, settings)
        os2sync_client.update_org_unit(ou_uuid, sts_org_unit)
        logger.info(f"Synced org_unit to fk-org: {ou_uuid}")
        return

    if e_uuid:
        sts_users = await get_sts_user(
            e_uuid, gql_session=graphql_session, settings=settings
        )
        os2sync_client.update_users(e_uuid, sts_users)

        logger.info(f"Synced user to fk-org: {e_uuid}")
        return

    logger.warn(
        f"Unable to update address, could not find org_unit or employee for: {uuid}"
    )


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

    if ou_uuid:
        sts_org_unit = get_sts_orgunit(ou_uuid, settings)
        os2sync_client.update_org_unit(ou_uuid, sts_org_unit)
        logger.info(f"Synced org_unit to fk-org: {ou_uuid}")
        return

    if e_uuid:
        sts_users = await get_sts_user(
            e_uuid, gql_session=graphql_session, settings=settings
        )
        os2sync_client.update_users(e_uuid, sts_users)
        logger.info(f"Synced user to fk-org: {e_uuid}")
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

    if ou_uuid:
        sts_org_unit = get_sts_orgunit(ou_uuid, settings)
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
        logger.info(f"Synced user to fk-org: {e_uuid}")
        return

    logger.warn(f"Unable to update ituser, could not find owners for: {uuid}")


@amqp_router.register("kle")
async def amqp_trigger_kle(context: Context, uuid: PayloadUUID, _: RateLimit):
    settings, graphql_session, os2sync_client = unpack_context(context=context)

    ou_uuid = await get_kle_org_unit_uuid(graphql_session, uuid)
    if ou_uuid:
        sts_org_unit = get_sts_orgunit(ou_uuid, settings)
        os2sync_client.update_org_unit(ou_uuid, sts_org_unit)
        logger.info(f"Synced org_unit to fk-org: {ou_uuid}")
        return

    logger.warn(f"Unable to update ituser, could not find owners for ituser: {uuid}")


@fastapi_router.post("/trigger/user/{uuid}")
async def trigger_user(
    request: Request,
    uuid: UUID,
) -> str:
    context: dict[str, Any] = request.app.state.context
    os2sync_client: OS2SyncClient = context["user_context"]["os2sync_client"]

    sts_users = await get_sts_user(
        str(uuid),
        gql_session=context["graphql_session"],
        settings=context["user_context"]["settings"],
    )
    os2sync_client.update_users(uuid, sts_users)
    logger.info(f"Synced user to fk-org: {uuid}")

    return "OK"


@fastapi_router.post("/trigger/orgunit/{uuid}", status_code=200)
async def trigger_orgunit(
    request: Request,
    uuid: UUID,
) -> str:
    context: dict[str, Any] = request.app.state.context
    sts_org_unit = get_sts_orgunit(
        str(uuid), settings=context["user_context"]["settings"]
    )
    os2sync_client: OS2SyncClient = context["user_context"]["os2sync_client"]
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
