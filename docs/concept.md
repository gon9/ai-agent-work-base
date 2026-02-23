# AI Agent Platform 構想 (Revised)

## 1. コンセプト: Workflow & Skills
「エージェント」という曖昧な存在を作るのではなく、**「Workflow（処理の流れ）」** と **「Skills（具体的な道具）」** を分離・構造化して管理するプラットフォームを目指す。

*   **Workflow**: タスクを達成するための手順書。グラフ構造（DAG）を持ち、YAMLで記述可能。
*   **Skills**: ワークフローから呼び出される具体的な機能（Web検索、ファイル操作、スライド生成など）。

これらを組み合わせることで、「Deep Research」や「プレゼン作成」といった目的別のエージェント的振る舞いを実現する。

## 2. アーキテクチャ

### 2.1 Workflow Engine (Core)
YAMLで定義されたグラフ構造を読み込み、実行するエンジン。
*   **YAML Definition**: 処理の流れ、分岐、並列実行などを記述。
*   **Graph Execution**: ノード間のデータの受け渡し、依存関係の解決を行う。
*   **Nodes**:
    *   **LLM Node**: プロンプトに基づいてLLMを実行・判断する。
    *   **Skill Node**: 特定のSkillを実行する。
    *   **Control Flow**: 分岐 (If/Switch)、ループなど。

### 2.2 Skills Layer
具体的な機能を提供するモジュール群。
*   **Research Skills**: Web検索, URLコンテンツ取得, 論文検索
*   **Office Skills**: PowerPoint生成, Excel操作
*   **System Skills**: ファイル読み書き, コマンド実行

### 2.3 User Interface
*   **Chat UI**: 実行トリガーおよび途中経過・結果の確認（Chainlit等）。
*   **Editor (Future)**: ワークフローの可視化・編集（まずはYAML直接編集からスタート）。

## 3. ワークフロー定義 (YAMLイメージ)
Dify等を参考に、宣言的にフローを定義する。

```yaml
name: "Deep Research"
description: "多角的な調査を行いレポートにまとめる"
inputs:
  - name: "topic"
    type: "string"

nodes:
  - id: "plan_research"
    type: "llm"
    prompt: |
      トピック「{{inputs.topic}}」について調査計画を立ててください。
      必要な検索キーワードをリストアップしてください。
    next: "execute_search"

  - id: "execute_search"
    type: "skill"
    skill: "google_search"
    params:
      queries: "{{plan_research.output.queries}}"
    next: "summarize"

  - id: "summarize"
    type: "llm"
    prompt: |
      以下の検索結果を元にレポートを作成してください。
      {{execute_search.output}}
    next: "end"
```

## 4. 目標ユースケース
1.  **Deep Research Agent**
    *   ユーザーのテーマ入力 -> 検索計画 -> 複数回検索 -> 情報統合 -> レポート作成
2.  **Presentation Generator**
    *   テーマ入力 -> 構成案作成 -> 各スライドの文章生成 -> Python/Marp等でスライドファイル生成

## 5. 技術スタック
*   **Language**: Python 3.12+
*   **Core**: Graph実行ロジック (自作 or LangGraph等の薄いラッパー)
*   **UI**: Chainlit
*   **Env**: Docker, uv
