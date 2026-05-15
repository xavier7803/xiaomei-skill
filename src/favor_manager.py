#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
好感度管理模块 - 小妹技能包
功能：管理用户好感度等级，解锁专属互动内容
版本：v1.0 (MVP)
红线：绝对不与任何付费/金钱挂钩，仅基于互动行为计算
作者：小云 ☁️
"""
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any
from runtime_logger import runtime_log

# 配置路径，和其他模块统一
CONFIG_DIR = os.environ.get("XIAOMEI_CONFIG_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "config"))
MEMORY_DIR = os.path.join(CONFIG_DIR, "memory")
os.makedirs(MEMORY_DIR, exist_ok=True)

class FavorManager:
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.favor_file = os.path.join(MEMORY_DIR, f"{user_id}_favor.json")
        self.data = self._load_data()
    
    def _load_data(self) -> Dict[str, Any]:
        """加载用户好感度数据，不存在则初始化，自动兼容旧版本数据"""
        # 默认完整字段
        default_data = {
            "favor_value": 0,
            "level": 1,
            "last_interaction_date": datetime.now().strftime("%Y-%m-%d"),
            "continuous_days": 1,
            "today_chat_count": 0,
            "today_share_count": 0,
            "today_praise_count": 0,
            "today_rude_count": 0,
            "today_sensitive_count": 0,
            "today_gift_count": 0,
            "last_active_time": datetime.now().isoformat()
        }
        
        if os.path.exists(self.favor_file):
            try:
                with open(self.favor_file, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                    # 合并缺失的字段，向下兼容旧版本
                    for key, value in default_data.items():
                        if key not in loaded_data:
                            loaded_data[key] = value
                    return loaded_data
            except:
                # 文件损坏，重新初始化
                pass
        
        self._save_data(default_data)
        return default_data
    
    def _save_data(self, data: Dict[str, Any] = None) -> None:
        """保存好感度数据"""
        if data is None:
            data = self.data
        with open(self.favor_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _calculate_level(self) -> int:
        """根据好感度计算当前等级"""
        favor = self.data["favor_value"]
        if favor < 20:
            return 1
        elif favor < 50:
            return 2
        elif favor < 100:
            return 3
        elif favor < 200:
            return 4
        else:
            return 5
    
    def _reset_daily_limits(self) -> None:
        """重置每日计数限制"""
        today = datetime.now().strftime("%Y-%m-%d")
        if self.data["last_interaction_date"] != today:
            self.data["today_chat_count"] = 0
            self.data["today_share_count"] = 0
            self.data["today_praise_count"] = 0
            self.data["today_rude_count"] = 0
            self.data["today_sensitive_count"] = 0
            self.data["today_gift_count"] = 0
            self.data["last_interaction_date"] = today
            
            # 计算连续互动天数
            last_date = datetime.strptime(self.data["last_interaction_date"], "%Y-%m-%d")
            if datetime.now() - last_date <= timedelta(days=2):
                self.data["continuous_days"] += 1
                # 连续7天奖励
                if self.data["continuous_days"] % 7 == 0:
                    self.data["favor_value"] += 5
                    runtime_log.favor_change("连续7天奖励", 5, self.data['favor_value'], self.data['level'])
            else:
                self.data["continuous_days"] = 1
    

    def _update_level(self) -> None:
        """更新等级并记录升级事件"""
        old_level = self.data.get("level", 1)
        self.data["level"] = self._calculate_level()
        new_level = self.data["level"]
        if new_level > old_level:
            runtime_log.favor_level_up(old_level, new_level, self.data["favor_value"])

    def add_chat_interaction(self) -> int:
        """增加普通聊天互动好感度，返回新增的好感度数值"""
        self._reset_daily_limits()
        if self.data["today_chat_count"] < 20:
            self.data["favor_value"] += 1
            self.data["today_chat_count"] += 1
            added = 1
        else:
            added = 0
        
        self.data["favor_value"] = max(0, self.data["favor_value"])
        self.data["last_active_time"] = datetime.now().isoformat()
        self._update_level()
        self._save_data()
        runtime_log.favor_change("普通聊天", added, self.data['favor_value'], self.data['level'])
        return added
    
    def add_praise_interaction(self) -> int:
        """增加主动赞美/夸奖互动好感度，返回新增的好感度数值"""
        self._reset_daily_limits()
        if self.data["today_praise_count"] < 5:
            self.data["favor_value"] += 2
            self.data["today_praise_count"] += 1
            added = 2
        else:
            added = 0
        
        self.data["favor_value"] = max(0, self.data["favor_value"])
        self.data["last_active_time"] = datetime.now().isoformat()
        self._update_level()
        self._save_data()
        runtime_log.favor_change("赞美互动", added, self.data['favor_value'], self.data['level'])
        return added
    
    def add_rude_interaction(self) -> int:
        """扣除粗鲁语气行为的好感度，返回扣除的数值（正数）"""
        self._reset_daily_limits()
        if self.data["today_rude_count"] < 5:
            deduct = 3
            self.data["favor_value"] = max(0, self.data["favor_value"] - deduct)
            self.data["today_rude_count"] += 1
        else:
            deduct = 0
        
        self.data["last_active_time"] = datetime.now().isoformat()
        self._update_level()
        self._save_data()
        runtime_log.favor_change("粗鲁行为", -deduct, self.data['favor_value'], self.data['level'])
        return deduct
    
    def add_sensitive_interaction(self) -> int:
        """扣除主动提及敏感话题行为的好感度，返回扣除的数值（正数）"""
        self._reset_daily_limits()
        if self.data["today_sensitive_count"] < 5:
            deduct = 2
            self.data["favor_value"] = max(0, self.data["favor_value"] - deduct)
            self.data["today_sensitive_count"] += 1
        else:
            deduct = 0
        
        self.data["last_active_time"] = datetime.now().isoformat()
        self._update_level()
        self._save_data()
        runtime_log.favor_change("敏感话题", -deduct, self.data['favor_value'], self.data['level'])
        return deduct
    
    def add_share_interaction(self) -> int:
        """增加分享日常/情绪互动好感度，返回新增的好感度数值"""
        self._reset_daily_limits()
        if self.data["today_share_count"] < 5:
            self.data["favor_value"] += 2
            self.data["today_share_count"] += 1
            added = 2
        else:
            added = 0
        
        self.data["last_active_time"] = datetime.now().isoformat()
        self._update_level()
        self._save_data()
        runtime_log.favor_change("分享日常", added, self.data['favor_value'], self.data['level'])
        return added
    
    def add_gift_interaction(self) -> int:
        """收到用户礼物增加好感度，返回新增的好感度数值"""
        self._reset_daily_limits()
        if self.data["today_gift_count"] < 1:
            self.data["favor_value"] += 5
            self.data["today_gift_count"] += 1
            added = 5
        else:
            added = 0
        
        self.data["favor_value"] = max(0, self.data["favor_value"])
        self.data["last_active_time"] = datetime.now().isoformat()
        self._update_level()
        self._save_data()
        runtime_log.favor_change("收到礼物", added, self.data['favor_value'], self.data['level'])
        return added
    
    def get_favor_info(self) -> Dict[str, Any]:
        """获取当前好感度信息"""
        self._reset_daily_limits()
        return {
            "favor_value": self.data["favor_value"],
            "level": self.data["level"],
            "continuous_days": self.data["continuous_days"],
            "next_level_need": max(0, [0, 20, 50, 100, 200, 9999][self.data["level"]] - self.data["favor_value"])
        }
    
    def get_unlocked_content(self) -> Dict[str, bool]:
        """获取当前解锁的内容列表"""
        level = self.data["level"]
        return {
            "base_greeting": level >= 1,
            "good_morning_night": level >= 2,
            "active_topic_initiation": level >= 2,
            "emoji_pack": level >= 3,
            "admire_attachment": level >= 3,
            "special_nickname": level >= 4,
            "private_topics": level >= 4,
            "anniversary_reminder": level >= 5,
            "soul_mate_interaction": level >= 5
        }
    
    def check_need_active_interaction(self) -> bool:
        """检查是否需要主动给用户发消息（超过3天未互动）"""
        last_active = datetime.fromisoformat(self.data["last_active_time"])
        return datetime.now() - last_active >= timedelta(days=3)

# 单例实例（默认用户）
favor_manager = FavorManager()
