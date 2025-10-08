# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
import datetime
from functools import lru_cache
from operator import itemgetter
from typing import Any
from typing import Dict
from typing import Iterator
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from uuid import UUID

import requests
import structlog
from fastramqpi.ra_utils.headers import TokenSettings
from gql import gql
from gql.client import AsyncClientSession
from more_itertools import first
from more_itertools import one
from more_itertools import only
from more_itertools import partition

from os2sync_export.config import Settings
from os2sync_export.config import get_os2sync_settings
from os2sync_export.os2sync_models import OrgUnit
from os2sync_export.templates import Person
from os2sync_export.templates import User

logger = structlog.stdlib.get_logger()


def get_mo_session():
    session = requests.Session()
    settings = get_os2sync_settings()
    session.verify = settings.ca_verify_os2mo

    session.headers = {
        "User-Agent": "os2mo-data-import-and-export",
    }

    session_headers = TokenSettings(
        auth_server=settings.fastramqpi.auth_server,
        client_id=settings.fastramqpi.client_id,
        client_secret=settings.fastramqpi.client_secret.get_secret_value(),
        auth_realm=settings.fastramqpi.auth_realm,
    ).get_headers()

    if session_headers:
        session.headers.update(session_headers)
    return session


class IT:
    def __init__(self, system_name: str, user_key: str):
        self.system_name = system_name
        self.user_key = user_key

    @classmethod
    def from_mo_json(cls, response: List):
        """
        Designed to parse the response from MO when requesting a users it-systems
        Concretely, expects a list of this style of object:

        {'itsystem': {'name': 'Active Directory',
              'reference': None,
              'system_type': None,
              'user_key': 'Active Directory',
              'uuid': 'a1608e69-c422-404f-a6cc-b873c50af111',
              'validity': {'from': '1900-01-01', 'to': None}},
         'org_unit': None,
         'person': {'givenname': 'Solveig',
                    'name': 'Solveig Kuhlenhenke',
                    'nickname': '',
                    'nickname_givenname': '',
                    'nickname_surname': '',
                    'surname': 'Kuhlenhenke',
                    'uuid': '23d2dfc7-6ceb-47cf-97ed-db6beadcb09b'},
         'user_key': 'SolveigK',
         'uuid': 'a2fb2581-c57a-46ad-8a21-30118a3859b7',
         'validity': {'from': '2003-08-13', 'to': None}}
        """
        return [
            cls(
                system_name=it_obj["itsystem"]["name"].strip(),
                user_key=it_obj["user_key"].strip(),
            )
            for it_obj in response
        ]

    def __repr__(self):
        return "{}(system_name={},user_key={})".format(
            self.__class__.__name__, self.system_name, self.user_key
        )

    def __eq__(self, other):
        if not isinstance(other, IT):
            raise TypeError("unexpected type: {}".format(other))

        return self.system_name == other.system_name and self.user_key == other.user_key


# truncate and warn all strings in dictionary,
# ensure not shortening uuids
def strip_truncate_and_warn(d, root, length):
    for k, v in list(d.items()):
        if isinstance(v, dict):
            strip_truncate_and_warn(v, root, length)
        elif isinstance(v, str):
            v = d[k] = v.strip()
            if len(v) > length:
                v = d[k] = v[:length]
                logger.warning(
                    "truncating to %d key '%s' for" " uuid '%s' to value '%s'",
                    length,
                    k,
                    root["Uuid"],
                    v,
                )


def os2mo_get(url, **params):
    # format url like {BASE}/service
    mo_url = get_os2sync_settings().fastramqpi.mo_url

    url = url.format(BASE=f"{mo_url}/service")
    session = get_mo_session()
    r = session.get(url, params=params)
    if r.status_code == 404:
        raise ValueError("No object found with this uuid")
    r.raise_for_status()

    try:
        # Log every query and response, but remove CPR numbers
        # this is wraped in try/except to avoid blocking the program by trying to log unexpected data
        res = r.json()
        if isinstance(res, dict) and res.get("cpr_no"):
            res.update({"cpr_no": "removed from logs"})
        logger.debug(f"os2mo_get {url=} returned {res=}")
    except:  # noqa: E722
        pass

    return r


def has_kle():
    os2mo_config = os2mo_get("{BASE}/configuration").json()
    return os2mo_config["show_kle"]


