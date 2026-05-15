#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人设自我生长器 v0.8.1
- 检测 R3 回复中包含的 persona.json 中不存在的个人信息
- 提取 LLM 编造的合理设定，写入 persona.json
- 确保下次相同问题回答一致，防止人设崩塌

设计原则：
  1. 只增长不覆盖 — 已有字段绝不改写
  2. 一致性校验 — 新信息不与现有人设矛盾（如不能突然说年龄 25）
  3. 标记来源 — 新增字段标注 created_by=llm，区分人工设定
  4. 写入后 R3 prompt 自动获取 — 下一次对话立即生效
"""
import os
import re
import json
import time
from typing import Dict, Optional, List, Set

AGENTS_DIR = os.environ.get(
    "XIAOMEI_AGENTS_DIR",
    os.path.expanduser("~/.openclaw/agents/xiaomei"),
)
PERSONA_PATH = os.path.join(AGENTS_DIR, "persona.json")

# 不可被 LLM 生长的核心字段（人工维护）
PROTECTED_FIELDS = {
    "name", "age", "identity", "birthday", "personality",
    "base_trait", "core_principle", "style", "boundary",
    "speech_style", "address_user", "forbidden",
    "core_purpose", "core_principles",
}

# 可生长的字段类型及一致性校验规则
GROWABLE_FIELDS = {
    # 字段名: (提取正则, 校验函数, 示例)
    "星座": (
        r"(双鱼|白羊|金牛|双子|巨蟹|狮子|处女|天秤|天蝎|射手|摩羯|水瓶)座?",
        lambda v, p: True,
    ),
    "血型": (
        r"[ABOab][型]",
        lambda v, p: True,
    ),
    "MBTI": (
        r"[IE][NS][FT][JP]",
        lambda v, p: True,
    ),
    "身高": (
        r"(?:身高|1米\\d|大约|大概|\\d{2,3}\\s*(?:cm|厘米|公分))",
        lambda v, p: 140 <= int(v) <= 180,
    ),
    "体重": (
        r"体重.*?(\d{2,3})\s*(?:kg|公斤|斤)?",
        lambda v, p: 35 <= int(v) <= 70,
    ),
    "家乡": (
        r"是(.{1,12}?)(?:人啦|人哦|人呢|人呀|人～|人，|人。|人！|人呢|人嘿嘿|地方|那边)",
        lambda v, p: 2 <= len(v) <= 15,
    ),
    "大学": (
        r"(?:大学|学校).*?(?:是|在|读的)\s*(.{2,12}?)(?:啦|哦|呢|～|呀|，|。|！|$|的)",
        lambda v, p: 3 <= len(v) <= 15,
    ),
    "专业方向": (
        r"(?:专业|主修|辅修|方向).*?(?:是|学|读)\s*(.{2,12}?)(?:啦|哦|呢|～|呀|，|。|！|$)",
        lambda v, p: 2 <= len(v) <= 12,
    ),
    "室友名字": (
        r"(?:室友|舍友|闺蜜).*?(?:叫|是|有)\s*(.{1,8}?)(?:[，。！？；\s]|$|，她|她很)",
        lambda v, p: 1 <= len(v) <= 8,
    ),
    "喜欢的食物": (
        r"(?:喜欢的食物|爱吃|喜欢吃|好吃的是?).*?(?:是|有)\s*(.{1,15}?)(?:[，。！？；\s]|$|，还|还有)",
        lambda v, p: 1 <= len(v) <= 20,
    ),
    "讨厌的食物": (
        r"(?:讨厌的食物|不爱吃|不喜欢吃|最怕吃).*?(?:是|有)\s*(.{1,15}?)(?:[，。！？；\s]|$|，还|还有)",
        lambda v, p: 1 <= len(v) <= 20,
    ),
    "喜欢的颜色": (
        r"(?:喜欢的颜色|最爱.*?颜色).*?(?:是|有)\s*(.{1,8}?)(?:[，。！？；\s]|$)",
        lambda v, p: 1 <= len(v) <= 8,
    ),
    "最近在读": (
        r"(?:最近在读|最近在看|在读).*?《?(.{1,25}?)》?(?:[，。！？；\s]|$|这本|挺|很|特别)",
        lambda v, p: 2 <= len(v) <= 30,
    ),
    "梦想": (
        r"(?:梦想|理想|愿望|目标).*?(?:是|想|希望)\s*(.{1,25}?)(?:[，。！？；\s]|$)",
        lambda v, p: 2 <= len(v) <= 30,
    ),
}


class PersonaGrower:
    """人设自我生长器 —— 从 LLM 回复中提取并持久化新设定"""

    def __init__(self):
        self.persona = self._load_persona()
        self._new_fields: Dict[str, dict] = {}

    def _load_persona(self) -> Dict:
        if not os.path.exists(PERSONA_PATH):
            return {}
        try:
            with open(PERSONA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_persona(self) -> bool:
        try:
            with open(PERSONA_PATH, "w", encoding="utf-8") as f:
                json.dump(self.persona, f, ensure_ascii=False, indent=4)
            return True
        except Exception:
            return False

    def grow_from_response(
        self,
        user_input: str,
        response: str,
        session_id: str = "",
    ) -> List[str]:
        """
        从 R3 回复中提取新的人设信息并生长。

        返回：新增的字段名列表（空 = 无生长）
        """
        grown = []

        for field_name, (pattern, validator) in GROWABLE_FIELDS.items():
            # 已有字段 → 跳过
            if field_name in self.persona:
                continue

            m = re.search(pattern, response)
            if not m:
                continue

            # 提取值：优先用捕获组，否则用完整匹配
            extracted = m.group(1) if m.lastindex and m.lastindex >= 1 else m.group(0).strip()
            # 对某些字段，从完整匹配中提取核心值
            extracted = self._postprocess(field_name, extracted)

            # 校验
            if not validator(extracted, self.persona):
                continue
            if not extracted or len(extracted) < 1:
                continue

            # 一致性检查：不与现有字段矛盾
            if not self._consistency_check(field_name, extracted):
                continue

            # 写入
            self.persona[field_name] = extracted
            self._new_fields[field_name] = {
                "value": extracted,
                "created_by": "llm",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source_session": session_id,
            }
            grown.append(field_name)

        if grown:
            self._save_persona()
            # 同时记录元数据（不暴露在 persona 主文件中）
            self._save_meta()

        return grown

    def _postprocess(self, field_name: str, raw: str) -> str:
        """字段专属清理"""
        raw = raw.strip().rstrip("。，！？；：、,.")

        # 通用校验：排除明显不是实体内容的噪声词
        NOISE_WORDS = {"哪里人", "哪人", "谁", "哪里", "什么", "怎么样"}
        cleaned = re.sub(r"^[？?！!~～]+", "", raw).strip()
        if cleaned in NOISE_WORDS or len(cleaned) < 2:
            return ""
        raw = cleaned

        if field_name == "星座":
            # 从"是双子座啦"等中提取完整"星座名+座"
            m = re.search(r"(双鱼|白羊|金牛|双子|巨蟹|狮子|处女|天秤|天蝎|射手|摩羯|水瓶)座", raw)
            if m:
                return m.group(0)
            # 兜底：只匹配星座名
            m = re.search(r"(双鱼|白羊|金牛|双子|巨蟹|狮子|处女|天秤|天蝎|射手|摩羯|水瓶)", raw)
            return m.group(0) + "座" if m else raw
        if field_name == "身高":
            # 处理 "1米62" "158cm" "160左右" "一米六出头" 等多种表达
            # 1) 数字+cm
            m = re.search(r"(\d{2,3})\s*(?:cm|厘米|公分)", raw, re.IGNORECASE)
            if m and 140 <= int(m.group(1)) <= 190:
                return m.group(1)
            # 2) 1米X
            m = re.search(r"1[.米]?([5-8])\s*[0-9]?\s*(?:米|m|出头|左右)?", raw)
            if m:
                base = int(m.group(1))
                return str(150 + (base - 5) * 10)
            # 3) 一米X
            m = re.search(r"一[.米]?([五六七八])\s*[零一二三四五六七八九]?\s*(?:出头|左右|不到|多)?", raw)
            if m:
                cmap = {"五":5,"六":6,"七":7,"八":8}
                base = cmap.get(m.group(1), 6)
                return str(150 + (base - 5) * 10)
            # 4) 纯数字（X00出头）
            m = re.search(r"(1[4-8]\d)(?:出头|左右|不到|而已)", raw)
            if m and 140 <= int(m.group(1)) <= 190:
                return m.group(1)
            return raw
        if field_name == "体重":
            m = re.search(r"(\d{2,3})", raw)
            return m.group(1) if m else raw
        if field_name == "血型":
            m = re.search(r"[ABOab][型]?", raw)
            if m:
                v = m.group(0).upper()
                if not v.endswith("型"):
                    v += "型"
                return v
        if field_name == "MBTI":
            m = re.search(r"([IE][NS][FT][JP])", raw.upper())
            return m.group(1) if m else raw

        # 截断过长值
        if len(raw) > 30:
            raw = raw[:30] + "…"

        return raw

    def _consistency_check(self, field_name: str, value: str) -> bool:
        """跨字段一致性：不自我矛盾"""
        p = self.persona

        # 年龄一致性
        if "age" in p:
            if field_name == "大学" and int(p["age"]) < 16:
                return False  # 16岁以下不可能上大学

        # 身高/体重合理范围（已由 validator 判断）

        # identity 一致性
        if "identity" in p:
            if "大学生" not in p["identity"] and field_name in ("大学", "室友名字"):
                return False  # 不是大学生不可能有大学/室友信息

        return True

    def _save_meta(self):
        """保存生长元数据（不影响 persona 主文件）"""
        meta_path = os.path.join(AGENTS_DIR, ".persona_growth_meta.json")
        meta = {}
        if os.path.exists(meta_path):
            try:
                meta = json.load(open(meta_path))
            except Exception:
                pass
        meta.update(self._new_fields)
        meta["_last_growth"] = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get_known_fields(self) -> Set[str]:
        """获取当前所有已知人设字段"""
        return set(self.persona.keys())

    def get_missing_prompt_hint(self) -> str:
        """
        生成提示文本，告诉 LLM 哪些人设字段目前缺失，
        LLM 被问到时可以合理编造。
        此提示注入到 R3 prompt 的人设信息段落。
        """
        missing = []
        for field in GROWABLE_FIELDS:
            if field not in self.persona:
                missing.append(field)

        if not missing:
            return ""

        hint = (
            "以下人设信息目前尚未设定："
            + "、".join(missing)
            + "。当用户问起这些内容时，请基于已有性格随机编造一个合理答案，"
            + "但要与现有人设保持一致（如年龄/身份/性格）。"
        )
        return hint


# 单例
persona_grower = PersonaGrower()
