# AI Agent Platform

WorkflowとSkillsを組み合わせてタスクを実行するAIエージェントプラットフォーム。
YAMLで定義されたグラフ構造（DAG）に基づいて、LLMと各種ツール（Skill）を連携させて動作します。

## コンセプト

*   **Workflow Definition (YAML)**: エージェントの振る舞い（思考・行動の順序）をYAMLファイルで宣言的に定義。
*   **Graph Engine**: 定義されたワークフローを解釈し、分岐やデータの受け渡しを制御して実行。
*   **Skills**: ワークフローから呼び出される具体的な機能モジュール（検索、ファイル操作、計算など）。

## ディレクトリ構成

*   `workflows/`: ワークフロー定義ファイル (.yaml)
*   `src/ai_agent_work_base/`
    *   `engine/`: ワークフロー実行エンジン (Executor, Loader, Context)
    *   `skills/`: スキル実装 (WebSearch, FileOps, Presentation etc.)
    *   `schemas/`: データスキーマ (Pydantic)
    *   `app.py`: Chainlit Web UI
    *   `cli.py`: CLI Entrypoint

## セットアップ

### 必要条件
*   Python 3.12+
*   uv (推奨)
*   OpenAI API Key

### インストール
```bash
uv sync
```

### 環境変数
`.env` ファイルを作成し、APIキーを設定してください。
```bash
cp .env.example .env
# OPENAI_API_KEY=sk-...
```

## 実行方法

### Web UI (Chainlit)
ブラウザ上でワークフローを選択し、対話的に実行できます。
```bash
uv run chainlit run src/ai_agent_work_base/app.py -w
```
アクセス: `http://localhost:8000`

### CLI
ターミナル上でワークフローを選択・実行できます。
```bash
uv run python -m ai_agent_work_base.cli
```

## 利用可能なワークフロー例
`workflows/` ディレクトリにYAMLファイルを追加することで拡張可能です。

*   **Deep Research**: 指定トピックについて検索計画→実行→レポート作成を行います。
*   **Presentation Generator**: 指定トピックの構成案作成→Marp形式スライドMarkdownの生成を行います。

## Dockerでの実行

```bash
docker build -t ai-agent-platform .
docker run -p 8000:8000 --env-file .env ai-agent-platform
```
