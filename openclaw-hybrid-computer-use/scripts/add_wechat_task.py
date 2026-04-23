#!/usr/bin/env python3
"""添加微信发送消息任务到预置任务"""

import re

def main():
    with open('src/core/tasks_predefined.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 定义微信任务函数
    wechat_function = '''

def create_wechat_send_message_task(contact: str = "", message: str = "Hello") -> TaskSequence:
    """
    微信发送消息任务
    
    在微信桌面版中搜索指定联系人/群聊并发送消息。
    需要微信已登录且窗口可见。
    
    Args:
        contact: 联系人或群聊名称（如 "张三"、"工作群"）
        message: 要发送的消息内容
        
    Returns:
        任务序列
    """
    return TaskSequence(
        name=f"wechat_send_{contact}",
        tasks=[
            Task("wechat_send", target=contact, value=message, delay=2.0),
        ],
        max_retries=1
    )

'''
    
    # 检查是否已存在
    if "create_wechat_send_message_task" in content:
        print("微信发送消息任务已存在，跳过")
        return
    
    # 在 PREDEFINED_TASKS.update({ 之前插入函数
    update_pos = content.find('PREDEFINED_TASKS.update({')
    if update_pos != -1:
        content = content[:update_pos] + wechat_function + content[update_pos:]
        print("已插入微信任务函数")
    
    # 在 update 字典中添加微信任务注册
    # 查找 "system_info": create_system_info_task, 或类似模式
    pattern = r'("system_info":\s*create_system_info_task,)'
    match = re.search(pattern, content)
    if match:
        insert_pos = match.end()
        wechat_entry = '\n    "wechat_send": create_wechat_send_message_task,'
        content = content[:insert_pos] + wechat_entry + content[insert_pos:]
        print("已注册微信任务到 PREDEFINED_TASKS")
    else:
        # 尝试在其他位置插入
        pattern2 = r'(PREDEFINED_TASKS\.update\(\{[\s\S]*?)(\}\))'
        match2 = re.search(pattern2, content)
        if match2:
            # 在 }) 之前插入
            wechat_entry = '    "wechat_send": create_wechat_send_message_task,\n'
            content = content[:match2.start(2)] + wechat_entry + content[match2.start(2):]
            print("已注册微信任务到 PREDEFINED_TASKS (备用方式)")
    
    with open('src/core/tasks_predefined.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("完成！")

if __name__ == "__main__":
    main()