def pick_address(addresses: list[dict], classes: list[UUID]) -> str | None:
    """Finds the correct address.

    The correct address has:
    * a visibility that is either "PUBLIC" or not set.
    * an address-type that is defined in settings

    If more than one address is found the one where the address-type appears first in settings is used.
    """
    relevant_adresses = [
        a for a in addresses if UUID(a["address_type"]["uuid"]) in classes
    ]
    public_relevant_adresses = [
        a
        for a in relevant_adresses
        if a.get("visibility") is None or a["visibility"]["scope"] == "PUBLIC"
    ]

    chosen_address = min(
        public_relevant_adresses,
        key=lambda a: classes.index(UUID(a["address_type"]["uuid"])),
        default=None,
    )
    return chosen_address["name"] if chosen_address else None


async def engagements_to_user(user, engagements, graphql_session, settings):
    """
    key_to_sort_by: This is a feature flag used to determine
    whether to use "extension_3" as job function, or display
    the contents of the "job_function" field.
        True - if wanting to be overriden with "extension_3".
        False - if wanting to display "job_function".
    """
    engagements = [
        e
        for e in engagements
        if await is_relevant(
            graphql_session=graphql_session,
            unit_uuid=UUID(e["org_unit"]["uuid"]),
            settings=settings,
        )
    ]
    # Feature flag in Settings. Set it to True, if wanting to use the extension field.
    # Default is False.
    use_extension_field = settings.use_extension_field_as_job_function
    for e in engagements:
        e["job_function"] = (
            e.get("extension_3")
            if use_extension_field and e.get("extension_3")
            else e.get("job_function").get("name")
        )

    for e in sorted(engagements, key=lambda e: (e["job_function"] + e.get("uuid"))):
        user["Positions"].append(
            {
                "OrgUnitUuid": e.get("org_unit").get("uuid"),
                "Name": e.get("job_function"),
                # Only used to find primary engagements work-address
                "is_primary": e.get("is_primary"),
            }
        )


def try_get_it_user_key(uuid: str, user_key_it_system_name) -> Optional[str]:
    """
    fetches all it-systems related to a user and return the ad-user_key if exists
    """
    it_response = os2mo_get("{BASE}/e/" + uuid + "/details/it").json()
    it_systems = IT.from_mo_json(it_response)
    it_systems = list(
        filter(lambda x: x.system_name == user_key_it_system_name, it_systems)
    )

    # if no ad OR multiple
    if len(it_systems) != 1:
        return None
    return one(it_systems).user_key


def get_work_address(positions, work_address_names) -> Optional[str]:
    # find the primary engagement and lookup the addresses for that unit
    primary = filter(lambda e: e["is_primary"], positions)
    try:
        primary_eng = one(primary)
    except ValueError:
        logger.warning(
            "Could not get unique primary engagement, using first found position"
        )
        primary_eng = first(positions)

    org_addresses = os2mo_get(
        "{BASE}/ou/" + primary_eng["OrgUnitUuid"] + "/details/address"
    ).json()
    # filter and sort based on settings and use the first match if any
    work_address: List[Dict] = list(
        filter(
            lambda addr: addr["address_type"]["name"] in work_address_names,
            org_addresses,
        )
    )
    work_address = list(
        sorted(
            work_address,
            key=lambda a: work_address_names.index(a["address_type"]["name"]),
        )
    )
    chosen_work_address: Dict = first(work_address, default={})
    return chosen_work_address.get("name")


def get_fk_org_uuid(
    it_accounts: List[Dict[str, Any]], mo_uuid: str, uuid_from_it_systems: List[str]
) -> str:
    """Find FK-org uuid from it-accounts based on the given list of it-system names."""
    it = list(
        filter(lambda i: i["itsystem"]["name"] in uuid_from_it_systems, it_accounts)
    )
    # Sort the relevant it-systems based on their position in the given list
    it.sort(key=lambda name: uuid_from_it_systems.index(name["itsystem"]["name"]))
    it_uuids = list(map(itemgetter("user_key"), it))
    # Use first matching it_system uuid or return mo_uuid if no matches were found in it-accounts
    return first(it_uuids, mo_uuid)


