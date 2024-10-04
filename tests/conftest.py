# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
from typing import Any
from typing import Callable
from typing import Generator
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from pydantic import SecretStr

from os2sync_export.config import AMQPConnectionSettings
from os2sync_export.config import FastRAMQPISettings
from os2sync_export.config import Settings
from os2sync_export.os2sync import WritableOS2SyncClient

DEFAULT_AMQP_URL = "amqp://guest:guest@msg_broker:5672/os2mo"


@pytest.fixture()
def set_settings() -> Generator[Callable[..., Settings], None, None]:
    """Fixture to mock get_settings."""

    def setup_mock_settings(
        *args: Any,
        municipality=1234,
        top_unit_uuid="baccbf9b-d699-4118-a6fe-aeb813631a15",
        amqp_url: str = DEFAULT_AMQP_URL,
        client_id: str = "tester",
        client_secret: SecretStr = SecretStr("hunter2"),
        **kwargs: Any,
    ) -> Settings:
        settings = Settings(
            *args,
            municipality=municipality,
            top_unit_uuid=top_unit_uuid,
            fastramqpi=FastRAMQPISettings(
                amqp=AMQPConnectionSettings(url=amqp_url),  # type: ignore
                client_id=client_id,
                client_secret=client_secret,
            ),  # type: ignore
            **kwargs,
        )
        return settings

    yield setup_mock_settings


@pytest.fixture()
def mock_settings(
    set_settings: Callable[..., Settings],
) -> Generator[Settings, None, None]:
    """Fixture to mock get_settings."""
    yield set_settings()


@pytest.fixture
def graphql_session() -> Generator[AsyncMock, None, None]:
    """Fixture for the GraphQL session."""
    yield AsyncMock()


@pytest.fixture
def graphql_client() -> Generator[AsyncMock, None, None]:
    """Fixture for the codegen client."""
    yield AsyncMock()


@pytest.fixture
def requests_session() -> Generator[MagicMock, None, None]:
    """Fixture for the requests session."""
    yield MagicMock()


@pytest.fixture
def mock_os2sync_client(
    mock_settings, requests_session
) -> Generator[WritableOS2SyncClient, None, None]:
    """Fixture for the os2sync_client."""
    yield WritableOS2SyncClient(settings=mock_settings, session=requests_session)


@pytest.fixture
def os2sync_client() -> Generator[AsyncMock, None, None]:
    """Fixture for the ModelClient."""
    yield AsyncMock()
