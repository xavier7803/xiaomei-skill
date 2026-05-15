#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主动互动触发模块 - 小妹技能包
功能：主动关心用户，维持关系热度，绝对不涉及任何礼物/索取内容
红线：所有话术均来自预设正向模板库，频率控制在最多每周1次，避免骚扰
作者：小云 ☁️
"""
import os
import json
import random
from datetime import datetime, timedelta
from typing import Optional
from favor_manager import favor_manager

# 配置路径
CONFIG_DIR = os.environ.get("XIAOMEI_CONFIG_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "config"))
os.makedirs(CONFIG_DIR, exist_ok=True)
LAST_SEND_FILE = os.path.join(CONFIG_DIR, "active_last_send.json")

# 主动消息模板库（100%从这里选取，绝不允许LLM生成）
ACTIVE_TEMPLATES = {
    # 久未互动模板（超过3天没聊天时用）
    "long_time_no_see": [
        "哥哥最近是不是很忙呀？好久没和你聊天了，我都有点想你啦~ 最近过得还好吗？😉",
        "好久没收到哥哥的消息啦，最近是不是遇到什么好玩的事呀？和我说说呗~",
        "哥哥最近在忙什么呀？都好久没理我了🥺 我都有点想你了~"
    ],
    # 关心类模板（结合记忆内容使用）
    "care": [
        "上次你说这周要考试/加班，进展怎么样呀？别太累了哦~",
        "最近降温了，哥哥要记得多穿点衣服哦，别感冒啦😘",
        "今天下雨了，哥哥出门有没有带伞呀？别淋湿了哦~",
        "哥哥今天上班辛不辛苦呀？要记得多喝水，适当休息一下哦~"
    ],
    # 日常分享模板（主动分享小日常，拉近距离）
    "share": [
        "今天我喝到超好喝的芒果西米露！想到哥哥上次说你也喜欢芒果，就来和你说啦😜",
        "刚才看到一只超可爱的小猫咪🐱 毛茸茸的，和哥哥一样可爱~",
        "今天天气超好呀！阳光暖暖的，哥哥有没有出门走走呀？",
        "我刚才听到一首超好听的歌！心情都变好了~ 哥哥最近有没有听到什么好听的歌呀？"
    ]
}

class ActiveInteractionManager:
    def __init__(self):
        self.last_send_data = self._load_last_send()
    
    def _load_last_send(self) -> dict:
        """加载上次主动发送消息的时间记录"""
        if os.path.exists(LAST_SEND_FILE):
            with open(LAST_SEND_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"last_send_time": ""}
    
    def _save_last_send(self) -> None:
        """保存上次主动发送消息的时间记录"""
        with open(LAST_SEND_FILE, "w", encoding="utf-8") as f:
            json.dump(self.last_send_data, f, ensure_ascii=False, indent=2)
    
    def _check_send_frequency(self) -> bool:
        """检查发送频率，最多每周发送1次主动消息"""
        if not self.last_send_data["last_send_time"]:
            return True
        last_send = datetime.fromisoformat(self.last_send_data["last_send_time"])
        return datetime.now() - last_send >= timedelta(days=7)
    
    def check_need_send(self) -> bool:
        """检查是否需要发送主动消息"""
        # 1. 检查发送频率，不到7天不能发
        if not self._check_send_frequency():
            return False
        # 2. 检查用户是否超过3天未互动
        return favor_manager.check_need_active_interaction()
    
    def generate_active_message(self) -> str:
        """生成主动消息，从模板库随机选取"""
        # 优先选用关心类模板，其次是久未互动，最后是日常分享
        template_type = random.choice(["care", "long_time_no_see", "share"])
        return random.choice(ACTIVE_TEMPLATES[template_type])
    
    def record_send_success(self) -> None:
        """记录主动消息发送成功，更新发送时间"""
        self.last_send_data["last_send_time"] = datetime.now().isoformat()
        self._save_last_send()

# 单例实例
active_interaction_manager = ActiveInteractionManager()
