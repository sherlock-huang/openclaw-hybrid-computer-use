"""
微信联系人精确选择器 (WeChat Contact Selector)

基于 OCR 技术识别微信窗口左侧的搜索结果列表，从中精确找到目标联系人并返回其屏幕坐标。

核心能力：
- 截取微信左侧列表区域并进行 OCR 文字识别；
- 提供两种匹配策略：
  1. find_contact_in_list: 宽松模式，支持精确匹配和模糊匹配，兼容旧版接口；
  2. find_contact_in_list_strict: 严格模式，仅接受精确匹配，并检测相似联系人冲突。
- 相似度冲突检测：通过 difflib.SequenceMatcher 计算字符串相似度，
  当列表中存在与目标名称高度相似的联系人时，主动报告冲突，防止误点。

使用场景：
- 配合 WeChatSmartSender 的 Step 2（搜索并选择联系人）使用；
- 任何需要通过名称而非固定坐标来点击微信联系人的自动化流程。
"""

import difflib
import logging
import time
from typing import List, Optional, Tuple

try:
    import win32gui
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

from src.perception.screen import ScreenCapture
from src.perception.ocr import TextRecognizer, TextBox

logger = logging.getLogger(__name__)


class ContactMatchResult:
    """
    联系人匹配结果。
    
    Attributes:
        matched: 是否成功匹配到联系人
        x, y: 联系人在屏幕上的绝对坐标（matched=True 时有效）
        matched_text: 实际匹配到的 OCR 文字内容
        all_texts: 列表区域中识别到的所有文字（用于调试和错误报告）
    """
    
    def __init__(self, matched: bool, x: int = 0, y: int = 0, 
                 matched_text: str = "", all_texts: List[str] = None):
        self.matched = matched
        self.x = x
        self.y = y
        self.matched_text = matched_text
        self.all_texts = all_texts or []


