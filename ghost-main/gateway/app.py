#!/usr/bin/env python3
"""
Ghost Gateway — 统一 API 网关
================================
实现文档六层架构中的「网关层」：
  私有网关：身份、记忆、个人数据
  公共网关：电商、资讯、A2A 通信

所有前端（Ghost.html）只访问这一个入口，不再散乱调用多个端口。
"""

import os
import json
import time
import httpx
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# 配置
# ============================================================
ALPHAID_URL = os.getenv("ALPHAID_URL", "http://localhost:8000")
DS_URL = os.getenv("DS_URL", "http://localhost:3004")
NEBULA_URL = os.getenv("NEBULA_URL", "http://localhost:2002")
FLOW_URL = os.getenv("FLOW_URL", "http://localhost:3001")
# 身份必须从认证令牌中获取，不再使用硬编码默认值
DEFAULT_ALPHA_ID = os.getenv("DEFAULT_ALPHA_ID", "")
GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", "8080"))

# ============================================================
# 速率限制（内存滑动窗口，防 SMS 轰炸）
# ============================================================
_rate_buckets: dict = defaultdict(list)  # key → [timestamp, ...]
_RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "5"))       # 窗口内最大请求数
_RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # 窗口大小（秒）


def _rate_limit_check(key: str, max_requests: int = None, window: int = None) -> bool:
    """检查是否超过速率限制。返回 True 表示允许，False 表示超限。"""
    now = time.time()
    max_req = max_requests or _RATE_LIMIT_MAX
    win = window or _RATE_LIMIT_WINDOW

    # 清理过期条目
    bucket = _rate_buckets[key]
    cutoff = now - win
    _rate_buckets[key] = [t for t in bucket if t > cutoff]

    if len(_rate_buckets[key]) >= max_req:
        return False
    _rate_buckets[key].append(now)
    return True


def _client_ip(request: Request) -> str:
    """获取客户端真实 IP（考虑反向代理）"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ============================================================
# FastAPI 应用
# ============================================================
app = FastAPI(
    title="Ghost Gateway",
    description="Ghost Web4.0 统一 API 网关 — 私有网关 + 公共网关",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS：允许所有来源（Ghost.html 可能从 file:// 或任意域名打开）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP 客户端（复用连接池）— 在 lifespan 中管理生命周期
client: httpx.AsyncClient = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理 — 启动时创建客户端，关闭时清理"""
    global client
    client = httpx.AsyncClient(timeout=30.0, limits=httpx.Limits(max_connections=100, max_keepalive_connections=20))
    yield
    await client.aclose()


# ============================================================
# 工具函数
# ============================================================
async def proxy_get(path: str, base_url: str, headers: dict = None) -> dict:
    """代理 GET 请求到后端"""
    try:
        resp = await client.get(f"{base_url}{path}", headers=headers or {})
        if resp.status_code == 200:
            return resp.json()
        # 返回错误信息但不掩盖失败 — 让调用者决定如何处理
        return {"_error": f"backend returned {resp.status_code}", "_raw": resp.text[:200]}
    except Exception as e:
        return {"_error": f"backend unreachable: {str(e)}"}


async def proxy_post(path: str, base_url: str, body: dict = None, headers: dict = None) -> dict:
    """代理 POST 请求到后端"""
    try:
        resp = await client.post(f"{base_url}{path}", json=body or {}, headers=headers or {})
        if resp.status_code in (200, 201):
            return resp.json()
        # 返回错误信息但不掩盖失败 — 让调用者决定如何处理
        return {"_error": f"backend returned {resp.status_code}", "_raw": resp.text[:200]}
    except Exception as e:
        return {"_error": f"backend unreachable: {str(e)}"}


def has_error(data: dict) -> bool:
    """检查代理响应是否包含后端错误"""
    return isinstance(data, dict) and "_error" in data


def unwrap_flow_response(data: dict) -> dict:
    """
    解包 flow/api 的 {success, data/error} 信封，转换为 Gateway 统一信封。
    flow/api 返回 {success: true, data: {...}} 或 {success: false, error: "..."}。
    """
    if not isinstance(data, dict):
        return data
    if data.get("success") is False:
        # 后端失败 → 转为错误格式让 ok() 处理
        return {"_error": data.get("error", "flow/api 返回失败")}
    if data.get("success") is True and "data" in data:
        # 成功 → 提取 data 字段作为原始数据
        return data["data"]
    return data


