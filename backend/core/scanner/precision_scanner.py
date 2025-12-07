"""
精确定位扫描器 (PrecisionScanner)

本模块负责实现核心的“精确双向挤压”算法，用于在已确定包含敏感内容的短文本块中，
以最小的 API 调用次数，精确定位出一个或多个敏感词的具体边界。

核心算法：精确双向挤压 (Precision Squeeze)
-----------------------------------------
该算法基于一个关键原则：如果从一个被拦截的文本中移除某个字符后，文本变为“安全”，
那么这个被移除的字符就是敏感边界的一部分，必须被保留。

算法流程：
1. **输入**：一个已知被拦截 (Blocked) 的短文本块。
2. **左侧挤压 (Left Squeeze)**：从文本左侧开始逐个移除字符，并探测剩余部分。
   一旦剩余文本变为“安全”(Safe)，说明刚刚被移除的字符是敏感词的左边界。立即停止，并保留该边界。
3. **右侧挤压 (Right Squeeze)**：同理，从文本右侧开始逐个移除字符。
   一旦剩余文本变为“安全”，说明刚被移除的字符是敏感词的右边界。立即停止，并保留该边界。
4. **最终验证 (Autopsy)**：为防止过度挤压，算法会再次探测由左右边界确定的最终文本，确保它本身仍然是“被拦截”的。
5. **递归处理**：如果文本中包含多个敏感词，在定位并提取第一个敏感词后，算法会对其余部分递归执行相同流程，直到所有敏感内容都被定位。

该算法确保了即使面对复杂的、由多个部分组成的敏感短语，也能准确地识别其完整形态，而不是返回一个不完整的片段。
"""
import asyncio
import logging
from typing import List, Callable, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SensitiveSegment:
    """
    用于封装扫描结果的数据类，代表一个被识别出的敏感文本段。

    Attributes:
        text: 敏感词的具体内容。
        start_pos: 敏感词在原始文本中的起始位置（包含）。
        end_pos: 敏感词在原始文本中的结束位置（不包含）。
    """
    text: str
    start_pos: int
    end_pos: int


