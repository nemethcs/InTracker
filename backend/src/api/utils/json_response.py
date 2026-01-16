"""Optimized JSON response utilities using orjson for faster serialization."""
from fastapi.responses import Response
import orjson
from typing import Any


class OptimizedJSONResponse(Response):
    """Fast JSON response using orjson for serialization.
    
    orjson is significantly faster than the standard library json module
    and provides better performance for large responses.
    """
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        """Render content to JSON bytes using orjson.
        
        Args:
            content: Content to serialize (dict, list, Pydantic model, etc.)
            
        Returns:
            JSON-encoded bytes
        """
        # If content is a Pydantic model, use model_dump with exclude_none
        if hasattr(content, "model_dump"):
            # Use model_dump with exclude_none for cleaner JSON
            # Optionally exclude unset fields for update responses
            return orjson.dumps(
                content.model_dump(exclude_none=True),
                option=orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_SERIALIZE_UUID
            )
        
        # For dict/list, serialize directly
        return orjson.dumps(
            content,
            option=orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_SERIALIZE_UUID
        )
