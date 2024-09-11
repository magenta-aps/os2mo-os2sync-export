# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from typing import Annotated
from typing import Dict
from uuid import UUID

import structlog
from fastapi import APIRouter
from fastapi import BackgroundTasks
from fastapi import Depends
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastramqpi.depends import LegacyGraphQLSession
from fastramqpi.depends import from_user_context
from fastramqpi.main import FastRAMQPI  # type: ignore
from fastramqpi.ramqp.depends import RateLimit
from fastramqpi.ramqp.mo import MORouter
from fastramqpi.ramqp.mo import PayloadUUID
from more_itertools import one
from more_itertools import only

from os2sync_export.__main__ import cleanup_duplicate_engagements
from os2sync_export.__main__ import main
from os2sync_export.autogenerated_graphql_client import GraphQLClient as GraphQLClient_
from os2sync_export.config import Settings
from os2sync_export.depends import GraphQLClient
from os2sync_export.os2mo import check_terminated_accounts
from os2sync_export.os2mo import find_employees
from os2sync_export.os2mo import get_address_org_unit_and_employee_uuids
from os2sync_export.os2mo import get_engagement_employee_uuid
from os2sync_export.os2mo import get_ituser_org_unit_and_employee_uuids
from os2sync_export.os2mo import get_kle_org_unit_uuid
from os2sync_export.os2mo import get_manager_org_unit_uuid
from os2sync_export.os2mo import get_sts_orgunit
from os2sync_export.os2mo import get_sts_user
from os2sync_export.os2mo import is_relevant
from os2sync_export.os2sync import OS2SyncClient
from os2sync_export.os2sync_models import convert_mo_to_fk_user

logger = structlog.stdlib.get_logger()

fastapi_router = APIRouter()
amqp_router = MORouter()

Settings_ = Annotated[Settings, Depends(from_user_context("settings"))]
OS2SyncClient_ = Annotated[OS2SyncClient, Depends(from_user_context("os2sync_client"))]


@fastapi_router.get("/")
async def index() -> Dict[str, str]:
    return {"name": "os2sync_export"}


@fastapi_router.post("/trigger", status_code=202)
async def trigger_all(
    background_tasks: BackgroundTasks,
    settings: Settings_,
    graphql_session: LegacyGraphQLSession,
    os2sync_client: OS2SyncClient_,
) -> Dict[str, str]:
    background_tasks.add_task(
        main,
        settings=settings,
        graphql_session=graphql_session,
        os2sync_client=os2sync_client,
    )
    return {"triggered": "OK"}


@fastapi_router.post("/cleanup_duplicate_engagements", status_code=202)
async def trigger_cleanup_duplicate_engagements(
    background_tasks: BackgroundTasks,
    settings: Settings_,
    graphql_session: LegacyGraphQLSession,
    os2sync_client: OS2SyncClient_,
) -> Dict[str, str]:
    background_tasks.add_task(
        cleanup_duplicate_engagements,
        settings=settings,
        graphql_session=graphql_session,
        os2sync_client=os2sync_client,
    )
    return {"triggered": "OK"}


@amqp_router.register("person")
async def amqp_trigger_employee(
    uuid: PayloadUUID,
    settings: Settings_,
    graphql_session: LegacyGraphQLSession,
    os2sync_client: OS2SyncClient_,
    _: RateLimit,
) -> None:
    try:
        sts_users = await get_sts_user(
            str(uuid),
            graphql_session=graphql_session,
            settings=settings,
        )
        logger.debug(
            f"Event registered for person with {uuid=}", fk_org_users=sts_users
        )
    except ValueError:
        os2sync_client.delete_user(uuid)
        logger.info(f"No fk-org user was found for {uuid=}. Deleting from fk-org")
    else:
        os2sync_client.update_users(uuid, sts_users)