def overwrite_position_uuids(sts_user: Dict, uuid_from_it_systems: List):
    # For each position check the it-system of the org-unit
    for p in sts_user["Positions"]:
        unit_uuid = p["OrgUnitUuid"]
        it = os2mo_get(f"{{BASE}}/ou/{unit_uuid}/details/it").json()
        p["OrgUnitUuid"] = get_fk_org_uuid(it, unit_uuid, uuid_from_it_systems)


def get_org_unit_hierarchy(titles: list[str]) -> Optional[Tuple[UUID, ...]]:
    """Find uuids of org_unit_hierarchy classes with the specified titles"""
    if not titles:
        return None
    org_unit_hierarchy_classes = os2mo_get(
        f"{{BASE}}/o/{organization_uuid()}/f/org_unit_hierarchy/"
    ).json()
    filtered_hierarchies = list(
        filter(
            lambda x: x["name"] in titles, org_unit_hierarchy_classes["data"]["items"]
        )
    )
    assert (
        len(filtered_hierarchies) > 0
    ), f"No org_unit_hierarchy classes found matching the titles {titles}."
    # Return tuple, not list, because lists can't be used as input to lru_cached functions.
    return tuple(UUID(o["uuid"]) for o in filtered_hierarchies)


async def get_sts_user_raw(
    uuid: str,
    settings: Settings,
    graphql_session: AsyncClientSession,
    fk_org_uuid: Optional[str] = None,
    user_key: Optional[str] = None,
    engagement_uuid: Optional[str] = None,
) -> Dict[str, Any]:
    employee = os2mo_get("{BASE}/e/" + uuid + "/").json()
    user = User(
        dict(
            uuid=fk_org_uuid or uuid,
            candidate_user_id=user_key,
            person=Person(employee, settings=settings),
        ),
        settings=settings,
    )

    sts_user = user.to_json()

    if settings.filter_users_by_it_system and user_key is None:
        # Skip user if filter is activated and there are no user_key to find in settings
        # By returning user without any positions it will be removed from fk-org
        return sts_user

    # use calculate_primary flag to get the is_primary boolean used in getting work-address
    engagements = os2mo_get(
        "{BASE}/e/" + uuid + "/details/engagement?calculate_primary=true"
    ).json()
    if engagement_uuid:
        engagements = list(filter(lambda e: e["uuid"] == engagement_uuid, engagements))

    await engagements_to_user(sts_user, engagements, graphql_session, settings)

    if not sts_user["Positions"]:
        # return immediately because users with no engagements are not synced.
        return sts_user
    if settings.uuid_from_it_systems:
        overwrite_position_uuids(sts_user, settings.uuid_from_it_systems)

    addresses = os2mo_get("{BASE}/e/" + uuid + "/details/address").json()
    if engagement_uuid is not None and settings.group_by_engagement_uuid:
        addresses = list(
            filter(lambda a: a["engagement_uuid"] == engagement_uuid, addresses)
        )

    sts_user["Email"] = pick_address(addresses, settings.email_scope_classes)
    sts_user["PhoneNumber"] = pick_address(
        addresses,
        settings.phone_scope_classes,
    )
    sts_user["Landline"] = pick_address(addresses, settings.landline_scope_classes)

    # Optionally find the work address of employees primary engagement.
    work_address_names = settings.employee_engagement_address
    if sts_user["Positions"] and work_address_names:
        sts_user["Location"] = get_work_address(
            sts_user["Positions"], work_address_names
        )

    truncate_length = max(36, settings.truncate_length)
    strip_truncate_and_warn(sts_user, sts_user, length=truncate_length)

    return sts_user


def group_accounts(
    users: List[Dict],
    uuid_from_it_systems: List[str],
    user_key_it_system_names: list[str],
) -> List:
    """Groups it accounts by their associated engagement"""
    # Find all unique engagement_uuids
    engagement_uuids = {
        u["engagement_uuid"]
        for u in users
        if u["itsystem"]["name"] in uuid_from_it_systems
        or u["itsystem"]["name"] in user_key_it_system_names
    }
    # Find relevant it-systems containing user_keys
    user_keys = list(
        filter(lambda x: x["itsystem"]["name"] in user_key_it_system_names, users)
    )
    # Find relevant it-systems containing uuids
    uuids = list(filter(lambda x: x["itsystem"]["name"] in uuid_from_it_systems, users))
    fk_org_accounts = []
    # Find uuid and user_key for each engagement.
    for eng_uuid in engagement_uuids:
        uuid = only(u["user_key"] for u in uuids if u["engagement_uuid"] == eng_uuid)
        try:
            user_key = min(
                [u for u in user_keys if u["engagement_uuid"] == eng_uuid],
                key=lambda it: user_key_it_system_names.index(it["itsystem"]["name"]),
            )["user_key"]
        except ValueError:
            user_key = None
        fk_org_accounts.append(
            {"engagement_uuid": eng_uuid, "uuid": uuid, "user_key": user_key}
        )
    if fk_org_accounts == []:
        try:
            user_key = min(
                user_keys,
                key=lambda it: user_key_it_system_names.index(it["itsystem"]["name"]),
            )["user_key"]
        except ValueError:
            user_key = None
        return [{"engagement_uuid": None, "uuid": None, "user_key": user_key}]
    return fk_org_accounts


