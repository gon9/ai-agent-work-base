import os
import glob
from pathlib import Path
from typing import Dict, Any
import chainlit as cl
from dotenv import load_dotenv

from ai_agent_work_base.core.llm import LLMClient
from ai_agent_work_base.engine.loader import WorkflowLoader
from ai_agent_work_base.engine.executor import GraphExecutor
from ai_agent_work_base.skills import load_all_skills
from ai_agent_work_base.schemas.workflow import NodeDefinition

# Load environment variables
load_dotenv()

# グローバル設定
WORKFLOW_DIR = Path("workflows")

def get_available_workflows():
    """workflowsディレクトリ内のYAMLファイルを取得"""
    files = list(WORKFLOW_DIR.glob("*.yaml")) + list(WORKFLOW_DIR.glob("*.yml"))
    workflows = []
    for f in files:
        try:
            wf = WorkflowLoader.load(f)
            workflows.append({"name": wf.name, "path": f, "obj": wf})
        except Exception as e:
            print(f"Error loading {f}: {e}")
    return workflows

@cl.on_chat_start
async def start():
    """セッション開始時にワークフロー選択を表示"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        await cl.Message(content="Error: OPENAI_API_KEY is not set.").send()
        return

    workflows = get_available_workflows()
    
    if not workflows:
        await cl.Message(content="ワークフローファイルが見つかりませんでした。workflows/ ディレクトリに .yaml ファイルを作成してください。").send()
        return

    actions = [
        cl.Action(name="select_workflow", value=str(w["path"]), label=w["name"], payload={"path": str(w["path"])})
        for w in workflows
    ]

    await cl.Message(
        content="実行したいワークフローを選択してください:",
        actions=actions
    ).send()

@cl.action_callback("select_workflow")
async def on_workflow_selected(action: cl.Action):
    """ワークフローが選択されたときの処理"""
    workflow_path = Path(action.payload["path"])
    try:
        workflow = WorkflowLoader.load(workflow_path)
    except Exception as e:
        await cl.Message(content=f"Error loading workflow: {e}").send()
        return

    # セッションに保存
    cl.user_session.set("current_workflow", workflow)
    
    # 既存のアクションを削除
    await action.remove()
    
    await cl.Message(content=f"**{workflow.name}** が選択されました。\n{workflow.description or ''}").send()

    # 入力の収集
    inputs = {}
    if workflow.inputs:
        for inp in workflow.inputs:
            res = await cl.AskUserMessage(content=f"**{inp.name}** を入力してください ({inp.description or ''}):", timeout=600).send()
            if res:
                inputs[inp.name] = res["output"]
            else:
                await cl.Message(content="入力がキャンセルされました。").send()
                return
    
    await execute_workflow(workflow, inputs)

async def execute_workflow(workflow, inputs):
    """ワークフローを実行する"""
    import asyncio
    llm_client = LLMClient()
    skills = load_all_skills()

    def sync_on_start(node: NodeDefinition):
        cl.run_sync(
            cl.Message(content=f"▶️ **Step: {node.id}** ({node.type}) executing...").send()
        )

    def sync_on_end(node: NodeDefinition, output: Any):
        out_str = str(output)
        if len(out_str) > 500:
            out_str = out_str[:500] + "..."
        cl.run_sync(
            cl.Message(content=f"✅ **Step: {node.id}** 完了\n```\n{out_str}\n```").send()
        )

    def run_sync():
        executor = GraphExecutor(
            workflow,
            skills,
            llm_client,
            on_node_start=sync_on_start,
            on_node_end=sync_on_end
        )
        return executor.execute(inputs)

    await cl.Message(content="🚀 ワークフローを実行します...").send()

    try:
        results = await asyncio.to_thread(run_sync)
        await cl.Message(content="🎉 ワークフローが完了しました！").send()

    except Exception as e:
        await cl.Message(content=f"❌ エラーが発生しました: {str(e)}").send()

    # 再実行ボタンなどを表示
    await cl.Message(
        content="次のタスクを実行しますか？",
        actions=[cl.Action(name="restart", value="restart", label="最初に戻る", payload={})]
    ).send()

@cl.action_callback("restart")
async def on_restart(action: cl.Action):
    await action.remove()
    await start()
