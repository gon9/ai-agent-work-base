import re
from typing import Any, Dict, List, Union

class WorkflowContext:
    """
    ワークフロー実行中の状態（変数）を管理するクラス
    """
    def __init__(self, initial_inputs: Dict[str, Any] = None):
        self._data: Dict[str, Any] = {}
        if initial_inputs:
            self._data["inputs"] = initial_inputs

    def set(self, key: str, value: Any):
        """変数を設定する (dot notation supported for top-level keys)"""
        # 現状は単純なキー設定のみだが、必要に応じてネスト対応
        self._data[key] = value

    def set_step_output(self, node_id: str, output: Any):
        """ステップの実行結果を保存する"""
        if node_id not in self._data:
            self._data[node_id] = {}
        # node_id.output でアクセスできるようにする
        # node_id 自体が辞書として output を持つ形にする
        self._data[node_id] = {"output": output}

    def get(self, key: str) -> Any:
        """変数を取得する (dot notation supported)"""
        parts = key.split(".")
        current = self._data
        
        try:
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
                
                if current is None:
                    return None
            return current
        except Exception:
            return None

    def resolve_template(self, text: str) -> str:
        """
        文字列中のテンプレート変数を置換する
        {{ key.subkey }} の形式に対応
        """
        if not isinstance(text, str):
            return text

        pattern = r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}"
        
        def replace_match(match):
            key = match.group(1)
            value = self.get(key)
            return str(value) if value is not None else match.group(0)

        return re.sub(pattern, replace_match, text)

    def resolve_value(self, value: Any) -> Any:
        """
        値に含まれる変数を再帰的に解決する
        """
        if isinstance(value, str):
            # 文字列全体が変数参照のみの場合は、型を維持して返す
            # "{{inputs.value}}" -> int(10) のように
            pattern_full = r"^\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}$"
            match = re.match(pattern_full, value)
            if match:
                key = match.group(1)
                val = self.get(key)
                return val if val is not None else value
            return self.resolve_template(value)
        
        if isinstance(value, dict):
            return {k: self.resolve_value(v) for k, v in value.items()}
            
        if isinstance(value, list):
            return [self.resolve_value(v) for v in value]
            
        return value
