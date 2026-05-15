#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小妹技能包主入口 — v0.8.0
合并：v0.7.5命令系统 + conversation_engine对话引擎 + first_launch首次引导
"""
import os
import sys
import re
import json
import uuid
from typing import List, Dict, Optional, Any

# 确保模块可导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ═══════════════ [v0.8.0] 启动时自动注入 API Key ═══════════════
# 当通过 OpenClaw Agent exec 调用时，DEEPSEEK_API_KEY 不在环境中
# 从 openclaw.json 自动读取并注入
if not os.environ.get("DEEPSEEK_API_KEY"):
    _openclaw_cfg = os.path.expanduser("~/.openclaw/openclaw.json")
    if os.path.exists(_openclaw_cfg):
        try:
            with open(_openclaw_cfg, "r") as _f:
                _cfg = json.load(_f)
            _providers = _cfg.get("models", {}).get("providers", {})
            _dsk = _providers.get("deepseek", {})
            _key = _dsk.get("apiKey", "")
            if _key:
                os.environ["DEEPSEEK_API_KEY"] = _key
        except Exception:
            pass

# --- 路径配置 ---
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_JSON_PATH = os.path.join(SKILL_DIR, "skill.json")
AGENT_DIR = os.path.expanduser("~/.openclaw/agents/xiaomei/")
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PERSONA_CONFIG_PATH = os.path.join(SRC_DIR, "config", "persona.json")
AGENT_CONFIG_PATH = os.path.join(AGENT_DIR, "config", "agent_config.json")

# --- 版本 ---
VERSION = "v0.8.1"
if os.path.exists(SKILL_JSON_PATH):
    try:
        with open(SKILL_JSON_PATH, "r", encoding="utf-8") as f:
            skill_info = json.load(f)
            VERSION = skill_info.get("version", VERSION)
    except Exception:
        pass


# ═══════════════ [v0.8.1] 初始化流程：确保 agent 目录有模板文件 ═══════════════
def _init_agent_dir():
    """
    首次启动或发布版升级时，将模板 persona/user_profile 复制到 agent 目录。
    规则：agent 目录已存在的文件 → 永不覆盖（保护用户数据）
          agent 目录不存在的文件 → 从模板复制（模板位于 skill 包内）
    """
    os.makedirs(AGENT_DIR, exist_ok=True)

    # 模板来源：优先 skill 包内 agent-config/templates/，其次 src/config/
    template_dirs = [
        os.path.join(SKILL_DIR, "agent-config", "templates"),
        os.path.join(SRC_DIR, "config"),
    ]

    files_to_init = {
        "persona.json": "人设模板",
        "user_profile.json": "用户画像模板",
    }

    for filename, desc in files_to_init.items():
        target = os.path.join(AGENT_DIR, filename)
        if os.path.exists(target):
            continue  # 用户数据已存在，不覆盖

        # 找模板
        for td in template_dirs:
            src = os.path.join(td, filename)
            if os.path.exists(src):
                import shutil
                shutil.copy2(src, target)
                break

_init_agent_dir()


def get_status_info():
    """获取状态信息"""
    dev_mode = False
    if os.path.exists(AGENT_CONFIG_PATH):
        try:
            with open(AGENT_CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
                dev_mode = config.get("dev_mode", False)
        except Exception:
            pass

    # 记忆统计
    try:
        from memory_engine import memory_engine
        mem_counts = memory_engine.get_memory_count()
        mem_info = f"热记忆{mem_counts['hot']}条 / 冷记忆{mem_counts['cold']}条 / 永久{mem_counts['permanent']}条"
    except Exception:
        mem_info = "记忆系统加载中..."

    # 好感度信息
    try:
        from favor_manager import favor_manager
        favor_info = favor_manager.get_favor_info()
        favor_str = f"Lv{favor_info['level']}（好感值{favor_info['favor_value']}，连续{favor_info['continuous_days']}天）"
    except Exception:
        favor_str = "加载中..."

    # Token 统计
    try:
        from token_tracker import token_tracker
        token_str = token_tracker.get_usage_text()
    except Exception:
        token_str = ""

    session_id = str(uuid.uuid4())[:8]
    return f"""🥰 凌啡哥哥，这是小妹的当前状态哦😘