@amqp_router.register("org_unit")
async def amqp_trigger_org_unit(
    uuid: PayloadUUID,
    settings: Settings_,
    graphql_session: LegacyGraphQLSession,
    os2sync_client: OS2SyncClient_,
    _: RateLimit,
) -> None:
    sts_org_unit = None
    if await is_relevant(
        graphql_session,
        uuid,
        settings,
    ):
        try:
            sts_org_unit = get_sts_orgunit(uuid, settings=settings)
        except ValueError:
            logger.info(f"Event registered but no org_unit was found with {uuid=}")
            os2sync_client.delete_orgunit(uuid)
    if sts_org_unit is None:
        os2sync_client.delete_orgunit(uuid)
    else:
        os2sync_client.upsert_org_unit(sts_org_unit)

    logger.info(f"Synced org_unit to fk-org: {uuid=}, now checking engagements")
    employees = await find_employees(graphql_session, uuid)
    for e in employees:
        await amqp_trigger_employee(e, settings, graphql_session, os2sync_client, _)


@amqp_router.register("address")
async def amqp_trigger_address(
    uuid: PayloadUUID,
    settings: Settings_,
    graphql_session: LegacyGraphQLSession,
    os2sync_client: OS2SyncClient_,
    _: RateLimit,
) -> None:
    try:
        ou_uuid, e_uuid = await get_address_org_unit_and_employee_uuids(
            graphql_session, uuid
        )
    except ValueError:
        logger.debug(f"No address found {uuid=}")
        return

    if ou_uuid and is_relevant(
        graphql_session,
        uuid,
        settings,
    ):
        try:
            sts_org_unit = get_sts_orgunit(ou_uuid, settings)
        except ValueError:
            logger.info("Related org_unit not found")
            return
        os2sync_client.update_org_unit(ou_uuid, sts_org_unit)
        logger.info(f"Synced org_unit to fk-org: {ou_uuid}")
        return

    if e_uuid:
        sts_users = await get_sts_user(
            e_uuid, graphql_session=graphql_session, settings=settings
        )
        os2sync_client.update_users(e_uuid, sts_users)
        return

    logger.warn(
        f"Unable to update address, could not find org_unit or employee for: {uuid}"
    )


@amqp_router.register("ituser")
async def amqp_trigger_it_user(
    uuid: PayloadUUID,
    settings: Settings_,
    graphql_session: LegacyGraphQLSession,
    os2sync_client: OS2SyncClient_,
    _: RateLimit,
) -> None:
    if settings.new:
        return
    try:
        ou_uuid, e_uuid = await get_ituser_org_unit_and_employee_uuids(
            graphql_session, uuid
        )
    except ValueError:
        logger.debug(f"Event registered but no it-user found with {uuid=}")
        return

    if settings.uuid_from_it_systems:
        terminated_users, terminated_org_units = await check_terminated_accounts(
            graphql_session=graphql_session,
            uuid=uuid,
            uuid_from_it_systems=settings.uuid_from_it_systems,
        )

        for terminate_uuid in terminated_org_units:
            logger.info(
                f"Found terminated it-user. Deleting fk-org user with uuid = {terminate_uuid}"
            )
            os2sync_client.delete_orgunit(terminate_uuid)
        for terminate_uuid in terminated_users:
            logger.info(
                f"Found terminated it-user. Deleting fk-org user with uuid = {terminate_uuid}"
            )
            os2sync_client.delete_user(terminate_uuid)

    if ou_uuid and await is_relevant(graphql_session, ou_uuid, settings):
        try:
            sts_org_unit = get_sts_orgunit(ou_uuid, settings)
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
            e_uuid, graphql_session=graphql_session, settings=settings
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
async def amqp_trigger_manager(
    uuid: PayloadUUID,
    settings: Settings_,
    graphql_session: LegacyGraphQLSession,
    os2sync_client: OS2SyncClient_,
    _: RateLimit,
) -> None:
    try:
        ou_uuid = await get_manager_org_unit_uuid(graphql_session, uuid)
    except ValueError:
        logger.debug(f"Event registered but no manager found with {uuid=}")
        return

    if ou_uuid and await is_relevant(
        graphql_session,
        ou_uuid,
        settings,
    ):
        try:
            sts_org_unit = get_sts_orgunit(ou_uuid, settings)
        except ValueError:
            logger.info("Related org_unit not found")
            return
        os2sync_client.update_org_unit(ou_uuid, sts_org_unit)
        logger.info(f"Synced org_unit to fk-org: {ou_uuid}")
        return

    logger.warn(f"Unable to update manager, could not find owners for: {uuid}")


