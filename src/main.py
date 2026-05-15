#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小妹技能包主入口 — v0.9.0
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

# ═══════════════ [v0.9.0] 启动时自动注入 LLM API Key ═══════════════
# 不再硬编码 DeepSeek。从 openclaw.json 读取 Agent 配置的 model，
# 根据 model 前缀匹配 provider，注入对应的 API Key + baseUrl。
# 环境变量：
#   XIAOMEI_API_KEY   — LLM API Key
#   XIAOMEI_API_BASE  — LLM API base URL（OpenAI 兼容）
#   XIAOMEI_MODEL     — 模型 ID
def _inject_llm_config():
    """从 openclaw.json 自动读取 Agent 配置的 LLM provider 并注入环境变量"""
    if os.environ.get("XIAOMEI_API_KEY"):
        return  # 已手动设置

    cfg_path = os.path.expanduser("~/.openclaw/openclaw.json")
    if not os.path.exists(cfg_path):
        return

    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        return

    # 1. 获取 Agent 配置的 model（如 volcengine/doubao-seed-2-0-pro-260215）
    agent_model = None
    agents_list = cfg.get("agents", {}).get("list", [])
    for a in agents_list:
        if a.get("id") == "xiaomei":
            agent_model = a.get("model", "")
            break

    if not agent_model:
        return

    # 2. 解析 provider 前缀
    if "/" not in agent_model:
        return
    provider_name = agent_model.split("/")[0]
    model_id = agent_model.split("/", 1)[1]

    # 3. 从 providers 中匹配
    providers = cfg.get("models", {}).get("providers", {})
    provider = providers.get(provider_name, {})

    api_key = provider.get("apiKey", "")
    base_url = provider.get("baseUrl", "")

    if api_key:
        os.environ["XIAOMEI_API_KEY"] = api_key
    if base_url:
        os.environ["XIAOMEI_API_BASE"] = base_url
    os.environ["XIAOMEI_MODEL"] = model_id

_inject_llm_config()

# --- 路径配置 ---
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_JSON_PATH = os.path.join(SKILL_DIR, "skill.json")
AGENT_DIR = os.path.expanduser("~/.openclaw/agents/xiaomei/")
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PERSONA_CONFIG_PATH = os.path.join(SRC_DIR, "config", "persona.json")
AGENT_CONFIG_PATH = os.path.join(AGENT_DIR, "config", "agent_config.json")

# --- 版本 ---
VERSION = "0.9.0"
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
                print(f"[init] 已复制 {desc} → {target}")
                break


# ═══════════════ 首次引导 ═══════════════

def is_first_launch():
    """检查是否首次启动"""
    return not os.path.exists(AGENT_CONFIG_PATH)


