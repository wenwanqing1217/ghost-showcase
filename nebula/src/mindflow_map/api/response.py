"""统一的 API 响应模型。"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一接口响应格式。"""

    success: bool = True
    data: T | None = None
    error: str | None = Field(default=None, description="失败时的错误信息")
    code: str | None = Field(default=None, description="业务错误码")
