import os
import chainlit as cl
from dotenv import load_dotenv
from ai_agent_work_base.core.llm import LLMClient
from ai_agent_work_base.planning.agent import PlanningAgent
from ai_agent_work_base.tools.basic_tools import EchoTool, ReverseTool
from ai_agent_work_base.tools.file_tools import FileWriteTool, FileReadTool
from ai_agent_work_base.tools.math_tools import CalculatorTool

# Load environment variables
load_dotenv()

def get_tools():
    """使用するツールを初期化して返す"""
    return [
        EchoTool(),
        ReverseTool(),
        FileWriteTool(),
        FileReadTool(),
        CalculatorTool(),
    ]

@cl.on_chat_start
async def start():
    """チャットセッション開始時の初期化"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        await cl.Message(content="Error: OPENAI_API_KEY is not set. Please check your .env file.").send()
        return

    try:
        # エージェントの初期化
        llm_client = LLMClient()
        tools = get_tools()
        agent = PlanningAgent(llm_client=llm_client, tools=tools)
        
        # セッションにエージェントを保存
        cl.user_session.set("agent", agent)
        
        await cl.Message(content="こんにちは！AIエージェントプラットフォームへようこそ。\nどのようなタスクをお手伝いしましょうか？").send()
    except Exception as e:
        await cl.Message(content=f"Initialization Error: {str(e)}").send()

@cl.on_message
async def main(message: cl.Message):
    """メッセージ受信時の処理"""
    agent = cl.user_session.get("agent")
    if not agent:
        await cl.Message(content="Agent not initialized. Please restart the session.").send()
        return

    # 非同期でエージェントを実行（同期関数をラップ）
    # make_asyncは関数をラップしてawaitableにする
    run_agent = cl.make_async(agent.run)
    
    msg = cl.Message(content="")
    await msg.send()
    
    try:
        # エージェント実行
        # 実行中であることを示すためにローディング表示が出ると良いが、
        # make_asyncでラップした場合の挙動による。
        # Chainlitはデフォルトで処理中はローディングインジケータが出る。
        
        response = await run_agent(message.content)
        
        msg.content = response
        await msg.update()
        
    except Exception as e:
        msg.content = f"Error: {str(e)}"
        await msg.update()
