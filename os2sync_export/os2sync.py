# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
import logging
from typing import Dict
from typing import Optional
from typing import Set
from typing import Tuple
from uuid import UUID

import requests
from tenacity import retry
from tenacity import retry_if_exception_type
from tenacity import stop_after_delay
from tenacity import wait_fixed

from os2sync_export import stub
from os2sync_export.config import get_os2sync_settings
from os2sync_export.os2sync_models import OrgUnit

retry_max_time = 60
logger = logging.getLogger(__name__)


class OS2SyncClient:
    def __init__(self, settings, session=None) -> None:
        self.settings = settings or get_os2sync_settings()
        self.session = session or self._get_os2sync_session()

    def _get_os2sync_session(self):
        session = requests.Session()

        if self.settings.os2sync_api_url == "stub":
            return stub.Session()

        session.verify = self.settings.os2sync_ca_verify_os2sync
        session.headers["User-Agent"] = "os2mo-data-import-and-export"
        session.headers["CVR"] = self.settings.municipality
        return session

    def os2sync_url(self, url):
        """format url like {BASE}/user"""
        url = url.format(BASE=self.settings.os2sync_api_url)
        return url

    def os2sync_get(self, url, **params) -> Dict:
        url = self.os2sync_url(url)
        r = self.session.get(url, params=params)
        if r.status_code == 404:
            raise KeyError(f"No object found at {url=}, {params=}")
        r.raise_for_status()
        return r.json()

    def os2sync_get_org_unit(self, uuid: UUID) -> OrgUnit:
        current = self.os2sync_get(f"{{BASE}}/orgUnit/{str(uuid)}")
        current.pop("Type")
        current.pop("Timestamp")
        return OrgUnit(**current)

    def os2sync_delete(self, url, **params):
        url = self.os2sync_url(url)
        try:
            r = self.session.delete(url, **params)
            r.raise_for_status()
            return r
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning("delete %r %r :404", url, params)
                return r

    def os2sync_post(self, url, **params):
        url = self.os2sync_url(url)
        r = self.session.post(url, **params)
        r.raise_for_status()
        return r

    def delete_orgunit(self, uuid: UUID):
        if uuid == self.settings.os2sync_top_unit_uuid:
            logger.error("Received event to delete top_unit_uuid - ignoring.")
            return
        logger.info("delete orgunit %s", uuid)
        self.os2sync_delete("{BASE}/orgUnit/" + str(uuid))

    def delete_user(self, uuid: UUID):
        self.os2sync_delete("{BASE}/user/" + str(uuid))

    def upsert_org_unit(self, org_unit: OrgUnit) -> None:
        try:
            current = self.os2sync_get_org_unit(uuid=org_unit.Uuid)
        except KeyError:
            logger.info(f"OrgUnit not found in os2sync - creating {org_unit.Uuid=}")
            self.os2sync_post("{BASE}/orgUnit/", json=org_unit.json())
            return

        # Avoid overwriting information that we cannot provide from os2mo.
        org_unit.LOSShortName = current.LOSShortName
        org_unit.Tasks = org_unit.Tasks or current.Tasks
        org_unit.ShortKey = org_unit.ShortKey or current.ShortKey
        org_unit.PayoutUnitUuid = org_unit.PayoutUnitUuid or current.PayoutUnitUuid
        org_unit.ContactPlaces = org_unit.ContactPlaces or current.ContactPlaces
        org_unit.ContactOpenHours = (
            org_unit.ContactOpenHours or current.ContactOpenHours
        )
        org_unit.SOR = org_unit.SOR or current.SOR

        logger.info(f"Syncing org_unit {org_unit}")

        self.os2sync_post("{BASE}/orgUnit/", json=org_unit.json())

    def trigger_hierarchy(self) -> UUID:
        """ "Triggers a job in the os2sync container that gathers the entire hierarchy from FK-ORG

        Returns: UUID

        """
        r = self.session.get(f"{self.settings.os2sync_api_url}/hierarchy")
        r.raise_for_status()
        return UUID(r.text)

    @retry(
        wait=wait_fixed(5),
        reraise=True,
        stop=stop_after_delay(10 * 60),
        retry=retry_if_exception_type(requests.HTTPError),
    )
    def get_hierarchy(self, request_uuid: UUID) -> Tuple[Set[UUID], Set[UUID]]:
        """Fetches the hierarchy from os2sync. Retries for 10 minutes until it is ready."""
        r = self.session.get(
            f"{self.settings.os2sync_api_url}/hierarchy/{str(request_uuid)}"
        )
        r.raise_for_status()
        hierarchy = r.json()["Result"]
        if hierarchy is None:
            raise ConnectionError("Check connection to FK-ORG")
        existing_os2sync_org_units = {UUID(o["Uuid"]) for o in hierarchy["OUs"]}
        existing_os2sync_users = {UUID(u["Uuid"]) for u in hierarchy["Users"]}
        return existing_os2sync_org_units, existing_os2sync_users

    def update_users(self, uuid: UUID, users):
        if all(u is None for u in users):
            # No fk-org user found. Delete user from fk-org
            self.delete_user(uuid)
            return

        for user in users:
            if user:
                logger.info(f"Syncing user {user['Uuid']=} to fk-org")
                self.os2sync_post("{BASE}/user", json=user)

    def update_org_unit(self, uuid: UUID, org_unit: Optional[OrgUnit]):
        if org_unit:
            self.upsert_org_unit(org_unit)
        else:
            self.delete_orgunit(uuid)
