"""
Validation utilities for A2A schemas.

Provides helper functions for validating requests and responses
with detailed error messages.
"""

from typing import TypeVar

from pydantic import ValidationError

from .knowledge import StoreKnowledgeRequest, StoreKnowledgeResponse

T = TypeVar("T", StoreKnowledgeRequest, StoreKnowledgeResponse)


class SchemaValidationError(Exception):
    """Raised when schema validation fails."""
    
    def __init__(self, message: str, errors: list[dict] | None = None):
        super().__init__(message)
        self.errors = errors or []


def validate_request(data: dict) -> StoreKnowledgeRequest:
    """
    Validate and parse a StoreKnowledgeRequest from a dictionary.
    
    Args:
        data: Dictionary containing request data
        
    Returns:
        Validated StoreKnowledgeRequest instance
        
    Raises:
        SchemaValidationError: If validation fails
    """
    try:
        return StoreKnowledgeRequest.model_validate(data)
    except ValidationError as e:
        errors = e.errors()
        error_messages = [
            f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
            for err in errors
        ]
        raise SchemaValidationError(
            f"Request validation failed: {'; '.join(error_messages)}",
            errors=[dict(err) for err in errors]
        ) from e


def validate_response(data: dict) -> StoreKnowledgeResponse:
    """
    Validate and parse a StoreKnowledgeResponse from a dictionary.
    
    Args:
        data: Dictionary containing response data
        
    Returns:
        Validated StoreKnowledgeResponse instance
        
    Raises:
        SchemaValidationError: If validation fails
    """
    try:
        return StoreKnowledgeResponse.model_validate(data)
    except ValidationError as e:
        errors = e.errors()
        error_messages = [
            f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
            for err in errors
        ]
        raise SchemaValidationError(
            f"Response validation failed: {'; '.join(error_messages)}",
            errors=[dict(err) for err in errors]
        ) from e


def validate_json(json_str: str, schema_type: type[T]) -> T:
    """
    Validate JSON string against a schema type.
    
    Args:
        json_str: JSON string to validate
        schema_type: Either StoreKnowledgeRequest or StoreKnowledgeResponse
        
    Returns:
        Validated schema instance
        
    Raises:
        SchemaValidationError: If validation fails
    """
    try:
        return schema_type.model_validate_json(json_str)
    except ValidationError as e:
        errors = e.errors()
        error_messages = [
            f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
            for err in errors
        ]
        raise SchemaValidationError(
            f"JSON validation failed for {schema_type.__name__}: {'; '.join(error_messages)}",
            errors=[dict(err) for err in errors]
        ) from e
