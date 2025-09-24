from datetime import datetime
from typing import List
from typing import Optional
from typing import Union
from uuid import UUID

from .async_base_client import AsyncBaseClient
from .base_model import UNSET
from .base_model import UnsetType
from .create_i_t_user import CreateITUser
from .create_i_t_user import CreateITUserItuserCreate
from .find_address_unit_or_person import FindAddressUnitOrPerson
from .find_address_unit_or_person import FindAddressUnitOrPersonAddresses
from .find_engagement_person import FindEngagementPerson
from .find_engagement_person import FindEngagementPersonEngagements
from .find_f_k_itsystem import FindFKItsystem
from .find_f_k_itsystem import FindFKItsystemItsystems
from .find_ituser_unit_or_person import FindItuserUnitOrPerson
from .find_ituser_unit_or_person import FindItuserUnitOrPersonItusers
from .find_k_l_e_unit import FindKLEUnit
from .find_k_l_e_unit import FindKLEUnitItusers
from .find_manager_unit import FindManagerUnit
from .find_manager_unit import FindManagerUnitManagers
from .input_types import AddressCreateInput
from .input_types import ClassFilter
from .input_types import EmployeeCreateInput
from .input_types import EngagementCreateInput
from .input_types import ITSystemFilter
from .input_types import ITUserCreateInput
from .input_types import OrganisationUnitCreateInput
from .read_orgunit import ReadOrgunit
from .read_orgunit import ReadOrgunitOrgUnits
from .read_user_i_t_accounts import ReadUserITAccounts
from .read_user_i_t_accounts import ReadUserITAccountsEmployees
from .terminate_i_t_user import TerminateITUser
from .terminate_i_t_user import TerminateITUserItuserTerminate
from .testing__address_create import TestingAddressCreate
from .testing__address_create import TestingAddressCreateAddressCreate
from .testing__employee_create import TestingEmployeeCreate
from .testing__employee_create import TestingEmployeeCreateEmployeeCreate
from .testing__engagement_create import TestingEngagementCreate
from .testing__engagement_create import TestingEngagementCreateEngagementCreate
from .testing__get_class import TestingGetClass
from .testing__get_class import TestingGetClassClasses
from .testing__get_itsystem import TestingGetItsystem
from .testing__get_itsystem import TestingGetItsystemItsystems
from .testing__ituser_create import TestingItuserCreate
from .testing__ituser_create import TestingItuserCreateItuserCreate
from .testing__org_unit_create import TestingOrgUnitCreate
from .testing__org_unit_create import TestingOrgUnitCreateOrgUnitCreate


def gql(q: str) -> str:
    return q