class WeChatContactSelector:
    """
    微信联系人选择器 - 基于 OCR 精确匹配搜索结果。
    
    该类通过 ScreenCapture 截取微信窗口左侧列表区域，
    再使用 TextRecognizer 进行 OCR 识别，
    最后在识别结果中查找目标联系人并返回其屏幕坐标。
    
    两种查找模式对比：
    - find_contact_in_list (宽松模式):
      优先精确匹配，其次支持模糊匹配（包含关系），
      若均未命中则 fallback 到外部按 Enter。
      适用于已知联系人名称唯一、对容错性有一定要求的场景。
    
    - find_contact_in_list_strict (严格模式):
      仅接受精确匹配（==），并在匹配前检测相似联系人冲突。
      如果列表中存在与目标名称相似度超过阈值（SIMILARITY_THRESHOLD）的联系人，
      或存在子串包含关系，则立即报告冲突并拒绝匹配。
      适用于高安全要求、需要零误发的场景（如 WeChatSmartSender 的 STRICT 模式）。
    """
    
    # 相似度阈值：使用 difflib.SequenceMatcher 计算出的比率超过此值，视为潜在冲突。
    # 默认 0.8（80% 相似），兼顾"张三"vs"张三丰"等常见误触场景。
    SIMILARITY_THRESHOLD = 0.8
    
    def __init__(self):
        self.screen = ScreenCapture()
        self.ocr = TextRecognizer()
    
    def _get_list_region(self, hwnd, list_width: int = 260) -> Optional[Tuple[int, int, int, int]]:
        """
        获取微信窗口左侧列表区域的屏幕坐标。
        
        通过 win32gui.GetWindowRect 获取窗口整体位置，
        然后截取左侧固定宽度（默认 260px）、顶部向下偏移 100px 的区域作为列表区。
        
        Returns:
            (left, top, width, height) 的元组，失败时返回 None
        """
        try:
            rect = win32gui.GetWindowRect(hwnd)
        except Exception as e:
            logger.error(f"获取窗口位置失败: {e}")
            return None
        
        wx, wy, wr, wb = rect
        window_width = wr - wx
        window_height = wb - wy
        
        return (
            wx,
            wy + 100,
            min(list_width, window_width),
            max(50, window_height - 150)
        )
    
    def _recognize_list(self, hwnd, list_width: int = 260) -> Tuple[List[TextBox], List[str], Optional[Tuple]]:
        """
        识别列表区域文字。
        
        流程：
        1. 调用 _get_list_region 获取列表区域坐标；
        2. 使用 ScreenCapture 截取该区域；
        3. 使用 TextRecognizer 进行 OCR 识别；
        4. 按文字框的垂直位置（y 坐标）排序，生成有序的文字列表。
        
        Returns:
            (text_boxes, all_texts, list_region)
            - text_boxes: 排序后的 TextBox 列表
            - all_texts: 提取出的纯文字列表
            - list_region: 实际截取的列表区域坐标
        """
        list_region = self._get_list_region(hwnd, list_width)
        if list_region is None:
            return [], [], None
        
        try:
            screenshot = self.screen.capture(region=list_region)
            text_boxes = self.ocr.recognize(screenshot)
        except Exception as e:
            logger.error(f"OCR识别列表失败: {e}")
            return [], [], list_region
        
        sorted_boxes = sorted(text_boxes, key=lambda b: b.bbox[1])
        all_texts = [box.text for box in sorted_boxes]
        return sorted_boxes, all_texts, list_region
    
    def find_contact_in_list(self, hwnd, contact_name: str, 
                             list_width: int = 260) -> ContactMatchResult:
        """
        在窗口左侧搜索结果列表中查找联系人坐标（宽松模式 / 兼容旧版接口）。
        
        匹配优先级：
        1. 精确匹配：OCR 识别到的文字与 contact_name 完全一致（去除首尾空格后 ==）；
        2. 模糊匹配：OCR 识别到的文字包含 contact_name（子串包含关系）；
        3. 若以上均未命中，返回 matched=False，由调用方决定是否 fallback 按 Enter。
        
        与 find_contact_in_list_strict 的区别：
        - 本方法允许模糊匹配，不检测相似联系人冲突；
        - 适用于对容错性要求较高、联系人名称相对唯一的场景。
        
        Args:
            hwnd: 微信窗口句柄
            contact_name: 要查找的联系人名称
            list_width: 左侧列表区域宽度（默认 260px）
            
        Returns:
            ContactMatchResult（包含是否匹配、坐标、匹配文字、全部识别文字）
        """
        sorted_boxes, all_texts, list_region = self._recognize_list(hwnd, list_width)
        
        if not sorted_boxes or list_region is None:
            return ContactMatchResult(False, all_texts=all_texts)
        
        logger.debug(f"列表区域识别到 {len(sorted_boxes)} 处文字: {all_texts}")
        
        # 优先精确匹配：名称完全一致
        for box in sorted_boxes:
            if contact_name == box.text.strip():
                center = box.center
                abs_x = list_region[0] + center[0]
                abs_y = list_region[1] + center[1]
                logger.info(f"精确匹配到联系人 '{contact_name}' @ ({abs_x}, {abs_y})")
                return ContactMatchResult(True, abs_x, abs_y, box.text, all_texts)
        
        # 模糊匹配：名称作为子串被包含
        for box in sorted_boxes:
            if contact_name in box.text:
                center = box.center
                abs_x = list_region[0] + center[0]
                abs_y = list_region[1] + center[1]
                logger.info(f"模糊匹配到联系人 '{contact_name}' in '{box.text}' @ ({abs_x}, {abs_y})")
                return ContactMatchResult(True, abs_x, abs_y, box.text, all_texts)
        
        logger.warning(f"未在列表中找到联系人 '{contact_name}'，识别结果: {all_texts}")
        return ContactMatchResult(False, all_texts=all_texts)
    
    def find_similar_names(self, contact_name: str, all_texts: List[str]) -> List[str]:
        """
        检测相似联系人冲突。
        
        对列表中识别到的每一个文字，使用 difflib.SequenceMatcher 计算与目标名称的相似度比率。
        同时检查是否存在子串包含关系（如"张三"与"张三丰"）。
        
        判定冲突的条件（满足其一即视为冲突）：
        1. 相似度比率 >= SIMILARITY_THRESHOLD（默认 0.8）；
        2. 目标名称与识别文字存在子串包含关系，且目标名称长度 >= 2。
        
        注意：完全匹配项（==）会被跳过，不作为冲突返回。
        
        Args:
            contact_name: 目标联系人名称
            all_texts: 列表中识别到的所有文字
            
        Returns:
            与目标名称相似度超过阈值的其他名称列表（不包含完全匹配项）
        """
        similar = []
        for text in all_texts:
            text_clean = text.strip()
            if text_clean == contact_name:
                continue
            ratio = difflib.SequenceMatcher(None, contact_name, text_clean).ratio()
            # 额外检查：如果目标名称是文本的前缀/子串，也视为潜在冲突
            is_substring = contact_name in text_clean or text_clean in contact_name
            if ratio >= self.SIMILARITY_THRESHOLD or (is_substring and len(contact_name) >= 2):
                similar.append(text_clean)
        return similar
    
    def find_contact_in_list_strict(self, hwnd, contact_name: str,
                                    list_width: int = 260) -> Tuple[bool, Optional[ContactMatchResult], List[str]]:
        """
        严格模式查找联系人。
        
        与 find_contact_in_list 的关键差异：
        1. 只接受精确匹配（去除首尾空格后 ==），不接受模糊子串匹配；
        2. 在尝试匹配前，先调用 find_similar_names 扫描整个列表，
           若发现与目标名称相似度超过阈值的联系人，立即以冲突失败返回；
        3. 返回值三元组额外包含 conflict_names，方便调用方了解冲突详情。
        
        设计目的：在高安全场景下，宁可拒绝发送也不冒险点错人。
        例如当列表中同时存在"李雷"和"李雷群"时，严格模式会报告冲突，
        避免自动化流程把私聊消息误发到群聊中。
        
        Returns:
            (success, match_result, conflict_names)
            - success: 是否找到唯一匹配的联系人
            - match_result: 匹配结果（success=True 时有效）
            - conflict_names: 冲突的相似联系人名称列表（非空时表示存在歧义）
        """
        sorted_boxes, all_texts, list_region = self._recognize_list(hwnd, list_width)
        
        if list_region is None:
            return False, None, []
        
        if not sorted_boxes:
            logger.warning(f"严格模式：列表区域未识别到任何文字")
            return False, ContactMatchResult(False, all_texts=all_texts), []
        
        # 检测相似联系人冲突：先扫描整个列表，确认没有易混淆的相似名称
        conflicts = self.find_similar_names(contact_name, all_texts)
        if conflicts:
            logger.error(f"严格模式：检测到相似联系人冲突 '{contact_name}' vs {conflicts}")
            return False, None, conflicts
        
        # 严格精确匹配：仅接受完全一致的文字
        for box in sorted_boxes:
            if contact_name == box.text.strip():
                center = box.center
                abs_x = list_region[0] + center[0]
                abs_y = list_region[1] + center[1]
                logger.info(f"严格模式精确匹配到联系人 '{contact_name}' @ ({abs_x}, {abs_y})")
                return True, ContactMatchResult(True, abs_x, abs_y, box.text, all_texts), []
        
        logger.warning(f"严格模式：未精确匹配到联系人 '{contact_name}'，识别结果: {all_texts}")
        return False, ContactMatchResult(False, all_texts=all_texts), []
    
    def click_contact(self, hwnd, contact_name: str, list_width: int = 260) -> bool:
        """
        查找并点击联系人（宽松模式）。
        
        先调用 find_contact_in_list 获取坐标，若匹配成功则使用 pyautogui 点击。
        
        Returns:
            是否成功点击
        """
        result = self.find_contact_in_list(hwnd, contact_name, list_width)
        if not result.matched:
            return False
        
        try:
            pyautogui.click(result.x, result.y)
            time.sleep(0.5)
            return True
        except Exception as e:
            logger.error(f"点击联系人失败: {e}")
            return False