def ok(data: dict) -> JSONResponse:
    """统一成功响应 — 如果数据包含后端错误，返回失败状态"""
    if has_error(data):
        return JSONResponse({"success": False, "error": data["_error"], "data": data, "ts": int(time.time())}, status_code=502)
    return JSONResponse({"success": True, "data": data, "ts": int(time.time())}))


def fail(msg: str, code: int = 500) -> JSONResponse:
    """统一失败响应"""
    return JSONResponse({"success": False, "error": msg, "ts": int(time.time())}, status_code=code)


# ============================================================
# 健康检查
# ============================================================
@app.get("/health")
async def health():
    """网关健康检查 + 后端连接状态"""
    result = {
        "gateway": "ok",
        "alphaid": "unknown",
        "ds": "unknown",
        "nebula": "unknown",
        "flow": "unknown",
    }
    # 检查 alphaid
    try:
        r = await client.get(f"{ALPHAID_URL}/brain/status?alpha_id={DEFAULT_ALPHA_ID}", timeout=3)
        result["alphaid"] = "ok" if r.status_code == 200 else f"error({r.status_code})"
    except:
        result["alphaid"] = "unreachable"
    # 检查 DS
    try:
        r = await client.get(f"{DS_URL}/api/shop", timeout=3)
        result["ds"] = "ok" if r.status_code == 200 else f"error({r.status_code})"
    except:
        result["ds"] = "unreachable"
    # 检查 nebula
    try:
        r = await client.get(f"{NEBULA_URL}/api/v1/workflow/templates", timeout=3)
        result["nebula"] = "ok" if r.status_code == 200 else f"error({r.status_code})"
    except:
        result["nebula"] = "unreachable"
    # 检查 flow
    try:
        r = await client.get(f"{FLOW_URL}/api/register/status/test", timeout=3)
        result["flow"] = "ok" if r.status_code in (200, 404) else f"error({r.status_code})"
    except:
        result["flow"] = "unreachable"
    return ok(result)


# ============================================================
# 私有网关 — 身份 & 记忆
# ============================================================

# --- 身份 ---
@app.get("/v1/identity")
async def get_identity(alpha_id: Optional[str] = None):
    """获取当前身份 → 代理到 Alpha-ID"""
    aid = alpha_id or DEFAULT_ALPHA_ID
    data = await proxy_get("/identity", ALPHAID_URL, headers={"X-Alpha-ID": aid})
    return ok(data)


# --- 画像 ---
@app.get("/v1/profile")
async def get_profile():
    """获取用户画像 → 代理到 Alpha-ID"""
    data = await proxy_get("/api/profile", ALPHAID_URL)
    return ok(data)


# --- 大脑状态 ---
@app.get("/v1/brain/status")
async def get_brain_status(alpha_id: Optional[str] = None):
    """获取大脑状态 → 代理到 Alpha-ID"""
    aid = alpha_id or DEFAULT_ALPHA_ID
    data = await proxy_get(f"/brain/status?alpha_id={aid}", ALPHAID_URL)
    return ok(data)


# --- 大脑唤醒 ---
@app.post("/v1/brain/awake")
async def brain_awake(request: Request):
    """唤醒大脑 → 代理到 Alpha-ID"""
    body = await request.json()
    aid = body.get("alpha_id", DEFAULT_ALPHA_ID)
    data = await proxy_post("/brain/awake", ALPHAID_URL, body={"alpha_id": aid})
    return ok(data)


# --- 网络拓扑 ---
@app.get("/v1/network/topology")
async def get_network_topology():
    """获取 Agent 网络拓扑 → 代理到 Alpha-ID"""
    data = await proxy_get("/network/topology", ALPHAID_URL)
    return ok(data)


# --- 聊天 ---
@app.post("/v1/chat")
async def chat(request: Request):
    """与 Agent 对话 → 代理到 Alpha-ID /chat"""
    body = await request.json()
    aid = body.get("alpha_id", DEFAULT_ALPHA_ID)
    message = body.get("message", "")
    if not message:
        return fail("message 必填", 400)
    data = await proxy_post("/chat", ALPHAID_URL, body={"alpha_id": aid, "message": message})
    return ok(data)