✅ 版本：{VERSION}
✅ 运行状态：在线乖乖待命，随时陪凌啡哥哥聊天呀~
✅ 当前模型：deepseek/deepseek-v4-pro
✅ 隐私模式：完全独立上下文，数据隔离，隐私绝对安全哒
✅ 记忆系统：{mem_info}
✅ 好感度：{favor_str}
✅ 开发者模式：{'✅ 已开启' if dev_mode else '❌ 已关闭'}
{token_str}
有什么想要调整的随时告诉小妹哦~我永远都在呀🥰"""


def handle_command(message: str):
    """处理系统命令（v0.7.5 完整命令系统）"""
    cmd = message.strip().lower()

    # 统一处理 /xiaomei 开头的命令
    xiaomei_match = re.match(r"^\s*/xiaomei(?:\s+(.+))?$", cmd, re.IGNORECASE)
    if xiaomei_match:
        sub_cmd = (xiaomei_match.group(1) or "").strip()

        # /xiaomei（无参数）= status
        if not sub_cmd:
            return get_status_info()

        # /xiaomei help
        if sub_cmd == "help":
            return f"""🥰 凌啡哥哥，这是小妹 v{VERSION} 的帮助说明哦：
👉 /xiaomei help → 查看当前帮助信息
👉 /xiaomei status → 查看小妹当前的运行状态和配置
👉 /xiaomei persona → 查看我的完整人设信息
👉 /xiaomei dev [on/off/status] → 开发者模式控制
👉 /xiaomei memory → 查看我记住的所有重要信息哦
👉 /xiaomei reset → 重置配置，重新走首次引导流程
有什么需要凌啡哥哥随时告诉我呀😘"""

        # /xiaomei status
        if sub_cmd == "status":
            return get_status_info()

        # /xiaomei persona
        if sub_cmd == "persona":
            if os.path.exists(PERSONA_CONFIG_PATH):
                try:
                    with open(PERSONA_CONFIG_PATH, "r", encoding="utf-8") as f:
                        persona = json.load(f)
                    return f"""🥰 凌啡哥哥，这是我的完整人设哦：
