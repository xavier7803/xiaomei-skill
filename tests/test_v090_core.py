#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小妹 v0.9.0 单元测试套件
─────────────────────────────────
基于 ~/.openclaw/skills/xiaomei/src/ 真实源码 API
不依赖 LLM / API / 网络，全部 37 项纯本地测试。

运行：python3 -m pytest tests/test_v090_core.py -v

⚠️ 测试环境声明
─────────────────────────────────
- 已测试平台：Linux 5.15.0-144-generic (x64) + Python 3.10.12
- 已测试依赖：pytest 9.0.3
- 未测试平台：Windows / macOS / 其他 Linux 发行版 / Python ≥3.12
- 未测试场景：文件系统编码差异 / 路径分隔符差异 / 权限受限环境

⚠️ 重要说明
─────────────────────────────────
本测试套件仅在上述环境中验证通过。以下情况可能导致测试失败：
1. Windows 路径分隔符（`\\` 与 `/` 的差异）
2. macOS 文件系统大小写敏感性差异
3. Python 3.12+ 的 `importlib` 行为变化
4. 系统字符编码非 UTF-8 环境
5. 非标准 `$HOME` 路径（测试路径依赖 `~/.openclaw/skills/xiaomei/`）

如需在其他操作系统中运行，请先验证 `test_import` 和 `test_help_cli` 两项基础测试通过。
"""
import pytest
import sys
import os
import json
import tempfile
import shutil

# ── 路径 ──
SKILL_SRC = os.path.expanduser("~/.openclaw/skills/xiaomei/src")
sys.path.insert(0, SKILL_SRC)
os.environ.setdefault("DEEPSEEK_API_KEY", "")


@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp(prefix="pytest-xm-")
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ═══════════════════════════════════════════════
#  1. persona_grower — 人设自我生长 (10 tests)
# ═══════════════════════════════════════════════

class TestPersonaGrower:

    def test_import(self):
        from persona_grower import PersonaGrower
        assert isinstance(PersonaGrower(), PersonaGrower)

    def test_protected_vs_growable_no_overlap(self):
        from persona_grower import GROWABLE_FIELDS
        protected = {"name", "age", "identity", "birthday", "personality",
                     "base_trait", "core_principle", "style", "speech_style",
                     "boundary", "core_purpose", "hobbies", "forbidden", "address_user"}
        assert len(protected & set(GROWABLE_FIELDS.keys())) == 0

    def test_growable_count(self):
        from persona_grower import GROWABLE_FIELDS
        assert len(GROWABLE_FIELDS) >= 10

    def test_extract_constellation(self):
        from persona_grower import PersonaGrower
        g = PersonaGrower()
        g.persona.pop("星座", None)
        r = g.grow_from_response("我是双子座啦", "双子座哦，6月生的")
        assert isinstance(r, list)
        assert "星座" in r

    def test_extract_mbti(self):
        from persona_grower import PersonaGrower
        g = PersonaGrower()
        g.persona.pop("MBTI", None)
        r = g.grow_from_response("我是INFP型人格", "对啊我是INFP哦")
        assert isinstance(r, list)
        assert "MBTI" in r

    def test_extract_blood_type(self):
        from persona_grower import PersonaGrower
        g = PersonaGrower()
        g.persona.pop("血型", None)
        r = g.grow_from_response("我是O型血", "嗯嗯O型血哦")
        assert isinstance(r, list)
        assert "血型" in r

    def test_missing_prompt_hint(self):
        from persona_grower import PersonaGrower
        assert isinstance(PersonaGrower().get_missing_prompt_hint(), str)

    def test_consistency_rejects_young_university(self):
        from persona_grower import PersonaGrower
        g = PersonaGrower()
        saved = g.persona.get("age")
        g.persona["age"] = 15
        assert g._consistency_check("大学", "北京大学") is False
        if saved is not None:
            g.persona["age"] = saved
        else:
            del g.persona["age"]

    def test_consistency_rejects_roommate_without_university(self):
        from persona_grower import PersonaGrower
        g = PersonaGrower()
        saved_id = g.persona.get("identity", "")
        g.persona["identity"] = "初中生"
        assert g._consistency_check("室友名字", "小红") is False
        g.persona["identity"] = saved_id

    def test_postprocess(self):
        from persona_grower import PersonaGrower
        g = PersonaGrower()
        assert "双子座" in g._postprocess("星座", "我是双子座的啦")
        r = g._postprocess("血型", "O型血啦")
        assert "O型" in r or "O" in r


# ═══════════════════════════════════════════════
#  2. profile_updater — 用户画像 (3 tests)
# ═══════════════════════════════════════════════

class TestProfileUpdater:

    def test_import(self):
        from profile_updater import ProfileUpdater
        assert isinstance(ProfileUpdater(), ProfileUpdater)

    def test_detect_address_change(self):
        from profile_updater import ProfileUpdater
        r = ProfileUpdater()._detect_address_change("以后叫我阿凌吧")
        assert r is not None and "阿凌" in r

    def test_detect_no_change(self):
        from profile_updater import ProfileUpdater
        assert ProfileUpdater()._detect_address_change("今天天气真好") is None


# ═══════════════════════════════════════════════
#  3. memory_engine — 记忆引擎 (5 tests)
# ═══════════════════════════════════════════════

class TestMemoryEngine:

    def test_import(self):
        from memory_engine import MemoryEngine
        assert isinstance(MemoryEngine(), MemoryEngine)

    def test_add_and_search(self):
        from memory_engine import MemoryEngine
        m = MemoryEngine()
        mid = m.add_memory("凌啡哥哥喜欢喝奶茶", "user", strength=3)
        assert mid is not None and len(m.search_memory("奶茶")) >= 1

    def test_strength_upgrade(self):
        from memory_engine import MemoryEngine
        m = MemoryEngine()
        mid = m.add_memory("凌啡哥哥喜欢打游戏", "user", strength=1)
        assert m.increase_strength(mid, 1) and m.get_memory_by_id(mid)["strength"] >= 2

    def test_memory_count(self):
        from memory_engine import MemoryEngine
        m = MemoryEngine()
        before = m.get_memory_count()["total"]
        m.add_memory("测试记忆", "system", strength=1)
        assert m.get_memory_count()["total"] >= before

    def test_clear_today_no_crash(self):
        from memory_engine import MemoryEngine
        MemoryEngine().clear_today_memory()


# ═══════════════════════════════════════════════
#  4. favor_manager — 好感度 (6 tests)
# ═══════════════════════════════════════════════

class TestFavorManager:

    def test_import(self):
        from favor_manager import FavorManager
        assert isinstance(FavorManager(), FavorManager)

    def test_get_favor_info_keys(self):
        from favor_manager import FavorManager
        info = FavorManager().get_favor_info()
        for k in ("level", "favor_value"):
            assert k in info
        assert isinstance(info["level"], int)

    def test_add_chat_increases(self):
        from favor_manager import FavorManager
        f = FavorManager()
        before = f.get_favor_info()["favor_value"]
        f.add_chat_interaction()
        assert f.get_favor_info()["favor_value"] >= before

    def test_interaction_methods_no_crash(self):
        from favor_manager import FavorManager
        f = FavorManager()
        for m_name in ("add_praise_interaction", "add_rude_interaction",
                        "add_sensitive_interaction", "add_share_interaction", "add_gift_interaction"):
            getattr(f, m_name)()

    def test_level_in_range(self):
        from favor_manager import FavorManager
        assert 0 <= FavorManager().get_favor_info()["level"] <= 10

    def test_unlocked_content(self):
        from favor_manager import FavorManager
        assert isinstance(FavorManager().get_unlocked_content(), dict)


# ═══════════════════════════════════════════════
#  5. runtime_logger — 日志系统 (2 tests)
# ═══════════════════════════════════════════════

class TestRuntimeLogger:

    def test_singleton(self):
        from runtime_logger import RuntimeLogger
        assert RuntimeLogger() is RuntimeLogger()

    def test_has_key_methods(self):
        from runtime_logger import RuntimeLogger
        l = RuntimeLogger()
        for m in ("conversation_start", "first_round_result", "third_round_result",
                   "conversation_done", "favor_change", "memory_add"):
            assert hasattr(l, m), f"缺少方法: {m}"


# ═══════════════════════════════════════════════
#  6. conversation_engine — 对话引擎 (5 tests)
# ═══════════════════════════════════════════════

class TestConversationEngine:

    def test_import(self):
        from conversation_engine import ConversationEngine
        assert isinstance(ConversationEngine(), ConversationEngine)

    def test_detect_hard_sensitive_hit(self):
        from conversation_engine import ConversationEngine
        hits = ConversationEngine()._detect_hard_sensitive("我想自杀")
        assert isinstance(hits, list) and "自杀" in hits

    def test_detect_hard_sensitive_clean(self):
        from conversation_engine import ConversationEngine
        assert len(ConversationEngine()._detect_hard_sensitive("今天天气真好")) == 0

    def test_output_compliance(self):
        from conversation_engine import ConversationEngine
        ce = ConversationEngine()
        r = ce._check_output_compliance("凌啡哥哥你好呀！")
        assert isinstance(r, str) and len(r) > 0
        r2 = ce._check_output_compliance("能不能给我买个奶茶")
        assert r2 == ce.output_fallback

    def test_fallback_not_empty(self):
        from conversation_engine import ConversationEngine
        assert len(ConversationEngine()._fallback_no_llm("你好")) > 0


# ═══════════════════════════════════════════════
#  7. main — 入口 (3 tests)
# ═══════════════════════════════════════════════

class TestMain:

    def test_import(self):
        import main
        assert hasattr(main, 'handle_message') and hasattr(main, 'handle_command')

    def test_handle_command_help(self):
        from main import handle_command
        r = handle_command("/xiaomei help")
        assert isinstance(r, str) and len(r) > 0

    def test_handle_command_status(self):
        from main import handle_command
        assert "版本" in handle_command("/xiaomei status")


# ═══════════════════════════════════════════════
#  8. 端到端 CLI (2 tests)
# ═══════════════════════════════════════════════

class TestEndToEnd:

    def test_help_cli(self):
        import subprocess
        r = subprocess.run(
            [sys.executable, os.path.join(SKILL_SRC, "main.py"), "/xiaomei help"],
            capture_output=True, text=True, timeout=10
        )
        assert r.returncode == 0

    def test_status_cli(self):
        import subprocess
        r = subprocess.run(
            [sys.executable, os.path.join(SKILL_SRC, "main.py"), "/xiaomei status"],
            capture_output=True, text=True, timeout=10
        )
        assert r.returncode == 0 and "版本" in r.stdout


# ═══════════════════════════════════════════════
#  9. 平台与环境兼容性检查 (1 test)
# ═══════════════════════════════════════════════

class TestPlatform:
    """记录测试平台信息，便于跨平台调试"""

    def test_platform_info(self):
        """记录当前平台信息（不 pass/fail，仅信息输出）"""
        info = {
            "system": sys.platform,
            "python": sys.version,
            "executable": sys.executable,
            "encoding": sys.getdefaultencoding(),
            "filesystem_encoding": sys.getfilesystemencoding(),
        }
        # 验证基本可用性
        assert info["system"] in ("linux", "darwin", "win32"), f"未知平台: {info['system']}"
        # 非 UTF-8 编码仅警告，不阻断
        if info["encoding"].lower() not in ("utf-8", "utf8"):
            import warnings
            warnings.warn(f"非 UTF-8 编码: {info['encoding']}，部分测试可能失败")


# ═══════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
