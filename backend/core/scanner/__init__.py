"""
文本扫描器模块 (Text Scanner Module)

职责分离后的新架构：
- text_segmenter.py: 负责文本分段
- event_emitter.py: 负责与前端的事件通信
- binary_searcher.py: 封装核心的二分查找算法
- text_scanner.py: 主协调器，整合其他模块完成扫描
"""

from .text_scanner import TextScanner
from .binary_searcher import SensitiveSegment

__all__ = ["TextScanner", "SensitiveSegment"]

