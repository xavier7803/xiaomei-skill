#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆检索中间件 v1.3
完全对齐第一轮LLM输出，轻量化本地检索，仅做基础过滤，相关性判断交给第二轮LLM
"""
import time
import random
from typing import List, Dict, Optional, Any
# 导入现有记忆系统实例
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from memory_engine import memory_engine

class MemoryRetrieval:
    def __init__(self):
        # 检索数量上限
        self.max_result = 10
        # 冷记忆唤醒延迟范围（秒）
        self.delay_min = 0.1
        self.delay_max = 0.5

    def _filter_by_level(self, memory: Dict[str, Any], trigger_scene: str) -> bool:
        """按触发场景过滤记忆层级"""
        level = memory.get("level", "")
        # 所有场景都排除过期记忆
        if level == "expired":
            return False
        if trigger_scene == "default":
            # 默认场景仅召回热记忆+永久记忆
            return level in ("hot", "permanent")
        elif trigger_scene == "cold_wakeup":
            # 冷记忆唤醒场景召回热+冷+永久记忆
            return level in ("hot", "cold", "permanent")
        else:
            # 非法触发场景，默认按default处理
            return level in ("hot", "permanent")

    def _filter_by_tag(self, memory: Dict[str, Any], tags: List[str]) -> bool:
        """标签基础过滤：记忆标签或内容包含任意一个输入标签即保留"""
        # 标签为空，不过滤，全部保留
        if not tags:
            return True
        memory_tags = memory.get("tags", [])
        memory_content = memory.get("content", "").lower()
        # 转小写匹配，不区分大小写
        lower_tags = [tag.lower() for tag in tags]
        # 检查记忆标签是否有匹配
        for tag in memory_tags:
            if tag.lower() in lower_tags:
                return True
        # 检查内容是否包含任意标签
        for tag in lower_tags:
            if tag in memory_content:
                return True
        return False

    def _sort_memories(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """极简排序：第一优先级时间倒序，第二优先级强度倒序"""
        return sorted(memories, key=lambda x: (-x.get("time", 0).timestamp(), -x.get("strength", 0)))

    def _simulate_delay(self, trigger_scene: str) -> None:
        """冷记忆唤醒场景模拟人类思考延迟"""
        if trigger_scene == "cold_wakeup":
            delay = random.uniform(self.delay_min, self.delay_max)
            time.sleep(delay)

    def search_memory_by_first_llm(self, trigger_scene: str, tags: List[str]) -> List[Dict[str, Any]]:
        """
        标准检索接口：基于第一轮LLM输出检索记忆
        :param trigger_scene: 第一轮输出触发场景，default/cold_wakeup，非法值按default处理
        :param tags: 第一轮输出的2-8个具象实词标签
        :return: 最多10条基础相关记忆，直接供第二轮LLM筛选，异常返回空列表
        """
        try:
            # 1. 参数校验
            if not trigger_scene or trigger_scene not in ("default", "cold_wakeup"):
                trigger_scene = "default"
            if not isinstance(tags, list):
                tags = []
            # 2. 层级过滤
            all_memories = memory_engine.memories
            level_filtered = [mem for mem in all_memories if self._filter_by_level(mem, trigger_scene)]
            # 3. 标签过滤
            tag_filtered = [mem for mem in level_filtered if self._filter_by_tag(mem, tags)]
            # 4. 排序
            sorted_memories = self._sort_memories(tag_filtered)
            # 5. 取前max_result条
            result = sorted_memories[:self.max_result]
            # 6. 冷记忆唤醒延迟模拟
            self._simulate_delay(trigger_scene)
            # 7. 格式化返回，适配第二轮LLM输入
            formatted_result = []
            for mem in result:
                formatted_result.append({
                    "memory_id": mem.get("id", ""),
                    "content": mem.get("content", ""),
                    "level": mem.get("level", ""),
                    "strength": mem.get("strength", 0),
                    "tags": mem.get("tags", []),
                    "time": mem.get("time", "").isoformat() if hasattr(mem.get("time", ""), "isoformat") else str(mem.get("time", ""))
                })
            return formatted_result
        except Exception as e:
            # 异常返回空列表，不阻塞主流程
            return []

# 单例实例
memory_retrieval = MemoryRetrieval()
