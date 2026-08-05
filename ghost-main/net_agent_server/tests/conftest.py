"""
Net-Agent Server 测试引导
==========================
- 设置安全配置环境变量（settings 在 import 时读取，必须最先设置）
- 将 ghost-main/ 与 net_agent_server/ 加入 sys.path（与 main.py 一致）
"""

import os
import sys
from pathlib import Path

# ── 安全配置必须在 import net_agent_common 之前设置 ──
os.environ.setdefault("NET_AGENT_JWT_SECRET", "test-secret-" + "x" * 40)
os.environ.setdefault("NET_AGENT_AES_KEY", "test-aes-" + "y" * 40)

_HERE = Path(__file__).resolve().parent          # net_agent_server/tests/
_SERVER = _HERE.parent                           # net_agent_server/
_GHOST_MAIN = _SERVER.parent                     # ghost-main/
for p in (str(_GHOST_MAIN), str(_SERVER)):
    if p not in sys.path:
        sys.path.insert(0, p)
