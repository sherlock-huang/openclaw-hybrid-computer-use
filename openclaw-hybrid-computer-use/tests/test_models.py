"""模型测试"""


def test_is_browser_action():
    from src.core.models import is_browser_action
    
    assert is_browser_action("browser_click") is True
    assert is_browser_action("browser_type") is True
    assert is_browser_action("click") is False
    assert is_browser_action("type") is False