async def get_sts_user(
    mo_uuid: str, graphql_session: AsyncClientSession, settings: Settings
) -> List[Dict[str, Any]]:
    try:
        users = await get_user_it_accounts(
            graphql_session=graphql_session, mo_uuid=mo_uuid
        )
        fk_org_accounts = group_accounts(
            users,
            settings.uuid_from_it_systems,
            settings.user_key_it_system_names,
        )
    except ValueError:
        logger.warn(f"Unable to map uuid/user_keys from it-systems for {mo_uuid=}.")
        fk_org_accounts = [{"engagement_uuid": None, "uuid": None, "user_key": None}]

    sts_users = [
        await get_sts_user_raw(
            mo_uuid,
            settings=settings,
            graphql_session=graphql_session,
            fk_org_uuid=it["uuid"],
            user_key=it["user_key"],
            engagement_uuid=it["engagement_uuid"],
        )
        for it in fk_org_accounts
    ]
    return sts_users


@lru_cache()
def organization_uuid() -> str:
    return one(os2mo_get("{BASE}/o/").json())["uuid"]


def org_unit_uuids(**kwargs: Any) -> Set[str]:
    org_uuid = organization_uuid()
    hierarchy_uuids = kwargs.get("hierarchy_uuids")
    if hierarchy_uuids:
        kwargs["hierarchy_uuids"] = tuple(str(u) for u in hierarchy_uuids)
    ous = os2mo_get(f"{{BASE}}/o/{org_uuid}/ou/", limit=999999, **kwargs).json()[
        "items"
    ]
    return set(map(itemgetter("uuid"), ous))


def manager_to_orgunit(unit_uuid: UUID) -> Optional[str]:
    manager = os2mo_get("{BASE}/ou/" + str(unit_uuid) + "/details/manager").json()
    # Return None if the orgunit has no manager or if the manager-role is vacant
    match len(manager):
        case 0:
            return None
        case 1:
            return (
                one(manager)["person"]["uuid"]
                if one(manager)["person"] is not None
                else None
            )
        case _:
            return (
                first(manager)["person"]["uuid"]
                if first(manager)["person"] is not None
                else None
            )


def itsystems_to_orgunit(orgunit, itsystems, uuid_from_it_systems):
    itsystems = filter(
        lambda i: i["itsystem"]["name"] not in uuid_from_it_systems, itsystems
    )
    for i in itsystems:
        orgunit["ItSystems"].append(i["itsystem"]["uuid"])


def address_type_is(
    address: Dict[str, Any], user_key=None, scope: str = "TEXT"
) -> bool:
    return (
        address["address_type"]["user_key"] == user_key
        and address["address_type"]["scope"] == scope
    )


def addresses_to_orgunit(orgunit, addresses, landline_scope_classes: List[UUID] = []):
    for a in addresses:
        if a["address_type"]["scope"] == "EMAIL":
            orgunit["Email"] = a["name"]
        elif a["address_type"]["scope"] == "EAN":
            orgunit["Ean"] = a["name"]
        elif a["address_type"]["scope"] == "PHONE":
            if a["address_type"]["uuid"] in landline_scope_classes:
                orgunit["Landline"] = a["name"]
            else:
                orgunit["PhoneNumber"] = a["name"]
        elif address_type_is(a, user_key="Contact", scope="DAR"):
            orgunit["Contact"] = a["name"]
        elif address_type_is(a, user_key="Location", scope="DAR"):
            orgunit["Location"] = a["name"]
        # Any DAR address that is not either "Contact" or "Location" is regarded as "Post"
        elif a["address_type"]["scope"] == "DAR":
            orgunit["Post"] = a["name"]
        elif a["address_type"]["scope"] == "PNUMBER":
            orgunit["PNR"] = a["name"]
        elif address_type_is(a, user_key="ContactOpenHours"):
            orgunit["ContactOpenHours"] = a["name"]
        elif address_type_is(a, user_key="DtrId"):
            orgunit["DtrId"] = a["name"]
        elif a["address_type"]["scope"] == "WWW":
            orgunit["Url"] = a["name"]