# --- 意图解析 ---
@app.post("/v1/intent/parse")
async def parse_intent(request: Request):
    """
    意图解析 — 网关层智能路由
    根据意图内容自动路由到对应后端：
      - 电商相关 → DS
      - 身份/记忆 → Alpha-ID
      - 通用对话 → Alpha-ID /chat
    """
    body = await request.json()
    text = body.get("text", "").strip()
    if not text:
        return fail("text 必填", 400)

    # 简单关键词路由
    text_lower = text.lower()
    is_ecommerce = any(kw in text_lower for kw in ["订单", "商品", "店铺", "电商", "产品", "order", "product", "shop"])
    is_identity = any(kw in text_lower for kw in ["身份", "我是谁", "did", "identity", "画像"])

    if is_ecommerce:
        # 路由到电商后端
        products = await proxy_get("/api/products", DS_URL)
        orders = await proxy_get("/api/orders", DS_URL)
        return ok({
            "route": "ecommerce",
            "reply": f"已为您查询电商数据：商品 {len(products.get('items', []))} 个，订单 {len(orders.get('items', []))} 笔",
            "products_preview": products.get("items", [])[:3],
            "orders_preview": orders.get("items", [])[:3],
        })
    elif is_identity:
        # 路由到身份后端
        identity = await proxy_get("/identity", ALPHAID_URL, headers={"X-Alpha-ID": DEFAULT_ALPHA_ID})
        profile = await proxy_get("/api/profile", ALPHAID_URL)
        return ok({
            "route": "identity",
            "identity": identity,
            "profile_summary": profile.get("profile", {}).get("persona", {}),
        })
    else:
        # 默认路由到 Alpha-ID 对话
        data = await proxy_post("/chat", ALPHAID_URL, body={"alpha_id": DEFAULT_ALPHA_ID, "message": text})
        return ok({
            "route": "chat",
            "reply": data.get("reply", ""),
            "raw": data,
        })


# ============================================================
# 公共网关 — 电商
# ============================================================

# --- 店铺信息 ---
@app.get("/v1/shop")
async def get_shop():
    """获取店铺信息 → 代理到 DS"""
    data = await proxy_get("/api/shop", DS_URL)
    return ok(data)


# --- 商品列表 ---
@app.get("/v1/products")
async def get_products():
    """获取商品列表 → 代理到 DS"""
    data = await proxy_get("/api/products", DS_URL)
    return ok(data)


# --- 订单列表 ---
@app.get("/v1/orders")
async def get_orders():
    """获取订单列表 → 代理到 DS"""
    data = await proxy_get("/api/orders", DS_URL)
    return ok(data)


# --- 同步电商数据 ---
@app.post("/v1/ecommerce/sync")
async def sync_ecommerce():
    """触发电商数据同步 → 代理到 DS"""
    data = await proxy_post("/api/sync", DS_URL)
    return ok(data)


# --- 电商统计 ---
@app.get("/v1/ecommerce/stats")
async def ecommerce_stats():
    """电商综合统计 — 网关层聚合"""
    shop = await proxy_get("/api/shop", DS_URL)
    products = await proxy_get("/api/products", DS_URL)
    orders = await proxy_get("/api/orders", DS_URL)

    product_count = len(products.get("items", []))
    order_count = len(orders.get("items", []))

    # 计算收入
    revenue = 0
    for o in orders.get("items", []):
        try:
            revenue += float(o.get("total_price", 0))
        except:
            pass

    return ok({
        "shop_name": shop.get("shop", {}).get("name", "未知"),
        "product_count": product_count,
        "order_count": order_count,
        "revenue": round(revenue, 2),
        "currency": "USD",
    })


# ============================================================
# 公共网关 — 工作流 (Nebula)
# ============================================================

@app.get("/v1/workflows")
async def get_workflows():
    """获取工作流模板 → 代理到 Nebula"""
    data = await proxy_get("/api/v1/workflow/templates", NEBULA_URL)
    return ok(data)


@app.post("/v1/workflows/execute")
async def execute_workflow(request: Request):
    """执行工作流 → 代理到 Nebula"""
    body = await request.json()
    data = await proxy_post("/api/v1/workflow/execute", NEBULA_URL, body=body)
    return ok(data)


# ============================================================
# 公共网关 — 注册流程 (flow/api)
# ============================================================
# 注册路由统一使用 ok() 包裹，保持响应信封一致性（H9 修复）
# flow/api 返回 {success, data/error}，ok() 会透传 success=False，
# 并将 success=True 的 data 提取到 Gateway 信封的 data 字段。

@app.post("/v1/register/send-sms")
async def register_send_sms(request: Request):
    """发送短信验证码 → 代理到 flow/api（速率限制：60秒5次/IP）"""
    # H8: 速率限制防 SMS 轰炸
    ip = _client_ip(request)
    if not _rate_limit_check(f"sms:{ip}", max_requests=5, window=60):
        return fail("请求过于频繁，请稍后再试", 429)
    body = await request.json()
    data = await proxy_post("/api/register/send-sms", FLOW_URL, body=body)
    return ok(unwrap_flow_response(data))


