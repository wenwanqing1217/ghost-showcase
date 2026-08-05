"""Gateway route modules."""

from routes.agent import router as agent_router
from routes.human import router as human_router
from routes.internal import router as internal_router
from routes.net import router as net_router
from routes.tools import router as tools_router

__all__ = ["agent_router", "human_router", "internal_router", "net_router", "tools_router"]
