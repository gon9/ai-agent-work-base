# 並列実行の設計

## 現状の問題

`deep_research.yaml`の`execute_search_1`ノードは1つしか動かない。
`plan_research`が「クエリ1、クエリ2、クエリ3」をテキストで出力しても、
それを1つのクエリとして検索しているだけで、並列化されていない。

```
plan_research (LLM) → execute_search_1 (skill) → summarize (LLM)
                       ↑ 1回しか動かない
```

## 解決策の比較

### 案A: `parallel`ノードタイプを追加

YAMLで並列実行を宣言的に記述する。

```yaml
- id: "fan_out"
  type: "parallel"
  items: "{{plan_research.output.queries}}"  # リストを受け取る
  node:                                       # 各要素に対して実行するノード定義
    type: "skill"
    skill: "web_search"
    params:
      query: "{{item}}"                       # 各要素を {{item}} で参照
  next: "summarize"
```

**メリット:**
- YAMLで意図が明確に表現できる
- 並列実行の制御（最大並列数など）をYAMLで指定できる
- 将来的な拡張性が高い

**デメリット:**
- スキーマ変更が必要（`NodeDefinition`に`parallel`タイプを追加）
- `GraphExecutor`に`asyncio`を使った並列実行ロジックが必要
- LLMの出力をリスト（JSON）として受け取る必要がある

---

### 案B: `foreach`ノードタイプを追加

リストの各要素に対してノードを逐次実行する（並列ではなく直列ループ）。

```yaml
- id: "search_loop"
  type: "foreach"
  items: "{{plan_research.output.queries}}"
  node:
    type: "skill"
    skill: "web_search"
    params:
      query: "{{item}}"
  next: "summarize"
```

**メリット:**
- 実装がシンプル（asyncio不要）
- 案Aと同じYAML構造で後から並列化に切り替えやすい

**デメリット:**
- 逐次なので遅い（Deep Researchには不向き）

---

### 案C: LLMにJSON出力させて動的ループ（最小変更）

`plan_research`がJSON配列を出力し、`executor`が動的にskillを複数回呼び出す。
YAMLスキーマは変えず、`skill`ノードに`foreach_input`フィールドを追加するだけ。

```yaml
- id: "plan_research"
  type: "llm"
  model: "gpt-4o-mini"
  output_format: "json"          # JSON出力を指示
  prompt: |
    クエリを3つJSON配列で出力してください:
    {"queries": ["クエリ1", "クエリ2", "クエリ3"]}
  next: "execute_search"

- id: "execute_search"
  type: "skill"
  skill: "web_search"
  foreach_input: "{{plan_research.output.queries}}"  # リストを受け取りループ
  params:
    query: "{{item}}"
  next: "summarize"
```

**メリット:**
- 変更量が少ない
- 既存のYAML構造を大きく変えない

**デメリット:**
- `foreach_input`という特殊フィールドが`skill`ノードにしか使えない
- 並列化されない（逐次ループ）
- LLMのJSON出力が不安定になりうる

---

## 推奨設計: 案A + 案B の段階的実装

### フェーズ1: `foreach`ノードタイプ（逐次ループ）

まず`foreach`を実装してYAMLの表現力を上げる。
LLMの出力はJSON形式で受け取るよう`output_format: json`を追加。

```
plan_research (LLM, JSON出力) → foreach (逐次ループ) → summarize (LLM)
```

### フェーズ2: `parallel`ノードタイプ（並列実行）

`foreach`と同じYAML構造のまま`type: parallel`に変えるだけで並列化できるようにする。
`asyncio.gather`で並列実行し、結果をリストとしてコンテキストに保存。

```
plan_research (LLM, JSON出力) → parallel (並列実行) → summarize (LLM)
```

---

## 必要な変更

### 1. `NodeDefinition`スキーマ

```python
class NodeDefinition(BaseModel):
    id: str
    type: Literal["llm", "skill", "condition", "foreach", "parallel", "end"]
    ...
    # foreach / parallel 用
    items: Optional[str] = None          # リストを参照するテンプレート変数
    node: Optional["NodeDefinition"] = None  # 各要素に対して実行するノード
```

### 2. LLMノードのJSON出力対応

```python
class NodeDefinition(BaseModel):
    ...
    output_format: Optional[Literal["text", "json"]] = "text"
```

LLMに`response_format={"type": "json_object"}`を渡し、出力をパースしてコンテキストに保存。

### 3. `GraphExecutor`の拡張

- `_execute_foreach_node`: リストを逐次実行し、結果をリストとして保存
- `_execute_parallel_node`: `asyncio.gather`で並列実行し、結果をリストとして保存

### 4. `WorkflowContext`の拡張

- `set_step_output`でリスト型の出力を扱えるようにする（現状は`{"output": value}`のみ）

---

## 更新後のYAML例（deep_research.yaml）

```yaml
name: "Deep Research"
description: "トピックについて調査を行い、レポートを作成します"
inputs:
  - name: "topic"
    type: "string"

nodes:
  - id: "plan_research"
    type: "llm"
    model: "gpt-4o-mini"
    output_format: "json"
    prompt: |
      あなたはプロのリサーチャーです。
      トピック「{{inputs.topic}}」について調査するための検索クエリを3つ考えてください。
      
      以下のJSON形式で出力してください:
      {"queries": ["クエリ1", "クエリ2", "クエリ3"]}
    next: "execute_searches"

  - id: "execute_searches"
    type: "parallel"
    items: "{{plan_research.output.queries}}"
    node:
      type: "skill"
      skill: "web_search"
      params:
        query: "{{item}}"
    next: "summarize"

  - id: "summarize"
    type: "llm"
    model: "gpt-4o"
    prompt: |
      以下の検索結果を元に、トピック「{{inputs.topic}}」についての詳細なレポートを日本語で作成してください。
      
      ## 検索結果
      {{execute_searches.output}}
    next: "end"
```
