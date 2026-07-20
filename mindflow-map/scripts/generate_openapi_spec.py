"""导出 OpenAPI Schema 到文件。"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import FastAPI

from mindflow_map.main import app
from mindflow_map.api.openapi_config import custom_openapi


async def main() -> None:
    """导出 OpenAPI Schema。"""
    # 触发 lifespan 以确保应用完全初始化
    async with app.router.startup():  # noqa: SIM117
        pass

    schema = custom_openapi(app)
    output = Path(__file__).resolve().parent.parent / "openapi.json"
    output.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OpenAPI schema exported to: {output}")


if __name__ == "__main__":
    asyncio.run(main())