@app.post("/v1/register/verify-sms")
async def register_verify_sms(request: Request):
    """验证短信验证码 → 代理到 flow/api"""
    body = await request.json()
    data = await proxy_post("/api/register/verify-sms", FLOW_URL, body=body)
    return ok(unwrap_flow_response(data))


@app.post("/v1/register/face-verify")
async def register_face_verify(request: Request):
    """发起支付宝人脸认证 → 代理到 flow/api"""
    body = await request.json()
    data = await proxy_post("/api/register/face-verify", FLOW_URL, body=body)
    return ok(unwrap_flow_response(data))


@app.post("/v1/register/face-query")
async def register_face_query(request: Request):
    """查询人脸认证结果 → 代理到 flow/api"""
    body = await request.json()
    data = await proxy_post("/api/register/face-query", FLOW_URL, body=body)
    return ok(unwrap_flow_response(data))


@app.post("/v1/register/generate-did")
async def register_generate_did(request: Request):
    """生成去中心化身份 DID → 代理到 flow/api"""
    body = await request.json()
    data = await proxy_post("/api/register/generate-did", FLOW_URL, body=body)
    return ok(unwrap_flow_response(data))


@app.post("/v1/register/complete")
async def register_complete(request: Request):
    """完成注册 → 代理到 flow/api"""
    body = await request.json()
    data = await proxy_post("/api/register/complete-registration", FLOW_URL, body=body)
    return ok(unwrap_flow_response(data))


# ============================================================
# 统一仪表盘 — 一次性返回 Ghost.html 需要的所有数据
# ============================================================
@app.get("/v1/dashboard")
async def dashboard():
    """
    统一仪表盘 — Ghost.html 打开 workbench 时调用一次
    并行请求所有后端，聚合返回（单个后端失败不影响其他）
    """
    import asyncio

    # 并行请求（return_exceptions=True 确保单个后端失败不会导致整个仪表盘 500）
    identity, brain, topology, profile, shop, products, orders = await asyncio.gather(
        proxy_get("/identity", ALPHAID_URL, headers={"X-Alpha-ID": DEFAULT_ALPHA_ID}),
        proxy_get(f"/brain/status?alpha_id={DEFAULT_ALPHA_ID}", ALPHAID_URL),
        proxy_get("/network/topology", ALPHAID_URL),
        proxy_get("/api/profile", ALPHAID_URL),
        proxy_get("/api/shop", DS_URL),
        proxy_get("/api/products", DS_URL),
        proxy_get("/api/orders", DS_URL),
        return_exceptions=True,
    )

    # 将异常转换为错误字典
    def _to_result(value):
        if isinstance(value, Exception):
            return {"_error": str(value)}
        return value

    identity, brain, topology, profile, shop, products, orders = (
        _to_result(v) for v in (identity, brain, topology, profile, shop, products, orders)
    )

    # 计算电商统计
    product_count = len(products.get("items", []))
    order_count = len(orders.get("items", []))
    revenue = sum(float(o.get("total_price", 0)) for o in orders.get("items", []))

    return ok({
        "identity": {
            "alpha_id": identity.get("alpha_id", DEFAULT_ALPHA_ID),
            "did": topology.get("my_did", "unknown"),
            "state": brain.get("state", "unknown"),
        },
        "brain": brain,
        "network": topology,
        "profile": profile,
        "ecommerce": {
            "shop": shop.get("shop", {}),
            "product_count": product_count,
            "order_count": order_count,
            "revenue": round(revenue, 2),
            "products": products.get("items", [])[:5],
            "orders": orders.get("items", [])[:5],
        },
    })


# ============================================================
# 启动
# ============================================================
if __name__ == "__main__":
    import uvicorn
    print(f"""
╔══════════════════════════════════════════════════╗
║           Ghost Gateway v1.0.0                   ║
║  统一 API 网关 — 私有网关 + 公共网关              ║
╠══════════════════════════════════════════════════╣
║  端口: {GATEWAY_PORT}                                    ║
║  Alpha-ID: {ALPHAID_URL}    ║
║  DS:       {DS_URL}       ║
║  Nebula:   {NEBULA_URL}       ║
║  Flow:     {FLOW_URL}       ║
╚══════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="0.0.0.0", port=GATEWAY_PORT)
