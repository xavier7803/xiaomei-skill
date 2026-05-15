#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token消耗统计模块 - 小妹技能包
功能：统计LLM调用的Token消耗，限制每日/每月使用量
版本：v1.0 (MVP)
作者：小云 ☁️
"""
import os
import json
from datetime import datetime
from typing import Tuple, Dict, Any
from llm_adapter import llm_adapter

# 配置路径，支持环境变量覆盖，和其他模块统一
CONFIG_DIR = os.environ.get("XIAOMEI_CONFIG_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "config"))
os.makedirs(CONFIG_DIR, exist_ok=True)
TOKEN_STATS_PATH = os.path.join(CONFIG_DIR, "token_stats.json")

class TokenTracker:
    def __init__(self):
        self.config = self._load_config()
        self.stats = self._load_stats()
        self.daily_used = self.stats.get("daily_used", 0)
        self.monthly_used = self.stats.get("monthly_used", 0)
        self.last_reset_date = self.stats.get("last_reset_date", "")
        self.last_reset_month = self.stats.get("last_reset_month", "")
        self._check_reset()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载LLM配置"""
        llm_config_path = os.path.join(CONFIG_DIR, "llm_config.json")
        with open(llm_config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _load_stats(self) -> Dict[str, Any]:
        """加载Token统计数据"""
        if os.path.exists(TOKEN_STATS_PATH):
            with open(TOKEN_STATS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "daily_used": 0,
            "monthly_used": 0,
            "last_reset_date": self._get_current_date(),
            "last_reset_month": self._get_current_month()
        }
    
    def _save_stats(self) -> None:
        """保存Token统计数据"""
        stats = {
            "daily_used": self.daily_used,
            "monthly_used": self.monthly_used,
            "last_reset_date": self.last_reset_date,
            "last_reset_month": self.last_reset_month
        }
        with open(TOKEN_STATS_PATH, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    
    def _get_current_date(self) -> str:
        """获取当前日期字符串 YYYY-MM-DD"""
        return datetime.now().strftime("%Y-%m-%d")
    
    def _get_current_month(self) -> str:
        """获取当前月份字符串 YYYY-MM"""
        return datetime.now().strftime("%Y-%m")
    
    def _check_reset(self) -> None:
        """检查是否需要重置统计数据"""
        current_date = self._get_current_date()
        current_month = self._get_current_month()
    
        # 每日重置
        if not self.last_reset_date or self.last_reset_date[:10] != current_date:
            self.daily_used = 0
            llm_adapter.reset_stats()
            self.last_reset_date = current_date
    
        # 每月重置
        if not self.last_reset_month or self.last_reset_month[:7] != current_month:
            self.monthly_used = 0
            self.last_reset_month = current_month
    
        self._save_stats()
    
    def add_usage(self, token_count: int) -> None:
        """增加Token使用量"""
        self._check_reset()
        self.daily_used += token_count
        self.monthly_used += token_count
        self._save_stats()
    
    def check_limit(self) -> Tuple[bool, str]:
        """检查是否超过使用限制
        返回：(是否可用，提示信息)
        """
        self._check_reset()
        daily_limit = self.config.get("daily_token_limit", 10000)
        
        if daily_limit <= 0:
            return True, "无Token使用限制"
        
        if self.daily_used >= daily_limit:
            return False, f"今日Token使用量已达上限({daily_limit}个)，请明日再使用LLM功能，或在配置中调整上限"
        
        remaining = daily_limit - self.daily_used
        return True, f"今日剩余可用Token：{remaining}个"
    
    def reset_daily(self) -> None:
        """重置今日使用量"""
        self.daily_used = 0
        llm_adapter.reset_stats()
        self._save_stats()
    
    def get_usage_stats(self) -> dict:
        """获取使用情况统计字典"""
        self._check_reset()
        daily_limit = self.config.get("daily_token_limit", 10000)
        percentage = int((self.daily_used / daily_limit) * 100) if daily_limit > 0 else 0
        return {
            "daily_used": self.daily_used,
            "daily_limit": daily_limit,
            "daily_percent": f"{percentage}%",
            "total_used": llm_adapter.total_token_used,
            "total_cost": f"{llm_adapter.total_token_used * 0.00001:.2f}元" if llm_adapter.total_token_used > 0 else "0元"
        }

    def get_usage_text(self) -> str:
        """获取使用情况文本"""
        self._check_reset()
        if not self.config.get("show_token_cost", True):
            return ""
        
        stats = self.get_usage_stats()
        if stats["daily_limit"] <= 0:
            return f"📊 Token使用：今日共消耗{stats['daily_used']}个，无上限"
        
        remaining = stats["daily_limit"] - stats["daily_used"]
        return f"📊 Token使用：今日已用{stats['daily_used']}个/{stats['daily_limit']}个({stats['daily_percent']})，剩余{remaining}个"

# 单例实例
token_tracker = TokenTracker()
