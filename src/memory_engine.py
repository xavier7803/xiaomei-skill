#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆管理引擎 - 小妹技能包
功能：三级记忆分层、自然遗忘机制、记忆搜索/存储/持久化
版本：v1.0.0 MVP
日志：通过 runtime_logger 记录写入/升级/老化
作者：小云 ☁️
"""
import os
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

# 配置路径，支持环境变量覆盖
CONFIG_DIR = os.environ.get("XIAOMEI_CONFIG_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "config"))
MEMORY_STORAGE_PATH = os.path.join(CONFIG_DIR, "memory")
os.makedirs(MEMORY_STORAGE_PATH, exist_ok=True)

from runtime_logger import runtime_log


class MemoryEngine:
    def __init__(self):
        self.memories: List[Dict[str, Any]] = []
        self.load_memory()
    
    def _get_memory_level(self, memory: Dict[str, Any]) -> str:
        """计算记忆层级：热/冷/永久/过期"""
        if memory["strength"] >= 5:
            return "permanent"
        memory_age = datetime.now() - memory["time"]
        if memory_age.days <= 7:
            return "hot"
        elif 7 < memory_age.days <= 90:
            return "cold"
        else:
            return "expired"
    
    def add_memory(self, content: str, role: str, time: Optional[datetime] = None, strength: int = 1) -> str:
        """添加新记忆，返回记忆ID"""
        memory_id = str(uuid.uuid4())
        memory = {
            "id": memory_id,
            "content": content,
            "role": role,
            "time": time if time else datetime.now(),
            "strength": strength,
            "tags": []
        }
        memory["level"] = self._get_memory_level(memory)
        self.memories.append(memory)
        self.save_memory()
        runtime_log.memory_add(memory_id, role, content)
        return memory_id
    
    def increase_strength(self, memory_id: str, increment: int = 1) -> bool:
        """增加记忆强度，提及一次加1；强度≥5自动升级为永久"""
        for mem in self.memories:
            if mem["id"] == memory_id:
                old_level = mem["level"]
                old_strength = mem["strength"]
                mem["strength"] = min(mem["strength"] + increment, 10)
                mem["level"] = self._get_memory_level(mem)
                self.save_memory()
                # 升级事件记录
                if mem["level"] != old_level:
                    runtime_log.memory_strength_up(
                        memory_id, mem["strength"], mem["level"]
                    )
                return True
        return False
    
    def apply_aging(self) -> None:
        """应用老化逻辑，90天未提及的记忆强度-1；强度≥5自动升级为永久"""
        now = datetime.now()
        for mem in self.memories:
            age = (now - mem["time"]).days
            if mem["level"] == "permanent":
                continue
            old_level = mem["level"]
            if age >= 90 and mem["strength"] > 1:
                mem["strength"] -= 1
            mem["level"] = self._get_memory_level(mem)
            if mem["level"] == "permanent" and old_level != "permanent":
                runtime_log.memory_strength_up(
                    mem["id"], mem["strength"], mem["level"]
                )
        self.save_memory()
        counts = self.get_memory_count()
        runtime_log.memory_aging(
            counts["hot"], counts["cold"], counts["permanent"], counts["total"]
        )
    
    def get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        for mem in self.memories:
            if mem["id"] == memory_id:
                return mem
        return None
    
    def search_memory(self, keyword: Optional[str] = None, time_range: Optional[int] = None, limit: int = 20) -> List[Dict[str, Any]]:
        result = []
        for mem in sorted(self.memories, key=lambda x: x["time"], reverse=True):
            if time_range is not None:
                age_days = (datetime.now() - mem["time"]).days
                if age_days > time_range:
                    continue
            if keyword is not None and keyword.lower() not in mem["content"].lower():
                continue
            result.append(mem)
            if len(result) >= limit:
                break
        return result
    
    def get_memory_count(self) -> Dict[str, int]:
        counts = {"hot": 0, "cold": 0, "permanent": 0, "total": 0}
        for mem in self.memories:
            if mem["level"] in counts:
                counts[mem["level"]] += 1
            counts["total"] += 1
        return counts
    
    def clear_today_memory(self) -> None:
        today = datetime.now().date()
        self.memories = [mem for mem in self.memories if mem["time"].date() != today]
        self.save_memory()
    
    def clear_all_memory(self) -> None:
        self.memories = []
        self.save_memory()

    def clear_expired_memory(self) -> int:
        before_count = len(self.memories)
        self.memories = [mem for mem in self.memories if mem["level"] != "expired"]
        cleared_count = before_count - len(self.memories)
        self.save_memory()
        return cleared_count
    
    def save_memory(self) -> None:
        serializable_memories = []
        for mem in self.memories:
            mem_copy = mem.copy()
            mem_copy["time"] = mem_copy["time"].isoformat()
            serializable_memories.append(mem_copy)
        
        current_month = datetime.now().strftime("%Y-%m")
        file_path = os.path.join(MEMORY_STORAGE_PATH, f"{current_month}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(serializable_memories, f, ensure_ascii=False, indent=2)
    
    def load_memory(self) -> None:
        self.memories = []
        for filename in os.listdir(MEMORY_STORAGE_PATH):
            if not filename.endswith(".json"):
                continue
            file_path = os.path.join(MEMORY_STORAGE_PATH, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    memories = json.load(f)
                    for mem in memories:
                        mem["time"] = datetime.fromisoformat(mem["time"])
                        mem["level"] = self._get_memory_level(mem)
                        self.memories.append(mem)
            except Exception as e:
                # 加载失败不阻塞主流程
                pass


# 单例实例
memory_engine = MemoryEngine()