class GraphQLClient(AsyncBaseClient):
    async def read_user_i_t_accounts(
        self, uuid: UUID, it_user_keys: Union[Optional[List[str]], UnsetType] = UNSET
    ) -> ReadUserITAccountsEmployees:
        query = gql(
            """
            query ReadUserITAccounts($uuid: UUID!, $it_user_keys: [String!]) {
              employees(filter: {uuids: [$uuid]}) {
                objects {
                  current {
                    fk_org_uuids: itusers(filter: {itsystem: {user_keys: "FK-ORG-UUID"}}) {
                      user_key
                      external_id
                    }
                    itusers: itusers(filter: {itsystem: {user_keys: $it_user_keys}}) {
                      uuid
                      user_key
                      external_id
                      person {
                        cpr_number
                        name
                        nickname
                      }
                      engagement {
                        extension_3
                        org_unit {
                          uuid
                          itusers(filter: {user_keys: "FK-ORG-UUID"}) {
                            user_key
                          }
                        }
                        job_function {
                          name
                        }
                      }
                      email: addresses(filter: {address_type: {scope: "EMAIL"}}) {
                        address_type {
                          uuid
                        }
                        visibility {
                          scope
                        }
                        value
                      }
                      phone: addresses(filter: {address_type: {scope: "PHONE"}}) {
                        address_type {
                          uuid
                        }
                        visibility {
                          scope
                        }
                        value
                      }
                    }
                  }
                }
              }
            }
            """
        )
        variables: dict[str, object] = {"uuid": uuid, "it_user_keys": it_user_keys}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return ReadUserITAccounts.parse_obj(data).employees

    async def read_orgunit(self, uuid: UUID) -> ReadOrgunitOrgUnits:
        query = gql(
            """
            query read_orgunit($uuid: UUID!) {
              org_units(filter: {uuids: [$uuid]}) {
                objects {
                  current {
                    uuid
                    name
                    parent {
                      uuid
                      itusers(filter: {user_keys: "FK-ORG-UUID"}) {
                        user_key
                      }
                    }
                    ancestors {
                      uuid
                    }
                    unit_type {
                      uuid
                    }
                    org_unit_level {
                      uuid
                    }
                    org_unit_hierarchy_model {
                      name
                    }
                    addresses {
                      address_type {
                        scope
                        uuid
                        user_key
                      }
                      name
                    }
                    itusers(filter: {user_keys: "FK-ORG-UUID"}) {
                      user_key
                    }
                    managers {
                      person {
                        itusers(filter: {itsystem: {user_keys: "FK-ORG-UUID"}}) {
                          external_id
                        }
                      }
                    }
                    kles {
                      kle_number {
                        uuid
                      }
                    }
                  }
                }
              }
            }
            """
        )
        variables: dict[str, object] = {"uuid": uuid}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return ReadOrgunit.parse_obj(data).org_units

    async def find_address_unit_or_person(
        self, uuid: UUID
    ) -> FindAddressUnitOrPersonAddresses:
        query = gql(
            """
            query FindAddressUnitOrPerson($uuid: UUID!) {
              addresses(filter: {uuids: [$uuid], from_date: null, to_date: null}) {
                objects {
                  validities {
                    org_unit {
                      uuid
                    }
                    person {
                      uuid
                    }
                  }
                }
              }
            }
            """
        )
        variables: dict[str, object] = {"uuid": uuid}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return FindAddressUnitOrPerson.parse_obj(data).addresses

    async def find_ituser_unit_or_person(
        self, uuid: UUID
    ) -> FindItuserUnitOrPersonItusers:
        query = gql(
            """
            query FindItuserUnitOrPerson($uuid: UUID!) {
              itusers(filter: {uuids: [$uuid], from_date: null, to_date: null}) {
                objects {
                  validities {
                    org_unit {
                      uuid
                    }
                    person {
                      uuid
                    }
                  }
                }
              }
            }
            """
        )
        variables: dict[str, object] = {"uuid": uuid}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return FindItuserUnitOrPerson.parse_obj(data).itusers

    async def find_k_l_e_unit(self, uuid: UUID) -> FindKLEUnitItusers:
        query = gql(
            """
            query FindKLEUnit($uuid: UUID!) {
              itusers(filter: {uuids: [$uuid], from_date: null, to_date: null}) {
                objects {
                  validities {
                    org_unit {
                      uuid
                    }
                  }
                }
              }
            }
            """
        )
        variables: dict[str, object] = {"uuid": uuid}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return FindKLEUnit.parse_obj(data).itusers

    async def find_manager_unit(self, uuid: UUID) -> FindManagerUnitManagers:
        query = gql(
            """
            query FindManagerUnit($uuid: UUID!) {
              managers(filter: {uuids: [$uuid], from_date: null, to_date: null}) {
                objects {
                  validities {
                    org_unit {
                      uuid
                    }
                  }
                }
              }
            }
            """
        )
        variables: dict[str, object] = {"uuid": uuid}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return FindManagerUnit.parse_obj(data).managers

    async def find_engagement_person(
        self, uuid: UUID
    ) -> FindEngagementPersonEngagements:
        query = gql(
            """
            query FindEngagementPerson($uuid: UUID!) {
              engagements(filter: {uuids: [$uuid], from_date: null, to_date: null}) {
                objects {
                  validities {
                    person {
                      uuid
                    }
                  }
                }
              }
            }
            """
        )
        variables: dict[str, object] = {"uuid": uuid}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return FindEngagementPerson.parse_obj(data).engagements

    async def find_f_k_itsystem(self) -> FindFKItsystemItsystems:
        query = gql(
            """
            query FindFKItsystem {
              itsystems(filter: {user_keys: "FK-ORG-UUID"}) {
                objects {
                  uuid
                }
              }
            }
            """
        )
        variables: dict[str, object] = {}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return FindFKItsystem.parse_obj(data).itsystems

    async def create_i_t_user(
        self,
        external_id: str,
        itsystem: UUID,
        person: UUID,
        user_key: str,
        from_: datetime,
    ) -> CreateITUserItuserCreate:
        query = gql(
            """
            mutation CreateITUser($external_id: String!, $itsystem: UUID!, $person: UUID!, $user_key: String!, $from: DateTime!) {
              ituser_create(
                input: {validity: {from: $from}, user_key: $user_key, itsystem: $itsystem, external_id: $external_id, person: $person}
              ) {
                uuid
              }
            }
            """
        )
        variables: dict[str, object] = {
            "external_id": external_id,
            "itsystem": itsystem,
            "person": person,
            "user_key": user_key,
            "from": from_,
        }
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return CreateITUser.parse_obj(data).ituser_create

    async def terminate_i_t_user(
        self, uuid: UUID, to: datetime
    ) -> TerminateITUserItuserTerminate:
        query = gql(
            """
            mutation TerminateITUser($uuid: UUID!, $to: DateTime!) {
              ituser_terminate(input: {uuid: $uuid, to: $to}) {
                uuid
              }
            }
            """
        )
        variables: dict[str, object] = {"uuid": uuid, "to": to}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return TerminateITUser.parse_obj(data).ituser_terminate

    async def testing__get_class(
        self, filter: Union[Optional[ClassFilter], UnsetType] = UNSET
    ) -> TestingGetClassClasses:
        query = gql(
            """
            query _testing__get_class($filter: ClassFilter) {
              classes(filter: $filter) {
                objects {
                  uuid
                }
              }
            }
            """
        )
        variables: dict[str, object] = {"filter": filter}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return TestingGetClass.parse_obj(data).classes

    async def testing__get_itsystem(
        self, filter: Union[Optional[ITSystemFilter], UnsetType] = UNSET
    ) -> TestingGetItsystemItsystems:
        query = gql(
            """
            query _testing__get_itsystem($filter: ITSystemFilter) {
              itsystems(filter: $filter) {
                objects {
                  uuid
                }
              }
            }
            """
        )
        variables: dict[str, object] = {"filter": filter}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return TestingGetItsystem.parse_obj(data).itsystems

    async def testing__employee_create(
        self, input: EmployeeCreateInput
    ) -> TestingEmployeeCreateEmployeeCreate:
        query = gql(
            """
            mutation _testing__employee_create($input: EmployeeCreateInput!) {
              employee_create(input: $input) {
                uuid
              }
            }
            """
        )
        variables: dict[str, object] = {"input": input}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return TestingEmployeeCreate.parse_obj(data).employee_create

    async def testing__engagement_create(
        self, input: EngagementCreateInput
    ) -> TestingEngagementCreateEngagementCreate:
        query = gql(
            """
            mutation _testing__engagement_create($input: EngagementCreateInput!) {
              engagement_create(input: $input) {
                uuid
              }
            }
            """
        )
        variables: dict[str, object] = {"input": input}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return TestingEngagementCreate.parse_obj(data).engagement_create

    async def testing__address_create(
        self, input: AddressCreateInput
    ) -> TestingAddressCreateAddressCreate:
        query = gql(
            """
            mutation _testing__address_create($input: AddressCreateInput!) {
              address_create(input: $input) {
                uuid
              }
            }
            """
        )
        variables: dict[str, object] = {"input": input}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return TestingAddressCreate.parse_obj(data).address_create

    async def testing__org_unit_create(
        self, input: OrganisationUnitCreateInput
    ) -> TestingOrgUnitCreateOrgUnitCreate:
        query = gql(
            """
            mutation _testing__org_unit_create($input: OrganisationUnitCreateInput!) {
              org_unit_create(input: $input) {
                uuid
              }
            }
            """
        )
        variables: dict[str, object] = {"input": input}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return TestingOrgUnitCreate.parse_obj(data).org_unit_create

    async def testing__ituser_create(
        self, input: ITUserCreateInput
    ) -> TestingItuserCreateItuserCreate:
        query = gql(
            """
            mutation _testing__ituser_create($input: ITUserCreateInput!) {
              ituser_create(input: $input) {
                uuid
              }
            }
            """
        )
        variables: dict[str, object] = {"input": input}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return TestingItuserCreate.parse_obj(data).ituser_create
