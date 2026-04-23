"""
微信联系人精确选择器

通过 OCR 识别搜索结果列表，精确点击目标联系人
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
    """联系人匹配结果"""
    
    def __init__(self, matched: bool, x: int = 0, y: int = 0, 
                 matched_text: str = "", all_texts: List[str] = None):
        self.matched = matched
        self.x = x
        self.y = y
        self.matched_text = matched_text
        self.all_texts = all_texts or []


class WeChatContactSelector:
    """微信联系人选择器 - 基于 OCR 精确匹配搜索结果"""
    
    SIMILARITY_THRESHOLD = 0.8  # 相似度阈值，超过视为冲突
    
    def __init__(self):
        self.screen = ScreenCapture()
        self.ocr = TextRecognizer()
    
    def _get_list_region(self, hwnd, list_width: int = 260) -> Optional[Tuple[int, int, int, int]]:
        """获取左侧列表区域"""
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
        识别列表区域文字
        
        Returns:
            (text_boxes, all_texts, list_region)
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
        在窗口左侧搜索结果列表中精确找到联系人坐标（兼容旧版接口）
        
        Args:
            hwnd: 微信窗口句柄
            contact_name: 要查找的联系人名称
            list_width: 左侧列表区域宽度（默认260px）
            
        Returns:
            ContactMatchResult
        """
        sorted_boxes, all_texts, list_region = self._recognize_list(hwnd, list_width)
        
        if not sorted_boxes or list_region is None:
            return ContactMatchResult(False, all_texts=all_texts)
        
        logger.debug(f"列表区域识别到 {len(sorted_boxes)} 处文字: {all_texts}")
        
        # 优先精确匹配
        for box in sorted_boxes:
            if contact_name == box.text.strip():
                center = box.center
                abs_x = list_region[0] + center[0]
                abs_y = list_region[1] + center[1]
                logger.info(f"精确匹配到联系人 '{contact_name}' @ ({abs_x}, {abs_y})")
                return ContactMatchResult(True, abs_x, abs_y, box.text, all_texts)
        
        # 模糊匹配
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
        检测相似联系人冲突
        
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
        严格模式查找联系人
        
        只接受精确匹配，并且会检测相似联系人冲突。
        
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
        
        # 检测相似联系人冲突
        conflicts = self.find_similar_names(contact_name, all_texts)
        if conflicts:
            logger.error(f"严格模式：检测到相似联系人冲突 '{contact_name}' vs {conflicts}")
            return False, None, conflicts
        
        # 严格精确匹配
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
        查找并点击联系人
        
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
