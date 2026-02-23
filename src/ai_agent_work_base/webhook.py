"""
Webhook サーバー

外部イベント（フォーム送信・メール転送・GitHub Actions等）を受け取り、
指定されたワークフローを自動起動するFastAPIサーバー。

起動方法:
    uv run uvicorn ai_agent_work_base.webhook:app --reload --port 8001
"""
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Header
from pydantic import BaseModel, Field

from .core.llm import LLMClient
from .engine.executor import GraphExecutor
from .engine.loader import WorkflowLoader
from .skills import load_all_skills

load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Agent Webhook Server",
    description="外部イベントでワークフローを自動起動するWebhookサーバー",
    version="0.1.0",
)

WORKFLOW_DIR = Path("workflows")


# -----------------------------------------------------------------------
# リクエスト / レスポンス スキーマ
# -----------------------------------------------------------------------

class WebhookRequest(BaseModel):
    """Webhookリクエストのスキーマ"""
    workflow: str = Field(..., description="実行するワークフロー名またはYAMLファイル名（拡張子なし可）")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="ワークフローへの入力パラメータ")
    async_run: bool = Field(default=True, description="Trueの場合はバックグラウンドで実行し即座に202を返す")


class WebhookResponse(BaseModel):
    """Webhookレスポンスのスキーマ"""
    status: str
    workflow: str
    message: str
    result: Optional[Dict[str, Any]] = None


class WorkflowResult(BaseModel):
    """ワークフロー実行結果のスキーマ"""
    workflow: str
    outputs: Dict[str, Any]


# -----------------------------------------------------------------------
# ヘルパー
# -----------------------------------------------------------------------

def _resolve_workflow_path(workflow_name: str) -> Path:
    """ワークフロー名からYAMLファイルパスを解決する。"""
    candidates = [
        WORKFLOW_DIR / workflow_name,
        WORKFLOW_DIR / f"{workflow_name}.yaml",
        WORKFLOW_DIR / f"{workflow_name}.yml",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise HTTPException(
        status_code=404,
        detail=f"ワークフロー '{workflow_name}' が見つかりません。workflows/ ディレクトリを確認してください。"
    )


def _run_workflow(workflow_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """ワークフローを同期実行して結果を返す。"""
    path = _resolve_workflow_path(workflow_name)
    workflow = WorkflowLoader.load(path)
    llm = LLMClient()
    skills = load_all_skills()

    def on_start(node):
        logger.info(f"[{workflow_name}] → [{node.type}] {node.id}")

    def on_end(node, output):
        preview = str(output)[:100].replace("\n", " ")
        logger.info(f"[{workflow_name}] ✓ {node.id}: {preview}")

    executor = GraphExecutor(workflow, skills, llm, on_node_start=on_start, on_node_end=on_end)
    return executor.execute(inputs)


# -----------------------------------------------------------------------
# エンドポイント
# -----------------------------------------------------------------------

@app.get("/health")
async def health():
    """ヘルスチェック"""
    return {"status": "ok"}


@app.get("/workflows")
async def list_workflows():
    """利用可能なワークフロー一覧を返す"""
    result = []
    for path in sorted(WORKFLOW_DIR.glob("*.yaml")):
        try:
            wf = WorkflowLoader.load(path)
            result.append({
                "name": wf.name,
                "file": path.name,
                "description": wf.description or "",
                "inputs": [
                    {"name": i.name, "type": i.type, "description": i.description or ""}
                    for i in (wf.inputs or [])
                ],
            })
        except Exception as e:
            logger.warning(f"ワークフロー読み込みエラー {path}: {e}")
    return {"workflows": result}


@app.post("/webhook", response_model=WebhookResponse, status_code=202)
async def trigger_workflow(
    req: WebhookRequest,
    background_tasks: BackgroundTasks,
    x_webhook_secret: Optional[str] = Header(default=None),
):
    """
    外部イベントを受け取りワークフローを起動する。

    - `async_run=true`（デフォルト）: バックグラウンドで実行し即座に202を返す
    - `async_run=false`: 実行完了まで待機して結果を返す（同期実行）
    """
    # ワークフローの存在確認（404を早期に返すため）
    _resolve_workflow_path(req.workflow)

    if req.async_run:
        background_tasks.add_task(_run_workflow, req.workflow, req.inputs)
        return WebhookResponse(
            status="accepted",
            workflow=req.workflow,
            message=f"ワークフロー '{req.workflow}' をバックグラウンドで起動しました。",
        )
    else:
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, _run_workflow, req.workflow, req.inputs
            )
            return WebhookResponse(
                status="completed",
                workflow=req.workflow,
                message=f"ワークフロー '{req.workflow}' が完了しました。",
                result=result,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook/inquiry", response_model=WebhookResponse, status_code=202)
async def trigger_inquiry(
    body: Dict[str, Any],
    background_tasks: BackgroundTasks,
):
    """
    問い合わせフォームからのWebhookを受け取り、inquiry_responseワークフローを起動する。

    期待するbody:
        {
            "sender": "yamada@example.com",
            "inquiry": "問い合わせ本文",
            "channel": "#support"  // 省略可
        }
    """
    sender = body.get("sender", "")
    inquiry = body.get("inquiry", "")
    if not inquiry:
        raise HTTPException(status_code=422, detail="'inquiry' フィールドが必要です。")

    inputs = {
        "sender": sender,
        "inquiry": inquiry,
        "channel": body.get("channel", ""),
    }
    background_tasks.add_task(_run_workflow, "inquiry_response", inputs)
    return WebhookResponse(
        status="accepted",
        workflow="inquiry_response",
        message=f"問い合わせを受け付けました。送信者: {sender}",
    )