def filter_kle(aspect: str, kle) -> List[str]:
    """Filters kle by aspect name

    KLE aspects can be "Udførende", "Ansvarlig" or "Indsigt"

    Returns:
        list of uuids
    """
    tasks_kle = filter(lambda k: one(k["kle_aspect"])["name"] == aspect, kle)
    task_uuids = set(k["kle_number"]["uuid"] for k in tasks_kle)
    return list(sorted(task_uuids))


def partition_kle(
    kle: List, use_contact_for_tasks: bool
) -> Tuple[List[str], List[str]]:
    """Collect kle uuids according to kle_aspect.

    Default is to return all KLE uuids as Tasks,
    If the setting 'use_contact_for_tasks' is set KLEs will be divided:

    * Aspect "Udførende" goes into "Tasks"
    * Aspect "Ansvarlig" goes into "ContactForTasks"

    Args:
        kle: A list of KLEs.

    Returns:
        Tuple(List, List)
    """

    if use_contact_for_tasks:
        tasks = filter_kle("Udførende", kle)
        ContactForTasks = filter_kle("Ansvarlig", kle)

        return tasks, ContactForTasks

    tasks_set = set()

    for k in kle:
        uuid = k["kle_number"]["uuid"]
        tasks_set.add(uuid)

    return list(sorted(tasks_set)), []


def kle_to_orgunit(org_unit: Dict, kle: List, use_contact_for_tasks: bool) -> None:
    """Mutates the dict "org_unit" to include KLE data"""
    tasks, contactfortasks = partition_kle(
        kle, use_contact_for_tasks=use_contact_for_tasks
    )
    if tasks:
        org_unit["Tasks"] = tasks
    if contactfortasks:
        org_unit["ContactForTasks"] = contactfortasks


def is_ignored(unit, settings):
    """Determine if unit should be left out of transfer

    Args:
        unit: The organization unit to enrich with kle information.
        settings: a dictionary

    Returns:
        Boolean
    """

    return (
        unit.get("org_unit_level")
        and UUID(unit["org_unit_level"]["uuid"]) in settings.ignored_unit_levels
    ) or (
        unit.get("org_unit_type")
        and UUID(unit["org_unit_type"]["uuid"]) in settings.ignored_unit_types
    )


def overwrite_unit_uuids(sts_org_unit: Dict, uuid_from_it_systems: List):
    # Overwrite UUIDs with values from it-account
    uuid = sts_org_unit["Uuid"]
    it = os2mo_get(f"{{BASE}}/ou/{uuid}/details/it").json()
    sts_org_unit["Uuid"] = get_fk_org_uuid(it, uuid, uuid_from_it_systems)
    # Also check if parent unit has a UUID from an it-account
    parent_uuid = sts_org_unit.get("ParentOrgUnitUuid")
    if parent_uuid:
        it = os2mo_get(f"{{BASE}}/ou/{parent_uuid}/details/it").json()
        sts_org_unit["ParentOrgUnitUuid"] = get_fk_org_uuid(
            it, parent_uuid, uuid_from_it_systems
        )


