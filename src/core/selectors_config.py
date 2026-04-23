"""选择器配置 - 常用网站的稳定选择器"""

from typing import Dict, List


# 常用网站的选择器配置
# 格式: {
#   "网站名": {
#       "元素名": ["首选选择器", "备选1", "备选2", ...]
#   }
# }

SELECTORS_CONFIG: Dict[str, Dict[str, List[str]]] = {
    # 淘宝
    "taobao": {
        "search_input": [
            "#q",
            "input[placeholder*='搜索']",
            ".search-combobox-input",
            "[data-spm='search'] input",
        ],
        "search_button": [
            ".btn-search",
            "button[type='submit']",
            ".search-btn",
        ],
        "product_item": [
            ".item",
            ".Card--doubleCardWrapper--L2XFE73",
            "[data-category='auctions']",
        ],
    },
    
    # 京东
    "jd": {
        "search_input": [
            "#key",
            "input[placeholder*='搜索']",
            ".search-input input",
        ],
        "search_button": [
            ".button",
            ".search-btn",
            "button[onclick*='search']",
        ],
        "product_item": [
            ".gl-item",
            ".goods-item",
            "[data-sku]",
        ],
    },
    
    # 百度
    "baidu": {
        "search_input": [
            "#kw",
            "input[name='wd']",
            ".s_ipt",
        ],
        "search_button": [
            "#su",
            "input[type='submit']",
            ".btn-search",
        ],
        "result_item": [
            ".result",
            ".c-container",
            "#content_left > div",
        ],
    },
    
    # 抖音
    "douyin": {
        "search_icon": [
            "[data-e2e='search-icon']",
            ".search-icon",
            "svg[fill='currentColor']",
        ],
        "search_input": [
            "[data-e2e='search-input']",
            "input[type='text']",
            ".search-input",
            "input[placeholder*='搜索']",
        ],
        "search_button": [
            "[data-e2e='search-button']",
            ".search-btn",
            "button:contains('搜索')",
        ],
        "video_item": [
            ".video-item",
            ".Xyhun5Yc",
            "[data-aweme-id]",
        ],
    },
    
    # B站
    "bilibili": {
        "search_input": [
            ".nav-search-input",
            ".search-input",
            "input[placeholder*='搜索']",
        ],
        "search_button": [
            ".nav-search-btn",
            ".search-btn",
            "button:contains('搜索')",
        ],
        "video_item": [
            ".video-list-item",
            ".card-list .card",
            ".video-item",
        ],
    },
    
    # 知乎
    "zhihu": {
        "search_input": [
            ".SearchBar-input input",
            "#q",
            "input[placeholder*='搜索']",
        ],
        "search_button": [
            ".SearchBar-searchBtn",
            "button:contains('搜索')",
        ],
        "content_item": [
            ".ContentItem",
            ".SearchResult-Card",
            ".List-item",
        ],
    },
    
    # GitHub
    "github": {
        "login_field": [
            "#login_field",
            "input[name='login']",
            "input[autocomplete='username']",
        ],
        "password_field": [
            "#password",
            "input[name='password']",
            "input[type='password']",
        ],
        "signin_button": [
            "input[type='submit']",
            ".btn-primary",
            "button:contains('Sign in')",
        ],
        "search_input": [
            ".header-search-input",
            "[data-testid='search-input']",
            "input[placeholder*='Search']",
        ],
    },
    
    # 微博
    "weibo": {
        "hot_item": [
            "[class*='hot']",
            ".rank-item",
            "[data-rank]",
        ],
    },
}


def get_selectors(site: str, element: str) -> List[str]:
    """
    获取指定网站元素的选择器列表
    
    Args:
        site: 网站名（如 "taobao", "jd"）
        element: 元素名（如 "search_input", "search_button"）
        
    Returns:
        选择器列表，按优先级排序
    """
    site_config = SELECTORS_CONFIG.get(site, {})
    return site_config.get(element, [])


def build_multi_selector(site: str, element: str) -> str:
    """
    构建多重选择器字符串
    
    Args:
        site: 网站名
        element: 元素名
        
    Returns:
        逗号分隔的选择器字符串
    """
    selectors = get_selectors(site, element)
    return ", ".join(selectors) if selectors else ""


def add_custom_selector(site: str, element: str, selectors: List[str]):
    """
    添加自定义选择器配置
    
    Args:
        site: 网站名
        element: 元素名
        selectors: 选择器列表
    """
    if site not in SELECTORS_CONFIG:
        SELECTORS_CONFIG[site] = {}
    SELECTORS_CONFIG[site][element] = selectors


# 通用选择器（当网站特定选择器都失败时使用）
GENERIC_SELECTORS = {
    "search_input": [
        "input[type='text']",
        "input[type='search']",
        "input[placeholder*='搜索']",
        "input[placeholder*='search']",
        "input[name*='search']",
        "input[id*='search']",
    ],
    "search_button": [
        "button[type='submit']",
        "input[type='submit']",
        "button:contains('搜索')",
        "button:contains('Search')",
        ".search-btn",
        ".btn-search",
    ],
    "button": [
        "button",
        "input[type='button']",
        "a[role='button']",
    ],
    "link": [
        "a",
        "a[href]",
    ],
    "input": [
        "input",
        "textarea",
    ],
}


def get_generic_selector(element_type: str) -> List[str]:
    """获取通用选择器"""
    return GENERIC_SELECTORS.get(element_type, [])
