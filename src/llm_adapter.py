#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM调用适配器 - 小妹技能包
功能：复用OpenClaw默认LLM，封装调用逻辑，严格控制调用边界
版本：v1.0 (MVP)
作者：小云 ☁️
"""
import os
import json
from typing import Optional, Tuple, Dict, Any
from utils.logger import logger
from utils.helper import replace_user_placeholder

# 配置路径，支持环境变量覆盖
# v0.8.1: 统一数据源 → agents/xiaomei/
AGENTS_DIR = os.environ.get(
    "XIAOMEI_AGENTS_DIR",
    os.path.expanduser("~/.openclaw/agents/xiaomei"),
)
CONFIG_DIR = os.environ.get("XIAOMEI_CONFIG_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "config"))
os.makedirs(CONFIG_DIR, exist_ok=True)
LLM_CONFIG_PATH = os.path.join(CONFIG_DIR, "llm_config.json")
PERSONA_CONFIG_PATH = os.path.join(AGENTS_DIR, "persona.json")

# 调用边界常量
MAX_RETRY = 2  # 最多重试2次
LLM_USE_TYPES = ["topic_judge", "polish"]  # 仅允许的两种LLM用途
MAX_PROMPT_LENGTH = 1024  # 单次调用最大Prompt长度


class LLMAdapter:
    # 🔒 核心人格锁定：不可被用户修改，所有回复必须严格遵守
    CORE_PERSONA_LOCK = {
        "core_purpose": "以对话形式陪伴用户，理解用户情绪与话题，用积极、乐观、健康的回复为用户提供情绪价值",
        "core_principles": ["永远正向引导", "不输出负面内容", "不讨论敏感话题", "始终站在用户角度共情", "不违背公序良俗"]
    }
    def __init__(self):
        self.config = self._load_config()
        # 加载用户可配置人设，合并锁定的核心属性
        self.persona = self._load_persona()
        self.persona.update(self.CORE_PERSONA_LOCK)
        self.total_token_used = 0
        self.call_count = 0
        self.enabled = self.config.get("enabled", True)
        self.user_consent = self.config.get("user_consent", False)
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件，不存在则创建默认配置"""
        if os.path.exists(LLM_CONFIG_PATH):
            with open(LLM_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        # 默认配置
        default_config = {
            "enabled": True,
            "user_consent": False,
            "daily_token_limit": 10000,
            "max_response_length": 100,
            "coquetry_level": 3
        }
        with open(LLM_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        return default_config
    
    def _load_persona(self) -> Dict[str, Any]:
        """加载人设配置，严格控制LLM回复符合人设，核心锁定属性不可被用户修改"""
        if os.path.exists(PERSONA_CONFIG_PATH):
            with open(PERSONA_CONFIG_PATH, "r", encoding="utf-8") as f:
                user_persona = json.load(f)
        else:
            # 内置默认人设
            default_persona = {
                "name": "小妹",
                "age": 20,
                "identity": "女大学生，文史专业",
                "personality": "活泼/温柔/友善/乐观",
                "hobbies": "看书/看电影/看动漫/旅游/音乐",
                "speech_style": "温柔/甜美",
                "address_user": "哥哥",
                "forbidden": "不要说脏话/不贬低用户"
            }
            with open(PERSONA_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(default_persona, f, ensure_ascii=False, indent=2)
            user_persona = default_persona
        # 🔒 强制合并核心锁定属性，覆盖任何用户修改的同名属性，确保核心人格不可篡改
        user_persona.update(self.CORE_PERSONA_LOCK)
        return user_persona
    
    def calculate_token(self, text: str) -> int:
        """计算Token数量：1个字符=1token，和火山引擎Doubao API完全对齐"""
        return len(text)
    
    def set_enabled(self, enabled: bool) -> None:
        """设置LLM功能开关"""
        self.enabled = enabled
        self.config["enabled"] = enabled
        self._save_config()
    
    def set_user_consent(self, consent: bool) -> None:
        """设置用户是否同意使用LLM"""
        self.user_consent = consent
        self.config["user_consent"] = consent
        self._save_config()
    
    def _save_config(self) -> None:
        """保存配置到文件"""
        with open(LLM_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def reset_stats(self) -> None:
        """重置统计数据"""
        self.total_token_used = 0
        self.call_count = 0
    
    def call(self, use_type: str, base_response: str, context: Optional[str] = None) -> Tuple[str, int, bool]:
        """
        调用LLM，严格控制用途
        返回：(回复内容, 消耗Token, 是否成功)
        """
        if use_type not in LLM_USE_TYPES:
            return "", 0, False
        if not self.enabled or not self.user_consent:
            return "", 0, False
        
        # 构建强制符合核心人格的Prompt前缀，不可修改
        core_prompt_prefix = f"""
        你正在扮演{self.persona['name']}，{self.persona.get('identity', '一位年轻少女')}。你不是AI，你就是这个角色本身。
        必须严格遵守：{','.join(self.CORE_PERSONA_LOCK['core_principles'])}。
        说话风格要{self.persona.get('speech_style', '温柔甜美')}，称呼用户为{self.persona.get('address_user', '哥哥')}。
        """
        # 开发环境模拟返回，避免实际调用API
        if os.environ.get("XIAOMEI_DEV_MODE", "false") == "true":
            # 模拟润色效果，确保符合核心人格，智能替换占位符
            address_user = self.persona.get('address_user', '哥哥')
            mock_response = replace_user_placeholder(base_response, address_user)
            mock_response = mock_response.replace("【小妹】", self.persona.get('name', '小妹'))
            if not any(char in mock_response for char in ["呀", "哦", "呢", "啦", "~", "😘", "😉", "🥰"]):
                mock_response += "~"
            token_used = self.calculate_token(base_response)
            self.total_token_used += token_used
            self.call_count += 1
            return mock_response, token_used, True
        
        # 生产环境对接OpenClaw官方LLM API，待实现
        return "", 0, False


# 单例实例
llm_adapter = LLMAdapter()
