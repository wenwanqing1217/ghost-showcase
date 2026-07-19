"""记忆层 - 本地 SQLite 存储"""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Text, JSON


class Base(DeclarativeBase):
    pass


class Memory(Base):
    """记忆模型"""
    __tablename__ = "memories"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(100), index=True)
    content: Mapped[str] = mapped_column(Text)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class MemoryStore:
    """记忆存储"""
    
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def init(self):
        """初始化数据库"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def save(self, user_id: str, content: str, metadata: Optional[Dict] = None) -> Memory:
        """保存记忆"""
        async with self.async_session() as session:
            memory = Memory(
                user_id=user_id,
                content=content,
                metadata=metadata,
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
