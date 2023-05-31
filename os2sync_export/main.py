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
from ramqp.depends import Context
from ramqp.depends import SleepOnError
from ramqp.mo import MORouter
from ramqp.mo import PayloadUUID

from os2sync_export import os2sync
from os2sync_export.__main__ import main
from os2sync_export.config import get_os2sync_settings
from os2sync_export.config import Settings
from os2sync_export.os2mo import get_sts_orgunit
from os2sync_export.os2mo import get_sts_user


logger = logging.getLogger(__name__)

fastapi_router = APIRouter()
amqp_router = MORouter()


async def update_single_user(uuid: UUID, gql_session, settings: Settings) -> None:
    sts_users = await get_sts_user(
        str(uuid), gql_session=gql_session, settings=settings
    )

    for sts_user in sts_users:
        if sts_user:
            os2sync.os2sync_post("{BASE}/user", json=sts_user)


async def update_single_orgunit(uuid: UUID, settings: Settings) -> None:
    sts_org_unit = get_sts_orgunit(str(uuid), settings=settings)

    if sts_org_unit:
        os2sync.upsert_org_unit(
            sts_org_unit,
            settings.os2sync_api_url,
        )
    else:
        os2sync.delete_orgunit(uuid)


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
    )
    return {"triggered": "OK"}


@amqp_router.register("person")
async def amqp_trigger_employee(
    context: Context, uuid: PayloadUUID, _: SleepOnError
) -> None:
    await update_single_user(
        uuid,
        gql_session=context["graphql_session"],
        settings=context["user_context"]["settings"],
    )
    logger.info(f"Synced user to fk-org: {uuid=}")


@amqp_router.register("org_unit")
async def amqp_trigger_org_unit(context: Context, uuid: PayloadUUID, _: SleepOnError):
    await update_single_orgunit(
        uuid,
        settings=context["user_context"]["settings"],
    )
    logger.info(f"Synced org_unit to fk-org: {uuid=}")


@fastapi_router.post("/trigger/user/{uuid}")
async def trigger_user(
    request: Request,
    uuid: UUID,
) -> str:
    context: dict[str, Any] = request.app.state.context

    await update_single_user(
        uuid,
        gql_session=context["graphql_session"],
        settings=context["user_context"]["settings"],
    )
    return "OK"


@fastapi_router.post("/trigger/orgunit/{uuid}", status_code=200)
async def trigger_orgunit(
    request: Request,
    uuid: UUID,
) -> str:
    context: dict[str, Any] = request.app.state.context
    await update_single_orgunit(
        uuid,
        settings=context["user_context"]["settings"],
    )

    return "OK"


def create_fastramqpi(**kwargs) -> FastRAMQPI:
    settings = get_os2sync_settings(**kwargs)
    settings.start_logging_based_on_settings()
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn)

    fastramqpi = FastRAMQPI(application_name="os2sync-export", settings=settings)

    amqpsystem = fastramqpi.get_amqpsystem()
    amqpsystem.router.registry.update(amqp_router.registry)
    fastramqpi.add_context(settings=settings)

    app = fastramqpi.get_app()
    app.include_router(fastapi_router)

    return fastramqpi


def create_app(**kwargs) -> FastAPI:
    fastramqpi = create_fastramqpi(**kwargs)
    return fastramqpi.get_app()