class PrecisionScanner:
    """精确定位扫描器 - 精确的双向挤压算法"""

    def __init__(self, session_id: str = ""):
        """
        初始化精确定位扫描器

        Args:
            session_id: 会话 ID（用于日志）
        """
        self.session_id = session_id or "default"
        logger.info(f"[{self.session_id}] [Precision] PrecisionScanner 已初始化")

    async def scan_precision(
        self,
        text: str,
        base_pos: int,
        probe_func: Callable,
        max_iterations: int = 1000
    ) -> List[SensitiveSegment]:
        """
        使用精确双向挤压算法精确定位敏感词

        Args:
            text: 待扫描的文本块（已知为 Blocked）
            base_pos: 该文本块在原始全文中的起始位置
            probe_func: 异步探测函数，接收文本返回 (is_blocked, block_reason)
            max_iterations: 最大迭代次数（防止死循环）

        Returns:
            敏感词段列表
        """
        results: List[SensitiveSegment] = []
        current_pos = 0  # 当前扫描位置（相对于 text）
        iteration_count = 0

        logger.debug(
            f"[{self.session_id}] [Precision] 开始精细扫描 | "
            f"文本长度: {len(text)} | 基础位置: {base_pos}"
        )

        while current_pos < len(text) and iteration_count < max_iterations:
            iteration_count += 1
            remaining_text = text[current_pos:]

            # 1. 探测剩余文本是否被拦截
            is_blocked, block_reason = await probe_func(remaining_text)

            if not is_blocked:
                # 剩余文本全部安全，扫描完成
                logger.debug(
                    f"[{self.session_id}] [Precision] 迭代 {iteration_count}: "
                    f"剩余文本安全，扫描完成"
                )
                break

            # 2. 执行精确双向挤压
            left_pos, right_pos = await self._precision_squeeze(
                remaining_text, probe_func
            )

            if left_pos < 0 or right_pos < 0 or left_pos >= right_pos:
                # 当精确挤压算法无法收敛时（例如，API 行为不稳定），启动备用策略。
                # 备用策略会尝试寻找最小的、能独立触发拦截的子字符串，以保证能返回一个有效结果。
                logger.warning(
                    f"[{self.session_id}] [Precision] 迭代 {iteration_count}: "
                    f"精确双向挤压失败 (left={left_pos}, right={right_pos})。尝试最小阻断子串搜索。"
                )
                sub_left, sub_right = await self._find_minimal_blocked_substring(remaining_text, probe_func)
                if 0 <= sub_left < sub_right:
                    keyword_text = remaining_text[sub_left:sub_right]
                    keyword_start = base_pos + current_pos + sub_left
                    keyword_end = base_pos + current_pos + sub_right
                    result = SensitiveSegment(text=keyword_text, start_pos=keyword_start, end_pos=keyword_end)
                    results.append(result)
                    logger.info(
                        f"[{self.session_id}] [Precision] 敏感词已锁定（Micro） | "
                        f"迭代: {iteration_count} | 词汇: '{keyword_text}' | 长度: {len(keyword_text)} | 位置: {keyword_start}-{keyword_end}"
                    )
                    break
                
                # 仍未找到 → 最后降级：将整个块作为敏感片段返回，避免丢失
                logger.warning(
                    f"[{self.session_id}] [Precision] Micro 搜索未命中，使用最终降级：整块返回。"
                )
                keyword_text = remaining_text
                keyword_start = base_pos + current_pos
                keyword_end = keyword_start + len(keyword_text)
                results.append(SensitiveSegment(text=keyword_text, start_pos=keyword_start, end_pos=keyword_end))
                break

            # 3. 记录结果
            keyword_text = remaining_text[left_pos:right_pos]
            keyword_start = base_pos + current_pos + left_pos
            keyword_end = keyword_start + len(keyword_text)

            result = SensitiveSegment(
                text=keyword_text,
                start_pos=keyword_start,
                end_pos=keyword_end
            )
            results.append(result)

            logger.info(
                f"[{self.session_id}] [Precision] 敏感词已锁定 | "
                f"迭代: {iteration_count} | 词汇: '{keyword_text}' | "
                f"长度: {len(keyword_text)} | 位置: {keyword_start}-{keyword_end}"
            )

            # 4. 切断该词，继续扫描剩余部分
            current_pos += right_pos

        if iteration_count >= max_iterations:
            logger.error(
                f"[{self.session_id}] [Precision] 达到最大迭代次数 ({max_iterations})，"
                f"可能存在死循环。已提取 {len(results)} 个敏感词。"
            )

        logger.debug(
            f"[{self.session_id}] [Precision] 精细扫描完成 | "
            f"总迭代: {iteration_count} | 敏感词数: {len(results)}"
        )

        return results

    async def _precision_squeeze(
        self,
        text: str,
        probe_func: Callable
    ) -> tuple:
        """
        精确双向挤压：从左右两端逐字符删除，直到变为 Safe（关键原则：If Safe -> Stop）

        Args:
            text: 待扫描的文本（已知为 Blocked）
            probe_func: 探测函数

        Returns:
            (left_pos, right_pos) - 敏感词的左右边界（相对位置）
        """
        if not text:
            return -1, -1
        
        # 预检查，确保输入文本符合算法预期（必须是被拦截的）
        is_input_blocked, _ = await probe_func(text)
        if not is_input_blocked:
            logger.warning(
                f"[{self.session_id}] [Precision] 警告：输入文本本身是 Safe，"
                f"不应该进入精确双向挤压。文本: '{text}'"
            )
            return -1, -1

        # 左削减：逐步去掉左侧前缀，直到刚好去多了变 Safe，为了包含关键字符，取上一个仍为 Blocked 的位置
        left_pos = 0
        for i in range(len(text)):
            candidate = text[i:]
            is_blocked, _ = await probe_func(candidate)
            logger.debug(
                f"[{self.session_id}] [Precision] 左削减步骤 {i}: "
                f"前缀裁剪 -> '{candidate}' | 状态: {'Blocked' if is_blocked else 'Safe'}"
            )
            if is_blocked:
                left_pos = i
            else:
                # 一旦 Safe，停止；left_pos 已是最后一个仍 Blocked 的 i（即需要包含的左边界）
                break
        else:
            # 循环完成但未找到 Safe 状态
            left_pos = 0
            logger.debug(
                f"[{self.session_id}] [Precision] 左削减完成 | "
                f"整个文本都是 Blocked，left_pos=0"
            )

        # 右削减：从右向左逐步裁剪后缀，记录最后一个仍为 Blocked 的长度
        right_pos = len(text)
        for j in range(len(text), 0, -1):
            candidate = text[:j]
            is_blocked, _ = await probe_func(candidate)
            
            logger.debug(
                f"[{self.session_id}] [Precision] 右削减步骤 {len(text) - j}: "
                f"后缀裁剪 -> '{candidate}' | 状态: {'Blocked' if is_blocked else 'Safe'}"
            )
            
            if is_blocked:
                right_pos = j
            else:
                # 一旦 Safe，停止；right_pos 已是最后一个仍 Blocked 的长度（即需要包含的右边界）
                break

        # 最终验证：确保结果确实是 Blocked，防止过度削减
        result_text = text[left_pos:right_pos]
        is_result_blocked, _ = await probe_func(result_text)
        
        logger.debug(
            f"[{self.session_id}] [Precision] 最终验证 | "
            f"结果: '{result_text}' | 状态: {'Blocked' if is_result_blocked else 'Safe'}"
        )
        
        if not is_result_blocked:
            # 如果最终提取的文本是安全的，说明算法在某种边缘情况下失效。
            logger.error(
                f"[{self.session_id}] [Precision] 算法错误：结果 '{result_text}' 是 Safe！"
                f"过度削减了。left_pos={left_pos}, right_pos={right_pos}"
            )
            return -1, -1

        logger.debug(
            f"[{self.session_id}] [Precision] 精确双向挤压结果 | "
            f"左边界: {left_pos} | 右边界: {right_pos} | "
            f"提取词汇: '{result_text}'"
        )

        return left_pos, right_pos

    async def _find_minimal_blocked_substring(self, text: str, probe_func) -> tuple:
        """
        最小阻断子串搜索（Micro Window）
        在较小文本上以从短到长的窗口搜索第一个被阻断的最短子串。
        复杂度 O(n^2)，但 n ≤ 50，可接受。
        返回 (l, r) 相对边界；找不到返回 (-1, -1)。
        """
        n = len(text)
        if n == 0:
            return -1, -1
        # 先确认整体确为 Blocked
        is_blocked, _ = await probe_func(text)
        if not is_blocked:
            return -1, -1
        # 从最短窗口开始
        for w in range(1, n + 1):
            for s in range(0, n - w + 1):
                seg = text[s:s + w]
                blocked, _ = await probe_func(seg)
                if blocked:
                    return s, s + w
        return -1, -1
