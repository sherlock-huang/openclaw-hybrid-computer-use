"""
微信桌面助手 (WeChat Desktop Helper)

================================================================================
Agent Guide / AI 代理使用指南
================================================================================

【总体架构】
本模块基于 PyAutoGUI + OCR + win32gui 实现微信桌面版的自动化操作。
核心入口是 WeChatHelper 类，辅助类包括：
- WeChatOCRValidator：OCR 验证器，负责验证聊天对象和消息是否发送成功
- WeChatContactSelector：联系人选择器（外部模块），处理下拉框/列表匹配
- AdaptiveCoordinateMapper：自适应坐标映射器，根据窗口尺寸计算控件坐标

【WeChatHelper 典型使用方式】
    helper = WeChatHelper()          # 初始化（自动检测依赖）
    success = helper.send_message_to_contact("张三", "你好")
    if not success:
        print(helper.last_error)     # 查看失败原因

【常见坑点】
1. RDP 截图问题：
   - 如果通过远程桌面(RDP)连接，ScreenCapture 可能截取到黑屏或旧画面。
   - 解决：保持 RDP 会话活跃，或使用 console session。
2. pyautogui FAILSAFE：
   - 本模块已设置 pyautogui.FAILSAFE = False，因为自动化环境鼠标可能在角落。
   - 手动调试时如果想启用安全机制，请改回 True。
3. clipboard vs typewrite：
   - 中文输入优先使用剪贴板 (pyperclip.copy + Ctrl+V)，比 typewrite 稳定。
   - typewrite 在中文输入法激活时可能输出拼音而非汉字。
   - 如果 pyperclip 不可用，会自动降级到 typewrite。

【微信窗口布局假设（基于 PC 版微信 3.x）】
    +----------------------------------------------------------+
    | [≡] 搜索框                       联系人名称  [⋯]          |  <- 顶部标题栏 ~80px
    +------+---------------------------------------------------+
    |      |                                                   |
    | 侧栏 |  联系人/群聊列表 (左侧面板)                         |  <- 左侧边栏 ~60px
    | ~60px|  宽度 ~280px                                       |
    |      |                                                   |
    |      +---------------------------------------------------+
    |      |                                                   |
    |      |  右侧聊天区域                                      |
    |      |  消息历史 + 输入框                                 |
    |      |                                                   |
    +------+---------------------------------------------------+
坐标计算的关键分界点：
- 左侧边栏右边界 ≈ rect[0] + 280
- 右侧聊天区域左边界 ≈ rect[0] + 280
- 输入框通常位于窗口底部偏右 65% 位置

【状态机说明】
微信自动化涉及的状态流转如下：

    chat_list（聊天列表）
         |
         | 点击搜索框 / Ctrl+F
         v
      search（全局搜索）
         |
         | 输入关键词 → 按 Enter / 点击结果
         v
    global_search_result（全局搜索结果页）  <- 危险！容易进错联系人
         |
         | 点击联系人 → 进入个人资料页
         v
   contact_profile（联系人资料页）
         |
         | 点击"发消息"按钮
         v
      chat（正常聊天窗口）  <- 目标状态

风险提示：
- 全局搜索后按 Enter 可能进入"全局搜索结果页"而非直接打开聊天窗口，
  此时继续输入会被当成搜索词，导致消息发送失败。
- 本模块的策略是优先使用 OCR 点击搜索结果，避免使用 Enter。

================================================================================
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

# 微信窗口可能的标题关键词，用于遍历查找
WECHAT_WINDOW_TITLES = ["微信", "WeChat"]


@dataclass
class ValidationResult:
    """
    OCR 验证结果数据类。

    Attributes:
        success: 验证是否通过
        found_text: OCR 识别到的实际文字（用于调试）
        confidence: OCR 置信度
        screenshot_path: 失败时保存的调试图路径（可选）
    """
    success: bool
    found_text: str
    confidence: float
    screenshot_path: Optional[str] = None


class WeChatOCRValidator:
    """
    微信 OCR 验证器。

    负责通过 OCR 截图验证以下场景：
    1. 当前聊天窗口顶部显示的是否为预期联系人
    2. 消息是否成功出现在聊天记录中
    3. 当前聊天是否为群聊

    设计原则：所有验证均基于视觉 OCR，不依赖内存读取或 API 调用，
    因此兼容不同版本的微信客户端。
    """

    def __init__(self):
        # ScreenCapture 负责截取指定屏幕区域
        self.screen = ScreenCapture()
        # TextRecognizer 负责识别截图中的文字
        self.ocr = TextRecognizer()
        self.logger = logging.getLogger(__name__)

    def _save_debug_screenshot(self, image, prefix: str) -> str:
        """
        保存调试图到 logs 目录，便于事后分析失败原因。

        Parameters:
            image: ScreenCapture 返回的图像对象
            prefix: 文件名前缀，建议描述场景（如 validate_contact_fail）

        Returns:
            保存后的绝对路径字符串
        """
        logs_dir = Path("logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = logs_dir / f"{prefix}_{timestamp}.png"
        self.screen.save(image, path)
        return str(path)

    def _estimate_left_panel_width(self, hwnd) -> int:
        """
        估算微信左侧面栏宽度。

        策略：截取窗口左侧区域，OCR 查找 "微信" 图标/文字，
        若找到则假设列表边界在其右侧不远处；否则回退到 280px。
        此值用于计算右侧聊天区域的起始 x 坐标。

        Parameters:
            hwnd: 微信窗口句柄

        Returns:
            int: 估算的左侧面板宽度（像素），默认 280
        """
        try:
            rect = win32gui.GetWindowRect(hwnd)
            wx, wy, wr, wb = rect
            ww = wr - wx
            # 扫描左侧 1/3 宽度、顶部 120px 区域
            left_region = (wx, wy, max(ww // 3, 200), 120)
            screenshot = self.screen.capture(region=left_region)
            texts = self.ocr.recognize(screenshot)
            # 查找 "微信" 或 "WeChat" 位置，取最靠右的 x 作为参考
            max_right = 0
            for box in texts:
                if "微信" in box.text or "WeChat" in box.text:
                    # box.center[0] 是相对于 region 的坐标
                    abs_right = wx + box.center[0] + 60  # 图标右侧再留 60px 边距
                    if abs_right > max_right:
                        max_right = abs_right
            if max_right > 0:
                # 转换为相对于窗口左边缘的宽度
                return min(int(max_right - wx), ww // 2)
        except Exception:
            pass
        return 280

    def validate_chat_contact(self, hwnd, expected_contact: str, save_screenshot_on_fail: bool = True,
                               is_group_chat: bool = False) -> ValidationResult:
        """
        验证当前聊天窗口中选中的联系人/群聊是否为预期对象。

        检测策略（按优先级）：
        1. 截取窗口顶部标题栏区域（动态估算左侧面板宽度以右，高度 80px），
           通过 OCR 查找预期联系人名称。
        2. 若标题栏未匹配， fallback 到右侧聊天区域上方 header 区域
           （y 偏移约 50px，高度 80px），有时联系人名称显示在此处。
        3. 扫描整个窗口顶部 120px 全宽度区域（覆盖不同布局版本）。

        Parameters:
            hwnd: 微信窗口句柄（win32 HWND）
            expected_contact: 期望的联系人/群聊名称
            save_screenshot_on_fail: 失败时是否保存调试图
            is_group_chat: 是否为群聊。群聊模式下匹配规则更宽松
                          （允许子串、前缀、前4字匹配）

        Returns:
            ValidationResult 对象。success=True 表示验证通过。

        Possible Failure Modes:
            - 窗口句柄无效或已关闭 → 返回 success=False, found_text=""
            - OCR 未识别到预期名称 → 返回 success=False，附带识别到的所有文字
            - 微信窗口被其他窗口遮挡 → OCR 可能识别到错误的文字
        """
        try:
            rect = win32gui.GetWindowRect(hwnd)
        except Exception as e:
            self.logger.error(f"获取窗口位置失败: {e}")
            return ValidationResult(False, "", 0.0)

        wx, wy, wr, wb = rect
        ww = wr - wx
        left_w = self._estimate_left_panel_width(hwnd)

        # 策略1：顶部标题栏区域（右侧面板顶部）
        title_region = (wx + left_w, wy, ww - left_w, 80)
        title_screenshot = self.screen.capture(region=title_region)
        title_texts = self.ocr.recognize(title_screenshot)
        for text_box in title_texts:
            if self._contact_match(expected_contact, text_box.text, is_group_chat):
                return ValidationResult(True, text_box.text, text_box.confidence)

        # 策略2：右侧聊天内容区域上方 header（y 偏移 50px，高度 80px）
        header_region = (wx + left_w, wy + 50, ww - left_w, 80)
        header_screenshot = self.screen.capture(region=header_region)
        header_texts = self.ocr.recognize(header_screenshot)
        for text_box in header_texts:
            if self._contact_match(expected_contact, text_box.text, is_group_chat):
                return ValidationResult(True, text_box.text, text_box.confidence)

        # 策略3：扫描整个窗口顶部 120px（覆盖布局差异/左侧面板宽度估算不准的情况）
        full_top_region = (wx, wy, ww, 120)
        full_top_screenshot = self.screen.capture(region=full_top_region)
        full_top_texts = self.ocr.recognize(full_top_screenshot)
        for text_box in full_top_texts:
            if self._contact_match(expected_contact, text_box.text, is_group_chat):
                return ValidationResult(True, text_box.text, text_box.confidence)

        # 所有策略均未匹配，汇总识别到的文字用于调试
        all_text = " ".join([t.text for t in title_texts + header_texts + full_top_texts])
        screenshot_path = None
        if save_screenshot_on_fail:
            screenshot_path = self._save_debug_screenshot(title_screenshot, f"wechat_validate_contact_fail")
        return ValidationResult(False, all_text, 0.0, screenshot_path)
    
    def _contact_match(self, expected: str, found: str, is_group_chat: bool = False) -> bool:
        """
        判断预期联系人名称是否匹配 OCR 识别到的文字。

        匹配规则：
        - 通用规则：expected 是 found 的子串即匹配（如 expected="张三"，found="张三 (2)"）
        - 群聊额外规则：
            a) found 是 expected 的子串（群聊名被截断，如 "技术交流群" 识别为 "技术"）
            b) 双方长度均 >=4 时，比较前 4 个字是否相同（适用于长群名被截断的场景）

        Parameters:
            expected: 预期名称
            found: OCR 实际识别到的文字
            is_group_chat: 是否启用群聊宽松匹配

        Returns:
            bool: 是否匹配
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
        发送前的最终确认：验证聊天对象无误。

        在按 Enter 发送消息前的最后一道防线。
        逻辑与 validate_chat_contact 基本相同，但会同时扫描
        顶部标题栏和右侧聊天 header 区域，确保万无一失。

        Parameters:
            hwnd: 微信窗口句柄
            expected_contact: 预期联系人名称
            save_screenshot_on_fail: 失败时是否保存调试图
            is_group_chat: 是否为群聊

        Returns:
            ValidationResult。success=True 表示可以放心发送。

        Possible Failure Modes:
            - 同 validate_chat_contact
            - 窗口在验证过程中被用户切换了聊天对象 → 拦截发送
        """
        try:
            rect = win32gui.GetWindowRect(hwnd)
        except Exception as e:
            self.logger.error(f"获取窗口位置失败: {e}")
            return ValidationResult(False, "", 0.0)

        wx, wy, wr, wb = rect
        ww = wr - wx
        left_w = self._estimate_left_panel_width(hwnd)

        # 同时验证顶部标题栏和右侧聊天区域上方
        title_region = (wx + left_w, wy, ww - left_w, 80)
        title_screenshot = self.screen.capture(region=title_region)
        title_texts = self.ocr.recognize(title_screenshot)

        for text_box in title_texts:
            if self._contact_match(expected_contact, text_box.text, is_group_chat):
                return ValidationResult(True, text_box.text, text_box.confidence)

        header_region = (wx + left_w, wy + 50, ww - left_w, 80)
        header_screenshot = self.screen.capture(region=header_region)
        header_texts = self.ocr.recognize(header_screenshot)

        for text_box in header_texts:
            if self._contact_match(expected_contact, text_box.text, is_group_chat):
                return ValidationResult(True, text_box.text, text_box.confidence)

        # 扫描整个窗口顶部 120px 全宽度区域
        full_top_region = (wx, wy, ww, 120)
        full_top_screenshot = self.screen.capture(region=full_top_region)
        full_top_texts = self.ocr.recognize(full_top_screenshot)
        for text_box in full_top_texts:
            if self._contact_match(expected_contact, text_box.text, is_group_chat):
                return ValidationResult(True, text_box.text, text_box.confidence)

        all_text = " ".join([t.text for t in title_texts + header_texts + full_top_texts])
        screenshot_path = None
        if save_screenshot_on_fail:
            screenshot_path = self._save_debug_screenshot(title_screenshot, f"wechat_pre_send_check_fail")
        return ValidationResult(False, all_text, 0.0, screenshot_path)

    def validate_group_chat_features(self, hwnd) -> ValidationResult:
        """
        验证当前聊天窗口是否具有群聊特征。

        通过 OCR 在右侧聊天 header 区域查找特征词：
        "群成员"、"群公告"、"Group Members"、"Group Notice"

        Parameters:
            hwnd: 微信窗口句柄

        Returns:
            ValidationResult。success=True 表示检测到群聊特征。

        Possible Failure Modes:
            - 微信版本不同，群聊按钮文案可能变化
            - 窗口尺寸过小导致按钮被折叠 → 可能检测失败
        """
        try:
            rect = win32gui.GetWindowRect(hwnd)
        except Exception as e:
            self.logger.error(f"获取窗口位置失败: {e}")
            return ValidationResult(False, "", 0.0)

        wx, wy, wr, wb = rect
        ww = wr - wx
        left_w = self._estimate_left_panel_width(hwnd)

        # 右侧聊天区域上方，查找群聊按钮区域
        header_region = (wx + left_w, wy + 50, ww - left_w, 80)
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
        """
        从消息中提取可用于模糊验证的标识符。

        当消息较长或含中文时，精确匹配可能因 OCR 误差失败。
        此时提取消息中的数字、时间、英文单词等"硬标识"进行模糊匹配。

        提取规则：
        - 时间格式：HH:MM 或 HH:MM:SS
        - 数字串：至少连续 2 位数字
        - ASCII 单词：至少 3 个连续英文字母
        - 过滤：去重，且长度 >=4 才保留（太短容易误匹配）

        Parameters:
            message: 预期发送的消息文本

        Returns:
            标识符字符串列表，按原始出现顺序排列
        """
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
        # 去重并过滤（长度 <4 的标识符容易误匹配，丢弃）
        seen = set()
        result = []
        for ident in identifiers:
            if ident not in seen and len(ident) >= 4:
                seen.add(ident)
                result.append(ident)
        return result

    def validate_message_sent(self, hwnd, expected_message: str, timeout: int = 3,
                              save_screenshot_on_fail: bool = True) -> ValidationResult:
        """
        验证消息是否成功出现在聊天记录中。

        检测策略（按优先级，在 timeout 内循环轮询）：
        1. 优先扫描底部小区域（最新消息通常在此），OCR 查找完整消息。
        2. 若未找到，扩大扫描整个右侧聊天区域，优先匹配右下角
           （自己发送的消息气泡通常在右侧）。
        3. 若完整消息未匹配，提取消息中的"硬标识"（数字、时间、英文），
           进行模糊匹配。

        Parameters:
            hwnd: 微信窗口句柄
            expected_message: 预期发送的消息文本
            timeout: 最大等待秒数（默认 3 秒）
            save_screenshot_on_fail: 失败时是否保存调试图

        Returns:
            ValidationResult。success=True 表示消息已出现在聊天记录中。

        Possible Failure Modes:
            - 消息发送成功但 OCR 未识别 → 可能因字体、颜色、气泡样式导致
            - 聊天窗口滚动导致消息不在可视区域 → 本函数不会自动滚动
            - 发送失败但返回 True（假阳性）→ 如果消息恰好已存在于历史记录中
            - 超时：网络延迟高或微信卡顿导致消息未及时显示
        """
        start = time.time()
        last_texts = ""
        identifiers = self._extract_identifiers(expected_message)
        
        while time.time() - start < timeout:
            try:
                rect = win32gui.GetWindowRect(hwnd)
            except Exception:
                # 窗口可能短暂不可用，等待后重试
                time.sleep(0.5)
                continue

            wx, wy, wr, wb = rect
            ww = wr - wx
            wh = wb - wy
            left_w = self._estimate_left_panel_width(hwnd)
            chat_ww = ww - left_w

            # 策略1：优先扫描底部小区域（最新消息通常在此）
            # 计算窗口尺寸，底部区域取最后 200px 或窗口高度的 1/3（取小者）
            bottom_region = (wx + left_w, wb - min(200, wh // 3), chat_ww, min(200, wh // 3))
            try:
                screenshot = self.screen.capture(region=bottom_region)
                texts = self.ocr.recognize(screenshot)
                for text_box in texts:
                    # 精确匹配
                    if expected_message in text_box.text:
                        return ValidationResult(True, text_box.text, text_box.confidence)
                    # 模糊匹配：标识符命中
                    if identifiers:
                        for ident in identifiers:
                            if ident in text_box.text:
                                self.logger.info(f"Fuzzy match: identifier '{ident}' found in bottom region")
                                return ValidationResult(True, text_box.text, text_box.confidence)
            except Exception as e:
                self.logger.warning(f"Bottom region OCR failed: {e}")

            # 策略2：扩大扫描整个右侧聊天区域
            chat_region = (wx + left_w, wy + 80, chat_ww, wh - 100)
            screenshot = self.screen.capture(region=chat_region)
            texts = self.ocr.recognize(screenshot)

            # 自己发送的消息通常在右下角区域，优先加权匹配此处
            # right_half_x: 聊天区域右半部分起始 x
            # bottom_third_y: 聊天区域下 1/3 起始 y
            right_half_x = wx + left_w + chat_ww // 2
            bottom_third_y = wy + 80 + int((wh - 100) * 0.65)
            
            # 2a. 精确匹配：右下角优先（自己发送的消息通常在右侧气泡中）
            for text_box in texts:
                box_x, box_y = text_box.center
                # text_box.center 是相对于 chat_region 的坐标，需转换为绝对坐标
                abs_box_x = chat_region[0] + box_x
                abs_box_y = chat_region[1] + box_y
                
                if expected_message in text_box.text:
                    if abs_box_x >= right_half_x and abs_box_y >= bottom_third_y:
                        return ValidationResult(True, text_box.text, text_box.confidence)
            
            # 2b. 精确匹配：全聊天区域（不限制位置）
            for text_box in texts:
                if expected_message in text_box.text:
                    return ValidationResult(True, text_box.text, text_box.confidence)
            
            # 2c. 模糊匹配：如果消息含数字/时间/英文，验证关键标识符
            if identifiers:
                # 先收集位于底部区域的所有文本框
                bottom_texts = []
                for text_box in texts:
                    box_x, box_y = text_box.center
                    abs_box_y = chat_region[1] + box_y
                    if abs_box_y >= bottom_third_y:
                        bottom_texts.append(text_box)
                
                # 优先在底部区域匹配标识符
                for ident in identifiers:
                    for text_box in bottom_texts:
                        if ident in text_box.text:
                            self.logger.info(f"Fuzzy match: identifier '{ident}' found in bottom area")
                            return ValidationResult(True, text_box.text, text_box.confidence)
                    
                    # 底部未命中，扩大至全聊天区域
                    for text_box in texts:
                        if ident in text_box.text:
                            self.logger.info(f"Fuzzy match: identifier '{ident}' found in chat area")
                            return ValidationResult(True, text_box.text, text_box.confidence)
                    
            # 本轮未匹配，记录识别到的文字用于最终失败报告
            last_texts = " ".join([t.text for t in texts])
            time.sleep(0.5)

        # 超时退出，保存调试图
        screenshot_path = None
        if save_screenshot_on_fail:
            try:
                screenshot_path = self._save_debug_screenshot(screenshot, f"wechat_validate_msg_fail")
            except Exception:
                pass
        return ValidationResult(False, last_texts, 0.0, screenshot_path)


class WeChatHelper:
    """
    微信桌面自动化助手主类。

    提供完整的微信消息发送流程：
    1. 查找并激活微信窗口
    2. 搜索并选择联系人
    3. 输入并发送消息
    4. 多重验证确保发送成功

    依赖：
    - pywin32：用于窗口句柄操作（FindWindow、SetForegroundWindow 等）
    - pyautogui：用于模拟鼠标点击和键盘输入
    - pyperclip（可选但推荐）：用于中文剪贴板粘贴

    重要配置：
    - FAILSAFE = False：禁用 pyautogui 的鼠标角落安全机制（自动化环境需要）
    - PAUSE = 0.05：每次 pyautogui 操作后的默认停顿时间（秒）
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.window_handle = None   # 微信窗口句柄（缓存）
        self.window_rect = None     # 微信窗口矩形坐标 (left, top, right, bottom)
        self.contact_selector = WeChatContactSelector()
        self.validator = WeChatOCRValidator()
        self.coord_mapper = AdaptiveCoordinateMapper()
        self.screen = ScreenCapture()
        self.ocr = TextRecognizer()
        self.last_error = ""        # 最后一次失败的错误信息

        # 检查必要依赖
        if not WIN32_AVAILABLE:
            raise ImportError("pywin32 required: py -m pip install pywin32")

        if not PYAUTOGUI_AVAILABLE:
            raise ImportError("pyautogui required: py -m pip install pyautogui")

        # 自动化环境禁用 fail-safe（鼠标在屏幕角落不会抛出异常）
        pyautogui.FAILSAFE = False
        # 每次 pyautogui 操作后停顿 50ms，减少操作过快导致的丢事件
        pyautogui.PAUSE = 0.05

    def find_wechat_window(self) -> Optional[int]:
        """
        查找微信窗口句柄。

        采用多级 fallback 策略（按优先级）：
        1. EnumWindows 遍历所有可见窗口，匹配标题含 "微信" 或 "WeChat"。
        2. FindWindow 通过类名 "WeChatMainWndForPC" 查找（不受标题变化影响）。
        3. FindWindow 通过固定标题 "微信" 或 "WeChat" 查找。
        4. 再次 EnumWindows，这次不限制可见性（包括最小化窗口）。

        找到后缓存句柄和窗口矩形到 self.window_handle / self.window_rect。

        Returns:
            窗口句柄（int）或 None（未找到）

        Possible Failure Modes:
            - 微信未运行 → 返回 None
            - 微信以管理员权限运行但当前进程不是 → 可能无法枚举到窗口
            - 多开微信 → 返回找到的第一个窗口
        """
        def callback(hwnd, extra):
            try:
                if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    for keyword in WECHAT_WINDOW_TITLES:
                        if keyword in title:
                            extra.append(hwnd)
                            return False  # 找到即停止枚举
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

        # 缓存首个找到的句柄
        if handles:
            self.window_handle = handles[0]
            try:
                self.window_rect = win32gui.GetWindowRect(self.window_handle)
                return self.window_handle
            except Exception:
                pass

        return None

    def activate_wechat(self) -> bool:
        """
        激活微信窗口（如果最小化则恢复，如果被遮挡则置顶）。

        激活流程：
        1. 如果窗口未找到，先调用 find_wechat_window()。
        2. 如果窗口最小化(IsIconic)，执行 SW_RESTORE 恢复。
        3. 如果窗口不可见，执行 SW_SHOW。
        4. 调用 SetForegroundWindow 尝试置顶（可能因权限失败，但不阻断流程）。
        5. 等待 0.8 秒让窗口完成渲染，然后更新 self.window_rect。

        Returns:
            bool: 激活成功/失败

        Possible Failure Modes:
            - 微信未运行 → 返回 False，last_error 记录 "WeChat window not found"
            - SetForegroundWindow 因权限或焦点抢占失败 → 记录 warning，继续执行
            - 窗口激活后被用户立即切换走 → 后续坐标计算可能偏差
        """
        if not self.window_handle:
            if not self.find_wechat_window():
                self.last_error = "WeChat window not found"
                return False

        try:
            # 窗口最小化时恢复
            if win32gui.IsIconic(self.window_handle):
                win32gui.ShowWindow(self.window_handle, win32con.SW_RESTORE)
            # 窗口隐藏时显示
            elif not win32gui.IsWindowVisible(self.window_handle):
                win32gui.ShowWindow(self.window_handle, win32con.SW_SHOW)

            try:
                # 尝试将窗口设为前台（可能因权限失败）
                win32gui.SetForegroundWindow(self.window_handle)
            except Exception as e:
                self.logger.warning(f"SetForegroundWindow failed: {e}, continuing anyway")
            # 等待窗口渲染完成，否则后续截图可能抓到旧画面
            time.sleep(0.8)

            # 更新窗口坐标缓存（窗口恢复后位置可能变化）
            self.window_rect = win32gui.GetWindowRect(self.window_handle)
            return True
        except Exception as e:
            self.last_error = f"Activate failed: {e}"
            self.logger.error(self.last_error)
            return False

    def _clear_search_box(self):
        """
        清除搜索框内容，用于退出全局搜索或其他弹窗状态。

        实现：按 Esc 键。微信中 Esc 通常用于关闭搜索、取消弹窗、返回上级。
        若按 Esc 异常（pyautogui 报错），静默忽略。
        """
        try:
            pyautogui.press('esc')
            time.sleep(0.2)
        except Exception:
            pass

    def _navigate_to_chat_list(self):
        """
        导航到微信聊天列表（保守策略）。

        执行步骤：
        1. 连续按两次 Esc，清除任何全局搜索、弹窗、子页面状态，回到最顶层。
        2. 如果知道窗口位置，点击左侧消息图标作为双重保险。
           尝试两个候选坐标（wx+35, wy+130）和（wx+35, wy+170），
           因为不同微信版本侧边栏图标位置略有差异。
        3. 点击后如果检测到全局搜索状态（_detect_state() == "search"），
           说明点到了搜索图标而非消息图标，继续尝试下一个候选坐标。

        Possible Failure Modes:
            - 窗口坐标未知（self.window_rect 为 None）→ 仅按 Esc，不点击
            - 两个候选坐标均触发搜索 → 最终停留在搜索状态，需外部修复
        """
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
        检测当前微信窗口状态。

        通过 OCR 扫描不同区域，推断当前处于以下哪种状态：
        - "chat": 正常聊天窗口（检测到"发送消息"、"Send"、"表情"等输入框特征）
        - "search": 全局搜索（中央区域出现"搜索"、"更多"等字样）
        - "contact_list": 通讯录（左侧出现"通讯录"、"新的朋友"等字样）
        - "contact_profile": 联系人资料页（出现"发消息"按钮）
        - "unknown": 无法判断（可能是加载中、或特殊页面）

        Returns:
            str: 状态标识字符串

        注意：状态检测基于 OCR，可能因分辨率、主题、弹窗干扰而误判。
              核心业务逻辑不应强依赖此函数的精确性。
        """
        if not self.window_rect:
            return "unknown"
        wx, wy, wr, wb = self.window_rect
        ww = wr - wx
        wh = wb - wy
        # 使用动态估算的左侧面板宽度（避免不同版本/分辨率硬编码 280px 失效）
        left_w = min(320, max(200, ww // 3))

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
        bottom_region = (wx + left_w, wy + int(wh * 0.85), ww - left_w, int(wh * 0.15))
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
        left_region = (wx, wy + 80, left_w, wh - 100)
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

        # 策略4: 检测联系人资料页（出现"发消息"按钮）
        profile_region = (wx + left_w, wy + wh // 4, ww - left_w, wh // 2)
        try:
            screenshot = self.screen.capture(region=profile_region)
            texts = self.ocr.recognize(screenshot)
            all_text = " ".join([t.text for t in texts])
            profile_keywords = ["发消息", "Message", "音视频通话", "Video Call", "朋友圈", "Moments"]
            for kw in profile_keywords:
                if kw in all_text:
                    return "contact_profile"
        except Exception:
            pass

        return "unknown"

    def _ensure_chat_state(self, contact: str) -> bool:
        """
        确保当前处于目标联系人的聊天窗口。

        不依赖 _detect_state() 的精确性，而是直接通过 OCR 验证聊天对象。
        如果已在目标聊天窗口，直接返回 True；否则尝试修复状态并返回 False，
        由调用方重新执行搜索流程。

        Parameters:
            contact: 目标联系人名称

        Returns:
            bool: True 表示已在目标聊天窗口；False 表示需要重新搜索
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
        elif state == "contact_profile":
            self.logger.info("检测到联系人资料页，尝试点击'发消息'进入聊天")
            self._click_message_button_in_profile()
            time.sleep(0.5)
            # 再次验证
            result = self.validator.validate_chat_contact(self.window_handle, contact)
            if result.success:
                self.logger.info(f"从资料页进入 '{contact}' 聊天窗口")
                return True

        # 尝试回到聊天列表，为后续搜索做准备
        self._navigate_to_chat_list()
        time.sleep(0.3)
        return False

    def _click_message_button_in_profile(self) -> bool:
        """
        在联系人资料页中点击'发消息'按钮，尝试进入聊天窗口。

        策略：扫描窗口右侧中央区域，OCR 查找 "发消息" / "Message"，
        点击匹配到的文本位置。若 OCR 未命中，则 fallback 到固定比例坐标。

        Returns:
            bool: 是否执行了点击操作
        """
        if not self.window_rect:
            return False
        wx, wy, wr, wb = self.window_rect
        ww = wr - wx
        wh = wb - wy
        left_w = min(320, max(200, ww // 3))

        # 扫描右侧中央偏上区域（"发消息"按钮通常在此）
        profile_region = (wx + left_w, wy + wh // 4, ww - left_w, wh // 2)
        try:
            screenshot = self.screen.capture(region=profile_region)
            texts = self.ocr.recognize(screenshot)
            for box in texts:
                if "发消息" in box.text or "Message" in box.text:
                    abs_x = profile_region[0] + box.center[0]
                    abs_y = profile_region[1] + box.center[1]
                    self.logger.info(f"点击'发消息'按钮 @ ({abs_x}, {abs_y})")
                    pyautogui.click(abs_x, abs_y)
                    return True
        except Exception as e:
            self.logger.warning(f"OCR 查找'发消息'按钮失败: {e}")

        # Fallback: 固定比例坐标（右侧中央偏上）
        fallback_x = wx + left_w + int((ww - left_w) * 0.5)
        fallback_y = wy + int(wh * 0.45)
        self.logger.info(f"Fallback 点击'发消息'预估坐标 @ ({fallback_x}, {fallback_y})")
        pyautogui.click(fallback_x, fallback_y)
        return True

    def _wait_for_chat_state(self, contact: str, timeout: float = 3.0, interval: float = 0.2) -> bool:
        """
        轮询等待进入目标联系人的聊天窗口。

        在 search_contact 点击联系人后调用，替代固定的 time.sleep，
        通过 OCR 验证当前是否已进入正确的聊天窗口。

        Parameters:
            contact: 目标联系人名称
            timeout: 最大等待秒数（默认 3.0）
            interval: 轮询间隔秒数（默认 0.2）

        Returns:
            bool: True 表示成功进入聊天窗口；False 表示超时未进入
        """
        start = time.time()
        while time.time() - start < timeout:
            # 优先验证联系人名称
            result = self.validator.validate_chat_contact(self.window_handle, contact)
            if result.success:
                self.logger.info(f"验证通过：已进入 '{contact}' 聊天窗口")
                return True

            # 其次检测是否处于聊天状态
            state = self._detect_state()
            if state == "chat":
                # 即使检测到 chat 状态，也再验证一次联系人
                result = self.validator.validate_chat_contact(self.window_handle, contact)
                if result.success:
                    return True
                # 如果处于 chat 但验证未通过，说明可能进错了聊天
                self.logger.warning(f"进入聊天状态但验证联系人失败， recognized: {result.found_text}")
                return False

            # 如果进入了联系人资料页，尝试点击"发消息"
            if state == "contact_profile":
                self.logger.info("检测到联系人资料页，尝试点击'发消息'")
                self._click_message_button_in_profile()

            time.sleep(interval)

        self.logger.warning(f"等待进入 '{contact}' 聊天窗口超时（{timeout}s）")
        return False

    def search_contact(self, contact: str, use_ocr_selector: bool = True) -> bool:
        """
        搜索并选择联系人，进入聊天窗口。

        执行流程：
        1. 先确保在聊天列表状态（_navigate_to_chat_list）。
        2. 点击左侧顶部搜索框（优先使用自适应坐标映射，fallback 到 Ctrl+F）。
        3. 全选并清空搜索框，通过剪贴板粘贴联系人名称（中文更可靠）。
        4. 等待搜索结果显示。
        5. 如果 use_ocr_selector=True：
           a) 优先扫描搜索下拉框区域，OCR 匹配联系人名称并点击。
           b) 若下拉框未匹配，扫描整个左侧列表区域。
        6. 最终 fallback：按 Enter（有进入全局搜索的风险，已在外部处理）。

        Parameters:
            contact: 要搜索的联系人/群聊名称
            use_ocr_selector: 是否启用 OCR 点击匹配（推荐 True）

        Returns:
            bool: 搜索并点击完成（不保证一定进入了正确聊天窗口，需后续验证）

        Possible Failure Modes:
            - 微信未激活 → 返回 False
            - OCR 未识别到联系人 → 依赖 Enter fallback，可能进入全局搜索
            - 搜索框坐标映射失败 → fallback 到 Ctrl+F，可能打开全局搜索
        """
        if not self.activate_wechat():
            return False

        try:
            # 1. 先确保在聊天列表状态
            self._navigate_to_chat_list()
            time.sleep(0.3)

            # 2. 点击左侧顶部搜索框
            # get_point_safe 根据窗口矩形和预定义模板返回坐标，失败时返回 None
            search_box = self.coord_mapper.get_point_safe("wechat_search_box", self.window_rect)
            if search_box:
                pyautogui.click(search_box[0], search_box[1])
            else:
                # Fallback: Ctrl+F（可能打开全局搜索，不理想，但比无法操作强）
                pyautogui.keyDown('ctrl')
                pyautogui.keyDown('f')
                pyautogui.keyUp('f')
                pyautogui.keyUp('ctrl')
            time.sleep(0.3)

            # 3. 输入联系人（使用剪贴板粘贴，中文输入更可靠）
            pyautogui.hotkey('ctrl', 'a')   # 全选已有内容
            pyautogui.press('delete')        # 清空
            try:
                import pyperclip
                pyperclip.copy(contact)
                pyautogui.hotkey('ctrl', 'v')  # 粘贴
            except Exception:
                # Fallback: 直接 typewrite（中文输入法激活时可能输出拼音）
                pyautogui.typewrite(contact, interval=0.01)
            time.sleep(0.8)

            if use_ocr_selector:
                wx, wy, wr, wb = self.window_rect

                # 4a. 优先：OCR 下拉框/搜索结果区域（搜索框下方，左侧列表内）
                # 扩大区域以覆盖更多可能的搜索结果
                # 宽度 min(320, wr-wx)：不超过列表宽度；高度 min(350, wb-wy-100)：向下延伸
                dropdown_region = (wx, wy + 70, min(320, wr - wx), min(350, wb - wy - 100))
                try:
                    screenshot = self.screen.capture(region=dropdown_region)
                    texts = self.ocr.recognize(screenshot)
                    self.logger.debug(f"Dropdown OCR: {[b.text for b in texts]}")

                    # 优先精确匹配，其次子串匹配（选择匹配度最高的）
                    best_match = None
                    best_score = -1.0
                    for box in texts:
                        text = box.text.strip()
                        if contact == text:
                            best_match = box
                            best_score = 100.0
                            break
                        elif contact in text:
                            # 子串匹配得分：contact 长度占 text 长度的比例
                            score = len(contact) / max(len(text), 1)
                            if score > best_score:
                                best_match = box
                                best_score = score

                    if best_match:
                        # box.center 是相对于 region 的坐标，需转换为屏幕绝对坐标
                        abs_x = dropdown_region[0] + best_match.center[0]
                        abs_y = dropdown_region[1] + best_match.center[1]
                        self.logger.info(f"OCR matched '{contact}' in dropdown @ ({abs_x}, {abs_y})")
                        pyautogui.click(abs_x, abs_y)
                        # 轮询等待进入聊天窗口，替代固定 sleep
                        if self._wait_for_chat_state(contact, timeout=3.0):
                            return True
                        # 超时未进入聊天窗口，但仍返回 True（点击已执行，后续由验证层拦截）
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
                            # 轮询等待进入聊天窗口
                            if self._wait_for_chat_state(contact, timeout=3.0):
                                return True
                            return True
                except Exception as e:
                    self.logger.warning(f"OCR list scan error: {e}")

            # 5. 最终 Fallback: 按 Enter
            # 注意：此操作有较高概率进入"全局搜索结果页"而非直接打开聊天
            pyautogui.press('enter')
            # 轮询等待进入聊天窗口
            if self._wait_for_chat_state(contact, timeout=3.0):
                return True
            return True

        except Exception as e:
            self.last_error = f"Search contact failed: {e}"
            self.logger.error(self.last_error)
            return False

    def send_message_to_contact(self, contact: str, message: str, max_retries: int = 3) -> bool:
        """
        向指定联系人发送消息，包含智能重试和状态恢复机制。

        完整流程（每轮重试）：
        1. 激活微信窗口。
        2. 验证是否已在目标聊天窗口；若不在，执行搜索。
        3. OCR 验证当前聊天对象是否正确。
        4. 点击输入框（自适应坐标 + 极端 fallback）。
        5. 粘贴消息（剪贴板优先，降级 typewrite）。
        6. 发送前最终确认（pre_send_final_check）。
        7. 按 Enter 发送。
        8. OCR 验证消息是否出现在聊天记录中。

        重试策略（3 种策略轮换）：
        - 第1次：ocr_dropdown（纯 OCR 点击，禁用 Enter fallback）
        - 第2次：ocr_list_wide（OCR 扫描全列表，允许 Enter fallback）
        - 第3次：esc_recovery（先 Esc 清空状态，再尝试）

        Parameters:
            contact: 联系人/群聊名称
            message: 要发送的消息文本
            max_retries: 最大重试次数（默认 3）

        Returns:
            bool: True 表示发送并验证成功；False 表示所有尝试均失败

        Possible Failure Modes:
            - 微信窗口未找到 → 立即返回 False
            - 联系人搜索失败 → 记录错误，进入下一次重试
            - 联系人验证失败（进错聊天）→ 拦截发送，重试
            - 发送前最终确认失败 → 拦截发送，重试
            - 消息验证失败（发送后未在聊天记录中找到）→ 重试
            - 所有重试耗尽 → 保存最终调试图到 logs/，返回 False
        """
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
            # 根据尝试次数选择策略（越往后越保守）
            strategy = strategies[min(attempt, len(strategies) - 1)]
            self.logger.info(f"Attempt {attempt + 1}/{max_retries} using strategy: {strategy['name']}")

            try:
                # 重试前状态修复
                if attempt > 0:
                    self._clear_search_box()
                    time.sleep(0.3)
                    # 第三次尝试前强制回到聊天列表，彻底重置状态
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
                    if state == "contact_profile":
                        self.logger.info("Detected contact profile page, attempting to click 'Send Message'")
                        if self._click_message_button_in_profile():
                            time.sleep(0.8)
                            # 再次验证
                            result = self.validator.validate_chat_contact(self.window_handle, contact)
                            if result.success:
                                self.logger.info("Successfully entered chat from profile page")
                            else:
                                self.logger.warning(f"Still failed after profile recovery: {result.found_text}")
                                continue
                        else:
                            continue
                    elif state != "chat":
                        self.logger.info(f"Detected state '{state}', will retry")
                        continue
                    else:
                        # 处于 chat 状态但验证失败，可能是进错了聊天
                        self.logger.warning("In chat state but contact mismatch, retrying")
                        continue

                # 3. Click input box with adaptive coords + template fallback
                rect = self.window_rect
                input_point = self.coord_mapper.get_point_safe("wechat_input_box", rect)
                if input_point:
                    pyautogui.click(input_point[0], input_point[1])
                else:
                    # 极端 fallback：根据窗口比例估算输入框位置
                    # 输入框通常位于窗口底部偏右约 65% 宽度处，92% 高度处
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

        # 所有尝试均失败，保存最后一张调试图以便人工排查
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
    """
    快速发送微信消息的便捷函数。

    无需手动实例化 WeChatHelper，一行代码完成发送。

    Parameters:
        contact: 联系人/群聊名称
        message: 要发送的消息文本

    Returns:
        bool: 发送成功/失败

    Example:
        >>> send_wechat_message("张三", "你好，这是测试消息")
        SUCCESS: Message sent to 张三
    """
    helper = WeChatHelper()
    success = helper.send_message_to_contact(contact, message)
    if success:
        helper.logger.info(f"SUCCESS: Message sent to {contact}")
        return True
    else:
        error_msg = helper.last_error or "Unknown error"
        helper.logger.error(f"FAILED: {error_msg}")
        return False
