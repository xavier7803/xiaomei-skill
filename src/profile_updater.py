#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户画像与人设偏好无感更新 v0.8.1
- 在每轮对话结束后自动检测是否需要更新
- 基于规则匹配（无LLM调用，零延迟）
- 变化量达到阈值才写入，避免频繁写盘

更新触发规则：
  1. address_user: 检测「叫我xx」「别叫xx」「不要叫xx」→ 提取新称呼
  2. dialog_style: 检测「太啰嗦」「太長」「简短点」「多说点」→ 调整风格
  3. interact_habit: 检测「多说点」「详细点」「简短点」「少说点」→ 调整交互
  4. usual_scene: 检测「我在xx」「刚xx完」「在xx中」→ 更新场景
"""
import os
import re
import json
import time

AGENTS_DIR = os.environ.get(
    "XIAOMEI_AGENTS_DIR",
    os.path.expanduser("~/.openclaw/agents/xiaomei"),
)
PROFILE_PATH = os.path.join(AGENTS_DIR, "user_profile.json")
PERSONA_PATH = os.path.join(AGENTS_DIR, "persona.json")

# 最小更新间隔（秒），避免高频写盘
MIN_UPDATE_INTERVAL = 300   # 5分钟
# 连续确认阈值：同一偏好被提及 N 次才更新
CONFIRM_THRESHOLD = 2


class ProfileUpdater:
    """用户画像无感更新器"""

    def __init__(self):
        self.profile = self._load(AGENTS_DIR, "user_profile.json")
        self.persona = self._load(AGENTS_DIR, "persona.json")
        # 临时计数：本轮检测到的偏好变更信号（不写盘，仅本对象生命周期）
        self._pending_profile = dict(self.profile)
        self._pending_persona = dict(self.persona)
        self._signal_counts = {}  # {field: count}

    def _load(self, dir_path: str, filename: str) -> dict:
        path = os.path.join(dir_path, filename)
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self, dir_path: str, filename: str, data: dict) -> bool:
        path = os.path.join(dir_path, filename)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except Exception:
            return False

    def update_after_turn(
        self,
        user_input: str,
        first_result: dict,
        third_result: dict,
    ) -> dict:
        """
        在每轮对话结束后调用，检测并更新画像。
        返回本次更新的字段列表（空 = 无变化）。
        """
        changes = []

        # ── 1. address_user 变更检测 ──
        new_address = self._detect_address_change(user_input)
        if new_address and new_address != self.persona.get("address_user", ""):
            # 称呼变更只需一次声明即生效（不需要确认阈值）
            self._pending_persona["address_user"] = new_address
            changes.append(f"address_user: {new_address}")

        # ── 2. dialog_style 偏好检测 ──
        style_change = self._detect_style_preference(user_input)
        if style_change:
            for k, v in style_change.items():
                key = f"dialog_style_{k}"
                self._signal_counts[key] = self._signal_counts.get(key, 0) + 1
                if self._signal_counts[key] >= CONFIRM_THRESHOLD:
                    self._pending_profile["dialog_style"] = v
                    changes.append(f"dialog_style: {v}")

        # ── 3. interact_habit 检测 ──
        habit_change = self._detect_interact_habit(user_input)
        if habit_change:
            key = f"interact_habit_{habit_change}"
            self._signal_counts[key] = self._signal_counts.get(key, 0) + 1
            if self._signal_counts[key] >= CONFIRM_THRESHOLD:
                self._pending_profile["interact_habit"] = habit_change
                changes.append(f"interact_habit: {habit_change}")

        # ── 4. usual_scene 检测 ──
        scene = self._detect_scene(user_input)
        if scene:
            # 场景直接更新（不需要确认阈值，因为场景切换是事实陈述）
            self._pending_profile["usual_scene"] = scene
            changes.append(f"usual_scene: {scene}")

        # ── 5. favor_level 渐进增长（基于 R1 的 favor 值） ──
        favor = first_result.get("favor_level", 3)
        # favor 由 favor_manager 持久化，这里只记录趋势

        # ── 写盘 ──
        if changes:
            # 检查写入间隔
            last_write = self.profile.get("_last_updated", 0)
            now = time.time()
            if now - last_write >= MIN_UPDATE_INTERVAL:
                self._pending_profile["_last_updated"] = now
                self._save(AGENTS_DIR, "user_profile.json", self._pending_profile)
                if any("address_user" in c for c in changes):
                    self._save(AGENTS_DIR, "persona.json", self._pending_persona)
                self.profile = dict(self._pending_profile)
                self.persona = dict(self._pending_persona)

        return {"changes": changes, "pending": bool(self._signal_counts)}

    # ═══════════════ 规则检测器 ═══════════════

    def _detect_address_change(self, text: str) -> str | None:
        """检测用户是否要求改变称呼"""
        patterns = [
            # 「叫我X就好」— 优先，效率最高
            (r"叫我\s*「?([^」\s，。！？；：、,.!?;:]{1,8})」?\s*(?:就好|就行|啦|吧|哦)", 1),
            # 「叫我X」通用
            (r"叫我\s*「?([^」\s，。！？；：、,.!?;:]{1,8})」?", 1),
            (r"喊我\s*「?([^」\s，。！？；：、,.!?;:]{1,8})」?", 1),
            # 「以后叫我X吧/好了/就行了」
            (r"以后叫我\s*(.+?)(?:吧|好了|就行|就行了|啦)[，。！？]?", 1),
            # 「不要叫我」「别叫」— 仅触发送显式覆盖
            (r"不要叫我\s*(.+?)(?:[，。！？；：、])", None),
            (r"别叫\s*(.+?)(?:[，。！？；：、])", None),
        ]
        for pat, group in patterns:
            m = re.search(pat, text)
            if m:
                if group is not None:
                    result = m.group(group).strip()
                    # 清理尾部残余词
                    result = re.sub(r'(就好|就行|就可以|就行啦|就可以啦|啦|吧|哦|呀|呢|罢了|得了|算了)+$', '', result)
                    if result and len(result) <= 8:
                        return result
                else:
                    return None
        return None

    def _detect_style_preference(self, text: str) -> dict | None:
        """检测用户对对话风格的口头偏好"""
        if re.search(r"太啰嗦|太长了|话太多了|说太多了|好啰嗦", text):
            return {"verbose": "less"}
        if re.search(r"太短了|多说点|详细点|展开说说|具体点", text):
            return {"verbose": "more"}
        if re.search(r"好可爱|太可爱了|好温柔|真温柔", text):
            return {"tone": "warm"}
        return None

    def _detect_interact_habit(self, text: str) -> str | None:
        """检测交互习惯偏好"""
        if re.search(r"长句|多打点字|多写点|展开说", text):
            return "长句、详细"
        if re.search(r"短句|简短点|少说点|简练|简洁", text):
            return "短句、轻互动"
        return None

    def _detect_scene(self, text: str) -> str | None:
        """检测用户当前场景"""
        scene_patterns = [
            (r"我[正就]在?上班", "工作"),
            (r"我[正就]在?公司", "工作"),
            (r"我[正就]在?开会", "工作"),
            (r"我[正就]在?开车", "通勤"),
            (r"我[正就]在?路上", "通勤"),
            (r"我[正就]在?地铁", "通勤"),
            (r"我[正就]在?公交", "通勤"),
            (r"刚到家|我[正就]在家|躺床|躺沙发", "居家休闲"),
            (r"我[正就]在?健身|跑步|锻炼", "运动"),
            (r"我[正就]在?图书馆|学习|看书", "学习"),
            (r"我[正就]在?咖啡厅|咖啡馆|奶茶店", "休闲"),
            (r"我[正就]在?打游戏|玩游戏", "游戏"),
        ]
        for pat, scene in scene_patterns:
            if re.search(pat, text):
                return scene
        return None


# 单例
profile_updater = ProfileUpdater()
