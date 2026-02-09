# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0
import json
from uuid import uuid4

import structlog

logger = structlog.stdlib.get_logger()


class Session:
    headers: dict[str, str] = {}
    text = str(uuid4())
    status_code = 404

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def close(self):
        pass

    def raise_for_status(self):
        pass

    def get(self, *args, **kwargs):
        logger.info("GET %r %r", args, kwargs)
        return self

    def delete(self, *args, **kwargs):
        logger.info("DELETE %r %r", args, kwargs)
        return self

    def post(self, *args, **kwargs):
        logger.info("POST %r %r", args, json.dumps(kwargs))
        return self

    def json(self):
        return {"Result": {"OUs": [], "Users": []}}