async def get_sts_orgunit(
    uuid: UUID, settings: Settings, graphql_session: AsyncClientSession
) -> Optional[OrgUnit]:
    base = parent = os2mo_get("{BASE}/ou/" + str(uuid) + "/").json()

    if is_ignored(base, settings):
        logger.info("Ignoring %r", base)
        return None
    top_unit_uuid = str(settings.top_unit_uuid)
    if not parent["uuid"] == top_unit_uuid:
        while parent.get("parent"):
            if parent["uuid"] == top_unit_uuid:
                break
            parent = parent["parent"]

    if not parent["uuid"] == top_unit_uuid:
        logger.debug(
            f"Unit with {uuid=} is not a unit below {top_unit_uuid=}. Ignoring"
        )
        return None

    sts_org_unit = {"ItSystems": [], "Name": base["name"], "Uuid": str(uuid)}

    if base.get("parent") and "uuid" in base["parent"]:
        sts_org_unit["ParentOrgUnitUuid"] = base["parent"]["uuid"]
    else:
        sts_org_unit["ParentOrgUnitUuid"] = None

    itsystems_to_orgunit(
        sts_org_unit,
        os2mo_get("{BASE}/ou/" + str(uuid) + "/details/it").json(),
        uuid_from_it_systems=settings.uuid_from_it_systems,
    )
    addresses_to_orgunit(
        sts_org_unit,
        os2mo_get("{BASE}/ou/" + str(uuid) + "/details/address").json(),
    )

    if settings.sync_managers:
        manager_uuid = manager_to_orgunit(uuid)
        if manager_uuid:
            if settings.uuid_from_it_systems:
                users = await get_user_it_accounts(
                    graphql_session=graphql_session, mo_uuid=manager_uuid
                )
                fk_org_accounts = group_accounts(
                    users,
                    settings.uuid_from_it_systems,
                    settings.user_key_it_system_names,
                )
                manager_uuid_from_it_accounts = first(fk_org_accounts)["uuid"]
                # Use managers mo uuid in case there are no fk-org ituser
                manager_uuid = manager_uuid_from_it_accounts or manager_uuid
            sts_org_unit["ManagerUuid"] = manager_uuid

    if settings.enable_kle and has_kle():
        kle_to_orgunit(
            sts_org_unit,
            os2mo_get("{BASE}/ou/" + str(uuid) + "/details/kle").json(),
            use_contact_for_tasks=settings.use_contact_for_tasks,
        )

    if settings.uuid_from_it_systems:
        overwrite_unit_uuids(sts_org_unit, settings.uuid_from_it_systems)

    strip_truncate_and_warn(sts_org_unit, sts_org_unit, settings.truncate_length)

    return OrgUnit(**sts_org_unit)


async def get_user_it_accounts(
    graphql_session: AsyncClientSession, mo_uuid: str
) -> List[Dict]:
    """Find fk-org user(s) details for the person with given MO uuid"""
    q = gql(
        """
    query GetITAccounts($uuid: UUID!) {
      employees(filter: { uuids: [$uuid] }) {
        objects {
          current {
            itusers {
              uuid
              user_key
              engagement_uuid
              itsystem {
                name
              }
            }
          }
        }
      }
    }
    """
    )
    res = await graphql_session.execute(q, variable_values={"uuid": mo_uuid})
    objects = one(res["employees"]["objects"])
    return objects["current"]["itusers"]


def is_terminated(to_date: str):
    if to_date is None:
        return False
    # TODO: What timezone should we use?
    return datetime.datetime.fromisoformat(to_date) <= datetime.datetime.now(
        tz=datetime.timezone.utc
    )


async def check_terminated_accounts(
    graphql_session: AsyncClientSession,
    uuid: UUID,
    uuid_from_it_systems: list[str],
) -> tuple[set[UUID], set[UUID]]:
    q = gql(
        """
        query GetITAccountEnddate($uuid: UUID!) {
          itusers(filter: { uuids: [$uuid], to_date: null, from_date: null }) {
            objects {
              validities {
                employee_uuid
                org_unit_uuid
                user_key
                itsystem {
                  name
                }
                validity {
                  to
                }
              }
            }
          }
        }
        """
    )
    res = await graphql_session.execute(q, variable_values={"uuid": str(uuid)})
    res = one(res["itusers"]["objects"])["validities"]
    relevant_it_users: Iterator = filter(
        lambda it: it["itsystem"]["name"] in uuid_from_it_systems, res
    )

    def filter_valid_uuid(obj: dict):
        """Some it-users contain user_keys that are not valid uuids"""

        try:
            UUID(obj["user_key"])
            return True
        except ValueError:
            return False

    relevant_it_users = filter(filter_valid_uuid, relevant_it_users)
    (
        active_itusers_,
        terminated_itusers_,
    ) = partition(lambda it: is_terminated(it["validity"]["to"]), relevant_it_users)
    # Ensure we won't delete fk-org users that are actually active because of old registrations
    active_fk_org_uuids = {o["user_key"] for o in active_itusers_}
    terminated_itusers = [
        it for it in terminated_itusers_ if it["user_key"] not in active_fk_org_uuids
    ]

    terminated_user_uuids = {
        UUID(o["user_key"]) for o in terminated_itusers if o["employee_uuid"]
    }
    terminated_org_unit_uuids = {
        UUID(o["user_key"]) for o in terminated_itusers if o["org_unit_uuid"]
    }
    return terminated_user_uuids, terminated_org_unit_uuids


