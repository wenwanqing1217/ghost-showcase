"""Structured error types and helpers for mindflow-map."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class MindFlowError(Exception):
    """Base exception for all mindflow-map errors."""

    def __init__(self, message: str, code: str = "UNKNOWN_ERROR", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = details or {}


class ToolExecutionError(MindFlowError):
    """Raised when a workflow tool fails during execution."""

    def __init__(self, message: str, tool_name: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, code="TOOL_EXECUTION_ERROR", details=details)
        self.tool_name = tool_name


class IntentParseError(MindFlowError):
    """Raised when intent parsing fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, code="INTENT_PARSE_ERROR", details=details)


class AlphaIDClientError(MindFlowError):
    """Raised when Alpha-ID client encounters an error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, code="ALPHA_ID_CLIENT_ERROR", details=details)


class ShortDramasClientError(MindFlowError):
    """Raised when ShortDramas client encounters an error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, code="SHORTDRAMAS_CLIENT_ERROR", details=details)


class WorkflowValidationError(MindFlowError):
    """Raised when workflow definition is invalid."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, code="WORKFLOW_VALIDATION_ERROR", details=details)


@dataclass
class ErrorResponse:
    """Structured error response for API endpoints."""

    success: bool = False
    error: str = ""
    code: str = "UNKNOWN_ERROR"
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "error": self.error,
            "code": self.code,
            "details": self.details,
        }