@amqp_router.register("engagement")
async def amqp_trigger_engagement(
    uuid: PayloadUUID,
    settings: Settings_,
    graphql_session: LegacyGraphQLSession,
    os2sync_client: OS2SyncClient_,
    _: RateLimit,
) -> None:
    try:
        e_uuid = await get_engagement_employee_uuid(graphql_session, uuid)
    except ValueError:
        logger.debug(f"Event registered but no engagement found with {uuid=}")
        return

    if e_uuid:
        sts_users = await get_sts_user(
            e_uuid, graphql_session=graphql_session, settings=settings
        )
        os2sync_client.update_users(e_uuid, sts_users)
        return

    logger.warn(f"Unable to update ituser, could not find owners for: {uuid}")


@amqp_router.register("kle")
async def amqp_trigger_kle(
    uuid: PayloadUUID,
    settings: Settings_,
    graphql_session: LegacyGraphQLSession,
    os2sync_client: OS2SyncClient_,
    _: RateLimit,
) -> None:
    try:
        ou_uuid = await get_kle_org_unit_uuid(graphql_session, uuid)
    except ValueError:
        logger.debug(f"Event registered but no KLE found with {uuid=}")
        return
    if ou_uuid and await is_relevant(
        graphql_session,
        ou_uuid,
        settings,
    ):
        try:
            sts_org_unit = get_sts_orgunit(ou_uuid, settings)
        except ValueError:
            logger.info("Related org_unit not found")
            return
        os2sync_client.update_org_unit(ou_uuid, sts_org_unit)
        logger.info(f"Synced org_unit to fk-org: {ou_uuid}")
        return

    logger.warn(f"Unable to update ituser, could not find owners for ituser: {uuid}")


@fastapi_router.post("/trigger/user/{uuid}")
async def trigger_user(
    uuid: UUID,
    settings: Settings_,
    graphql_session: LegacyGraphQLSession,
    os2sync_client: OS2SyncClient_,
) -> str:
    sts_users = await get_sts_user(
        str(uuid),
        graphql_session=graphql_session,
        settings=settings,
    )
    os2sync_client.update_users(uuid, sts_users)
    logger.info(f"Synced user to fk-org: {uuid}")

    return "OK"


async def read_fk_users_from_person(graphql_client: GraphQLClient, uuid: UUID):
    it_accounts = await graphql_client.read_user_i_t_accounts(uuid)
    current_accounts = one(it_accounts.objects).current
    if current_accounts is None:
        return
    fk_accounts = current_accounts.fk_org_users
    ad_accounts = current_accounts.a_d_users
    return fk_accounts, ad_accounts


