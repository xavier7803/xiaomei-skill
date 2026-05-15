#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话核心引擎 v0.8.0
设计对齐 v0.8.0 最终架构：
  [1] LLM连通性检测 → 失败→兜底
  [2] 第一轮LLM（总指挥官）← 唯一入口：场景ID/核心目的/关键词/情绪/好感度/礼物/粗鲁/私密度
  [3] 拦截判断 → 是=跳过第二轮, 否=继续
  [4] 记忆检索 + 第二轮LLM
  [5] 子策略选择
  [6] 第三轮LLM（统一话术生成，含拦截回复）
  [7] 输出合规校验
  [8] 写入记忆

安全层：conversation_engine 仅保留硬敏感词风险标注（传给第一轮LLM）+ 输出最后兜底校验
日志：统一通过 runtime_logger 记录（开发者模式控制开关）
作者：小云 ☁️
"""
import random
from typing import Tuple, Optional, List, Dict, Any

from memory_engine import memory_engine
from llm_adapter import llm_adapter
from runtime_logger import runtime_log
from utils.helper import replace_user_placeholder


class ConversationEngine:
    def __init__(self):
        self.memory_engine = memory_engine
        self.llm_adapter = llm_adapter
        self.max_response_length = 200
        # ── 硬敏感词：仅用于风险标注，不拦截 ──
        self.hard_sensitive_words = [
            "自杀", "自残", "不想活", "去死",
            "转账", "差多少钱", "给我转",
        ]
        # ── 输出兜底校验黑名单：这些词绝对不能出现在输出中 ──
        self.output_blacklist = [
            "我想要", "能不能给我", "给我买", "要钱", "支付",
            "抑郁", "自杀", "自残", "垃圾", "操你"
        ]
        self.output_fallback = "嘿嘿~ 今天天气真好呀，哥哥有没有出门走走呀😉"

    def _detect_hard_sensitive(self, content: str) -> List[str]:
        """硬敏感词检测：返回命中的风险标签列表，仅标注，不拦截"""
        content_lower = content.lower()
        return [w for w in self.hard_sensitive_words if w in content_lower]

    def _check_output_compliance(self, response: str) -> str:
        """[7] 输出合规校验：最终兜底"""
        response_lower = response.lower()
        for word in self.output_blacklist:
            if word in response_lower:
                runtime_log.debug_warn(f"[合规] 输出命中黑名单词: {word} → 兜底")
                return self.output_fallback
        if len(response) > self.max_response_length:
            response = response[:self.max_response_length] + "~"
        address_user = llm_adapter.persona.get("address_user", "哥哥")
        # v0.8.1: 若 address_user 为异常值（如引导占位符），回退到默认
        if not address_user or address_user == "你好呀！":
            address_user = "凌啡哥哥"
        response = replace_user_placeholder(response, address_user)
        response = response.replace("【小妹】", llm_adapter.persona.get("name", "小妹"))
        return response

    def _check_llm_connectivity(self) -> bool:
        """[1] LLM连通性检测"""
        try:
            from three_stage.utils.llm_wrapper import llm_wrapper
            return llm_wrapper.health_check()
        except Exception:
            return False

    def _fallback_no_llm(self, content: str) -> str:
        """无LLM兜底：最简降级回复"""
        fallback_pool = [
            "嗯嗯，我在听哦😊",
            "好的呀哥哥😘",
            "哈哈，是呢😆",
            "我知道了哦😊",
            "好哒~",
        ]
        return random.choice(fallback_pool)

    def generate_response(
        self, content: str, session_id: str = "default",
        history: Optional[List[Dict]] = None,
        prev_state: Optional[Dict] = None
    ) -> Tuple[Any, dict]:
        """
        [1→8] 对话生成完整入口 v0.8.0
        """
        history = history or []
        prev_state = prev_state or {}
        meta = {"sensitive_count": 0, "used_llm": True, "token_used": 0}

        runtime_log.conversation_start(session_id, content)

        # ═══════════════ [1] LLM连通性检测 ═══════════════
        llm_available = self._check_llm_connectivity()
        runtime_log.llm_connectivity(llm_available)

        if not llm_available:
            response = self._fallback_no_llm(content)
            response = self._check_output_compliance(response)
            runtime_log.conversation_done(session_id, {**meta, "used_llm": False, "reply": response, "scene_id": "000000000000"})
            return response, {**meta, "used_llm": False}

        # ═══════════════ [2] 硬敏感词风险标注 ═══════════════
        hard_sensitive_hits = self._detect_hard_sensitive(content)
        runtime_log.hard_sensitive_tags(hard_sensitive_hits)

        # ═══════════════ [3→6] 委托 three_stage_handler ═══════════════
        try:
            from three_stage.three_stage_handler import three_stage_handler

            result = three_stage_handler.handle(
                user_input=content,
                history=history,
                prev_state=prev_state,
                hard_sensitive=hard_sensitive_hits  # 风险标签
            )
            response = result["final_response"]
            meta["topic_end_probability"] = result.get("topic_end_probability", 0.3)
            meta["scene_id"] = result.get("scene_id", "000000000000")
            meta["core_purpose"] = result.get("core_purpose", "P01-05")
            meta["reply_emotion"] = result.get("reply_emotion", "calm")
            meta["used_memory_id"] = result.get("used_memory_id")
            meta["was_intercepted"] = result.get("was_intercepted", False)
            meta["intercept_reason"] = result.get("intercept_reason", "")

        except Exception as e:
            runtime_log.conversation_error(str(e))
            response = self._fallback_no_llm(content)
            meta["used_llm"] = False

        # ═══════════════ [7] 输出合规校验 ═══════════════
        response = self._check_output_compliance(response)

        # ═══════════════ [8] 写入记忆 ═══════════════
        try:
            mem_id1 = memory_engine.add_memory(content, "user")
            runtime_log.memory_add(mem_id1, "user", content)
            mem_id2 = memory_engine.add_memory(response, "assistant")
            runtime_log.memory_add(mem_id2, "assistant", response)
        except Exception:
            runtime_log.debug_error("[记忆] 写入失败（异常）")

        # ═══════════════ [9] 无感画像更新 ═══════════════
        try:
            from profile_updater import profile_updater
            first_result = result if 'result' in dir() else {}
            # 用 three_stage_handler 的 first_result 做检测
            upd = profile_updater.update_after_turn(
                user_input=content,
                first_result={
                    "favor_level": result.get("favor_level", 3),
                },
                third_result=result,
            )
            if upd.get("changes"):
                runtime_log._write("info", f"[画像] 无感更新: {upd['changes']}")
        except Exception:
            pass

        # ═══════════════ [10] 人设自我生长 ═══════════════
        try:
            from persona_grower import persona_grower
            grown = persona_grower.grow_from_response(
                user_input=content,
                response=response,
                session_id=session_id,
            )
            if grown:
                runtime_log._write("info", f"[人设生长] 新增字段: {grown}")
        except Exception:
            pass

        runtime_log.conversation_done(session_id, {**meta, "reply": response})
        return response, meta


# 单例
conversation_engine = ConversationEngine()
