from typing import Any
from typing import Callable
from typing import Generator

import pytest

from os2sync_export.config import Settings

DEFAULT_AMQP_URL = "amqp://guest:guest@msg_broker:5672/os2mo"


@pytest.fixture()
def set_settings() -> Generator[Callable[..., Settings], None, None]:
    """Fixture to mock get_settings."""

    def setup_mock_settings(
        *args: Any,
        municipality=1234,
        os2sync_top_unit_uuid="baccbf9b-d699-4118-a6fe-aeb813631a15",
        amqp_url: str = DEFAULT_AMQP_URL,
        client_id: str = "tester",
        client_secret: str = "hunter2",
        **kwargs: Any
    ) -> Settings:
        settings = Settings(
            *args,
            municipality=municipality,
            os2sync_top_unit_uuid=os2sync_top_unit_uuid,
            amqp={"url": amqp_url},
            client_id=client_id,
            client_secret=client_secret,
            **kwargs
        )
        return settings

    yield setup_mock_settings
