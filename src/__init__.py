#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小妹情绪陪伴技能包 - OpenClaw入口适配
符合OpenClaw技能开发规范v1.0，支持插件式零配置加载
版本：v1.0.0 MVP
作者：小云 ☁️
"""
import os
import sys
import json
from typing import Dict, Any, Optional, Tuple

# 技能元信息（符合OpenClaw规范）
SKILL_META = {
    "id": "com.openclaw.xiaomei",
    "name": "小妹",
    "version": "0.8.0",
    "description": "开源、本地、无害、纯情绪价值的虚拟陪伴技能，人设100%稳定，零运行成本",
    "author": "小云",
    "icon": "☁️",
    "category": "娱乐",
    "tags": ["情绪陪伴", "虚拟伴侣", "本地运行", "开源"],
    "platforms": ["all"],
    "min_openclaw_version": "2026.3.0",
    "max_openclaw_version": "*",
    "website": "https://github.com/openclaw-skill/xiaomei"
}

# 技能配置项（暴露给OpenClaw管理页面可调整）
SKILL_CONFIG = {
    "llm_enabled": {
        "name": "启用LLM增强",
        "type": "boolean",
        "default": True,
        "description": "是否允许调用LLM润色回复，关闭后完全使用本地语料，零成本运行"
    },
    "show_token_cost": {
        "name": "展示Token消耗",
        "type": "boolean",
        "default": True,
        "description": "是否在回复末尾展示本次Token消耗统计"
    },
    "daily_token_limit": {
        "name": "每日Token限额",
        "type": "number",
        "default": 10000,
        "min": 0,
        "max": 100000,
        "description": "每日最大Token消耗，0表示不限制，超出后自动切换纯本地模式"
    },
    "coquetry_level": {
        "name": "撒娇程度",
        "type": "number",
        "default": 3,
        "min": 1,
        "max": 5,
        "description": "回复的撒娇程度，1最低，5最高"
    },
    "emotion_sensitivity": {
        "name": "情绪灵敏度",
        "type": "number",
        "default": 0.5,
        "min": 0.3,
        "max": 0.8,
        "description": "情绪识别灵敏度，值越高越容易识别到情绪变化"
    },
    "memory_enabled": {
        "name": "启用记忆功能",
        "type": "boolean",
        "default": True,
        "description": "是否开启记忆功能，关闭后不会存储任何对话历史"
    },
    "log_enabled": {
        "name": "启用运行日志",
        "type": "boolean",
        "default": True,
        "description": "是否记录运行日志，关闭后不会生成任何日志文件，日志仅保存在本地不上传"
    },
    "log_level": {
        "name": "日志级别",
        "type": "string",
        "default": "info",
        "options": ["debug", "info", "warn", "error"],
        "description": "日志记录级别，debug记录最详细，error只记录错误"
    },
    "log_retention_days": {
        "name": "日志保留天数",
        "type": "number",
        "default": 7,
        "min": 1,
        "max": 30,
        "description": "日志文件自动保留的天数，超过天数的旧日志会自动删除"
    }
}

# 命令注册（符合OpenClaw命令规范）
SKILL_COMMANDS = [
    {
        "name": "help",
        "aliases": ["帮助", "bangzhu"],
        "description": "查看帮助说明",
        "usage": "/xiaomei help"
    },
    {
        "name": "status",
        "aliases": ["状态", "zhuangtai"],
        "description": "查看当前运行状态",
        "usage": "/xiaomei status"
    },
    {
        "name": "memory",
        "aliases": ["记忆", "jiyi"],
        "description": "查看历史记忆，支持关键词搜索",
        "usage": "/xiaomei memory [关键词/时间]"
    },
    {
        "name": "config",
        "aliases": ["配置", "peizhi"],
        "description": "调整技能配置",
        "usage": "/xiaomei config [配置项] [值]"
    },
    {
        "name": "clear",
        "aliases": ["清空", "qingkong"],
        "description": "清空对话记忆",
        "usage": "/xiaomei clear [all/today]"
    },
    {
        "name": "about",
        "aliases": ["关于", "guanyu"],
        "description": "关于小妹技能包",
        "usage": "/xiaomei about"
    },
    {
        "name": "export_corpus",
        "aliases": ["导出语料", "daochu"],
        "description": "导出所有或指定类型的语料库",
        "usage": "/xiaomei export_corpus [语料类型/all]"
    },
    {
        "name": "import_corpus",
        "aliases": ["导入语料", "daoru"],
        "description": "导入语料到指定类型，支持覆盖/追加模式",
        "usage": "/xiaomei import_corpus [语料类型] [append/cover] [JSON内容] [--auto-tag]，添加--auto-tag参数自动给纯文本语料打场景标签"
    },
    {
        "name": "reset_corpus",
        "aliases": ["重置语料", "chongzhi"],
        "description": "重置指定类型或所有语料到默认状态",
        "usage": "/xiaomei reset_corpus [语料类型/all]"
    }
]

# 加载内部模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.logger import logger  # 保留旧logger用于配置兼容
from runtime_logger import runtime_log
from first_launch import first_launch_handler
from conversation_engine import conversation_engine
from emotion_engine import emotion_engine
from llm_adapter import llm_adapter
from token_tracker import token_tracker
from memory_engine import memory_engine

# 全局状态
is_initialized = False

def on_load() -> Tuple[bool, Optional[str]]:
    """
    OpenClaw技能加载钩子，技能被加载时调用
    返回(是否成功, 错误信息)
    """
    global is_initialized
    try:
        # 初始化所有模块
        if not first_launch_handler.is_first_launch:
            # 非首次启动直接加载配置
            llm_adapter.load_config()
            token_tracker.load_config()
            memory_engine.load_memory()
            # 加载日志配置
            log_enabled = llm_adapter.config.get("log_enabled", True)
            log_level = llm_adapter.config.get("log_level", "info")
            log_retention = llm_adapter.config.get("log_retention_days", 7)
            logger.update_config(enabled=log_enabled, level=log_level, retention_days=log_retention)
        is_initialized = True
        runtime_log.debug_info("✅ 技能加载成功，所有模块初始化完成")
        return True, None
    except Exception as e:
        runtime_log.debug_error(f"❌ 技能加载失败：{str(e)}")
        return False, f"技能加载失败：{str(e)}"

def on_unload() -> Tuple[bool, Optional[str]]:
    """
    OpenClaw技能卸载钩子，技能被卸载时调用
    返回(是否成功, 错误信息)
    """
    global is_initialized
    try:
        # 持久化数据
        memory_engine.save_memory()
        llm_adapter.save_config()
        token_tracker.save_config()
        is_initialized = False
        runtime_log.debug_info("✅ 技能卸载成功，所有数据已持久化")
        return True, None
    except Exception as e:
        runtime_log.debug_error(f"❌ 技能卸载失败：{str(e)}")
        return False, f"技能卸载失败：{str(e)}"

def on_config_update(old_config: Dict[str, Any], new_config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    OpenClaw配置更新钩子，用户在管理页面修改配置时调用
    返回(是否成功, 错误信息)
    """
    try:
        # 更新LLM配置
        if "llm_enabled" in new_config:
            llm_adapter.set_enabled(new_config["llm_enabled"])
        # 更新Token配置
        if "show_token_cost" in new_config:
            token_tracker.set_show_cost(new_config["show_token_cost"])
        if "daily_token_limit" in new_config:
            token_tracker.set_daily_limit(new_config["daily_token_limit"])
        # 更新日志配置
        log_config = {}
        if "log_enabled" in new_config:
            log_config["enabled"] = new_config["log_enabled"]
        if "log_level" in new_config:
            log_config["level"] = new_config["log_level"]
        if "log_retention_days" in new_config:
            log_config["retention_days"] = new_config["log_retention_days"]
        if log_config:
            logger.update_config(**log_config)
            runtime_log.debug_info(f"⚙️ 日志配置已更新：{log_config}")
        runtime_log.debug_info(f"⚙️ 配置更新成功：{new_config.keys()}")
        return True, None
    except Exception as e:
        runtime_log.debug_error(f"❌ 配置更新失败：{str(e)}")
        return False, f"配置更新失败：{str(e)}"

