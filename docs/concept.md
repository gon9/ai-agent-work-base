# AI Agent Platform 構想

## 1. プロジェクトの背景と目的
現在、複数のAIエージェントが散在しており、管理・運用が煩雑になっている。
本プロジェクトでは、これらを統合し、効率的に管理・実行できる単一のプラットフォームを構築することを目的とする。

## 2. アーキテクチャ概要
システムは主に以下の3つのレイヤーとユーザーインターフェースで構成される。

### 2.1 Core Components

1.  **Workflow & Orchestration Layer (頭脳)**
    *   AI（LLM）を活用してタスクを分解し、実行計画（ワークフロー）を構築する。
    *   動的なワークフローの制御、状態管理を行う。

2.  **Tool Execution Layer (手足の制御)**
    *   ワークフローからの指示を受け、適切なツールを選択・呼び出しを行う。
    *   ツールの実行結果を整形し、Workflow Layerへフィードバックする。

3.  **Tool Definitions (道具)**
    *   具体的な機能の実装（Web検索、ファイル操作、API連携など）。
    *   各ツールはモジュール化され、容易に追加・削除可能とする。

### 2.2 User Interface
*   **Chat UI**: ChatGPTライクな対話型インターフェース。
*   **音声入力**: OS（macOS等）の音声認識機能を利用するため、アプリ側では特別な実装を行わない。

## 3. 技術スタック
*   **Language**: Python 3.12+
*   **Package Manager**: uv
*   **Containerization**: Docker (Multi-stage build)
*   **Linter/Formatter**: ruff
*   **Testing**: pytest

## 4. 開発ロードマップ
1.  **構想整理 & ドキュメント化** (Current)
2.  **プロジェクトセットアップ**: `uv`, `git`, ディレクトリ構成の初期化
3.  **Core Backend 実装**:
    *   Tool定義のインターフェース設計
    *   Workflowエンジンのプロトタイプ実装
4.  **Frontend 実装**:
    *   CLIでの対話テスト
    *   Web/App UIの実装
5.  **Docker化 & 統合テスト**
