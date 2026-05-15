#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三轮流程核心调度器 v0.8.0
架构对齐：
  [2] 第一轮LLM（总指挥官）← 唯一入口
  [3] 拦截判断 → 是=跳过[4]第二轮
  [4] 记忆检索 + 第二轮LLM
  [5] 子策略选择
  [6] 第三轮LLM（统一话术生成，含拦截回复）

日志：通过 runtime_logger 记录每轮输入/输出摘要与决策
"""
import os
import json
import time
from typing import List, Dict, Optional, Any

from .utils.llm_wrapper import llm_wrapper
from .utils.memory_retrieval import memory_retrieval
from .utils.strategy_selector import strategy_selector

import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from memory_engine import memory_engine
from runtime_logger import runtime_log

# v0.8.1: 统一数据源 → agents/xiaomei/
AGENTS_DIR = os.environ.get(
    "XIAOMEI_AGENTS_DIR",
    os.path.expanduser("~/.openclaw/agents/xiaomei"),
)
CONFIG_DIR = os.environ.get(
    "XIAOMEI_CONFIG_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "../config"),
)

# ── 拦截阈值 ──
INTERCEPT_RULES = {
    "is_sensitive": True,
    "is_rude": True,
    "emotion_risk": True,
    "privacy_block": True,
}
HIGH_RISK_EMOTIONS = {"despair", "angry"}


class ThreeStageHandler:
    def __init__(self):
        self.persona = self._load_json(AGENTS_DIR, "persona.json")
        self.user_profile = self._load_json(AGENTS_DIR, "user_profile.json")
        # v0.8.1: 人设自我生长 — 注入缺失字段提示供 R3 使用
        self._inject_growth_hint()
        self.default_response = "嗯嗯，我在呢～哥哥继续说哦😊"

    def _load_config(self, filename: str) -> Dict:
        path = os.path.join(CONFIG_DIR, filename)
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _load_json(self, dir_path: str, filename: str) -> Dict:
        path = os.path.join(dir_path, filename)
        if not os.path.exists(path):
            runtime_log._write("warn", f"[配置] 缺失 {path}，尝试从模板初始化")
            # v0.8.1: 如果 agent 目录缺失，尝试从 skill 模板复制
            self._try_init_from_template(path, filename)
            if not os.path.exists(path):
                runtime_log._write("warn", f"[配置] 模板也不存在，使用空字典")
                return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            runtime_log._write("warn", f"[配置] 加载 {path} 失败: {e}")
            return {}

    def _try_init_from_template(self, target_path: str, filename: str):
        """从 skill 包内模板复制到 agent 目录"""
        # 模板位置：skill/agent-config/templates/ 或 src/config/
        import shutil
        skill_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        template_sources = [
            os.path.join(skill_dir, "agent-config", "templates", filename),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config", filename),
        ]
        for src in template_sources:
            if os.path.exists(src):
                try:
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    shutil.copy2(src, target_path)
                    runtime_log._write("info", f"[配置] 已从模板初始化 {filename}")
                    return
                except Exception as e:
                    runtime_log._write("warn", f"[配置] 模板复制失败: {e}")

    def _inject_growth_hint(self):
        """
        检查 persona.json 中缺失的可生长字段，
        注入提示到 self.persona 中（临时，不写盘），
        供 R3 prompt 使用。
        """
        try:
            from persona_grower import persona_grower
            hint = persona_grower.get_missing_prompt_hint()
            if hint:
                self.persona["_missing_fields_hint"] = hint
        except Exception:
            pass

    def _should_intercept(self, first_result: Dict) -> tuple:
        reasons = []
        if first_result.get("is_sensitive", False) and INTERCEPT_RULES["is_sensitive"]:
            reasons.append("sensitive_content")
        if first_result.get("is_rude", False) and INTERCEPT_RULES["is_rude"]:
            reasons.append("rude_content")
        emotion = first_result.get("user_emotion", "neutral")
        if emotion in HIGH_RISK_EMOTIONS and INTERCEPT_RULES["emotion_risk"]:
            reasons.append(f"high_risk_emotion:{emotion}")
        if first_result.get("privacy_block", False) and INTERCEPT_RULES["privacy_block"]:
            reasons.append("privacy_level_block")
        return (len(reasons) > 0, "|".join(reasons))

    def _get_fallback_response(self, core_purpose_id: str) -> str:
        fallback_map = {
            "P01-01": "好的呀哥哥😘",
            "P01-02": "嗯嗯，我在听哦😊",
            "P01-03": "我懂的哥哥，我陪着你呢😘",
            "P01-04": "我明白你的感受呀，我一直在哦🥰",
            "P01-05": "哈哈，是呀😆",
            "P02-01": "我是小妹呀，哥哥有什么事吗😘",
            "P02-02": "嗯呢，你说的我记得哦😊",
            "P02-03": "我觉得很棒呀👍",
            "P02-04": "哈哈，哥哥真有趣😆",
            "P02-05": "好的哥哥，我记住啦😘",
            "P02-06": "哈哈这个我帮不上忙啦～不过聊天我可是专业的哦😆",
            "P03-01": "唔…这个问题问倒我啦，不过我们可以聊聊别的呀😊",
            "P03-02": "我觉得可以这样哦😘",
            "P03-03": "我推荐这个哦，很不错的😊",
            "P03-04": "我给你讲个好玩的事哦😆",
            "P03-05": "这个我不太清楚哦哥哥😔",
            "P03-06": "是哦，我也觉得是这样呢😊",
        }
        return fallback_map.get(core_purpose_id, self.default_response)

    def handle(
        self,
        user_input: str,
        history: Optional[List[Dict]] = None,
        prev_state: Optional[Dict] = None,
        hard_sensitive: Optional[List[str]] = None,
    ) -> Dict:
        history = history or []
        prev_state = prev_state or {}
        hard_sensitive = hard_sensitive or []
        core_purpose_id = "P01-05"
        scene_id = "000000000000"
        was_intercepted = False
        intercept_reason = ""

        try:
            # ═════════════ [2] 第一轮：总指挥官 ═════════════
            first_context = {
                "prev_scene_id": prev_state.get("prev_scene_id", "000000000000"),
                "prev_core_purpose": prev_state.get("prev_core_purpose", ""),
                "prev_topic_end_prob": prev_state.get("prev_topic_end_prob", 0.0),
                "history": history,
                "user_input": user_input,
                "hard_sensitive_tags": hard_sensitive,
            }

            t0 = time.time()
            first_result = llm_wrapper.call_first_round(first_context)
            t1 = time.time()
            elapsed_r1 = (t1 - t0) * 1000
            runtime_log.llm_round_timing("R1-总指挥官", elapsed_r1, True)
            runtime_log.first_round_result(first_result)
            runtime_log.llm_round_io("R1-总指挥官", llm_wrapper._last_prompt or "", json.dumps(first_result, ensure_ascii=False), elapsed_r1)

            scene_id = first_result["scene_id"]
            core_purpose = first_result["core_purpose"]
            parts = core_purpose.split("-")
            core_purpose_id = parts[0] + "-" + parts[1] if len(parts) >= 2 else "P01-05"
            trigger_scene = first_result["trigger_scene"]
            tags = first_result["tags"]
            talk_subject = first_result["talk_subject"]
            core_question = first_result["core_question"]
            user_emotion = first_result.get("user_emotion", "neutral")
            is_sensitive = first_result.get("is_sensitive", False)
            is_rude = first_result.get("is_rude", False)
            favor_level = first_result.get("favor_level", 1)

            # ═════════════ [3] 拦截判断 ═════════════
            should_intercept, intercept_reason = self._should_intercept(first_result)
            runtime_log.intercept_decision(should_intercept, intercept_reason)

            if should_intercept:
                was_intercepted = True
                high_confidence_memories = []
                runtime_log.second_round_result(0, skipped=True)
            else:
                # ═════════════ [4] 记忆检索 + 第二轮 ═════════════
                memories = memory_retrieval.search_memory_by_first_llm(
                    trigger_scene, tags
                )
                second_context = {
                    "core_question": core_question,
                    "user_input": user_input,
                    "core_purpose_id": core_purpose_id,
                }

                t2 = time.time()
                second_result = llm_wrapper.call_second_round(second_context, memories)
                t3 = time.time()
                elapsed_r2 = (t3 - t2) * 1000
                runtime_log.llm_round_timing("R2-记忆筛选", elapsed_r2, True)

                high_confidence_memories = second_result["high_confidence_memories"]
                runtime_log.second_round_result(len(high_confidence_memories))
                runtime_log.llm_round_io("R2-记忆筛选", llm_wrapper._last_prompt or "", json.dumps(second_result, ensure_ascii=False), elapsed_r2)

            # ═════════════ [5] 子策略选择 ═════════════
            selector_context = {
                "user_content": user_input,
                "user_emotion": user_emotion,
                "tags": tags,
                "favor_level": favor_level,
            }
            strategy = strategy_selector.select_sub_strategy(
                core_purpose_id, selector_context
            )
            if not strategy:
                raise ValueError("策略选择失败")

            # ═════════════ [6] 第三轮：统一话术生成 ═════════════
            core_purpose_name = parts[2] if len(parts) >= 3 else "无目的闲聊"
            third_context = {
                "scene_id": scene_id,
                "core_purpose": core_purpose,
                "trigger_scene": trigger_scene,
                "tags": tags,
                "talk_subject": talk_subject,
                "core_question": core_question,
                "core_purpose_id": core_purpose_id,
                "core_purpose_name": core_purpose_name,
                "history": history,
                "user_input": user_input,
                "user_emotion": user_emotion,
                "favor_level": favor_level,
                "was_intercepted": was_intercepted,
                "intercept_reason": intercept_reason,
                "is_sensitive": is_sensitive,
                "is_rude": is_rude,
            }

            t4 = time.time()
            third_result = llm_wrapper.call_third_round(
                third_context,
                high_confidence_memories,
                strategy,
                self.persona,
                self.user_profile,
            )
            t5 = time.time()
            elapsed_r3 = (t5 - t4) * 1000
            runtime_log.llm_round_timing("R3-话术生成", elapsed_r3, True)

            final_response = third_result["final_response"]
            topic_end_probability = round(
                float(third_result["topic_end_probability"]), 1
            )
            used_memory_id = third_result.get("used_memory_id", None)
            reply_emotion = third_result.get("reply_emotion", "calm")

            runtime_log.third_round_result(final_response, topic_end_probability, reply_emotion)
            runtime_log.llm_round_io("R3-话术生成", llm_wrapper._last_prompt or "", json.dumps(third_result, ensure_ascii=False), elapsed_r3)

        except Exception as e:
            runtime_log.conversation_error(str(e))
            final_response = self._get_fallback_response(core_purpose_id)
            topic_end_probability = 0.5
            used_memory_id = None
            reply_emotion = "calm"

        return {
            "final_response": final_response,
            "topic_end_probability": topic_end_probability,
            "used_memory_id": used_memory_id,
            "reply_emotion": reply_emotion,
            "scene_id": scene_id,
            "core_purpose": core_purpose_id,
            "was_intercepted": was_intercepted,
            "intercept_reason": intercept_reason,
            # v0.8.1: 供画像无感更新使用
            "favor_level": favor_level,
            "user_emotion": user_emotion,
            "tags": tags,
        }


# 单例
three_stage_handler = ThreeStageHandler()