def _run_first_launch(user_input: str = "") -> str:
    """执行首次引导流程，返回欢迎信息"""
    os.makedirs(os.path.dirname(AGENT_CONFIG_PATH), exist_ok=True)

    # 初始化 agent 目录（复制模板）
    _init_agent_dir()

    # 同意就保存 first_launch_completed 标记
    consent_markers = ["同意", "好的", "好", "可以", "行", "是", "yes", "ok", "嗯", "1"]
    consented = any(m in user_input.lower() for m in consent_markers) if user_input else True

    if consented:
        config = {
            "first_launch_completed": True,
            "created_at": __import__('datetime').datetime.now().isoformat(),
            "version": VERSION,
        }
        with open(AGENT_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        # 读取 persona 获取 address_user 称呼
        address_user = "哥哥"
        if os.path.exists(PERSONA_CONFIG_PATH):
            try:
                with open(PERSONA_CONFIG_PATH, "r", encoding="utf-8") as f:
                    address_user = json.load(f).get("address_user", "哥哥")
            except Exception:
                pass

        return f"🎉 初始化完成！我是小妹，{address_user}以后可以随时找我聊天哦～"

    return f"⚠️ 隐私规则\n━━━━━━━━━━━━━━━━━━━━\n• 所有对话数据存储在本地\n• 不会上传到任何服务器\n• LLM API 调用由你的 OpenClaw 配置控制\n\n回复「同意」或「好」继续～"


# ═══════════════ 命令系统 ═══════════════

def _show_help() -> str:
    return (
        f"🌟 小妹 v{VERSION}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"帮助命令:\n"
        f"  /xiaomei help      显示本帮助\n"
        f"  /xiaomei status    查看运行状态\n"
        f"  /xiaomei dev       切换开发者模式\n"
        f"  /xiaomei memory    浏览近期记忆\n"
        f"  /reset_persona     重置人设为默认\n"
        f"  /reset             重置全部配置\n"
    )


def _show_status() -> str:
    """显示运行状态"""
    model = os.environ.get("XIAOMEI_MODEL", "(未配置)")
    api_ok = bool(os.environ.get("XIAOMEI_API_KEY"))

    # 记忆数量
    mem_count = 0
    try:
        from memory_engine import MemoryEngine
        mem = MemoryEngine()
        mem_count = mem.get_memory_count()
    except Exception:
        pass

    # 好感度
    favor_info = {"level": 3, "favor_value": 50}
    try:
        from favor_manager import FavorManager
        fm = FavorManager()
        favor_info = fm.get_favor_info()
    except Exception:
        pass

    return (
        f"🌟 小妹 v{VERSION}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 LLM: {model}\n"
        f"🔑 API: {'已配置' if api_ok else '未配置（语料库模式）'}\n"
        f"🧠 记忆: {mem_count} 条\n"
        f"💝 好感度: Lv.{favor_info['level']} ({favor_info['favor_value']})\n"
    )


def handle_command(cmd: str) -> str:
    """处理 /xiaomei 开头的命令"""
    cmd = cmd.strip()

    # /xiaomei help
    if re.search(r'(?:^|\s)help(?:\s|$)', cmd, re.IGNORECASE):
        return _show_help()

    # /xiaomei status
    if re.search(r'(?:^|\s)status(?:\s|$)', cmd, re.IGNORECASE):
        return _show_status()

    # /xiaomei dev [on|off|status]
    if re.search(r'(?:^|\s)dev(?:\s|$)', cmd, re.IGNORECASE):
        return _toggle_dev_mode(cmd)

    # /xiaomei memory
    if re.search(r'(?:^|\s)memory(?:\s|$)', cmd, re.IGNORECASE):
        return _browse_memory()

    # 默认 /xiaomei → 显示状态
    return _show_status()


def _toggle_dev_mode(cmd: str) -> str:
    """切换开发者模式"""
    config = {}
    if os.path.exists(AGENT_CONFIG_PATH):
        try:
            with open(AGENT_CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            pass

    current = config.get("dev_mode", False)

    if "on" in cmd:
        config["dev_mode"] = True
        action = "已开启"
    elif "off" in cmd:
        config["dev_mode"] = False
        action = "已关闭"
    else:
        return f"🔧 开发者模式: {'🟢 开启' if current else '⚫ 关闭'}"

    with open(AGENT_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    return f"🔧 开发者模式 {action}"


def _browse_memory() -> str:
    """浏览近期记忆"""
    try:
        from memory_engine import MemoryEngine
        mem = MemoryEngine()
        memories = mem.search_memory("", limit=5)
        if not memories:
            return "🧠 暂时还没有记忆呢～"
        lines = ["🧠 近期记忆:"]
        for i, m in enumerate(memories, 1):
            content = m.get("content", "")[:40]
            lines.append(f"  {i}. {content}...")
        return "\n".join(lines)
    except Exception as e:
        return f"⚠️ 记忆系统异常: {e}"


# ═══════════════ 对话入口 ═══════════════

def chat(user_input: str, history: Optional[List[Dict]] = None) -> str:
    """
    主对话入口。
    如果首次启动，走引导流程；否则走 conversation_engine。
    """
    user_input = user_input.strip()
    if not user_input:
        return "嗯？哥哥想说什么呀～"

    # 首次启动 → 引导
    if is_first_launch() and not user_input.startswith("/"):
        return _run_first_launch(user_input)

    # 命令路由
    if user_input.startswith("/xiaomei"):
        return handle_command(user_input)

    # 特殊命令
    if user_input == "/reset_persona":
        return _reset_persona()
    if user_input == "/reset":
        return _reset_all()

    # 对话引擎
    try:
        from conversation_engine import ConversationEngine
        engine = ConversationEngine()
        history = history or []
        return engine.chat(user_input, history)
    except Exception as e:
        # 降级兜底
        return f"唔…好像出了点小问题({str(e)[:30]})，等会儿再说好不好～"


def _reset_persona() -> str:
    """重置人设为默认"""
    persona_path = os.path.join(AGENT_DIR, "persona.json")
    template = os.path.join(SRC_DIR, "config", "persona.json")
    if os.path.exists(template):
        import shutil
        shutil.copy2(template, persona_path)
        return "✅ 人设已恢复为默认值"
    return "⚠️ 未找到人设模板"


def _reset_all() -> str:
    """重置全部配置"""
    import shutil
    if os.path.exists(AGENT_DIR):
        shutil.rmtree(AGENT_DIR)
    return "🔄 已重置，下次对话将重新初始化"


# ═══════════════ CLI 入口 ═══════════════

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
        print(chat(user_input))
    else:
        print(f"小妹 v{VERSION} 🌟")
        print("用法: python3 main.py <消息>")
        print("示例: python3 main.py '你好呀'")
