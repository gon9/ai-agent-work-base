"""Webhookサーバーのユニットテスト（正常系・異常系）"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from ai_agent_work_base.webhook import app

client = TestClient(app)


# -----------------------------------------------------------------------
# ヘルスチェック
# -----------------------------------------------------------------------

def test_health():
    """ヘルスチェックエンドポイントが200を返す"""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# -----------------------------------------------------------------------
# ワークフロー一覧
# -----------------------------------------------------------------------

def test_list_workflows():
    """ワークフロー一覧が取得できる"""
    resp = client.get("/workflows")
    assert resp.status_code == 200
    data = resp.json()
    assert "workflows" in data
    assert isinstance(data["workflows"], list)
    # deep_research と inquiry_response が含まれているはず
    names = [w["file"] for w in data["workflows"]]
    assert any("deep_research" in n for n in names)
    assert any("inquiry_response" in n for n in names)


# -----------------------------------------------------------------------
# /webhook 汎用エンドポイント（正常系）
# -----------------------------------------------------------------------

def test_webhook_async_accepted():
    """/webhook に async_run=true でPOSTすると202が返る"""
    with patch("ai_agent_work_base.webhook._run_workflow") as mock_run:
        mock_run.return_value = {}
        resp = client.post("/webhook", json={
            "workflow": "inquiry_response",
            "inputs": {"sender": "test@example.com", "inquiry": "テスト", "channel": ""},
            "async_run": True
        })
    assert resp.status_code == 202
    assert resp.json()["status"] == "accepted"


def test_webhook_sync_completed():
    """/webhook に async_run=false でPOSTすると完了結果が返る"""
    mock_result = {"summarize_inquiry": {"output": "要約"}, "generate_response": {"output": "返答"}}
    with patch("ai_agent_work_base.webhook._run_workflow", return_value=mock_result):
        resp = client.post("/webhook", json={
            "workflow": "inquiry_response",
            "inputs": {"sender": "test@example.com", "inquiry": "テスト", "channel": ""},
            "async_run": False
        })
    assert resp.status_code == 202
    assert resp.json()["status"] == "completed"
    assert resp.json()["result"] is not None


# -----------------------------------------------------------------------
# /webhook 汎用エンドポイント（異常系）
# -----------------------------------------------------------------------

def test_webhook_workflow_not_found():
    """存在しないワークフロー名を指定すると404が返る"""
    resp = client.post("/webhook", json={
        "workflow": "nonexistent_workflow",
        "inputs": {},
        "async_run": True
    })
    assert resp.status_code == 404


# -----------------------------------------------------------------------
# /webhook/inquiry 専用エンドポイント（正常系）
# -----------------------------------------------------------------------

def test_webhook_inquiry_accepted():
    """/webhook/inquiry に正しいbodyをPOSTすると202が返る"""
    with patch("ai_agent_work_base.webhook._run_workflow") as mock_run:
        mock_run.return_value = {}
        resp = client.post("/webhook/inquiry", json={
            "sender": "yamada@example.com",
            "inquiry": "料金について教えてください",
            "channel": "#support"
        })
    assert resp.status_code == 202
    assert resp.json()["status"] == "accepted"
    assert "yamada@example.com" in resp.json()["message"]


# -----------------------------------------------------------------------
# /webhook/inquiry 専用エンドポイント（異常系）
# -----------------------------------------------------------------------

def test_webhook_inquiry_missing_inquiry():
    """/webhook/inquiry に inquiry がない場合は422が返る"""
    resp = client.post("/webhook/inquiry", json={
        "sender": "yamada@example.com"
    })
    assert resp.status_code == 422


def test_webhook_inquiry_empty_inquiry():
    """/webhook/inquiry に inquiry が空文字の場合は422が返る"""
    resp = client.post("/webhook/inquiry", json={
        "sender": "yamada@example.com",
        "inquiry": ""
    })
    assert resp.status_code == 422