async def read_person_accounts(
    graphql_client: GraphQLClient,
    uuid: UUID,
    top_unit_uuid: UUID,
    hierarchy_user_keys: list[str],
    filtered_org_units: list[UUID],
):
    fk_accounts, ad_accounts = await read_fk_users_from_person(
        graphql_client=graphql_client, uuid=uuid
    )
    # create
    # For each AD account that has no fk-account - create one
    # This step could be moved into it-user event handling!

    # update
    # For each fk-account (including newly created) with a matching AD/Omada account - update fk-org user
    for f in ad_accounts:
        relevant_fk_account = only(
            filter(lambda fk: fk.external_id == f.external_id, fk_accounts)
        )
        fk_uuid = relevant_fk_account.user_key if relevant_fk_account else f.external_id
        mo_user_info = await graphql_client.read_user(uuids=f.uuid)
        current = one(mo_user_info.objects).current

        def filter_engagements_by_ancestor(
            eng,
        ):
            org_unit = one(eng.org_unit)
            return org_unit.uuid == top_unit_uuid or top_unit_uuid in {
                o.uuid for o in org_unit.ancestors
            }

        if current is None or current.engagement is None:
            yield fk_uuid, None
        assert current and current.engagement

        current.engagement = list(
            filter(filter_engagements_by_ancestor, current.engagement)
        )

        def filter_engagements_by_org_unit_filter(
            eng,
        ):
            org_unit = one(eng.org_unit)
            return org_unit.uuid != filtered_org_units and not {
                o.uuid for o in org_unit.ancestors
            }.intersection(set(filtered_org_units))

        if filtered_org_units:
            current.engagement = list(
                filter(filter_engagements_by_org_unit_filter, current.engagement)
            )

        if hierarchy_user_keys:

            def filter_engagements_by_hierarchy(
                eng,
            ):
                org_unit = one(eng.org_unit)
                return only(org_unit.org_unit_hierarchy_model) in hierarchy_user_keys

            current.engagement = list(
                filter(filter_engagements_by_hierarchy, current.engagement)
            )

        yield fk_uuid, current

    # delete
    # for each fk-account with no matching AD/Omada account - delete fk-org user


@fastapi_router.post("/trigger/new/user/{uuid}")
async def trigger_user_new(
    uuid: UUID,
    settings: Settings_,
    graphql_client: GraphQLClient,
    os2sync_client: OS2SyncClient_,
) -> str:
    async for fk_uuid, user_info in read_person_accounts(
        graphql_client=graphql_client,
        uuid=uuid,
        top_unit_uuid=settings.top_unit_uuid,
        hierarchy_user_keys=settings.filter_hierarchy_names,
        filtered_org_units=settings.filter_orgunit_uuid,
    ):
        fk_org_user = convert_mo_to_fk_user(
            fk_org_uuid=fk_uuid, user=user_info, settings=settings
        )
        if fk_org_user.Positions:
            os2sync_client.os2sync_post(
                "{BASE}/user", json=jsonable_encoder(fk_org_user)
            )
            logger.info(f"Synced user to fk-org: {uuid}")
        else:
            os2sync_client.delete_user(fk_uuid)
            logger.info(f"Deleted user without relevant engagement: {uuid}")

    return "ok"


@fastapi_router.post("/trigger/orgunit/{uuid}", status_code=200)
async def trigger_orgunit(
    uuid: UUID,
    settings: Settings_,
    graphql_session: LegacyGraphQLSession,
    os2sync_client: OS2SyncClient_,
) -> str:
    try:
        sts_org_unit = get_sts_orgunit(uuid, settings=settings)
    except ValueError:
        logger.info("Org_unit not found")
        return "Org_unit not found"
    os2sync_client.update_org_unit(uuid, sts_org_unit)
    logger.info(f"Synced org_unit to fk-org: {uuid}")
    return "OK"


def create_fastramqpi(**kwargs) -> FastRAMQPI:
    settings: Settings = Settings(**kwargs)
    fastramqpi = FastRAMQPI(
        application_name="os2sync-export",
        settings=settings.fastramqpi,
        graphql_client_cls=GraphQLClient_,
        graphql_version=22 if settings.new else 3,
    )

    amqpsystem = fastramqpi.get_amqpsystem()
    amqpsystem.router.registry.update(amqp_router.registry)
    fastramqpi.add_context(
        settings=settings,
        os2sync_client=OS2SyncClient(settings=settings),
    )

    app = fastramqpi.get_app()
    app.include_router(fastapi_router)

    return fastramqpi


def create_app() -> FastAPI:
    fastramqpi = create_fastramqpi()
    return fastramqpi.get_app()