def extract_uuid(objects, obj_type) -> str | None:
    """Extracts uuids of employees or org_units
    When querying eg. addresses we get a list of changes to that address.
    We need to extract the uuid of the employee or org_unit, assuming they do not change.
    """
    return only(set(o.get(obj_type) for o in objects if o.get(obj_type)))


async def get_address_org_unit_and_employee_uuids(
    graphql_session: AsyncClientSession, mo_uuid: UUID
):
    """Fetches org_unit or employee, for an address by its UUID.

    Returns:
        tuple[str|None, str|None]
    """

    q = gql(
        """
    query GetAddress($uuid: UUID!) {
      addresses(filter: { uuids: [$uuid], from_date: null, to_date: null }) {
        objects {
          validities {
            employee_uuid
            org_unit_uuid
          }
        }
      }
    }
    """
    )
    mo_uuid_str = str(mo_uuid)
    result = await graphql_session.execute(
        q,
        variable_values={
            "uuid": mo_uuid_str,
        },
    )
    objects = one(result["addresses"]["objects"])["validities"]
    employee_uuid = extract_uuid(objects, "employee_uuid")
    org_unit_uuid = extract_uuid(objects, "org_unit_uuid")
    return org_unit_uuid, employee_uuid


async def get_ituser_org_unit_and_employee_uuids(
    graphql_session: AsyncClientSession, mo_uuid: UUID
):
    """Finds an ituser by its UUID."""

    q = gql(
        """
    query GetItUser($uuid: UUID!) {
      itusers(filter: { uuids: [$uuid], from_date: null, to_date: null }) {
        objects {
          validities {
            employee_uuid
            org_unit_uuid
          }
        }
      }
    }
    """
    )
    mo_uuid_str = str(mo_uuid)
    result = await graphql_session.execute(
        q,
        variable_values={
            "uuid": mo_uuid_str,
        },
    )

    objects = one(result["itusers"]["objects"])["validities"]
    employee_uuid = extract_uuid(objects, "employee_uuid")
    org_unit_uuid = extract_uuid(objects, "org_unit_uuid")
    return org_unit_uuid, employee_uuid


async def get_manager_org_unit_uuid(graphql_session: AsyncClientSession, mo_uuid: UUID):
    """Finds manager org_unit UUID, by manager UUID."""

    q = gql(
        """
    query GetManager($uuid: UUID!) {
      managers(filter: { uuids: [$uuid], from_date: null, to_date: null }) {
        objects {
          validities {
            employee_uuid
            org_unit_uuid
          }
        }
      }
    }
    """
    )
    mo_uuid_str = str(mo_uuid)
    result = await graphql_session.execute(
        q,
        variable_values={
            "uuid": mo_uuid_str,
        },
    )

    objects = one(result["managers"]["objects"])["validities"]
    org_unit_uuid = extract_uuid(objects, "org_unit_uuid")
    return org_unit_uuid


async def get_engagement_employee_uuid(
    graphql_session: AsyncClientSession, mo_uuid: UUID
):
    """Finds an employee UUID from engagement UUID."""

    q = gql(
        """
    query GetEngagement($uuid: UUID!) {
      engagements(filter: { uuids: [$uuid], from_date: null, to_date: null }) {
        objects {
          validities {
            employee_uuid
            org_unit_uuid
          }
        }
      }
    }
    """
    )
    mo_uuid_str = str(mo_uuid)
    result = await graphql_session.execute(
        q,
        variable_values={
            "uuid": mo_uuid_str,
        },
    )

    objects = one(result["engagements"]["objects"])["validities"]
    employee_uuid = extract_uuid(objects, "employee_uuid")
    return employee_uuid