✨ 姓名：{persona.get('name', '小妹')}
✨ 年龄：{persona.get('age', '20')}
✨ 性格：{persona.get('personality', '活泼可爱')}
✨ 说话风格：{persona.get('speech_style', '温柔甜美')}
✨ 生日：{persona.get('birthday', '6月15日')}
✨ 喜好：{persona.get('hobbies', '看书/看电影/动漫/游戏/历史')}
✨ 对你的称呼：{persona.get('address_user', '哥哥')}
有什么想要调整的随时告诉我呀😘"""
                except Exception:
                    pass
            return "😢 暂时还没有设置人设信息哦，首次对话会引导你配置哒~"

        # /xiaomei dev
        if sub_cmd.startswith("dev"):
            dev_parts = sub_cmd.split()
            dev_action = dev_parts[1].lower() if len(dev_parts) > 1 else "status"
            dev_mode = False
            if os.path.exists(AGENT_CONFIG_PATH):
                try:
                    with open(AGENT_CONFIG_PATH, "r", encoding="utf-8") as f:
                        config = json.load(f)
                        dev_mode = config.get("dev_mode", False)
                except Exception:
                    pass

            if dev_action == "status":
                return f"🔧 开发者模式当前状态：{'✅ 已开启' if dev_mode else '❌ 已关闭'}"
            elif dev_action == "on":
                config = {}
                if os.path.exists(AGENT_CONFIG_PATH):
                    try:
                        with open(AGENT_CONFIG_PATH, "r", encoding="utf-8") as f:
                            config = json.load(f)
                    except Exception:
                        pass
                config["dev_mode"] = True
                os.makedirs(os.path.dirname(AGENT_CONFIG_PATH), exist_ok=True)
                with open(AGENT_CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                os.environ["XIAOMEI_DEV_MODE"] = "true"
                return "✅ 开发者模式已开启，会记录全链路调试日志哦"
            elif dev_action == "off":
                config = {}
                if os.path.exists(AGENT_CONFIG_PATH):
                    try:
                        with open(AGENT_CONFIG_PATH, "r", encoding="utf-8") as f:
                            config = json.load(f)
                    except Exception:
                        pass
                config["dev_mode"] = False
                os.makedirs(os.path.dirname(AGENT_CONFIG_PATH), exist_ok=True)
                with open(AGENT_CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                os.environ["XIAOMEI_DEV_MODE"] = "false"
                return "✅ 开发者模式已关闭"

        # /xiaomei memory
        if sub_cmd == "memory":
            try:
                from memory_engine import memory_engine
                memories = memory_engine.search_memory(limit=10)
                if not memories:
                    return "📝 暂时还没有记住什么特别的事情呢~ 多和我说说话我就会记住的哦😘"
                lines = ["📝 小妹记住的事情："]
                for i, mem in enumerate(memories, 1):
                    preview = mem['content'][:50] + ("..." if len(mem['content']) > 50 else "")
                    lines.append(f"  {i}. [{mem['level']}] {preview}")
                return "\n".join(lines)
            except Exception as e:
                return f"⚠️ 记忆查询失败：{e}"

        # /xiaomei reset
        if sub_cmd == "reset":
            try:
                from first_launch import FIRST_LAUNCH_FLAG, GUIDE_STATUS_PATH
                if os.path.exists(FIRST_LAUNCH_FLAG):
                    os.remove(FIRST_LAUNCH_FLAG)
                if os.path.exists(GUIDE_STATUS_PATH):
                    os.remove(GUIDE_STATUS_PATH)
                return "✅ 已重置配置，下次对话将重新走首次引导流程~"
            except Exception as e:
                return f"⚠️ 重置失败：{e}"

        # 未知子命令
        return "⚠️ 未知命令哦，输入 /xiaomei help 查看支持的命令列表呀😘"

    # 兼容旧命令
    if cmd in ("/help", "help"):
        return handle_command("/xiaomei help")
    if cmd in ("/status", "status"):
        return handle_command("/xiaomei status")

    # check_tmp 的 /uninstall 处理（从 check_tmp 保留）
    if cmd == "/uninstall":
        return """
