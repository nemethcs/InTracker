"""API versioning utilities and configuration."""
from enum import Enum
from typing import Optional
from fastapi import Header, HTTPException, status


class APIVersion(str, Enum):
    """Supported API versions."""
    V1 = "v1"
    # Future versions can be added here:
    # V2 = "v2"
    # V3 = "v3"


# Current default API version
DEFAULT_API_VERSION = APIVersion.V1

# Latest API version
LATEST_API_VERSION = APIVersion.V1


def get_api_version(
    api_version: Optional[str] = Header(None, alias="X-API-Version"),
) -> APIVersion:
    """Get API version from header or use default.
    
    Args:
        api_version: Optional API version from X-API-Version header
        
    Returns:
        APIVersion enum value
        
    Raises:
        HTTPException: If version is invalid
    """
    if api_version is None:
        return DEFAULT_API_VERSION
    
    try:
        version = APIVersion(api_version.lower())
        return version
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid API version: {api_version}. Supported versions: {[v.value for v in APIVersion]}",
        )


def validate_api_version(version: str) -> bool:
    """Validate if API version is supported.
    
    Args:
        version: API version string
        
    Returns:
        True if version is supported, False otherwise
    """
    try:
        APIVersion(version.lower())
        return True
    except ValueError:
        return False
