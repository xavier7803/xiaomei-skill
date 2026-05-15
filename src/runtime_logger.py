#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一运行时日志模块 — 小妹技能包 v0.8.0

整合了旧版 debug_utils + logger 的两个割裂体系。
开关：环境变量 XIAOMEI_DEVELOP_MODE=true/false（关闭时不记录任何日志）。
输出：config/logs/xiaomei_runtime_YYYY-MM-DD.log（按天滚动，保留 7 天）。
覆盖：对话生成 / 好感度变更 / 记忆写入与升级 / LLM三轮调用 / 拦截决策 / 异常。

职责边界：
- 开发模式=开 → 持久化文件日志 + OpenClaw调试面板（可选）
- 开发模式=关 → 完全不执行日志操作
- 隐私保障：不记录用户完整对话内容，仅记录摘要/状态/数值
"""
import os
import json
import time
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
import logging
from typing import Optional, Any, Dict, List


# ═══════════════ 开关 ═══════════════
DEVELOP_MODE = os.environ.get("XIAOMEI_DEVELOP_MODE", "true").lower() == "true"

# ═══════════════ 路径 ═══════════════
# CONFIG_DIR 默认指向 src/config（runtime_logger.py 在 src/ 下）
CONFIG_DIR = os.environ.get(
    "XIAOMEI_CONFIG_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "config"),
)
LOG_DIR = os.path.join(CONFIG_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# ═══════════════ OpenClaw 调试面板（可选） ═══════════════
try:
    from openclaw import debug
    HAS_OPENCLAW_DEBUG = True
except ImportError:
    HAS_OPENCLAW_DEBUG = False


class RuntimeLogger:
    """统一运行时日志器：文件 + 可选调试面板"""
    _instance: Optional["RuntimeLogger"] = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if RuntimeLogger._initialized:
            return
        RuntimeLogger._initialized = True
        self._file_logger = None
        self._setup_file_logger()

    def _setup_file_logger(self):
        if not DEVELOP_MODE:
            self._file_logger = None
            return
        try:
            log_name = "xiaomei_runtime"
            self._file_logger = logging.getLogger(log_name)
            self._file_logger.setLevel(logging.DEBUG)
            self._file_logger.propagate = False
            if self._file_logger.handlers:
                return
            log_file = os.path.join(LOG_DIR, f"{log_name}.log")
            handler = TimedRotatingFileHandler(
                log_file, when="D", interval=1, backupCount=7, encoding="utf-8", delay=False,
            )
            handler.suffix = "%Y-%m-%d"
            handler.setFormatter(logging.Formatter(
                "%(asctime)s | %(levelname)-5s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            ))
            self._file_logger.addHandler(handler)
        except Exception:
            self._file_logger = None

    @property
    def is_dev(self) -> bool:
        return DEVELOP_MODE

    # ── 内部写入 ──

    def _write(self, level: str, message: str):
        if not self._file_logger:
            return
        method = getattr(self._file_logger, level, self._file_logger.info)
        method(message)

    def _panel(self, panel_level: str, content: str, **kwargs):
        """写入 OpenClaw 调试面板（非阻塞）"""
        if not DEVELOP_MODE or not HAS_OPENCLAW_DEBUG:
            return
        try:
            fn = getattr(debug, panel_level, debug.info)
            fn(content, **kwargs)
        except Exception:
            pass

    # ═══════════════ 公开 API ═══════════════

    # ── 对话生成 ──

    def conversation_start(self, session_id: str, input_preview: str):
        """对话开始"""
        msg = f"[会话] {session_id} | 用户输入(首30字): {input_preview[:30]}"
        self._write("info", msg)
        self._panel("info", msg, session_id=session_id)

    def llm_connectivity(self, available: bool):
        """LLM连通性检测结果"""
        tag = "✅" if available else "❌"
        msg = f"[连通性] LLM={tag}"
        self._write("info" if available else "warn", msg)

    def hard_sensitive_tags(self, tags: List[str]):
        """硬敏感词风险标注"""
        if tags:
            msg = f"[敏感标注] 硬敏感词命中: {tags}"
            self._write("warn", msg)
            self._panel("warn", msg)

    def first_round_result(self, result: Dict):
        """第一轮总指挥官结果摘要（不记录用户原文）"""
        msg = (
            f"[R1-总指挥] scene={result.get('scene_id','?')} "
            f"purpose={result.get('core_purpose','?')} "
            f"emotion={result.get('user_emotion','?')} "
            f"sensitive={result.get('is_sensitive')} "
            f"rude={result.get('is_rude')} "
            f"favor={result.get('favor_level')} "
            f"gift={result.get('is_gift')} "
            f"privacy={result.get('privacy_level')} "
            f"pBlock={result.get('privacy_block')}"
        )
        self._write("info", msg)
        self._panel("info", msg)

    def intercept_decision(self, should_intercept: bool, reason: str):
        """拦截判断结果"""
        if should_intercept:
            msg = f"[拦截] 触发 — 原因: {reason} — 跳过第二轮"
            self._write("warn", msg)
            self._panel("warn", msg)
        else:
            self._write("info", "[拦截] 未触发 — 正常流程继续")

    def second_round_result(self, memory_count: int, skipped: bool = False):
        """第二轮记忆筛选结果"""
        if skipped:
            self._write("info", "[R2-记忆] 已跳过（拦截模式）")
        else:
            msg = f"[R2-记忆] 高置信记忆数: {memory_count}"
            self._write("info", msg)

    def third_round_result(self, response_preview: str, topic_end: float, reply_emotion: str):
        """第三轮话术生成结果摘要"""
        msg = (
            f"[R3-话术] 回复(首40字): {response_preview[:40]} "
            f"| 结束概率={topic_end} | 情绪={reply_emotion}"
        )
        self._write("info", msg)
        self._panel("info", msg)

    def conversation_done(self, session_id: str, meta: Dict):
        """对话完成"""
        msg = (
            f"[会话完成] {session_id} | "
            f"scene={meta.get('scene_id','?')} "
            f"intercepted={meta.get('was_intercepted')} "
            f"llm={'✅' if meta.get('used_llm') else '❌'} "
            f"reply_preview={str(meta.get('reply','?'))[:30]}"
        )
        self._write("info", msg)

    def conversation_error(self, error_msg: str):
        """对话异常"""
        msg = f"[异常] 对话生成失败: {error_msg}"
        self._write("error", msg)
        self._panel("error", msg)

    # ── 好感度变更 ──

    def favor_change(
        self, action: str, delta: int,
        new_value: int, new_level: int, reason: str = ""
    ):
        """好感度变更记录"""
        sign = "+" if delta >= 0 else ""
        msg = (
            f"[好感度] {action} {sign}{delta} → "
            f"当前={new_value} 等级=Lv.{new_level}"
            + (f" ({reason})" if reason else "")
        )
        level = "info" if delta >= 0 else "warn"
        self._write(level, msg)

    def favor_level_up(self, old_level: int, new_level: int, favor_value: int):
        """好感度升级事件"""
        msg = f"[好感度] ⬆️ 升级 Lv.{old_level} → Lv.{new_level} (好感度={favor_value})"
        self._write("info", msg)
        self._panel("info", msg)

    # ── 记忆写入与升级 ──

    def memory_add(self, memory_id: str, role: str, content_preview: str):
        """记忆写入"""
        msg = f"[记忆] 写入 {memory_id[:8]} | role={role} | 内容(首30字): {content_preview[:30]}"
        self._write("info", msg)

    def memory_strength_up(self, memory_id: str, new_strength: int, new_level: str):
        """记忆强度提升/等级变化"""
        msg = f"[记忆] ⬆️ {memory_id[:8]} 强度→{new_strength} 等级→{new_level}"
        self._write("info", msg)

    def memory_aging(self, hot: int, cold: int, permanent: int, total: int):
        """记忆老化执行"""
        msg = f"[记忆] 老化执行 | 热={hot} 冷={cold} 永久={permanent} 总计={total}"
        self._write("info", msg)

    # ── LLM 轮次耗时 ──

    def llm_round_timing(self, round_name: str, elapsed_ms: float, success: bool):
        """LLM调用耗时"""
        tag = "✅" if success else "❌"
        msg = f"[计时] {round_name} | {tag} | {elapsed_ms:.0f}ms"
        self._write("debug", msg)

    # ── LLM 输入输出完整记录 ──

    def llm_round_io(self, round_name: str, prompt: str, result: str, elapsed_ms: float = 0):
        """
        记录LLM每轮的完整输入(Prompt)和输出(Result)。
        隐私：Prompt中用户输入部分已由调用方截断至50字。
        """
        if not self._file_logger:
            return
        sep = "─" * 60
        # 输入（截断防止日志过大）
        prompt_truncated = prompt[:3000]
        result_truncated = result[:2000]
        msg = (
            f"[LLM-IO] {round_name} | {elapsed_ms:.0f}ms\n"
            f"{sep}\n"
            f"── PROMPT ──\n{prompt_truncated}\n"
            f"── RESULT ──\n{result_truncated}\n"
            f"{sep}"
        )
        self._write("debug", msg)
        self._panel("debug", f"{round_name}: {elapsed_ms:.0f}ms ✓" if result else f"{round_name}: ❌")

    # ── 兼容旧 debug_utils API ──

    def debug_info(self, content: Any, **kwargs):
        """兼容旧 debug_info：写入 info 级别 + 调试面板"""
        if not DEVELOP_MODE:
            return
        msg = str(content)
        self._write("info", f"[DEBUG] {msg}")
        self._panel("info", msg, **kwargs)

    def debug_error(self, content: Any, **kwargs):
        """兼容旧 debug_error：写入 error 级别 + 调试面板"""
        if not DEVELOP_MODE:
            return
        msg = str(content)
        self._write("error", f"[DEBUG_ERR] {msg}")
        self._panel("error", msg, **kwargs)

    def debug_warn(self, content: Any, **kwargs):
        if not DEVELOP_MODE:
            return
        msg = str(content)
        self._write("warn", f"[DEBUG_WARN] {msg}")
        self._panel("warn", msg, **kwargs)

    def debug_debug(self, content: Any, **kwargs):
        if not DEVELOP_MODE:
            return
        msg = str(content)
        self._write("debug", f"[DEBUG_DETAIL] {msg}")
        self._panel("debug", msg, **kwargs)


# 全局单例
runtime_log = RuntimeLogger()
