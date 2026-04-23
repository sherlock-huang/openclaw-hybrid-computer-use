"""
WeChat Desktop Helper

Automate WeChat desktop operations using PyAutoGUI (better Chinese input support)
"""

import logging
import time
import os
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Tuple, List
from pathlib import Path

try:
    import win32gui
    import win32con
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
from src.utils.adaptive_coords import AdaptiveCoordinateMapper
from src.utils.wechat_contact_selector import WeChatContactSelector, ContactMatchResult

logger = logging.getLogger(__name__)

WECHAT_WINDOW_TITLES = ["微信", "WeChat"]


@dataclass
class ValidationResult:
    success: bool
    found_text: str
    confidence: float
    screenshot_path: Optional[str] = None


class WeChatOCRValidator:
    """WeChat OCR Validator for contact and message validation"""

    def __init__(self):
        self.screen = ScreenCapture()
        self.ocr = TextRecognizer()

    def _save_debug_screenshot(self, image, prefix: str) -> str:
        """保存调试图到 logs 目录"""
        logs_dir = Path("logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = logs_dir / f"{prefix}_{timestamp}.png"
        self.screen.save(image, path)
        return str(path)

    def validate_chat_contact(self, hwnd, expected_contact: str, save_screenshot_on_fail: bool = True,
                               is_group_chat: bool = False) -> ValidationResult:
        """Validate the correct contact is selected in the chat window title area."""
        try:
            rect = win32gui.GetWindowRect(hwnd)
        except Exception as e:
            logger.error(f"获取窗口位置失败: {e}")
            return ValidationResult(False, "", 0.0)

        # Top title bar area (left list width ~280px)
        title_region = (rect[0] + 280, rect[1], rect[2] - rect[0] - 280, 80)
        screenshot = self.screen.capture(region=title_region)
        texts = self.ocr.recognize(screenshot)
        for text_box in texts:
            if self._contact_match(expected_contact, text_box.text, is_group_chat):
                return ValidationResult(True, text_box.text, text_box.confidence)

        # Fallback: 验证右侧聊天内容区域上方是否有联系人名称
        header_region = (rect[0] + 280, rect[1] + 60, rect[2] - rect[0] - 280, 60)
        header_screenshot = self.screen.capture(region=header_region)
        header_texts = self.ocr.recognize(header_screenshot)
        for text_box in header_texts:
            if self._contact_match(expected_contact, text_box.text, is_group_chat):
                return ValidationResult(True, text_box.text, text_box.confidence)

        all_text = " ".join([t.text for t in texts + header_texts])
        screenshot_path = None
        if save_screenshot_on_fail:
            screenshot_path = self._save_debug_screenshot(screenshot, f"wechat_validate_contact_fail")
        return ValidationResult(False, all_text, 0.0, screenshot_path)
    
    def _contact_match(self, expected: str, found: str, is_group_chat: bool = False) -> bool:
        """
        判断预期联系人是否匹配识别到的文字
        
        群聊模式下放宽匹配规则，允许前缀/子串匹配
        """
        if expected in found:
            return True
        if is_group_chat:
            # 群聊名称可能较长被截断，允许互为前缀/子串
            if found in expected:
                return True
            # 允许前 4 个字匹配（适用于"技术群"被识别为"技术"）
            if len(expected) >= 4 and len(found) >= 4:
                if expected[:4] == found[:4]:
                    return True
        return False

    def pre_send_final_check(self, hwnd, expected_contact: str,
                               save_screenshot_on_fail: bool = True,
                               is_group_chat: bool = False) -> ValidationResult:
        """
        发送前的最终确认：验证聊天对象无误
        在按 Enter 前调用，作为最后一道防线
        """
        try:
            rect = win32gui.GetWindowRect(hwnd)
        except Exception as e:
            logger.error(f"获取窗口位置失败: {e}")
            return ValidationResult(False, "", 0.0)

        # 同时验证顶部标题栏和右侧聊天区域上方
        title_region = (rect[0] + 280, rect[1], rect[2] - rect[0] - 280, 80)
        title_screenshot = self.screen.capture(region=title_region)
        title_texts = self.ocr.recognize(title_screenshot)
        
        for text_box in title_texts:
            if self._contact_match(expected_contact, text_box.text, is_group_chat):
                return ValidationResult(True, text_box.text, text_box.confidence)
        
        header_region = (rect[0] + 280, rect[1] + 60, rect[2] - rect[0] - 280, 60)
        header_screenshot = self.screen.capture(region=header_region)
        header_texts = self.ocr.recognize(header_screenshot)
        
        for text_box in header_texts:
            if self._contact_match(expected_contact, text_box.text, is_group_chat):
                return ValidationResult(True, text_box.text, text_box.confidence)
        
        all_text = " ".join([t.text for t in title_texts + header_texts])
        screenshot_path = None
        if save_screenshot_on_fail:
            screenshot_path = self._save_debug_screenshot(title_screenshot, f"wechat_pre_send_check_fail")
        return ValidationResult(False, all_text, 0.0, screenshot_path)
    
    def validate_group_chat_features(self, hwnd) -> ValidationResult:
        """
        验证当前聊天窗口是否具有群聊特征
        
        通过 OCR 查找 "群成员"、"群公告" 等特征词
        """
        try:
            rect = win32gui.GetWindowRect(hwnd)
        except Exception as e:
            logger.error(f"获取窗口位置失败: {e}")
            return ValidationResult(False, "", 0.0)
        
        # 右侧聊天区域上方，查找群聊按钮区域
        header_region = (rect[0] + 280, rect[1] + 60, rect[2] - rect[0] - 280, 60)
        header_screenshot = self.screen.capture(region=header_region)
        texts = self.ocr.recognize(header_screenshot)
        
        group_keywords = ["群成员", "群公告", "Group Members", "Group Notice"]
        found_texts = []
        for text_box in texts:
            found_texts.append(text_box.text)
            for kw in group_keywords:
                if kw in text_box.text:
                    return ValidationResult(True, text_box.text, text_box.confidence)
        
        return ValidationResult(False, " ".join(found_texts), 0.0)

    def _extract_identifiers(self, message: str) -> List[str]:
        """从消息中提取可用于模糊验证的标识符（数字、时间、ASCII 等）"""
        import re
        identifiers = []
        # 提取时间格式 (HH:MM, HH:MM:SS)
        time_patterns = re.findall(r'\d{1,2}:\d{2}(?::\d{2})?', message)
        identifiers.extend(time_patterns)
        # 提取数字串（至少 2 位）
        num_patterns = re.findall(r'\d{2,}', message)
        identifiers.extend(num_patterns)
        # 提取 ASCII 单词（至少 3 个字符）
        ascii_patterns = re.findall(r'[a-zA-Z]{3,}', message)
        identifiers.extend(ascii_patterns)
        # 去重并过滤
        seen = set()
        result = []
        for ident in identifiers:
            if ident not in seen and len(ident) >= 4:
                seen.add(ident)
                result.append(ident)
        return result

    def validate_message_sent(self, hwnd, expected_message: str, timeout: int = 3,
                              save_screenshot_on_fail: bool = True) -> ValidationResult:
        """Validate the message appears in the chat history."""
        start = time.time()
        last_texts = ""
        identifiers = self._extract_identifiers(expected_message)
        
        while time.time() - start < timeout:
            try:
                rect = win32gui.GetWindowRect(hwnd)
            except Exception:
                time.sleep(0.5)
                continue

            # 优先扫描底部小区域（最新消息通常在此）
            ww = rect[2] - rect[0] - 280
            wh = rect[3] - rect[1]
            bottom_region = (rect[0] + 280, rect[3] - min(200, wh // 3), ww, min(200, wh // 3))
            try:
                screenshot = self.screen.capture(region=bottom_region)
                texts = self.ocr.recognize(screenshot)
                for text_box in texts:
                    if expected_message in text_box.text:
                        return ValidationResult(True, text_box.text, text_box.confidence)
                    if identifiers:
                        for ident in identifiers:
                            if ident in text_box.text:
                                self.logger.info(f"Fuzzy match: identifier '{ident}' found in bottom region")
                                return ValidationResult(True, text_box.text, text_box.confidence)
            except Exception as e:
                self.logger.warning(f"Bottom region OCR failed: {e}")

            # 扩大扫描整个右侧聊天区域
            chat_region = (rect[0] + 280, rect[1] + 80, ww, wh - 100)
            screenshot = self.screen.capture(region=chat_region)
            texts = self.ocr.recognize(screenshot)
            
            # 优先查找右下角区域（自己发送的消息通常在右侧）
            right_half_x = rect[0] + 280 + ww // 2
            bottom_third_y = rect[1] + 80 + int((wh - 100) * 0.65)
            
            # 1. 精确匹配（右下角优先）
            for text_box in texts:
                box_x, box_y = text_box.center
                abs_box_x = chat_region[0] + box_x
                abs_box_y = chat_region[1] + box_y
                
                if expected_message in text_box.text:
                    if abs_box_x >= right_half_x and abs_box_y >= bottom_third_y:
                        return ValidationResult(True, text_box.text, text_box.confidence)
            
            for text_box in texts:
                if expected_message in text_box.text:
                    return ValidationResult(True, text_box.text, text_box.confidence)
            
            # 2. 模糊匹配：如果消息含中文，验证关键标识符是否出现在底部区域
            if identifiers:
                bottom_texts = []
                for text_box in texts:
                    box_x, box_y = text_box.center
                    abs_box_y = chat_region[1] + box_y
                    if abs_box_y >= bottom_third_y:
                        bottom_texts.append(text_box)
                
                for ident in identifiers:
                    for text_box in bottom_texts:
                        if ident in text_box.text:
                            self.logger.info(f"Fuzzy match: identifier '{ident}' found in bottom area")
                            return ValidationResult(True, text_box.text, text_box.confidence)
                    
                    for text_box in texts:
                        if ident in text_box.text:
                            self.logger.info(f"Fuzzy match: identifier '{ident}' found in chat area")
                            return ValidationResult(True, text_box.text, text_box.confidence)
                    
            last_texts = " ".join([t.text for t in texts])
            time.sleep(0.5)

        screenshot_path = None
        if save_screenshot_on_fail:
            try:
                screenshot_path = self._save_debug_screenshot(screenshot, f"wechat_validate_msg_fail")
            except Exception:
                pass
        return ValidationResult(False, last_texts, 0.0, screenshot_path)


class WeChatHelper:
    """WeChat Desktop Helper"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.window_handle = None
        self.window_rect = None
        self.contact_selector = WeChatContactSelector()
        self.validator = WeChatOCRValidator()
        self.coord_mapper = AdaptiveCoordinateMapper()
        self.screen = ScreenCapture()
        self.ocr = TextRecognizer()
        self.last_error = ""

        if not WIN32_AVAILABLE:
            raise ImportError("pywin32 required: py -m pip install pywin32")

        if not PYAUTOGUI_AVAILABLE:
            raise ImportError("pyautogui required: py -m pip install pyautogui")

        pyautogui.FAILSAFE = False  # 自动化环境禁用 fail-safe
        pyautogui.PAUSE = 0.05

    def find_wechat_window(self) -> Optional[int]:
        """Find WeChat window handle"""
        def callback(hwnd, extra):
            try:
                if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    for keyword in WECHAT_WINDOW_TITLES:
                        if keyword in title:
                            extra.append(hwnd)
                            return False
            except Exception:
                pass
            return True

        handles = []
        try:
            win32gui.EnumWindows(callback, handles)
        except Exception as e:
            self.logger.warning(f"EnumWindows error: {e}")

        # Fallback: 通过类名查找微信窗口（不受标题变化影响）
        if not handles:
            try:
                hwnd = win32gui.FindWindow("WeChatMainWndForPC", None)
                if hwnd:
                    handles.append(hwnd)
            except Exception:
                pass
        
        # Fallback: 通过常见标题查找
        if not handles:
            for title in ["微信", "WeChat"]:
                try:
                    hwnd = win32gui.FindWindow(None, title)
                    if hwnd:
                        handles.append(hwnd)
                        break
                except Exception:
                    pass
        
        # Fallback: 遍历所有顶级窗口（包括不可见窗口）
        if not handles:
            try:
                def enum_callback(hwnd, extra):
                    if win32gui.IsWindow(hwnd):
                        try:
                            title = win32gui.GetWindowText(hwnd)
                            for keyword in WECHAT_WINDOW_TITLES:
                                if keyword in title:
                                    extra.append(hwnd)
                                    return False
                        except Exception:
                            pass
                    return True
                win32gui.EnumWindows(enum_callback, handles)
            except Exception:
                pass

        if handles:
            self.window_handle = handles[0]
            try:
                self.window_rect = win32gui.GetWindowRect(self.window_handle)
                return self.window_handle
            except Exception:
                pass

        return None

    def activate_wechat(self) -> bool:
        """Activate WeChat window"""
        if not self.window_handle:
            if not self.find_wechat_window():
                self.last_error = "WeChat window not found"
                return False

        try:
            if win32gui.IsIconic(self.window_handle):
                win32gui.ShowWindow(self.window_handle, win32con.SW_RESTORE)
            elif not win32gui.IsWindowVisible(self.window_handle):
                win32gui.ShowWindow(self.window_handle, win32con.SW_SHOW)

            try:
                win32gui.SetForegroundWindow(self.window_handle)
            except Exception as e:
                self.logger.warning(f"SetForegroundWindow failed: {e}, continuing anyway")
            time.sleep(0.8)

            self.window_rect = win32gui.GetWindowRect(self.window_handle)
            return True
        except Exception as e:
            self.last_error = f"Activate failed: {e}"
            self.logger.error(self.last_error)
            return False

    def _clear_search_box(self):
        """清除搜索框内容"""
        try:
            pyautogui.press('esc')
            time.sleep(0.2)
        except Exception:
            pass

    def _navigate_to_chat_list(self):
        """导航到微信聊天列表（保守策略：先 Esc 退出任何搜索/弹窗状态）"""
        # 先按 Esc 清除任何全局搜索、弹窗等状态
        self._clear_search_box()
        time.sleep(0.2)
        self._clear_search_box()
        time.sleep(0.2)
        
        # 如果知道窗口位置，再点击左侧消息图标作为双重保险
        if self.window_rect:
            wx, wy, wr, wb = self.window_rect
            # 尝试两个可能的聊天列表图标位置（不同微信版本布局有差异）
            candidates = [(wx + 35, wy + 130), (wx + 35, wy + 170)]
            for cx, cy in candidates:
                try:
                    pyautogui.click(cx, cy)
                    time.sleep(0.3)
                    # 点击后如果检测到全局搜索，说明点到了搜索图标，继续下一个候选
                    if self._detect_state() == "search":
                        self._clear_search_box()
                        time.sleep(0.2)
                        continue
                    # 如果进入聊天或未知状态，认为成功
                    break
                except Exception as e:
                    self.logger.warning(f"导航点击失败 ({cx}, {cy}): {e}")

    def _detect_state(self) -> str:
        """
        检测当前微信窗口状态
        Returns: "chat" | "search" | "contact_list" | "unknown"
        """
        if not self.window_rect:
            return "unknown"
        wx, wy, wr, wb = self.window_rect
        ww = wr - wx
        wh = wb - wy

        # 策略1: 检测全局搜索特征（中央区域出现"搜索"字样）
        center_region = (wx + ww // 4, wy + wh // 4, ww // 2, wh // 2)
        try:
            screenshot = self.screen.capture(region=center_region)
            texts = self.ocr.recognize(screenshot)
            all_text = " ".join([t.text for t in texts])
            search_keywords = ["搜索", "更多", "查找", "Search", "Find"]
            for kw in search_keywords:
                if kw in all_text:
                    return "search"
        except Exception:
            pass

        # 策略2: 检测右侧是否有聊天输入框特征（底部有"发送消息"提示或输入区域）
        bottom_region = (wx + 280, wy + int(wh * 0.85), ww - 280, int(wh * 0.15))
        try:
            screenshot = self.screen.capture(region=bottom_region)
            texts = self.ocr.recognize(screenshot)
            input_hints = ["发送消息", "Send", "按住", "说话", "表情"]
            for t in texts:
                for hint in input_hints:
                    if hint in t.text:
                        return "chat"
        except Exception:
            pass

        # 策略3: 检测通讯录特征
        left_region = (wx, wy + 80, min(280, ww), wh - 100)
        try:
            screenshot = self.screen.capture(region=left_region)
            texts = self.ocr.recognize(screenshot)
            all_text = " ".join([t.text for t in texts])
            contact_keywords = ["通讯录", "新的朋友", "群聊", "标签", "Contacts"]
            for kw in contact_keywords:
                if kw in all_text:
                    return "contact_list"
        except Exception:
            pass

        return "unknown"

    def _ensure_chat_state(self, contact: str) -> bool:
        """
        确保当前处于目标联系人的聊天窗口。
        直接验证聊天对象，不依赖状态检测的准确性。
        """
        # 直接验证是否在目标联系人聊天窗口
        result = self.validator.validate_chat_contact(self.window_handle, contact)
        if result.success:
            self.logger.info(f"已在 '{contact}' 聊天窗口")
            return True
        
        # 不在目标聊天，尝试修复状态
        state = self._detect_state()
        if state == "search":
            self.logger.info("检测到全局搜索状态，尝试退出")
            self._clear_search_box()
            time.sleep(0.3)
        
        self._navigate_to_chat_list()
        time.sleep(0.3)
        return False

    def search_contact(self, contact: str, use_ocr_selector: bool = True) -> bool:
        """Search and select a contact"""
        if not self.activate_wechat():
            return False

        try:
            # 1. 先确保在聊天列表状态
            self._navigate_to_chat_list()
            time.sleep(0.3)

            # 2. 点击左侧顶部搜索框
            search_box = self.coord_mapper.get_point_safe("wechat_search_box", self.window_rect)
            if search_box:
                pyautogui.click(search_box[0], search_box[1])
            else:
                # Fallback: Ctrl+F（可能打开全局搜索，不理想）
                pyautogui.keyDown('ctrl')
                pyautogui.keyDown('f')
                pyautogui.keyUp('f')
                pyautogui.keyUp('ctrl')
            time.sleep(0.3)

            # 3. 输入联系人（使用剪贴板粘贴，中文输入更可靠）
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('delete')
            try:
                import pyperclip
                pyperclip.copy(contact)
                pyautogui.hotkey('ctrl', 'v')
            except Exception:
                # Fallback: 直接 typewrite
                pyautogui.typewrite(contact, interval=0.01)
            time.sleep(0.8)

            if use_ocr_selector:
                wx, wy, wr, wb = self.window_rect

                # 4a. 优先：OCR 下拉框/搜索结果区域（搜索框下方，左侧列表内）
                # 扩大区域以覆盖更多可能的搜索结果
                dropdown_region = (wx, wy + 70, min(320, wr - wx), min(350, wb - wy - 100))
                try:
                    screenshot = self.screen.capture(region=dropdown_region)
                    texts = self.ocr.recognize(screenshot)
                    self.logger.debug(f"Dropdown OCR: {[b.text for b in texts]}")

                    # 优先精确匹配
                    best_match = None
                    best_score = -1.0
                    for box in texts:
                        text = box.text.strip()
                        if contact == text:
                            best_match = box
                            best_score = 100.0
                            break
                        elif contact in text:
                            score = len(contact) / max(len(text), 1)
                            if score > best_score:
                                best_match = box
                                best_score = score

                    if best_match:
                        abs_x = dropdown_region[0] + best_match.center[0]
                        abs_y = dropdown_region[1] + best_match.center[1]
                        self.logger.info(f"OCR matched '{contact}' in dropdown @ ({abs_x}, {abs_y})")
                        pyautogui.click(abs_x, abs_y)
                        time.sleep(0.8)
                        return True

                    self.logger.warning(f"OCR dropdown no exact match. Recognized: {[b.text for b in texts]}")
                except Exception as e:
                    self.logger.warning(f"OCR dropdown error: {e}")

                # 4b. Fallback: 扫描左侧整个列表区域
                list_region = (wx, wy + 70, min(320, wr - wx), wb - wy - 100)
                try:
                    screenshot = self.screen.capture(region=list_region)
                    texts = self.ocr.recognize(screenshot)
                    for box in texts:
                        if contact in box.text:
                            abs_x = list_region[0] + box.center[0]
                            abs_y = list_region[1] + box.center[1]
                            self.logger.info(f"OCR matched '{contact}' in list @ ({abs_x}, {abs_y})")
                            pyautogui.click(abs_x, abs_y)
                            time.sleep(0.8)
                            return True
                except Exception as e:
                    self.logger.warning(f"OCR list scan error: {e}")

            # 5. 最终 Fallback: 按 Enter
            pyautogui.press('enter')
            time.sleep(1.0)
            return True

        except Exception as e:
            self.last_error = f"Search contact failed: {e}"
            self.logger.error(self.last_error)
            return False

    def send_message_to_contact(self, contact: str, message: str, max_retries: int = 3) -> bool:
        """Send message to contact with intelligent retry and state recovery"""
        self.logger.info(f"Sending to {contact}")
        self.last_error = ""

        if not self.activate_wechat():
            return False

        # 所有策略都优先使用 OCR 点击，避免 Enter 进入全局搜索
        strategies = [
            {"name": "ocr_dropdown", "use_ocr": True, "enter_fallback": False},
            {"name": "ocr_list_wide", "use_ocr": True, "enter_fallback": True},
            {"name": "esc_recovery", "use_ocr": True, "enter_fallback": True},
        ]

        for attempt in range(max_retries):
            strategy = strategies[min(attempt, len(strategies) - 1)]
            self.logger.info(f"Attempt {attempt + 1}/{max_retries} using strategy: {strategy['name']}")

            try:
                # 重试前状态修复
                if attempt > 0:
                    self._clear_search_box()
                    time.sleep(0.3)
                    # 第三次尝试前强制回到聊天列表
                    if attempt == 2:
                        self._navigate_to_chat_list()
                        time.sleep(0.5)

                # 1. 如果已经处于目标联系人聊天窗口，跳过搜索
                if self._ensure_chat_state(contact):
                    self.logger.info("Already in target chat window")
                else:
                    # 搜索联系人
                    if not self.search_contact(contact, use_ocr_selector=strategy["use_ocr"]):
                        self.last_error = f"Attempt {attempt + 1}: Failed to search contact"
                        continue

                    # 如果策略允许 Enter fallback，search_contact 会按 Enter
                    # 此时可能进入全局搜索，需要检测并修复
                    if strategy.get("enter_fallback"):
                        time.sleep(0.5)
                        state = self._detect_state()
                        if state == "search":
                            self.logger.warning("Enter fallback led to global search, attempting recovery")
                            self._clear_search_box()
                            time.sleep(0.3)
                            self._navigate_to_chat_list()
                            time.sleep(0.3)
                            # 重试一次搜索（不用 Enter）
                            if not self.search_contact(contact, use_ocr_selector=True):
                                continue

                # 2. Validate correct contact is selected
                result = self.validator.validate_chat_contact(self.window_handle, contact)
                if not result.success:
                    self.logger.warning(f"Attempt {attempt + 1}: Contact validation failed, recognized: {result.found_text}")
                    self.last_error = f"Attempt {attempt + 1}: Contact validation failed"
                    # 如果检测到非聊天状态，尝试修复
                    state = self._detect_state()
                    if state != "chat":
                        self.logger.info(f"Detected state '{state}', will retry")
                    continue

                # 3. Click input box with adaptive coords + template fallback
                rect = self.window_rect
                input_point = self.coord_mapper.get_point_safe("wechat_input_box", rect)
                if input_point:
                    pyautogui.click(input_point[0], input_point[1])
                else:
                    # 极端 fallback
                    pyautogui.click(rect[0] + int((rect[2] - rect[0]) * 0.65), rect[1] + int((rect[3] - rect[1]) * 0.92))
                time.sleep(0.2)

                # 4. Type message（使用剪贴板粘贴，中文输入更可靠）
                try:
                    import pyperclip
                    pyperclip.copy(message)
                    pyautogui.hotkey('ctrl', 'v')
                except Exception:
                    pyautogui.typewrite(message, interval=0.01)
                time.sleep(0.2)

                # 5. 发送前最终确认
                pre_check = self.validator.pre_send_final_check(self.window_handle, contact)
                if not pre_check.success:
                    self.logger.warning(f"Attempt {attempt + 1}: Pre-send check failed, recognized: {pre_check.found_text}")
                    self.last_error = f"Attempt {attempt + 1}: Pre-send contact mismatch"
                    continue

                # 6. Send
                pyautogui.press('enter')
                time.sleep(0.5)

                # 7. Validate message sent
                result = self.validator.validate_message_sent(self.window_handle, message, timeout=3)
                if not result.success:
                    self.logger.warning(f"Attempt {attempt + 1}: Message validation failed, recognized: {result.found_text}")
                    self.last_error = f"Attempt {attempt + 1}: Message validation failed"
                    continue

                self.logger.info("Message sent successfully")
                return True

            except Exception as e:
                self.last_error = f"Attempt {attempt + 1}: Send failed: {e}"
                self.logger.error(self.last_error)
                continue

        # 所有尝试均失败，保存最后一张调试图
        try:
            if self.window_handle:
                rect = win32gui.GetWindowRect(self.window_handle)
                debug_screen = ScreenCapture().capture(region=rect)
                path = Path("logs") / f"wechat_retry_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                path.parent.mkdir(parents=True, exist_ok=True)
                ScreenCapture().save(debug_screen, path)
                self.last_error += f" (debug screenshot: {path})"
        except Exception:
            pass

        return False


def send_wechat_message(contact: str, message: str) -> bool:
    """Quick function to send WeChat message"""
    helper = WeChatHelper()
    success = helper.send_message_to_contact(contact, message)
    if success:
        print(f"SUCCESS: Message sent to {contact}")
        return True
    else:
        error_msg = helper.last_error or "Unknown error"
        print(f"FAILED: {error_msg}")
        return False
