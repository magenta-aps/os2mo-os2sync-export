# Generated by ariadne-codegen on 2024-09-11 09:50

from datetime import datetime
from typing import Any
from typing import Callable
from typing import Dict

from fastramqpi.ariadne import parse_graphql_datetime

SCALARS_PARSE_FUNCTIONS: Dict[Any, Callable[[Any], Any]] = {
    datetime: parse_graphql_datetime
}
SCALARS_SERIALIZE_FUNCTIONS: Dict[Any, Callable[[Any], Any]] = {}