⚠️ 你确定要卸载小妹技能包吗？
请选择卸载模式：
👉 输入 `y` 完全卸载：所有记忆、配置、数据全部清除
👉 输入 `k` 保留数据卸载：仅删除程序，记忆和人设保留
👉 输入 `n` 取消卸载操作
"""
    if cmd == "y":
        import subprocess
        try:
            uninstall_script = os.path.join(SRC_DIR, "..", "uninstall.sh")
            subprocess.Popen(["bash", uninstall_script, "--non-interactive"], shell=False)
            return "✅ 正在后台执行完全卸载... 🥺 很遗憾不能继续陪伴凌啡哥哥啦~"
        except Exception as e:
            return f"❌ 卸载失败：{e}"
    if cmd == "k":
        import subprocess
        try:
            uninstall_script = os.path.join(SRC_DIR, "..", "uninstall.sh")
            subprocess.Popen(["bash", uninstall_script, "--non-interactive", "--keep-data"], shell=False)
            return "✅ 数据已保留，下次安装可直接继承~ 🥺 凌啡哥哥要想我哦~"
        except Exception as e:
            return f"❌ 卸载失败：{e}"
    if cmd == "/reset":
        try:
            from first_launch import FIRST_LAUNCH_FLAG
            guide_status_path = os.path.join(SRC_DIR, "config", ".guide_status")
            if os.path.exists(FIRST_LAUNCH_FLAG):
                os.remove(FIRST_LAUNCH_FLAG)
            if os.path.exists(guide_status_path):
                os.remove(guide_status_path)
            return "✅ 已重置配置引导，下次对话将重新走首次引导~"
        except Exception as e:
            return f"⚠️ 重置失败：{e}"

    return None


def handle_message(user_input: str, history: Optional[List[Dict]] = None, prev_state: Optional[Dict] = None) -> Dict:
    """
    统一消息处理入口 (v0.8.0)
    流程：命令拦截 → 首次引导 → 对话引擎
    """
    history = history or []
    prev_state = prev_state or {}

    # ── 第一优先级：命令拦截 ──
    if re.match(r"^\s*/xiaomei(?:\s|$)", user_input, re.IGNORECASE) or \
       user_input.strip().lower() in ("/help", "help", "/status", "status",
                                       "/uninstall", "/reset", "y", "k", "n"):
        command_result = handle_command(user_input)
        if command_result is not None:
            return {
                "final_response": command_result,
                "topic_end_probability": 0.5,
                "used_memory_id": None,
                "reply_emotion": "happy",
                "scene_id": "000000000000",
                "core_purpose": "P01-05"
            }

    # ── 第二优先级：首次启动引导 ──
    try:
        from first_launch import first_launch_handler, FIRST_LAUNCH_FLAG

        if first_launch_handler.is_first_launch or first_launch_handler.is_in_guide():
            completed, guide_response = first_launch_handler.process_input(user_input)
            if completed:
                with open(FIRST_LAUNCH_FLAG, "w") as f:
                    f.write("completed")
            return {
                "final_response": guide_response,
                "topic_end_probability": 0.5 if not completed else 0,
                "used_memory_id": None,
                "reply_emotion": "happy",
                "scene_id": "000000000000",
                "core_purpose": "P01-05"
            }
    except Exception as e:
        # 引导模块加载失败，继续尝试对话引擎
        pass

    # ── 第三优先级：对话引擎 ──
    try:
        from conversation_engine import conversation_engine

        session_id = prev_state.get("session_id", str(uuid.uuid4()))
        response_text, meta = conversation_engine.generate_response(user_input, session_id)

        # 尝试获取情绪
        try:
            from emotion_engine import emotion_engine as ee
            emotion, _, _ = ee.detect_emotion(response_text)
        except Exception:
            emotion = "happy"

        return {
            "final_response": response_text,
            "topic_end_probability": meta.get("topic_end_probability", 0.3),
            "used_memory_id": meta.get("used_memory_id"),
            "reply_emotion": emotion,
            "scene_id": meta.get("scene_id", "000000000000"),
            "core_purpose": meta.get("core_purpose", "P01-05")
        }
    except Exception as e:
        pass

    # ── 兜底 ──
    return {
        "final_response": "😘 凌啡哥哥好呀，我是小妹🥰，有什么想聊的都可以告诉我哦~",
        "topic_end_probability": 0.3,
        "used_memory_id": None,
        "reply_emotion": "happy",
        "scene_id": "000000000000",
        "core_purpose": "P01-05"
    }


if __name__ == "__main__":
    # v0.8.0: Agent/CLI 调用入口
    # 用法: python3 main.py "用户输入内容"
    if len(sys.argv) > 1:
        user_input = sys.argv[1]
    else:
        # stdin 兜底（管道模式）
        if not sys.stdin.isatty():
            user_input = sys.stdin.read().strip()
        else:
            # 交互模式
            user_input = input("凌啡哥哥，想说什么呀: ").strip()

    if not user_input:
        user_input = "/xiaomei status"

    result = handle_message(user_input)
    print(result["final_response"])