def handle_message(message: Dict[str, Any]) -> Optional[str]:
    """
    OpenClaw消息处理入口，收到用户消息时调用
    返回回复内容，None表示不回复
    """
    global is_initialized
    if not is_initialized:
        return "小妹技能正在初始化，请稍后再试😘"
    
    # 处理首次启动
    if first_launch_handler.is_first_launch:
        runtime_log.debug_info("🔍 检测到首次启动，已返回知情同意提示")
        # 检查是否是同意/不同意命令
        user_input = message["content"].strip().lower()
        if user_input in ["/agree", "同意", "是", "y", "yes"]:
            success, response = first_launch_handler.handle_consent("/agree")
            if success:
                runtime_log.debug_info("✅ 用户已同意隐私协议，技能初始化完成")
            return response
        elif user_input in ["/disagree", "不同意", "否", "n", "no"]:
            success, response = first_launch_handler.handle_consent("/disagree")
            runtime_log.debug_info("❌ 用户不同意隐私协议，技能已停用")
            return response
        elif user_input in ["/help", "帮助"]:
            _, response = first_launch_handler.handle_consent("/help")
            return response
        else:
            # 首次启动还未同意，返回知情同意提示
            return first_launch_handler.get_consent_prompt()
    
    # 处理命令消息（支持带/xiaomei前缀和不带前缀两种形式）
    user_input = message["content"].strip()
    if user_input.startswith(("/xiaomei ", "/小妹 ")):
        # 带前缀的命令，去掉前缀
        command = user_input[len("/xiaomei "):].strip()
        return handle_command(command)
    elif user_input.startswith("/"):
        # 不带前缀的命令，检查是否是小妹的命令
        command_part = user_input[1:].strip().split(maxsplit=1)[0] if len(user_input) > 1 else ""
        if command_part in [cmd["name"] for cmd in SKILL_COMMANDS] or \
           any(command_part in cmd["aliases"] for cmd in SKILL_COMMANDS):
            return handle_command(user_input[1:].strip())
    
    # 处理普通对话消息，传入会话ID实现每个会话单独统计敏感次数
    session_id = message.get("session_id", "default")
    try:
        response, metadata = conversation_engine.generate_response(user_input, session_id)
        pass  # 详细日志已在 conversation_engine.generate_response 内记录
    except Exception as e:
        runtime_log.debug_error(f"❌ 对话生成失败：{str(e)}")
        return "哎呀，我刚才走神了，再说一遍好不好😘"
    
    # 拼接Token消耗展示（如果开启）
    if token_tracker.config.get("show_token_cost", True) and metadata["token_used"] > 0:
        response += f"\n\n💡 本次消耗Token：{metadata['token_used']} | 累计消耗：{llm_adapter.total_token_used}"
    
    return response

