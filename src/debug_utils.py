#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试工具模块 - 对接OpenClaw内置调试面板
开关控制：通过环境变量XIAOMEI_DEVELOP_MODE控制，true开启，false关闭
当前MVP测试阶段默认开启，正式上线可调整为默认关闭
作者：小云 ☁️
"""
import os
# 开发模式开关，默认开启（MVP测试阶段）
DEVELOP_MODE = os.environ.get("XIAOMEI_DEVELOP_MODE", "true").lower() == "true"

# 尝试导入OpenClaw调试接口
try:
    from openclaw import debug
    HAS_OPENCLAW_DEBUG = True
except ImportError:
    HAS_OPENCLAW_DEBUG = False

def debug_log(log_type: str, content: any, **kwargs):
    """
    输出调试信息到OpenClaw调试面板，开发模式关闭时不执行任何操作
    log_type: 日志类型 info/error/warn/debug
    content: 日志内容
    kwargs: 额外参数，会一起输出到面板
    """
    if not DEVELOP_MODE or not HAS_OPENCLAW_DEBUG:
        return
    
    try:
        log_method = getattr(debug, log_type, debug.info)
        log_method(content, **kwargs)
    except:
        # 调试接口调用失败不影响主流程
        pass

# 快捷方法
def debug_info(content: any, **kwargs):
    debug_log("info", content, **kwargs)

def debug_error(content: any, **kwargs):
    debug_log("error", content, **kwargs)

def debug_warn(content: any, **kwargs):
    debug_log("warn", content, **kwargs)

def debug_debug(content: any, **kwargs):
    debug_log("debug", content, **kwargs)
