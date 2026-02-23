"""SlackNotifySkillのユニットテスト（正常系・異常系）"""
import pytest
from unittest.mock import patch, MagicMock
from ai_agent_work_base.skills.slack import SlackNotifySkill


# -----------------------------------------------------------------------
# 正常系
# -----------------------------------------------------------------------

def test_slack_notify_success():
    """Webhook URLが設定されていてPOSTが成功する場合"""
    skill = SlackNotifySkill()
    skill._webhook_url = "https://hooks.slack.com/services/test"

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = b"ok"
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = skill.execute(message="テストメッセージ")

    assert "完了" in result


def test_slack_notify_with_title():
    """タイトル付きで送信できる"""
    skill = SlackNotifySkill()
    skill._webhook_url = "https://hooks.slack.com/services/test"

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = b"ok"
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
        result = skill.execute(message="本文", title="タイトル")

    assert "タイトル" in result

    # payloadにheaderブロックが含まれているか確認
    import json
    call_args = mock_open.call_args
    req = call_args[0][0]
    payload = json.loads(req.data.decode("utf-8"))
    block_types = [b["type"] for b in payload["blocks"]]
    assert "header" in block_types


def test_slack_notify_with_channel():
    """チャンネル指定が正しくpayloadに含まれる"""
    skill = SlackNotifySkill()
    skill._webhook_url = "https://hooks.slack.com/services/test"

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = b"ok"
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
        skill.execute(message="本文", channel="#general")

    import json
    req = mock_open.call_args[0][0]
    payload = json.loads(req.data.decode("utf-8"))
    assert payload.get("channel") == "#general"


# -----------------------------------------------------------------------
# 異常系
# -----------------------------------------------------------------------

def test_slack_notify_no_webhook_url():
    """SLACK_WEBHOOK_URLが未設定の場合はRuntimeErrorを送出する"""
    skill = SlackNotifySkill()
    skill._webhook_url = None

    with pytest.raises(RuntimeError, match="SLACK_WEBHOOK_URL"):
        skill.execute(message="テスト")


def test_slack_notify_api_error():
    """Slack APIがエラーを返した場合はRuntimeErrorを送出する"""
    skill = SlackNotifySkill()
    skill._webhook_url = "https://hooks.slack.com/services/test"

    mock_resp = MagicMock()
    mock_resp.status = 400
    mock_resp.read.return_value = b"invalid_payload"
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        with pytest.raises(RuntimeError, match="Slack送信に失敗"):
            skill.execute(message="テスト")


def test_slack_skill_name():
    """スキル名が正しく返される"""
    skill = SlackNotifySkill()
    assert skill.name == "slack_notify"


def test_slack_skill_parameters():
    """parametersにmessageが必須として含まれる"""
    skill = SlackNotifySkill()
    params = skill.parameters
    assert "message" in params["properties"]
    assert "message" in params["required"]
