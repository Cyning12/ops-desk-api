"""token 计数（契约 §1d E5）。

用 bge-m3 真实 tokenizer（sentencepiece），不用字符近似——混合语料
字符/token 比波动大（英文 ~4、代码 ~1.5-2、中文 ~1）。

只加载 tokenizer（几 MB 词表），不加载模型权重（~2.3GB）：
数 token 与向量化是两个阶段。懒加载 + 可注入 fake，测试与模型文件解耦。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol


class TokenCounter(Protocol):
    def count(self, text: str) -> int: ...


class BgeM3TokenCounter:
    """生产用计数器：首次 count 时才下载/加载 tokenizer。"""

    def __init__(self, model_name: str = "BAAI/bge-m3") -> None:
        self._model_name = model_name
        self._tok = None

    def _load(self):
        if self._tok is None:
            from transformers import AutoTokenizer  # 延迟导入，模块加载保持轻量

            self._tok = AutoTokenizer.from_pretrained(self._model_name)
        return self._tok

    def count(self, text: str) -> int:
        return len(self._load().encode(text, add_special_tokens=False))


class FuncTokenCounter:
    """测试/调试用：包装任意计数函数（如 lambda t: len(t.split())）。"""

    def __init__(self, fn: Callable[[str], int]) -> None:
        self._fn = fn

    def count(self, text: str) -> int:
        return self._fn(text)
