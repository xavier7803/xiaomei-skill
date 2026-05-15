#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
子策略选择器
每个P标签独立配置选择模式：random（均等概率随机选取）/match（场景匹配最优）
"""
import os
import json
import random
import jieba
from typing import List, Dict, Optional, Any

# 配置路径
CONFIG_DIR = os.environ.get("XIAOMEI_CONFIG_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../config"))
STRATEGY_TEMPLATE_PATH = os.path.join(CONFIG_DIR, "strategy_template.config")
DEFAULT_STRATEGY_ID = "S-P01-05-01"

class StrategySelector:
    def __init__(self):
        # 加载策略模板配置
        self.strategy_config = self._load_strategy_config()
        # 分词器用于场景匹配
        self.tokenizer = jieba.Tokenizer()

    def _load_strategy_config(self) -> Dict:
        """加载策略模板配置文件"""
        if not os.path.exists(STRATEGY_TEMPLATE_PATH):
            return {"core_purpose_list": []}
        try:
            with open(STRATEGY_TEMPLATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return {"core_purpose_list": []}

    def _get_purpose_config(self, core_purpose_id: str) -> Optional[Dict]:
        """根据核心目的ID获取对应配置"""
        for purpose in self.strategy_config.get("core_purpose_list", []):
            if purpose.get("core_purpose_id") == core_purpose_id:
                return purpose
        return None

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """简单词袋Jaccard相似度计算，用于场景匹配"""
        if not text1 or not text2:
            return 0.0
        words1 = set([word for word in self.tokenizer.lcut(text1.lower()) if len(word)>=2])
        words2 = set([word for word in self.tokenizer.lcut(text2.lower()) if len(word)>=2])
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)

    def _select_random(self, sub_strategies: List[Dict]) -> Dict:
        """随机模式：均等概率选取子策略"""
        if not sub_strategies:
            return {}
        return random.choice(sub_strategies)

    def _select_match(self, sub_strategies: List[Dict], context: Dict) -> Dict:
        """匹配模式：根据上下文场景匹配最优子策略"""
        if not sub_strategies:
            return {}
        # 提取上下文关键信息：用户输入内容、用户情绪、标签
        user_content = context.get("user_content", "")
        user_emotion = context.get("user_emotion", "")
        tags = context.get("tags", [])
        # 拼接上下文特征文本
        context_text = f"{user_content} {user_emotion} {' '.join(tags)}"
        # 计算每个子策略的匹配相似度
        max_similarity = -1
        best_strategy = sub_strategies[0]
        for strategy in sub_strategies:
            scene_desc = strategy.get("scene_adaptation_desc", "")
            similarity = self._calculate_similarity(context_text, scene_desc)
            if similarity > max_similarity:
                max_similarity = similarity
                best_strategy = strategy
        return best_strategy

    def select_sub_strategy(self, core_purpose_id: str, context: Optional[Dict] = None) -> Dict:
        """
        选择子策略核心接口
        :param core_purpose_id: 第一轮输出的核心目的ID，如P02-05
        :param context: 上下文信息，包含user_content、user_emotion、tags等，match模式需要
        :return: 选中的子策略完整配置，异常返回空字典
        """
        try:
            # 1. 获取对应P标签的配置
            purpose_config = self._get_purpose_config(core_purpose_id)
            if not purpose_config:
                return {}
            sub_strategies = purpose_config.get("sub_strategies", [])
            if not sub_strategies:
                return {}
            # 2. 获取选择模式，默认random
            select_mode = purpose_config.get("strategy_select_mode", "random")
            # 3. 按模式选择
            if select_mode == "match" and context:
                return self._select_match(sub_strategies, context)
            else:
                return self._select_random(sub_strategies)
        except Exception as e:
            # 异常返回第一个子策略兜底
            purpose_config = self._get_purpose_config(core_purpose_id)
            if purpose_config and purpose_config.get("sub_strategies"):
                return purpose_config["sub_strategies"][0]
            return {}

# 单例实例
strategy_selector = StrategySelector()
