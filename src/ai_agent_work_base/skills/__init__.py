from typing import List
from .base import BaseSkill
from .basic import EchoSkill, ReverseSkill
from .file import FileWriteSkill, FileReadSkill
from .math import CalculatorSkill
from .research import WebSearchSkill
from .presentation import SlideGenerationSkill
from .pptx_generation import PptxGenerationSkill
from .pptxjs_generation import PptxJsGenerationSkill
from .slack import SlackNotifySkill
from .self_debug import SelfDebugSkill

def load_all_skills() -> List[BaseSkill]:
    """全ての利用可能なスキルをインスタンス化して返す"""
    return [
        EchoSkill(),
        ReverseSkill(),
        FileWriteSkill(),
        FileReadSkill(),
        CalculatorSkill(),
        WebSearchSkill(),
        SlideGenerationSkill(),
        PptxGenerationSkill(),
        PptxJsGenerationSkill(),
        SlackNotifySkill(),
        SelfDebugSkill(),
    ]