async def get_kle_org_unit_uuid(graphql_session: AsyncClientSession, mo_uuid: UUID):
    """Finds an KLE org_unit UUID, by KLE UUID."""

    q = gql(
        """
    query GetKLEs($uuid: UUID!) {
      kles(filter: { uuids: [$uuid], from_date: null, to_date: null }) {
        objects {
          validities {
            org_unit_uuid
          }
        }
      }
    }
    """
    )
    mo_uuid_str = str(mo_uuid)
    result = await graphql_session.execute(
        q,
        variable_values={
            "uuid": mo_uuid_str,
        },
    )

    objects = one(result["kles"]["objects"])["validities"]
    org_unit_uuid = extract_uuid(objects, "org_unit_uuid")
    return org_unit_uuid


async def is_relevant(
    graphql_session: AsyncClientSession,
    unit_uuid: UUID,
    settings: Settings,
) -> bool:
    """Checks whether an organisation unit should be synced to fk-org

    Checks that
    * the unit is below the top unit uuid
    * is part of the correct org_unit_hierarchies
    """

    # Top unit is always relevant
    if unit_uuid == settings.top_unit_uuid:
        return True

    query = """
    query QueryAncestors($uuid: UUID!) {
      org_units(filter: { uuids: [$uuid] }) {
        objects {
          current {
            ancestors {
              uuid
            }
            org_unit_hierarchy_model {
              name
            }
            itusers {
              itsystem {
                name
              }
            }
          }
        }
      }
    }
    """
    res = await graphql_session.execute(
        gql(query), variable_values={"uuid": str(unit_uuid)}
    )
    if not res["org_units"]["objects"]:
        logger.warn("No unit found")
        return False

    org_unit = one(res["org_units"]["objects"])["current"]

    if org_unit["ancestors"] is None:
        # We won't sync other root organisation units than the one specified in settings
        return False
    # Check that the configured top unit is in the units ancestors
    ancestors = {UUID(a["uuid"]) for a in org_unit["ancestors"]}
    is_below_top_uuid: bool = settings.top_unit_uuid in ancestors

    # Check if the unit or any of its ancestors are filtered.
    if unit_uuid in settings.filter_orgunit_uuid or any(
        uuid in ancestors for uuid in settings.filter_orgunit_uuid
    ):
        logger.debug(f"Orgunit is filtered based on settings {unit_uuid=}")
        return False

    if settings.filter_hierarchy_names:
        # Check that the unit is part of the correct org_unit hierarchy
        is_in_hierarchies: bool = (
            False
            if org_unit["org_unit_hierarchy_model"] is None
            else org_unit["org_unit_hierarchy_model"]["name"]
            in settings.filter_hierarchy_names
        )
        # If there are an it-account we sync it regardless of the hierarchy
        has_it_account: bool = any(
            it["itsystem"]["name"] in settings.uuid_from_it_systems
            for it in org_unit["itusers"]
        )

        logger.debug(
            f"is_relevant check found that {is_below_top_uuid=}, {is_in_hierarchies=}, {has_it_account=}"
        )
        return is_below_top_uuid and (is_in_hierarchies or has_it_account)
    logger.debug(f"is_relevant check found that {is_below_top_uuid=}")
    return is_below_top_uuid


async def find_employees(
    graphql_session: AsyncClientSession, org_unit_uuid: UUID
) -> set[UUID]:
    query = """
    query QueryEmployees($uuid: UUID!) {
      engagements(filter: { org_unit: { uuids: [$uuid] } }) {
        objects {
          current {
            person {
              uuid
            }
          }
        }
      }
    }
    """
    res = await graphql_session.execute(
        gql(query), variable_values={"uuid": str(org_unit_uuid)}
    )
    return {
        UUID(one(e["current"]["person"])["uuid"]) for e in res["engagements"]["objects"]
    }


async def fk_org_uuid_to_mo_uuid(
    graphql_session: AsyncClientSession, uuids: set[UUID], it_system_names: list[str]
):
    query = """
        query GetFKOrgUserMap($user_keys: [String!]) {
          itusers(filter: { user_keys: $user_keys }) {
            objects {
              current {
                person {
                  uuid
                }
                user_key
                itsystem {
                  name
                }
              }
            }
          }
        }
    """
    res = await graphql_session.execute(
        gql(query), variable_values={"user_keys": [str(u) for u in uuids]}
    )
    res = res["itusers"]["objects"]
    itusers: Iterator = filter(
        lambda i: i["current"]["itsystem"]["name"] in it_system_names, res
    )
    return {
        UUID(r["current"]["user_key"]): UUID(one(r["current"]["person"])["uuid"])
        for r in itusers
    }
