"""工作流 API"""

from fastapi import APIRouter
from pydantic import BaseModel

from mindflow_map.workflows.engine import WorkflowEngine

router = APIRouter()
# workflow_engine 由 main.py lifespan 注入，此处不预先实例化


class WorkflowExecuteRequest(BaseModel):
    text: str
    user_id: str = "default"


class WorkflowExecuteResponse(BaseModel):
    success: bool
    result: dict
    workflow_id: str


@router.post("/execute", response_model=WorkflowExecuteResponse)
async def execute_workflow(request: WorkflowExecuteRequest):
    """执行工作流"""
    try:
        result = await workflow_engine.execute(request.text, user_id=request.user_id)
        return WorkflowExecuteResponse(
            success=True,
            result=result,
            workflow_id="workflow-001",
        )
    except Exception as e:
        return WorkflowExecuteResponse(
            success=False,
            result={"error": str(e)},
            workflow_id="workflow-001",
        )


@router.get("/templates")
async def list_workflows():
    """列出可用工作流模板"""
    return {
        "templates": [
            {
                "id": "map-navigation",
                "name": "智能导航",
                "description": "地点搜索 + 路线规划 + 时间推荐",
                "examples": ["怎么去中关村", "明天去故宫怎么走", "查一下附近的咖啡厅"],
            },
            {
                "id": "douyin-publish",
                "name": "短剧自动发布",
                "description": "AI生成剧本 + 自动发布到抖音",
                "examples": ["帮我发一个短剧", "生成一个霸道总裁剧本"],
            },
            {
                "id": "shopify-optimize",
                "name": "电商优化",
                "description": "Shopify店铺自动运营",
                "examples": ["优化我的店铺", "生成商品文案"],
            },
        ]
    }
