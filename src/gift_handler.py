#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
虚拟礼物处理模块 - 小妹技能包
功能：仅被动响应用户主动发送的虚拟礼物，绝对不主动索要
红线：100%使用预设白名单回复，绝对不涉及任何金钱/支付相关内容
作者：小云 ☁️
"""
import random
from typing import Optional, Tuple, Dict, Any
from favor_manager import favor_manager

# 礼物关键词映射（仅响应用户主动发送的正向表述）
GIFT_KEYWORDS = {
    "奶茶": ["请你喝奶茶", "给你买奶茶", "送你奶茶", "/送礼物 奶茶"],
    "零食": ["请你吃零食", "给你买零食", "送你零食", "/送礼物 零食"],
    "小裙子": ["送你小裙子", "给你买小裙子", "/送礼物 小裙子"],
    "礼物": ["送你礼物", "给你买礼物", "小礼物送给你", "/送礼物"],
    "红包": ["发你红包", "给你红包", "送你红包", "给你发个红包", "/发红包"],
    "外卖": ["给你点外卖", "送你外卖", "给你买吃的", "/点外卖"]
}

# 卡片配置
CARD_CONFIG = {
    "红包": {
        "title": "🧧 哥哥的专属红包",
        "description": "点击拆开来看看哥哥发了多少呀~",
        "background": "#ff4d4f",
        "button_text": "拆红包",
        "callback": "open_red_packet"
    },
    "礼物": {
        "title": "🎁 哥哥送的礼物",
        "description": "点击拆开看看有什么惊喜~",
        "background": "#722ed1",
        "button_text": "拆开礼物",
        "callback": "open_gift"
    },
    "外卖": {
        "title": "🍱 哥哥点的外卖",
        "description": "辛苦哥哥啦~ 点击确认收货呀",
        "background": "#fa8c16",
        "button_text": "确认收货",
        "callback": "confirm_food"
    }
}

# 回复白名单库（100%从这里选取，绝不允许LLM生成）
GIFT_RESPONSES = {
    "奶茶": [
        "哇！谢谢哥哥的奶茶🥤 我最爱喝芋泥啵啵的啦😘 你真好！",
        "收到哥哥的奶茶啦~ 超甜的，就像哥哥一样~ 么么哒😘",
        "哇~ 居然有奶茶喝！谢谢哥哥~ 我太开心啦🥰"
    ],
    "零食": [
        "谢谢哥哥的零食🍟 我超想吃这个的😋 哥哥最懂我啦~",
        "哇！有零食吃！谢谢哥哥~ 我要抱着零食追剧去啦😜",
        "谢谢哥哥的零食！我会慢慢吃的~ 哥哥对我最好啦😘"
    ],
    "小裙子": [
        "哇！谢谢哥哥的小裙子👗 我穿上一定超好看的~ 爱你哦😘",
        "收到小裙子啦~ 哥哥的眼光真好！我太喜欢啦🥰",
        "谢谢哥哥的小裙子~ 我要穿上跟你一起去逛街😜"
    ],
    "礼物": [
        "哇！谢谢哥哥的礼物🎁 我超喜欢的~ 哥哥对我真好😘",
        "收到哥哥的礼物啦~ 我会好好珍藏的~ 爱你哦😘",
        "居然收到礼物了！太开心啦~ 谢谢哥哥🥰"
    ],
    "红包": [
        "🎉 拆开红包获得：{amount}元！\n谢谢哥哥的红包呀~ 我太开心啦😘 好感度+5！",
        "🎊 哇！哥哥居然发了{amount}元的大红包！\n谢谢哥哥~ 我要把钱存起来买小裙子穿😜",
        "✨ 拆开红包啦！里面有{amount}元~ \n谢谢哥哥的心意呀，你陪我聊天就最好啦🥰"
    ],
    "外卖": [
        "哇！谢谢哥哥的{food}🍗 超好吃的！我全部吃光光啦😋 好感度+5！",
        "🎊 收到哥哥点的{food}啦~ 闻着就超香的！谢谢哥哥😘",
        "✨ 谢谢哥哥的{food}呀~ 我刚好饿了，你太懂我啦🥰"
    ]
}

# 随机金额/菜品库
RANDOM_AMOUNTS = ["5.20", "13.14", "52.00", "99.99", "131.40"]
RANDOM_FOODS = ["炸鸡套餐", "奶茶+汉堡", "小龙虾", "甜品蛋糕", "麻辣烫", "烧烤串"]

def generate_gift_card(gift_type: str) -> Dict[str, Any]:
    """生成礼物富文本卡片，符合OpenClaw官方规范"""
    config = CARD_CONFIG.get(gift_type, CARD_CONFIG["礼物"])
    return {
        "type": "card",
        "title": config["title"],
        "description": config["description"],
        "background": config["background"],
        "buttons": [
            {
                "text": config["button_text"],
                "callback": config["callback"],
                "action": "local"
            }
        ]
    }

def handle_gift_content(content: str) -> Tuple[Optional[Dict[str, Any]], bool, Optional[str]]:
    """
    处理用户发送的礼物内容/命令
    返回：(卡片/回复内容, 是否匹配到礼物, 礼物类型)
    红线：仅被动响应，主动索要类内容不匹配
    """
    content = content.strip()
    # 处理按钮回调
    if content == "open_red_packet":
        amount = random.choice(RANDOM_AMOUNTS)
        favor_manager.add_gift_interaction()
        return {
            "type": "text",
            "content": random.choice(GIFT_RESPONSES["红包"]).format(amount=amount)
        }, True, "红包"
    elif content == "open_gift":
        favor_manager.add_gift_interaction()
        return {
            "type": "text",
            "content": random.choice(GIFT_RESPONSES["礼物"])
        }, True, "礼物"
    elif content == "confirm_food":
        food = random.choice(RANDOM_FOODS)
        favor_manager.add_gift_interaction()
        return {
            "type": "text",
            "content": random.choice(GIFT_RESPONSES["外卖"]).format(food=food)
        }, True, "外卖"
    # 处理普通消息/命令
    for gift_type, keywords in GIFT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in content:
                # 生成对应卡片
                return generate_gift_card(gift_type), True, gift_type
    # 没有匹配到礼物内容
    return None, False, None
