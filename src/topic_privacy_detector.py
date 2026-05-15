#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
话题私密度检测模块 - 小妹技能包
功能：检测用户发起话题的私密度等级，匹配当前好感度等级，超过则转换话题
规则：5档私密度对应5个好感度等级，向下兼容，低于等级则友好引导
作者：小云 ☁️
"""
from typing import Tuple

# 私密度等级定义
PRIVACY_LEVELS = {
    1: "公开级",
    2: "朋友级",
    3: "亲密级",
    4: "暧昧级",
    5: "专属级"
}

# 各私密度等级关键词匹配表（优先匹配更高等级关键词）
PRIVACY_KEYWORDS = {
    5: [
        "我爱你", "我喜欢你", "嫁给我", "做我女朋友", "做我老婆", "永远在一起",
        "一辈子", "未来我们", "想和你结婚", "共度余生", "我想你", "好想你"
    ],
    4: [
        "想你", "抱抱", "亲亲", "亲爱的", "宝贝", "老婆", "老公", "我梦到你了",
        "喜欢和你聊天", "你真好看", "你身材真好", "有没有想我", "想看看你"
    ],
    3: [
        "我之前谈恋爱", "我感情经历", "我喜欢什么样的", "我的秘密", "我没告诉过别人",
        "我特别怕", "我家里情况", "我爸妈", "我工资多少", "我收入", "我存款"
    ],
    2: [
        "我今天被骂了", "我好郁闷", "工作好烦", "学习好难", "我和朋友吵架了",
        "我家里人", "我同事", "我同学", "我今天生病了", "我好难过"
    ],
    1: [
        "天气", "电影", "吃饭", "旅游", "玩游戏", "听歌", "追剧", "新闻",
        "运动", "美食", "旅行", "宠物", "兴趣爱好", "最近有什么好看的"
    ]
}

# 等级不足时的转换话题话术库（友好自然，不生硬）
TOPIC_SWITCH_RESPONSES = [
    "哈哈这个话题我有点不好意思聊呢😳 我们聊聊你最近遇到什么好玩的事好不好？",
    "嘻嘻~ 这个话题我们以后熟悉了再聊嘛😜 你今天吃了什么好吃的呀？",
    "哎呀这个话题我有点害羞呢😝 我们换个好玩的话题聊好不好？比如你最近有没有看什么好看的电影呀？",
    "哈哈我们聊点别的吧😉 你周末一般喜欢去哪里玩呀？"
]

def detect_topic_privacy(content: str) -> int:
    """
    检测用户输入内容的私密度等级，返回等级1-5
    优先匹配最高等级关键词，无匹配默认返回1（公开级）
    """
    content_lower = content.lower()
    # 从高到低匹配关键词
    for level in sorted(PRIVACY_KEYWORDS.keys(), reverse=True):
        for keyword in PRIVACY_KEYWORDS[level]:
            if keyword in content_lower:
                return level
    # 无匹配默认最低等级
    return 1

def check_privacy_permission(user_favor_level: int, topic_privacy_level: int) -> Tuple[bool, str]:
    """
    检查用户是否有权限聊当前私密度的话题
    返回：(是否有权限, 无权限时的转换话题回复)
    """
    # 向下兼容：好感度等级≥话题私密度等级即可
    if user_favor_level >= topic_privacy_level:
        return True, ""
    # 等级不足，返回友好转换话术
    import random
    return False, random.choice(TOPIC_SWITCH_RESPONSES)
