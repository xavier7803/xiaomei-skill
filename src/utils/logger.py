#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行日志工具类 - 小妹技能包
功能：按天滚动记录日志，自动清理旧日志，支持开关和级别调整
隐私保障：不记录任何用户对话内容，仅记录运行状态和事件
版本：v1.0
"""
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from typing import Optional

# 配置路径，支持环境变量覆盖
CONFIG_DIR = os.environ.get("XIAOMEI_CONFIG_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config"))
LOG_DIR = os.path.join(CONFIG_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

class Logger:
    _instance: Optional["Logger"] = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, enabled: bool = True, level: str = "info", retention_days: int = 7):
        if Logger._initialized:
            return
        Logger._initialized = True
        self.enabled = enabled
        self.level = level.lower()
        self.retention_days = retention_days
        self.logger = None
        self._setup_logger()

    def _setup_logger(self):
        """初始化日志器"""
        if not self.enabled:
            # 关闭日志，创建空日志器
            self.logger = logging.getLogger("xiaomei")
            self.logger.addHandler(logging.NullHandler())
            return
        
        # 日志级别映射
        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warn": logging.WARNING,
            "error": logging.ERROR
        }
        log_level = level_map.get(self.level, logging.INFO)

        # 创建日志器
        self.logger = logging.getLogger("xiaomei")
        self.logger.setLevel(log_level)
        self.logger.propagate = False

        # 避免重复添加handler
        if self.logger.handlers:
            return

        # 创建按天滚动的文件handler，最多保留retention_days天日志
        log_file = os.path.join(LOG_DIR, "xiaomei.log")
        file_handler = TimedRotatingFileHandler(
            log_file,
            when="D",
            interval=1,
            backupCount=self.retention_days,
            encoding="utf-8",
            delay=True
        )
        file_handler.suffix = "%Y-%m-%d"
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def update_config(self, enabled: Optional[bool] = None, level: Optional[str] = None, retention_days: Optional[int] = None):
        """更新日志配置"""
        if enabled is not None:
            self.enabled = enabled
        if level is not None:
            self.level = level.lower()
        if retention_days is not None:
            self.retention_days = retention_days
        # 重新初始化日志器
        Logger._initialized = False
        self._setup_logger()

    def debug(self, message: str):
        """记录debug日志"""
        if self.enabled and self.level == "debug":
            self.logger.debug(message)

    def info(self, message: str):
        """记录info日志"""
        if self.enabled and self.level in ["debug", "info"]:
            self.logger.info(message)

    def warn(self, message: str):
        """记录warn日志"""
        if self.enabled and self.level in ["debug", "info", "warn"]:
            self.logger.warning(message)

    def error(self, message: str, exc_info: Optional[Exception] = None):
        """记录error日志，可传入异常对象记录堆栈"""
        if self.enabled:
            if exc_info:
                self.logger.error(message, exc_info=exc_info)
            else:
                self.logger.error(message)

# 全局单例实例
logger = Logger()
