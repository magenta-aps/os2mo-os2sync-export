# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from typing import Iterable
from uuid import UUID

import structlog
from fastapi.encoders import jsonable_encoder
from more_itertools import first
from more_itertools import one
from more_itertools import only
from more_itertools import partition
from pydantic import ValidationError

from os2sync_export.autogenerated_graphql_client.find_address_unit_or_person import (
    FindAddressUnitOrPersonAddresses,
)
from os2sync_export.autogenerated_graphql_client.find_engagement_person import (
    FindEngagementPersonEngagements,
)
from os2sync_export.autogenerated_graphql_client.find_ituser_unit_or_person import (
    FindItuserUnitOrPersonItusers,
)
from os2sync_export.autogenerated_graphql_client.find_k_l_e_unit import (
    FindKLEUnitItusers,
)
from os2sync_export.autogenerated_graphql_client.find_manager_unit import (
    FindManagerUnitManagers,
)
from os2sync_export.autogenerated_graphql_client.read_orgunit import (
    ReadOrgunitOrgUnitsObjectsCurrent,
)
from os2sync_export.autogenerated_graphql_client.read_orgunit import (
    ReadOrgunitOrgUnitsObjectsCurrentParent,
)
from os2sync_export.autogenerated_graphql_client.read_user_i_t_accounts import (
    ReadUserITAccountsEmployeesObjectsCurrentFkOrgUuids,
)
from os2sync_export.autogenerated_graphql_client.read_user_i_t_accounts import (
    ReadUserITAccountsEmployeesObjectsCurrentItusers,
)
from os2sync_export.autogenerated_graphql_client.read_user_i_t_accounts import (
    ReadUserITAccountsEmployeesObjectsCurrentItusersEmail,
)
from os2sync_export.autogenerated_graphql_client.read_user_i_t_accounts import (
    ReadUserITAccountsEmployeesObjectsCurrentItusersPhone,
)
from os2sync_export.config import Settings
from os2sync_export.depends import GraphQLClient
from os2sync_export.os2mo import addresses_to_orgunit
from os2sync_export.os2sync import OS2SyncClient
from os2sync_export.os2sync_models import OrgUnit
from os2sync_export.os2sync_models import Person
from os2sync_export.os2sync_models import Position
from os2sync_export.os2sync_models import User

logger = structlog.stdlib.get_logger()


async def read_fk_users_from_person(
    graphql_client: GraphQLClient, uuid: UUID, it_user_keys: list[str]
) -> tuple[
    list[ReadUserITAccountsEmployeesObjectsCurrentFkOrgUuids],
    list[ReadUserITAccountsEmployeesObjectsCurrentItusers],
]:
    it_accounts = await graphql_client.read_user_i_t_accounts(
        uuid=uuid, it_user_keys=it_user_keys
    )
    current_accounts = one(it_accounts.objects).current
    if current_accounts is None:
        return [], []
    fk_accounts = current_accounts.fk_org_uuids
    ad_accounts = current_accounts.itusers
    return fk_accounts, ad_accounts


async def ensure_mo_fk_org_user_exists(
    graphql_client: GraphQLClient,
    os2sync_user: User,
    fk_org_it_users: list[ReadUserITAccountsEmployeesObjectsCurrentFkOrgUuids],
):
    fk_org_account = only(
        filter(lambda f: f.external_id == os2sync_user.Uuid, fk_org_it_users)
    )
    if fk_org_account is None:
        # New user, create it-user in MO. This should trigger a new sync of that user.
        pass
    pass


async def delete_fk_org_user(
    fk_org_it_user: ReadUserITAccountsEmployeesObjectsCurrentFkOrgUuids,
):
    raise NotImplementedError


def convert_and_filter(
    settings: Settings,
    fk_org_users: list[ReadUserITAccountsEmployeesObjectsCurrentFkOrgUuids],
    it_users: list[ReadUserITAccountsEmployeesObjectsCurrentItusers],
) -> tuple[list[User], set[UUID]]:
    # TODO: add filtering for it_users
    delete_fk_org_users = {
        UUID(fk_org_user.external_id)
        for fk_org_user in fk_org_users
        if fk_org_user.user_key not in {a.user_key for a in it_users}
    }
    # Map user-keys to uuids using uuids from FK-org it account if it exists, else use the it-users external id (eg objectGUID)
    fk_org_uuids = {
        it.user_key: UUID(
            only({f.external_id for f in fk_org_users if f.user_key == it.user_key})
            or it.external_id
        )
        for it in it_users
    }
    os2sync_updates = []
    for it_user in it_users:
        try:
            os2sync_updates.append(
                convert_to_os2sync(
                    settings=settings, it=it_user, uuid=fk_org_uuids[it_user.user_key]
                )
            )
        except ValidationError:
            delete_fk_org_users.add(fk_org_uuids[it_user.user_key])

    return os2sync_updates, delete_fk_org_users


