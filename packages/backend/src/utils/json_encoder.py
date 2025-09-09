"""
Custom JSON encoders and utilities for datetime serialization.
"""

import json
from datetime import datetime, date
from typing import Any
from uuid import UUID


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects."""
    
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


def jsonable_encoder_custom(obj: Any) -> Any:
    """
    Custom version of FastAPI's jsonable_encoder that handles datetime properly.
    """
    from fastapi.encoders import jsonable_encoder
    
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, date):
        return obj.isoformat()
    elif isinstance(obj, UUID):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: jsonable_encoder_custom(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [jsonable_encoder_custom(item) for item in obj]
    else:
        return jsonable_encoder(obj)