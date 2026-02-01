# AI Agent Platform

AIエージェント機能を統合管理するプラットフォーム。
LLMを用いてユーザーの要求を分析し、適切なツールを選択してタスクを実行します。

## 特徴

*   **Planning Agent**: ユーザーの依頼をステップに分解し、計画的に実行します。
*   **Tool Usage**: ファイル操作、計算、文字列操作などのツールを利用可能。
*   **Chat UI**: Chainlitを使用したチャットインターフェース。
*   **CLI**: ターミナルから直接対話可能なCLIモード。

## 必要条件

*   Python 3.12+
*   Docker (推奨)
*   OpenAI API Key

## セットアップ

### ローカル開発環境

1.  依存関係のインストール (uvを使用)
    ```bash
    uv sync
    ```

2.  環境変数の設定
    `.env.example` を `.env` にコピーし、APIキーを設定してください。
    ```bash
    cp .env.example .env
    # .env を編集して OPENAI_API_KEY を設定
    ```

### 実行方法

#### Chat UI (推奨)
```bash
uv run chainlit run src/ai_agent_work_base/app.py -w
```
ブラウザで `http://localhost:8000` にアクセスしてください。

#### CLI
```bash
uv run python -m ai_agent_work_base
```

## Dockerでの実行

1.  イメージのビルド
    ```bash
    docker build -t ai-agent-platform .
    ```

2.  コンテナの実行
    ```bash
    docker run -p 8000:8000 --env-file .env ai-agent-platform
    ```

## 構成

*   `src/ai_agent_work_base/core`: エージェント、ツールの基底クラス
*   `src/ai_agent_work_base/tools`: 具体的なツールの実装
*   `src/ai_agent_work_base/planning`: 計画立案・実行エンジン
*   `src/ai_agent_work_base/app.py`: Chainlit UI エントリーポイント
*   `src/ai_agent_work_base/cli.py`: CLI エントリーポイント