async def delete_mo_fk_org_users(
    graphql_client: GraphQLClient, external_id: UUID
) -> None:
    pass


def choose_public_address(
    candidates: Iterable[ReadUserITAccountsEmployeesObjectsCurrentItusersEmail]
    | Iterable[ReadUserITAccountsEmployeesObjectsCurrentItusersPhone],
    priority: list[UUID],
) -> str | None:
    if not candidates:
        return None
    # Filter visibility
    candidates_filtered = [
        c for c in candidates if c.visibility is None or c.visibility.scope == "PUBLIC"
    ]

    try:
        res = min(
            (c for c in candidates_filtered if c.address_type.uuid in priority),
            key=lambda p: priority.index(p.address_type.uuid),
        )
    except ValueError:
        res = first(candidates_filtered, default=None)  # type: ignore

    return res.value if res else None


def find_phone_numbers(
    phones: list[ReadUserITAccountsEmployeesObjectsCurrentItusersPhone],
    landline_scope_classes: list[UUID],
    phone_scope_classes: list[UUID],
) -> tuple[str | None, str | None]:
    """Find landline numbers and mobile numbers from the users phone numbers"""
    mobile_candidates, landline_candidates = partition(
        lambda p: p.address_type.uuid in landline_scope_classes, phones
    )
    landline = choose_public_address(landline_candidates, landline_scope_classes)
    mobile = choose_public_address(mobile_candidates, phone_scope_classes)

    return landline, mobile


def convert_to_os2sync(
    settings: Settings,
    it: ReadUserITAccountsEmployeesObjectsCurrentItusers,
    uuid: UUID,
) -> User:
    if it.person is None:
        raise ValueError(
            "The given it-account has no 'person' connected and is therefore invalid."
        )
    mo_person = one(it.person)
    cpr = mo_person.cpr_number if settings.sync_cpr else None
    person = Person(Name=mo_person.nickname or mo_person.name, Cpr=cpr)
    landline, mobile = find_phone_numbers(
        it.phone, settings.landline_scope_classes, settings.phone_scope_classes
    )

    email = choose_public_address(it.email, settings.email_scope_classes)

    positions = [
        Position(
            Name=i.extension_3
            if settings.use_extension_field_as_job_function and i.extension_3
            else i.job_function.name,
            OrgUnitUuid=one(i.org_unit).uuid,
        )
        for i in it.engagement or []
    ]

    return User(
        Uuid=uuid,
        UserId=it.user_key,
        Person=person,
        Positions=positions,
        PhoneNumber=mobile,
        Landline=landline,
        Email=email,
    )


async def sync_mo_user_to_fk_org(
    graphql_client: GraphQLClient,
    settings: Settings,
    os2sync_client: OS2SyncClient,
    uuid: UUID,
) -> tuple[list[User], set[UUID]]:
    """Handles sync of a persons users to fk-org.

    Returns a list of users synced to fk-org and a set of uuids representing users deleted from fk-org.
    """
    fk_org_users, it_users = await read_fk_users_from_person(
        graphql_client=graphql_client,
        uuid=uuid,
        it_user_keys=settings.it_system_user_keys,
    )
    logger.info(
        "Found the following itusers",
        uuid=uuid,
        fk_org_users=fk_org_users,
        ad_users=it_users,
    )
    updates_fk, deletes_fk = convert_and_filter(settings, fk_org_users, it_users)
    for os2sync_user in updates_fk:
        await ensure_mo_fk_org_user_exists(graphql_client, os2sync_user, fk_org_users)
        os2sync_client.update_user(os2sync_user)
    for deleted_user_uuid in deletes_fk:
        await delete_mo_fk_org_users(graphql_client, deleted_user_uuid)
        os2sync_client.delete_user(deleted_user_uuid)
    return updates_fk, deletes_fk


