# Workflow YAML 仕様書

YAMLファイルで定義されたワークフローは、`workflows/` ディレクトリに配置します。
エンジンがノードをグラフとして解釈し、順番に実行します。

---

## トップレベル構造

```yaml
name: "ワークフロー名"           # 必須: 表示名
description: "説明"             # 任意
inputs:                         # 任意: 外部から受け取る入力変数
  - name: "topic"
    type: "string"
    description: "調査するトピック"
nodes:                          # 必須: ノードのリスト（実行順に記述）
  - id: "first_node"
    ...
```

| フィールド    | 必須 | 説明 |
|-------------|------|------|
| `name`      | ✅   | UI・ログに表示されるワークフロー名 |
| `description` | -  | 説明文 |
| `inputs`    | -    | 外部から渡す変数の定義リスト |
| `nodes`     | ✅   | ノード定義のリスト |

---

## inputs

```yaml
inputs:
  - name: "topic"       # 必須: 変数名（テンプレート内で {{inputs.topic}} で参照）
    type: "string"      # 必須: string / integer / boolean
    description: "..."  # 任意
```

---

## ノード共通フィールド

```yaml
- id: "node_id"         # 必須: ユニークなID（英数字・アンダースコア）
  type: "llm"           # 必須: ノードタイプ（下記参照）
  name: "表示名"         # 任意
  next: "next_node_id"  # 任意: 次に実行するノードID。"end" で終了
```

---

## ノードタイプ

### 1. `llm` — LLMに問い合わせる

```yaml
- id: "summarize"
  type: "llm"
  model: "gpt-4o-mini"          # 任意: モデル名（省略時は環境変数 OPENAI_MODEL）
  output_format: "json"         # 任意: "text"（デフォルト）または "json"
  prompt: |
    {{inputs.topic}} について要約してください。
    前のステップの結果: {{prev_node.output}}
  next: "next_node"
```

| フィールド       | 必須 | 説明 |
|---------------|------|------|
| `prompt`      | ✅   | プロンプト文字列。テンプレート変数使用可 |
| `model`       | -    | 使用するOpenAIモデル名 |
| `output_format` | -  | `json` を指定するとレスポンスをJSONとしてパースし辞書で返す |

### 2. `skill` — スキルを実行する

```yaml
- id: "search"
  type: "skill"
  skill: "web_search"           # 必須: スキル名
  params:                       # スキルに渡すパラメータ（テンプレート変数使用可）
    query: "{{inputs.topic}}"
  next: "next_node"
```

利用可能なスキル一覧:

| スキル名           | 説明 |
|------------------|------|
| `web_search`     | Web検索（Tavily → DuckDuckGo フォールバック） |
| `slack_notify`   | Slack Incoming Webhookで通知 |
| `generate_slides`| Marp形式のMarkdownスライドを生成・保存 |
| `file_write`     | ファイルに書き込む |
| `file_read`      | ファイルを読み込む |
| `calculator`     | 数式を計算する |
| `echo`           | 入力をそのまま返す（デバッグ用） |

### 3. `foreach` — リストの各要素に対してノードを繰り返す

```yaml
- id: "search_each"
  type: "foreach"
  items: "{{plan.output.queries}}"   # 必須: リストを返すテンプレート変数
  node:                              # 必須: 各要素に対して実行するインラインノード
    type: "skill"                    # "llm" または "skill"
    skill: "web_search"
    params:
      query: "{{item}}"              # {{item}} で現在の要素を参照
  next: "next_node"
```

- `items` には `list` を返すテンプレート変数を指定します
- `node.type` は `llm` または `skill` のみ（foreachのネストは不可）
- 各要素は `{{item}}` で参照できます
- 実行結果はリストとして `{{node_id.output}}` に格納されます

### 4. `condition` — 条件分岐（実装予定）

```yaml
- id: "check_quality"
  type: "condition"
  branches:
    "high": "publish_node"
    "low": "retry_node"
  next: "default_node"
```

---

## テンプレート変数

ノードの `prompt` / `params` 内で `{{ }}` を使って変数を参照できます。

| 変数パターン                    | 説明 |
|-------------------------------|------|
| `{{inputs.変数名}}`            | ワークフローへの入力値 |
| `{{ノードID.output}}`          | 指定ノードの出力（文字列 or 辞書） |
| `{{ノードID.output.キー}}`     | JSON出力ノードの特定キー |
| `{{item}}`                    | `foreach` ノード内での現在の要素 |

---

## ワークフロー終了

- `next: "end"` を指定するとワークフローが終了します
- 最後のノードに `next` を省略した場合も終了します

---

## 実例

```yaml
name: "問い合わせ自動対応"
inputs:
  - name: "inquiry"
    type: "string"
  - name: "sender"
    type: "string"

nodes:
  - id: "summarize"
    type: "llm"
    model: "gpt-4o-mini"
    prompt: |
      以下の問い合わせを3行で要約してください。
      送信者: {{inputs.sender}}
      内容: {{inputs.inquiry}}
    next: "notify"

  - id: "notify"
    type: "skill"
    skill: "slack_notify"
    params:
      title: "新しい問い合わせ"
      message: "{{summarize.output}}"
    next: "end"
```

---

## バリデーションルール

- `id` はワークフロー内でユニークであること
- `next` に指定するIDは同一ワークフロー内に存在するか `"end"` であること
- `foreach` の `items` は実行時にリストに解決されること
- `llm` ノードに `output_format: "json"` を指定する場合、プロンプトでJSON形式を明示的に指示すること