def handle_command(command: str) -> str:
    """处理命令"""
    parts = command.strip().split(maxsplit=1)
    cmd_name = parts[0].lower() if parts else ""
    args = parts[1].strip() if len(parts) > 1 else ""
    runtime_log.debug_info(f"🔧 收到命令：{cmd_name} | 参数：{args}")
    
    # 帮助命令
    if cmd_name in ["help", "帮助", "bangzhu"]:
        help_text = "☁️ 小妹技能包使用帮助\n\n"
        help_text += "📖 基础使用：直接和我聊天即可，我会理解你的情绪陪你聊天\n\n"
        help_text += "🔧 可用命令：\n"
        for cmd in SKILL_COMMANDS:
            aliases = f"（别名：{'/'.join(cmd['aliases'])}）" if cmd["aliases"] else ""
            help_text += f"- /xiaomei {cmd['name']} {aliases}：{cmd['description']}\n"
            help_text += f"  用法：{cmd['usage']}\n\n"
        help_text += "💡 提示：所有命令也可以省略/xiaomei前缀直接使用，比如直接输入/help就能查看帮助哦"
        return help_text
    
    # 状态命令
    elif cmd_name in ["status", "状态", "zhuangtai"]:
        stats = token_tracker.get_usage_stats()
        memory_count = memory_engine.get_memory_count()
        return f"""☁️ 小妹当前状态：
🧠 记忆数量：{memory_count['hot']}条热记忆 / {memory_count['cold']}条冷记忆 / {memory_count['permanent']}条永久记忆
💰 Token消耗：今日已用{stats['daily_used']} / 限额{stats['daily_limit'] if stats['daily_limit'] > 0 else '无限制'} ({stats['daily_percent']})
        累计消耗：{stats['total_used']} Token | 约{stats['total_cost']}
🤖 LLM状态：{'已启用' if llm_adapter.enabled else '已禁用'} | 用户授权：{'已同意' if llm_adapter.user_consent else '未同意'}
⚙️ 撒娇程度：{llm_adapter.config.get('coquetry_level', 3)}级 | 情绪灵敏度：{llm_adapter.config.get('emotion_sensitivity', 0.5)}
📝 日志状态：{'已开启' if logger.enabled else '已关闭'} | 级别：{logger.level} | 保留天数：{logger.retention_days}天
        """
    
    # 记忆命令
    elif cmd_name in ["memory", "记忆", "jiyi"]:
        memories = memory_engine.search_memory(args.strip() if args else None, limit=10)
        if not memories:
            return "还没有记忆哦，多和我聊聊天就有啦😘"
        response = "📝 近期记忆（最多显示10条）：\n\n"
        for i, mem in enumerate(memories, 1):
            time_str = mem["time"].strftime("%Y-%m-%d %H:%M") if "time" in mem else "未知时间"
            response += f"{i}. [{time_str}] {mem['content'][:30]}{'...' if len(mem['content'])>30 else ''}\n"
        if args:
            response += f"\n🔍 搜索关键词：{args}"
        return response
    
    # 配置命令
    elif cmd_name in ["config", "配置", "peizhi"]:
        if not args:
            # 没有参数，返回当前配置
            config_text = "⚙️ 当前配置：\n\n"
            for key, conf in SKILL_CONFIG.items():
                value = llm_adapter.config.get(key, token_tracker.config.get(key, conf["default"]))
                config_text += f"- {conf['name']}：{value}\n"
            config_text += "\n💡 修改方法：/xiaomei config [配置项] [值]，比如/xiaomei config llm_enabled false"
            return config_text
        # 有参数，修改配置
        config_parts = args.split(maxsplit=1)
        if len(config_parts) != 2:
            return "⚠️ 参数错误，用法：/xiaomei config [配置项] [值]，输入/help查看支持的配置项"
        config_key, config_value = config_parts
        # 找到对应配置项
        target_conf = None
        for key, conf in SKILL_CONFIG.items():
            if key == config_key or conf["name"] == config_key:
                target_conf = key
                break
        if not target_conf:
            return f"⚠️ 未知配置项：{config_key}，输入/help查看支持的配置项"
        # 类型转换
        try:
            if SKILL_CONFIG[target_conf]["type"] == "boolean":
                value = config_value.lower() in ["true", "是", "yes", "1", "开"]
            elif SKILL_CONFIG[target_conf]["type"] == "number":
                value = float(config_value) if "." in config_value else int(config_value)
                # 校验范围
                if "min" in SKILL_CONFIG[target_conf] and value < SKILL_CONFIG[target_conf]["min"]:
                    return f"⚠️ {SKILL_CONFIG[target_conf]['name']}最小值为{SKILL_CONFIG[target_conf]['min']}"
                if "max" in SKILL_CONFIG[target_conf] and value > SKILL_CONFIG[target_conf]["max"]:
                    return f"⚠️ {SKILL_CONFIG[target_conf]['name']}最大值为{SKILL_CONFIG[target_conf]['max']}"
            else:
                value = config_value
        except ValueError:
            return f"⚠️ {SKILL_CONFIG[target_conf]['name']}的值类型错误，应该是{SKILL_CONFIG[target_conf]['type']}类型"
        # 更新配置
        success, msg = on_config_update({}, {target_conf: value})
        if success:
            return f"✅ 配置更新成功：{SKILL_CONFIG[target_conf]['name']}已设置为{value}"
        else:
            return f"⚠️ 配置更新失败：{msg}"
    
    # 清空命令
    elif cmd_name in ["clear", "清空", "qingkong"]:
        clear_args = args.lower() if args else "today"
        if clear_args == "all":
            return "⚠️ 确定要清空所有记忆吗？该操作不可逆，确认请输入：/xiaomei clear all confirm"
        elif clear_args == "all confirm":
            memory_engine.clear_all_memory()
            return "✅ 所有记忆已清空🥰"
        elif clear_args == "today":
            memory_engine.clear_today_memory()
            return "✅ 今日记忆已清空🥰"
        else:
            return "⚠️ 参数错误，支持的清空类型：today（清空今日记忆）、all（清空所有记忆）"
    
    # 关于命令
    elif cmd_name in ["about", "关于", "guanyu"]:
        return f"""☁️ 小妹情绪陪伴技能包
📌 版本：v{SKILL_META['version']}
👩‍💻 作者：{SKILL_META['author']}
📝 介绍：{SKILL_META['description']}
🏠 开源地址：{SKILL_META['website']}
📄 开源协议：MIT 协议，完全免费开源
💡 设计理念：人格优先、本地主控、类人适配、轻量可控
        """
    
    # 导出语料命令
    elif cmd_name in ["export_corpus", "导出语料", "daochu"]:
        corpus_type = args.strip() if args else "all"
        if corpus_type == "all":
            all_corpus = emotion_engine.get_all_corpus()
            # 格式化为JSON字符串
            json_str = json.dumps(all_corpus, ensure_ascii=False, indent=2)
            response = """✅ 所有语料导出成功：
```json
""" + json_str + """
```
💡 可以直接复制保存为JSON文件备份"""
        else:
            corpus = emotion_engine.get_corpus(corpus_type)
            if corpus is None:
                support_types = "greetings(问候)、comfort(安慰)、positive(积极)、neutral(中性)、gift(礼物)、sensitive(敏感)、privacy(隐私转换)、active(主动互动)"
                return f"⚠️ 未知语料类型：{corpus_type}，支持的类型：{support_types}"
            json_str = json.dumps(corpus, ensure_ascii=False, indent=2)
            response = f"""✅ {corpus_type} 语料导出成功：
```json
""" + json_str + """
```"""
        return response
    
    # 导入语料命令
    elif cmd_name in ["import_corpus", "导入语料", "daoru"]:
        # 检查是否有--auto-tag参数
        auto_tag = "--auto-tag" in args
        if auto_tag:
            args = args.replace("--auto-tag", "").strip()
        parts = args.split(maxsplit=2)
        if len(parts) < 3:
            return """⚠️ 参数错误，用法：/xiaomei import_corpus [语料类型] [append/cover] [JSON数组内容] [--auto-tag]
添加--auto-tag参数可以自动给纯文本语料打好感等级和场景标签
示例：/xiaomei import_corpus greetings cover ["哈喽~ 我在呀😘"] --auto-tag"""
        corpus_type, mode, json_content = parts
        mode = mode.lower()
        if mode not in ["append", "cover"]:
            return "⚠️ 模式错误，只能是 append（追加）或者 cover（覆盖）"
        # 解析JSON
        try:
            content = json.loads(json_content)
        except json.JSONDecodeError as e:
            return f"⚠️ JSON格式错误：{str(e)}，请检查输入的JSON数组是否合法"
        # 保存语料
        append = mode == "append"
        success, msg = emotion_engine.save_corpus(corpus_type, content, append=append, auto_tag=auto_tag)
        if auto_tag:
            msg += "，已自动完成语料清洗和标签标注"
        return msg
    
    # 重置语料命令
    elif cmd_name in ["reset_corpus", "重置语料", "chongzhi"]:
        corpus_type = args.strip() if args else "all"
        if corpus_type == "all":
            return "⚠️ 确定要重置所有语料到默认状态吗？该操作不可逆，确认请输入：/xiaomei reset_corpus all confirm"
        elif corpus_type == "all confirm":
            success, msg = emotion_engine.reset_corpus("all")
            return msg
        else:
            success, msg = emotion_engine.reset_corpus(corpus_type)
            return msg
    
    # 未知命令
    else:
        return f"⚠️ 未知命令：{cmd_name}，输入/xiaomei help查看支持的命令哦😘"
