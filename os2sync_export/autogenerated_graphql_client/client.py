# Generated by ariadne-codegen on 2024-09-10 08:55
# Source: queries.graphql

from .async_base_client import AsyncBaseClient
from .version import Version
from .version import VersionVersion


def gql(q: str) -> str:
    return q


class GraphQLClient(AsyncBaseClient):
    async def version(self) -> VersionVersion:
        query = gql(
            """
            query Version {
              version {
                mo_version
                mo_hash
              }
            }
            """
        )
        variables: dict[str, object] = {}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return Version.parse_obj(data).version
