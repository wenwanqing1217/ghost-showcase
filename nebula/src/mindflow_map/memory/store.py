"""记忆层 - 存储后端（SQLite / PostgreSQL 双模式）"""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Text, JSON

from mindflow_map.config import settings


class Base(DeclarativeBase):
    pass


class Memory(Base):
    """记忆模型"""
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(100), index=True)
    content: Mapped[str] = mapped_column(Text)
    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class PrecheckJob(Base):
    """内容预审任务模型"""
    __tablename__ = "precheck_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(50), default="video")
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending|scanning|approved|rejected|manual_review
    ai_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    platform_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    platform_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    callback_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


def _is_sqlite_url(url: str) -> bool:
    return "sqlite" in url.lower()


class MemoryStore:
    """记忆存储（自动适配 SQLite / PostgreSQL）"""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        self._use_sqlite = _is_sqlite_url(self.database_url)
        # PostgreSQL 需要 pool_pre_ping 检测断连
        engine_kwargs = {"echo": False}
        if not self._use_sqlite:
            engine_kwargs["pool_pre_ping"] = True
            engine_kwargs["pool_recycle"] = 3600
        self.engine = create_async_engine(self.database_url, **engine_kwargs)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init(self):
        """初始化数据库（create_all — 适用于 SQLite 和 PostgreSQL）"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def save(self, user_id: str, content: str, meta: Optional[Dict] = None) -> Memory:
        """保存记忆"""
        async with self.async_session() as session:
            memory = Memory(
                user_id=user_id,
                content=content,
                meta=meta,
            )
            session.add(memory)
            await session.commit()
            await session.refresh(memory)
            return memory
    
    async def get_recent(self, user_id: str, limit: int = 10) -> List[Memory]:
        """获取最近记忆"""
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Memory)
                .where(Memory.user_id == user_id)
                .order_by(Memory.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
    
    async def get_all(self, user_id: str) -> List[Memory]:
        """获取所有记忆"""
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Memory)
                .where(Memory.user_id == user_id)
                .order_by(Memory.created_at.desc())
            )
            return list(result.scalars().all())
    
    async def clear(self, user_id: str):
        """清空记忆"""
        async with self.async_session() as session:
            from sqlalchemy import delete
            await session.execute(
                delete(Memory).where(Memory.user_id == user_id)
            )
            await session.commit()
    
    async def create_precheck_job(self, job_id: str, user_id: str, title: str, content_type: str = "video", callback_url: Optional[str] = None) -> PrecheckJob:
        """创建内容预审任务"""
        async with self.async_session() as session:
            job = PrecheckJob(
                job_id=job_id,
                user_id=user_id,
                title=title,
                content_type=content_type,
                status="pending",
                callback_url=callback_url,
            )
            session.add(job)
            await session.commit()
            await session.refresh(job)
            return job
    
    async def get_precheck_job(self, job_id: str) -> Optional[PrecheckJob]:
        """获取预审任务"""
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(PrecheckJob).where(PrecheckJob.job_id == job_id)
            )
            return result.scalar_one_or_none()
    
    async def list_precheck_jobs(self, user_id: str, limit: int = 20) -> List[PrecheckJob]:
        """获取用户预审任务列表"""
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(PrecheckJob)
                .where(PrecheckJob.user_id == user_id)
                .order_by(PrecheckJob.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
    
    async def update_precheck_job(self, job_id: str, **kwargs) -> Optional[PrecheckJob]:
        """更新预审任务"""
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(PrecheckJob).where(PrecheckJob.job_id == job_id)
            )
            job = result.scalar_one_or_none()
            if not job:
                return None
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            await session.commit()
            await session.refresh(job)
            return job
