"""Database session 回归测试：SQLite 父目录自动创建（CI 无 data/ 目录时曾 58 失败）。"""

from __future__ import annotations

import pytest

from mindflow_map.models.session import Database, _ensure_sqlite_parent_dir


@pytest.mark.parametrize(
    "url",
    [
        "sqlite+aiosqlite:///./mindflow_map.db",
        "sqlite:///:memory:",
    ],
)
def test_sqlite_urls_do_not_crash(tmp_path, url: str) -> None:
    """内存库 / 相对路径均不抛异常（相对路径不强制创建 tmp 目录）。"""
    if url == "sqlite:///:memory:":
        assert _ensure_sqlite_parent_dir(url) is None
        return
    _ensure_sqlite_parent_dir(url)


def test_ensure_sqlite_parent_dir_creates_missing_dir(tmp_path) -> None:
    """默认 database_url 指向不存在的 data/ 目录时，连接前应自动 mkdir。"""
    db_file = tmp_path / "data" / "mindflow_map.db"
    url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    assert not db_file.parent.exists()
    _ensure_sqlite_parent_dir(url)
    assert db_file.parent.is_dir()


def test_database_ctor_with_missing_parent_dir(tmp_path) -> None:
    """Database 构造即确保父目录存在，随后可正常建表连接。"""
    import asyncio

    from mindflow_map.models.database import Base

    db_file = tmp_path / "data" / "mindflow_map.db"
    url = f"sqlite+aiosqlite:///{db_file.as_posix()}"

    async def _run() -> None:
        db = Database(url)
        assert db_file.parent.is_dir()
        async with db.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await db.close()

    asyncio.run(_run())
    assert db_file.exists() or len(list(db_file.parent.glob("*.db"))) > 0
