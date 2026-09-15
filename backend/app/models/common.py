from typing import Annotated, Any

from bson import ObjectId
from pydantic import BeforeValidator

PyObjectId = Annotated[str, BeforeValidator(str)]


def object_id_str(value: Any) -> str:
    if isinstance(value, ObjectId):
        return str(value)
    return value