def filter_relevant_orgunit(
    settings: Settings, orgunit_data: ReadOrgunitOrgUnitsObjectsCurrent
) -> bool:
    # Root unit is always relevant
    if orgunit_data.uuid == settings.top_unit_uuid:
        return True
    # There can only be one root in fk-org
    if orgunit_data.parent is None:
        return False
    ancestor_uuids = {a.uuid for a in orgunit_data.ancestors}
    # Ensure the unit is in the correct part of the tree
    if settings.top_unit_uuid not in ancestor_uuids:
        return False

    # Ensure the unit or any of it's ancestors are not filtered
    if orgunit_data.uuid in settings.filter_orgunit_uuid or any(
        uuid in ancestor_uuids for uuid in settings.filter_orgunit_uuid
    ):
        return False
    # If the unit has an fk-org account it is considered relevant
    # This enables syncing specific units outside the usually relevant hierarchies
    if orgunit_data.itusers:
        return True
    # Ensure the unit has the correct org_unit_hierarchy (if relevant)
    if settings.filter_hierarchy_names:
        if (
            not orgunit_data.org_unit_hierarchy_model
            or orgunit_data.org_unit_hierarchy_model.name
            not in settings.filter_hierarchy_names
        ):
            return False
    # Ensure the unit level or type is not ignored
    if (
        orgunit_data.org_unit_level
        and orgunit_data.org_unit_level.uuid in settings.ignored_unit_levels
    ):
        return False
    if (
        orgunit_data.unit_type
        and orgunit_data.unit_type.uuid in settings.ignored_unit_types
    ):
        return False
    # If all above checks are ok, the unit is relevant to sync to os2sync
    return True


def find_fk_org_uuid(
    unit: ReadOrgunitOrgUnitsObjectsCurrent | ReadOrgunitOrgUnitsObjectsCurrentParent,
):
    fk_org_account = only(unit.itusers)
    return fk_org_account.user_key if fk_org_account else unit.uuid


def mo_orgunit_to_os2sync(
    settings: Settings, orgunit_data: ReadOrgunitOrgUnitsObjectsCurrent
) -> OrgUnit:
    if not filter_relevant_orgunit(settings=settings, orgunit_data=orgunit_data):
        raise ValueError()
    unit_fk_org_uuid = find_fk_org_uuid(orgunit_data)
    parent_fk_org_uuid = (
        find_fk_org_uuid(orgunit_data.parent) if orgunit_data.parent else None
    )
    kle_numbers = (
        {k.kle_number.uuid for k in orgunit_data.kles} if settings.enable_kle else set()
    )
    # We can only sync one manager:
    manager = first(orgunit_data.managers, default=None)
    # A manager is always one person
    manager_person = (
        only(manager.person)
        if manager is not None and manager.person is not None
        else None
    )
    manager_uuid = (
        UUID(first(manager_person.itusers).external_id)
        if manager_person is not None
        else None
    )

    ## Reuse old logic for selecting addresses. Create an empty dictionary which is then mutated by addresses_to_orgunit to include the correct os2sync-field to address mapping.
    addresses: dict[str, str] = dict()
    addresses_to_orgunit(addresses, addresses=jsonable_encoder(orgunit_data.addresses))

    return OrgUnit(
        Uuid=unit_fk_org_uuid,
        Name=orgunit_data.name,
        ParentOrgUnitUuid=parent_fk_org_uuid,
        Tasks=kle_numbers,
        ManagerUuid=manager_uuid if settings.sync_managers else None,
        **addresses,  # type: ignore[arg-type]
    )


def find_object_unit(
    object_info: FindAddressUnitOrPersonAddresses
    | FindItuserUnitOrPersonItusers
    | FindManagerUnitManagers
    | FindKLEUnitItusers,
) -> set[UUID]:
    validities = one(object_info.objects).validities  # type: ignore [attr-defined]
    org_unit_uuids = {
        o.uuid for org in validities if org.org_unit for o in org.org_unit
    }
    return org_unit_uuids


def find_object_person(
    object_info: FindAddressUnitOrPersonAddresses
    | FindItuserUnitOrPersonItusers
    | FindEngagementPersonEngagements,
) -> set[UUID]:
    validities = one(object_info.objects).validities  # type: ignore [attr-defined]
    person_uuids = {o.uuid for org in validities if org.person for o in org.person}
    return person_uuids


async def find_fk_itsystem_uuid(graphql_client: GraphQLClient):
    res = await graphql_client.find_f_k_itsystem()
    return one(res.objects).uuid
