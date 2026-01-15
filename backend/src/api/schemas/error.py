"""Error response schemas for standardized API error handling."""
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Detailed error information."""
    field: Optional[str] = Field(None, description="Field name if error is field-specific")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code for programmatic handling")


class ErrorResponse(BaseModel):
    """Standardized error response format.
    
    All API errors should follow this format for consistency.
    """
    error: str = Field(..., description="Error type/category")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[list[ErrorDetail]] = Field(None, description="Detailed error information")
    code: Optional[str] = Field(None, description="Error code for programmatic handling")
    timestamp: Optional[str] = Field(None, description="Error timestamp (ISO format)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "validation_error",
                "message": "Invalid input data",
                "details": [
                    {
                        "field": "email",
                        "message": "Invalid email format",
                        "code": "INVALID_EMAIL"
                    }
                ],
                "code": "VALIDATION_ERROR",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class SuccessResponse(BaseModel):
    """Standardized success response format."""
    success: bool = Field(True, description="Operation success status")
    message: Optional[str] = Field(None, description="Success message")
    data: Optional[Any] = Field(None, description="Response data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {}
            }
        }
