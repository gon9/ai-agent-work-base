import yaml
from pathlib import Path
from typing import Union, Dict
from ..schemas.workflow import WorkflowDefinition

class WorkflowLoader:
    """
    YAMLファイルからワークフロー定義を読み込むクラス
    """
    
    @staticmethod
    def load(source: Union[str, Path]) -> WorkflowDefinition:
        """
        YAMLファイルまたはYAML文字列からWorkflowDefinitionを生成する
        """
        if isinstance(source, Path):
            with open(source, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        elif isinstance(source, str):
            # 改行が含まれている場合は明らかにファイルパスではないのでYAML文字列として扱う
            if "\n" in source:
                data = yaml.safe_load(source)
            else:
                # パスのように見える場合はファイルとして試行
                try:
                    path = Path(source)
                    # ファイル名の長さ制限などを考慮し、存在確認で例外が出たら文字列として扱う
                    if path.exists() and (path.suffix in ['.yaml', '.yml']):
                        with open(path, "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f)
                    else:
                        # 文字列としてパース
                        data = yaml.safe_load(source)
                except OSError:
                    # ファイル名が長すぎる場合などはここに来るはず
                    data = yaml.safe_load(source)
        else:
            raise ValueError("Source must be a file path or YAML string")

        return WorkflowDefinition(**data)
