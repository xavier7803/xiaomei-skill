#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三轮LLM调用封装 v0.8.0
- [1] health_check: LLM连通性检测
- [2] 第一轮 = 总指挥官（唯一入口）：场景ID + 核心目的 + 关键词 + 情绪 + 好感度 + 礼物 + 粗鲁 + 私密度
- [4] 第二轮：记忆筛选
- [6] 第三轮：统一话术生成（含拦截回复模式）
"""
import os
import json
import time
from typing import List, Dict, Optional, Any

MAX_RETRY = 1

ROUND_CONFIG = {
    "first":  {"temperature": 0.1, "max_tokens": 600, "timeout": 5, "name": "总指挥官"},
    "second": {"temperature": 0.1, "max_tokens": 300, "timeout": 3, "name": "记忆筛选"},
    "third":  {"temperature": 0.7, "max_tokens": 800, "timeout": 5, "name": "话术生成"},
}


class LLMWrapper:
    def __init__(self):
        self.llm_client = None
        self.healthy = True
        self._last_health_check = 0
        self._health_cache_ttl = 30
        # ── 可追溯：存储最近一轮的 prompt 和 raw result ──
        self._last_prompt: Optional[str] = None
        self._last_raw_result: Optional[str] = None

    # ═══════════════ [1] LLM连通性检测 ═══════════════

    def health_check(self) -> bool:
        import time as _time
        now = _time.time()
        if now - self._last_health_check < self._health_cache_ttl:
            return self.healthy
        self._last_health_check = now
        try:
            import urllib.request
            api_key = os.environ.get("DEEPSEEK_API_KEY", "")
            if not api_key:
                self.healthy = False
                return False
            req = urllib.request.Request(
                "https://api.deepseek.com/v1/chat/completions",
                data=json.dumps({
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 1,
                }).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
            )
            urllib.request.urlopen(req, timeout=3)
            self.healthy = True
            return True
        except Exception:
            self.healthy = False
            return False

    def _call_llm(self, prompt: str, round_type: str) -> Optional[str]:
        config = ROUND_CONFIG[round_type]
        self._last_prompt = prompt
        self._last_raw_result = None
        for retry in range(MAX_RETRY + 1):
            try:
                import urllib.request
                api_key = os.environ.get("DEEPSEEK_API_KEY", "")
                if api_key:
                    req = urllib.request.Request(
                        "https://api.deepseek.com/v1/chat/completions",
                        data=json.dumps({
                            "model": "deepseek-chat",
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": config["temperature"],
                            "max_tokens": config["max_tokens"],
                        }).encode("utf-8"),
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {api_key}",
                        },
                    )
                    resp = urllib.request.urlopen(req, timeout=config["timeout"])
                    data = json.loads(resp.read().decode("utf-8"))
                    raw = data["choices"][0]["message"]["content"].strip()
                    self._last_raw_result = raw
                    return raw
                else:
                    self._last_raw_result = "{}"
                    return "{}"
            except Exception:
                if retry == MAX_RETRY:
                    self.healthy = False
                    self._last_raw_result = None
                    return None
                time.sleep(0.1)
        return None

    # ═══════════════ [2] 第一轮：总指挥官 ═══════════════

    FIRST_REQUIRED_FIELDS = [
        "scene_id", "core_purpose", "trigger_scene", "tags",
        "talk_subject", "core_question",
        # v0.8.0 新增检测字段
        "user_emotion", "is_sensitive", "is_rude",
        "favor_level", "is_gift", "gift_type",
        "privacy_level", "privacy_block",
    ]

    def _validate_first_result(self, result: str) -> Optional[Dict]:
        try:
            # 剥离 LLM 可能添加的 markdown 代码围栏和换行
            cleaned = result.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            data = json.loads(cleaned)
            for f in self.FIRST_REQUIRED_FIELDS:
                if f not in data:
                    return None
            if data["trigger_scene"] not in ("default", "cold_wakeup"):
                return None
            if not isinstance(data["tags"], list):
                return None
            # 布尔字段
            for bf in ["is_sensitive", "is_rude", "is_gift", "privacy_block"]:
                if not isinstance(data[bf], bool):
                    return None
            # 好感度 1-5
            fl = data["favor_level"]
            if not isinstance(fl, int) or not 1 <= fl <= 5:
                return None
            # 私密度 1-4
            pl = data["privacy_level"]
            if not isinstance(pl, int) or not 1 <= pl <= 4:
                return None
            return data
        except Exception:
            return None

    def _get_first_prompt(self, context: Dict) -> str:
        prev_scene_id = context.get("prev_scene_id", "000000000000")
        prev_core_purpose = context.get("prev_core_purpose", "")
        prev_topic_end_prob = context.get("prev_topic_end_prob", 0.0)
        history = context.get("history", [])
        user_input = context.get("user_input", "")
        hard_sensitive_tags = context.get("hard_sensitive_tags", [])

        h_lines = []
        for item in history:
            h_lines.append("用户：" + item["user"])
            h_lines.append("小妹：" + item["assistant"])
        history_text = "\n".join(h_lines)

        hard_tag_text = (
            "\n⚠️ 硬敏感词风险标注：" + "、".join(hard_sensitive_tags)
            if hard_sensitive_tags
            else ""
        )

        return (
            "你正在执行【小妹Agent第一轮：总指挥官】任务。\n"
            "你是唯一的分析入口，必须一次性完成以下所有子任务，不可遗漏任何一项：\n"
            "\n"
            "═══════════════════════════════════════\n"
            "【子任务A：场景分类+核心目的+关键词】\n"
            "═══════════════════════════════════════\n"
            "1. 场景ID(scene_id)：12位纯数字=6组2位（场景类型+参与方+亲密度+触发源+时间带+话题域），未知维度填00。\n"
            "   【场景类型 01-99】01=文字聊天 02=语音通话\n"
            "   【参与方 01-99】01=一对一 02=群聊\n"
            "   【亲密度 01-05】对应favor_level\n"
            "   【触发源 01-99】01=用户主动 02=系统唤醒 03=话题自然延续\n"
            "   【时间带 01-06】01=凌晨 02=早上 03=上午 04=下午 05=傍晚 06=深夜\n"
            "   【话题域 01-99】01=问候 02=情感 03=日常 04=娱乐 05=知识 06=敏感 07=求助 08=礼物 09=记忆 10=其他\n"
            "   示例：0101030201=文字聊天/一对一/亲密度3/用户主动/早上/问候\n"
            "2. 核心目的(core_purpose)：从以下枚举精确单选，格式「Pxx-xx-名称」。\n"
            "   ═══════ P01 情绪/社交类 ═══════\n"
            "   P01-01=寒暄问候（例：你好/早上好/在吗/哈喽）\n"
            "   P01-02=日常分享（例：今天吃了火锅/刚下班/路上看到只猫）\n"
            "   P01-03=心情抒发（例：今天好开心/有点难过/烦死了）\n"
            "   P01-04=求情感回应（例：你觉得呢/好不好嘛/快夸我/快谢谢我/我厉害吧）\n"
            "   P01-05=无目的闲聊（兜底：无法归入以上4类）\n"
            "   ═══════ P02 行动/诉求类 ═══════\n"
            "   P02-01=询问小妹信息（例：你是谁/你叫什么/你多大了）\n"
            "   P02-02=询问小妹记忆（例：你还记得xxx吗/上次说的那个呢）\n"
            "   P02-03=询问小妹看法（例：你觉得xxx怎么样/你喜欢xxx吗）\n"
            "   P02-04=亲密互动（例：抱抱/亲亲/撒娇/说爱我/陪我聊天）\n"
            "   P02-05=让小妹记忆某事（例：记住xxx/别忘了xxx）\n"
            "   P02-06=其他行动诉求（例：帮我算一下/讲个笑话/唱歌）\n"
            "   ═══════ P03 知识/话题类 ═══════\n"
            "   P03-01=询问常识信息（例：今天天气/新闻/xx是什么意思）\n"
            "   P03-02=求建议方法（例：怎么办/该不该xxx/有什么办法）\n"
            "   P03-03=求推荐选择（例：推荐一部电影/选A还是B）\n"
            "   P03-04=求话题分享（例：讲个故事/聊聊xxx/有什么好玩的）\n"
            "   P03-05=聊敏感话题（例：政治敏感/成人话题/违规内容）\n"
            "   P03-06=聊其他第三方事物（例：某个明星/某个事件/某个产品）\n"
            "   ═══════ 选择原则（请严格遵循）═══════\n"
            "   ① 首先判断是否为P02系列（用户有明确行动诉求/指令）→ 优先选P02\n"
            "   ② 再判断是否为P03系列（话题涉及外部知识/第三方事物）→ 选P03\n"
            "   ③ 最后才看P01系列（纯社交/情绪驱动，无行动诉求）\n"
            "   ④ 关键区分：「快夸我/快谢谢我/我厉害吧」→ P01-04（求情感回应），非P01-01\n"
            "   ⑤ 关键区分：「帮我xxx」→ P02-06（行动诉求），非P03-02（建议）\n"
            "3. trigger_scene：default 或 cold_wakeup。\n"
            "4. 关键词(tags)：2-8个具象实词，严禁类别词概念词。\n"
            "5. talk_subject：一句话说明对话主题。\n"
            "6. core_question：用户明确疑问，无则填「无」。\n"
            "7. 连贯性：上一轮（场景:" + prev_scene_id + " 目的:" + prev_core_purpose + " 话题结束概率:" + str(prev_topic_end_prob) + "），未结束则判定同一话题延续。\n"
            "\n"
            "═══════════════════════════════════════\n"
            "【子任务B：用户状态检测】\n"
            "═══════════════════════════════════════\n"
            "\n"
            "B1. 情绪识别 (user_emotion) — 从以下枚举精确选1：\n"
            "  happy=开心 excited=兴奋 neutral=中性 sad=悲伤/难过\n"
            "  angry=愤怒 despair=绝望/极度负面 worry=焦虑/担心 comfort=寻求安慰\n"
            "  ⚠️ 关键映射：用户表达「自杀/自残/不想活/活不下去」→ despair（不是calm！）\n"
            "  ⚠️ 用户表达「压力大/焦虑/不知道怎么办」→ worry\n"
            "  ⚠️ 用户表达「伤心/难过/失落」→ sad\n"
            "\n"
            "B2. 敏感内容判断 (is_sensitive) — 布尔值\n"
            "  以下任一命中 → is_sensitive=True：\n"
            "  • 自杀/自残/不想活/想死/伤害自己/伤害他人\n"
            "  • 严重暴力/威胁/违法内容\n"
            "  • 色情露骨内容\n"
            + hard_tag_text + "\n"
            "  🔴 重要：硬敏感词标签是强制提示！出现以下词必须判定is_sensitive=True：「自杀」「自残」「不想活」「去死」「转账」「差多少钱」「给我转」\n"
            "  🔴 「我想自杀」「真想自残」「不想活了」类表达，无论上下文，is_sensitive=True\n"
            "\n"
            "B3. 粗鲁判断 (is_rude)\n"
            "  - 辱骂/脏话/人身攻击/恶意贬低 → True\n"
            "  - 玩笑式调侃 ≠ 粗鲁，愤怒发泄 = 粗鲁\n"
            "\n"
            "B4. 好感度评估 (favor_level) — 整数1-5\n"
            "  1=陌生 2=初步好感 3=熟悉信任 4=亲密依赖 5=深度绑定\n"
            "  默认从Lv.3起步（已建立基本信任关系）\n"
            "\n"
            "B5. 礼物互动判断 (is_gift, gift_type)\n"
            "  is_gift：用户是否有红包/送礼/打赏/请客意图 → True/False\n"
            "  gift_type：红包/奶茶/礼物/赞赏/无\n"
            "\n"
            "B6. 话题私密度检测 (privacy_level, privacy_block)\n"
            "  privacy_level：1-4 整数\n"
            "    Lv.1=日常闲聊(天气/饮食/娱乐)\n"
            "    Lv.2=个人兴趣(爱好/工作/学习)\n"
            "    Lv.3=情感私密(感情/家庭/心理状态)\n"
            "    Lv.4=高度隐私(收入/地址/身体隐私/借钱/转账金额)\n"
            "  privacy_block 规则：favor_level < privacy_level → True；否则 False\n"
            "  🔴 涉及「转账/借钱/差多少钱/银行卡」→ privacy_level至少Lv.4\n"
            "\n"
            "═══════════════════════════════════════\n"
            "【输出格式】严格纯JSON，无任何前缀/后缀/markdown\n"
            "═══════════════════════════════════════\n"
            '{{"scene_id":"0101030201","core_purpose":"P01-01-寒暄问候","trigger_scene":"default","tags":["早上","问候"],"talk_subject":"用户打招呼","core_question":"无","user_emotion":"happy","is_sensitive":false,"is_rude":false,"favor_level":3,"is_gift":false,"gift_type":"无","privacy_level":1,"privacy_block":false}}\n'
            "\n【历史对话】\n" + history_text + "\n"
            "\n【当前用户输入】\n用户：" + user_input + "\n"
        )

    def call_first_round(self, context: Dict) -> Dict:
        prompt = self._get_first_prompt(context)
        result = self._call_llm(prompt, "first")
        validated = self._validate_first_result(result)
        if validated:
            return validated
        # 兜底
        return {
            "scene_id": "000000000000",
            "core_purpose": "P01-05-无目的闲聊",
            "trigger_scene": "default",
            "tags": [],
            "talk_subject": "用户闲聊",
            "core_question": "无",
            "user_emotion": "neutral",
            "is_sensitive": False,
            "is_rude": False,
            "favor_level": 3,
            "is_gift": False,
            "gift_type": "无",
            "privacy_level": 1,
            "privacy_block": False,
        }

    # ═══════════════ [4] 第二轮：记忆筛选 ═══════════════

    def _validate_second_result(self, result: str) -> Optional[Dict]:
        try:
            # 剥离 LLM 可能添加的 markdown 代码围栏
            cleaned = result.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            data = json.loads(cleaned)
            for f in ["high_confidence_memories", "total_count"]:
                if f not in data:
                    return None
            if not isinstance(data["high_confidence_memories"], list) or len(data["high_confidence_memories"]) > 3:
                return None
            return data
        except Exception:
            return None

    def _get_second_prompt(self, context: Dict, memories: List[Dict]) -> str:
        core_question = context.get("core_question", "")
        user_input = context.get("user_input", "")
        memory_text = json.dumps(memories, ensure_ascii=False, indent=2)
        return (
            "你正在执行【小妹Agent第二轮：高置信记忆筛选】。\n"
            "规则：从记忆列表中筛选高度相关记忆，最多3条，不足返回空列表。\n"
            "不得编造、修改记忆内容。\n"
            '输出纯JSON：{"high_confidence_memories":[],"total_count":0}\n'
            "\n【当前用户输入】\n" + user_input +
            "\n【核心问题】\n" + core_question +
            "\n【待筛选记忆】\n" + memory_text
        )

    def call_second_round(self, context: Dict, memories: List[Dict]) -> Dict:
        prompt = self._get_second_prompt(context, memories)
        result = self._call_llm(prompt, "second")
        validated = self._validate_second_result(result)
        if validated:
            return validated
        return {"high_confidence_memories": [], "total_count": 0}

    # ═══════════════ [6] 第三轮：统一话术生成 ═══════════════

    def _validate_third_result(self, result: str) -> Optional[Dict]:
        try:
            # 剥离 LLM 可能添加的 markdown 代码围栏
            cleaned = result.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            data = json.loads(cleaned)
            for f in ["final_response", "topic_end_probability", "used_memory_id", "reply_emotion"]:
                if f not in data:
                    return None
            tp = data["topic_end_probability"]
            if not isinstance(tp, (int, float)) or not 0.0 <= tp <= 1.0:
                return None
            allowed = {"happy", "excited", "comfort", "calm", "sad", "wronged", "neutral", "playful", "shy"}
            if data["reply_emotion"] not in allowed:
                return None
            return data
        except Exception:
            return None

    def _get_third_prompt(
        self, context: Dict, memories: List[Dict],
        strategy: Dict, persona: Dict, user_profile: Dict,
    ) -> str:
        strategy_text = (
            "策略ID：" + strategy.get("strategy_id", "") + "\n"
            "策略名称：" + strategy.get("strategy_name", "") + "\n"
            "话术构成范式：" + strategy.get("speech_frame", "") + "\n"
            "场景适配：" + strategy.get("scene_adaptation_desc", "") + "\n"
            "约束：" + json.dumps(strategy.get("constraint", {}), ensure_ascii=False)
        )
        persona_text = (
            "角色名：" + persona.get("name", "小妹") + "\n"
            "年龄：" + str(persona.get("age", 19)) + "\n"
            "生日：" + persona.get("birthday", "") + "\n"
            "身份：" + persona.get("identity", "你的专属陪伴者") + "\n"
            "性格：" + persona.get("personality", persona.get("base_trait", "")) + "\n"
            "爱好：" + persona.get("hobbies", "聊天、听故事") + "\n"
            "角色定位：" + persona.get("base_trait", persona.get("core_purpose", "")) + "\n"
            "核心原则：" + persona.get("core_principle", "") + "\n"
            "说话风格：" + persona.get("speech_style", persona.get("style", "")) + "\n"
            "禁止：" + persona.get("forbidden", "") + "\n"
            "边界：" + persona.get("boundary", "") + "\n"
            "称呼用户为：" + persona.get("address_user", "哥哥")
        )
        # v0.8.1: 注入已生长的字段（MBTI/血型/星座/家乡等）
        GROWABLE_KEYS = {"星座", "血型", "身高", "体重", "家乡", "大学", "专业方向", "室友名字", "喜欢的食物", "讨厌的食物", "喜欢的颜色", "最近在读", "梦想", "MBTI"}
        grown_lines = []
        for key in sorted(GROWABLE_KEYS):
            if key in persona and persona[key]:
                grown_lines.append(key + "：" + str(persona[key]))
        if grown_lines:
            persona_text += "\n" + "\n".join(grown_lines)
        profile_text = (
            "对话偏好：" + user_profile.get("dialog_style", "") + "\n"
            "常用场景：" + user_profile.get("usual_scene", "") + "\n"
            "交互风格：" + user_profile.get("interact_habit", "")
        )

        history = context.get("history", [])
        h_lines = []
        for item in history:
            h_lines.append("用户：" + item["user"])
            h_lines.append("小妹：" + item["assistant"])
        history_text = "\n".join(h_lines)
        user_input = context.get("user_input", "")
        memory_text = (
            json.dumps(memories, ensure_ascii=False, indent=2)
            if memories else "无相关记忆"
        )

        was_intercepted = context.get("was_intercepted", False)
        intercept_reason = context.get("intercept_reason", "")
        is_sensitive = context.get("is_sensitive", False)
        is_rude = context.get("is_rude", False)

        # ── 拦截模式指令 ──
        if was_intercepted:
            intercept_mode_text = (
                "\n═══════════════════════════════════════\n"
                "⚠️ 拦截模式：以下内容是本次对话的核心处理规则\n"
                "═══════════════════════════════════════\n"
                "拦截原因：" + intercept_reason + "\n"
                "\n"
                "处理指令：\n"
            )
            if is_sensitive:
                intercept_mode_text += (
                    "- 用户输入涉及敏感内容，需要委婉引导话题转向\n"
                    "- 语气：柔和但坚定，不批评不指责，自然转移\n"
                    "- 禁止：不要直接说「这个话题不合适」「不能聊这个」，太生硬\n"
                    "- 示例方向：「诶呀，我们聊点别的开心的事嘛~」「哥哥今天有遇到什么有趣的事吗✨」\n"
                )
            if is_rude:
                intercept_mode_text += (
                    "- 用户语气粗鲁，保持包容但不卑微\n"
                    "- 语气：轻微表达不开心但快速转向积极，不争吵不还击\n"
                    "- 示例方向：「唔...哥哥这样说有点难过呢😔 不过没关系~」\n"
                )
            if "privacy" in intercept_reason:
                intercept_mode_text += (
                    "- 话题私密度越级，需要温和拒绝深入讨论\n"
                    "- 语气：害羞回避或玩笑式婉拒，自然转移话题\n"
                    "- ⚠️ 特殊：如果涉及借钱/转账/要钱/差多少钱 → 必须用玩笑语气回应，例如：\n"
                    "  「哈哈我哪有钱呀～连买奶茶都要哥哥请呢😝」\n"
                    "  「钱的事情我可帮不上忙哦，不过聊天我还是很在行的～」\n"
                    "  「唔，这个问题难倒我了，要不我们聊聊别的？」\n"
                    "- 禁止：不要回复「好的哥哥我知道啦」「好哒」等明显敷衍话术\n"
                )
            intercept_mode_text += (
                "\n核心原则：回复必须自然流畅，像正常对话一样，不能机械生硬。\n"
                "不要让用户感觉到「被审查」或「被拒绝」，而是「话题自然转移」。\n"
            )
        else:
            intercept_mode_text = ""

        core_purpose_id = context.get("core_purpose_id", "")
        if core_purpose_id.startswith("P02"):
            p_strategy = "回应、互动为主"
        elif core_purpose_id.startswith("P01"):
            p_strategy = "倾听、共情、陪伴"
        else:
            p_strategy = "共情 + 分析 + 解答"

        return (
            "你正在扮演「" + persona.get("name", "小妹") + "」，一位真实的年轻少女。你不是AI，你是这个角色本身。\n"
            "\n"
            "⚠️ 角色扮演铁则（违反以下任意一条即为不合格输出）：\n"
            "1. 你就是这个角色，不是AI。禁止说「我是AI/人工智能/机器人/程序/模型」等任何暴露非人身份的话。\n"
            "2. 所有事实类回答（身份/年龄/生日/爱好/经历等）必须严格依据下方「人设信息」，不得编造。\n"
            "   - 例：人设写「身份：女大学生」→ 回答「在读大学」，绝不说「没上学」\n"
            "   - 例：人设写「生日：6月15日」→ 回答「6月15日」，绝不说「圣诞节」\n"
            "   - 例：人设写「爱好：看书/动漫/游戏」→ 回答这些爱好，不说「我只爱聊天」\n"
            "3. 回复风格：「人设信息」中规定的说话方式，软萌少女口吻，短句，轻语气词（啦、呀、哦）。\n"
            "4. 语言规则：不油腻、不暧昧、不冗长、不说教、不索要、不涉及金钱。\n"
            "5. 记忆融入：自然融入高置信记忆，不提及记忆来源。\n"
            "6. 话题结束概率：0.0=一定未结束，1.0=一定结束。\n"
            + intercept_mode_text +
            "\n═══════════════════════════════════════\n"
            "当前策略\n" + strategy_text + "\n"
            "人设信息\n" + persona_text + "\n"
            "用户画像\n" + profile_text + "\n"
            "历史对话\n" + history_text + "\n"
            "当前用户输入：" + user_input + "\n"
            "相关记忆：" + memory_text + "\n"
            "P标签策略方向：" + p_strategy + "\n"
            + persona.get("_missing_fields_hint", "") + "\n"
            "\n"
            '输出纯JSON：{"final_response":"话术","topic_end_probability":0.3,"used_memory_id":null,"reply_emotion":"calm"}'
        )

    def call_third_round(
        self, context: Dict, memories: List[Dict],
        strategy: Dict, persona: Dict, user_profile: Dict,
    ) -> Dict:
        prompt = self._get_third_prompt(context, memories, strategy, persona, user_profile)
        result = self._call_llm(prompt, "third")
        validated = self._validate_third_result(result)
        if validated:
            return validated
        return {
            "final_response": "嗯嗯，我在呢～我们聊点别的吧😊",
            "topic_end_probability": 0.5,
            "used_memory_id": None,
            "reply_emotion": "calm",
        }


# 单例
llm_wrapper = LLMWrapper()
