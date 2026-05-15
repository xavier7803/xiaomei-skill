#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场景匹配核心工具类
严格遵循12位场景ID编码标准与双名单通配符匹配规则
"""
from typing import List
def match_single_scene(current_scene: str, rule_scene: str) -> bool:
    """
    匹配单个场景规则，支持X通配符（大小写不敏感）
    :param current_scene: 当前对话的12位纯数字场景ID，无通配符
    :param rule_scene: 规则场景ID，可包含X通配符
    :return: 是否匹配
    """
    # 长度校验，必须都是12位
    if len(current_scene) != 12 or len(rule_scene) != 12:
        return False
    # 逐位匹配
    for i in range(12):
        rule_char = rule_scene[i].upper()
        # 通配符直接跳过
        if rule_char == 'X':
            continue
        # 非通配符必须完全匹配
        if rule_char != current_scene[i]:
            return False
    return True
def match_whitelist(current_scene: str, whitelist: List[str]) -> bool:
    """
    白名单匹配：任意一个规则匹配即通过
    :param current_scene: 当前场景ID
    :param whitelist: 白名单规则列表
    :return: 是否匹配白名单
    """
    # 空白名单默认全匹配
    if not whitelist:
        return True
    for rule in whitelist:
        if match_single_scene(current_scene, rule.strip()):
            return True
    return False
def match_blacklist(current_scene: str, blacklist: List[str]) -> bool:
    """
    黑名单匹配：任意一个规则匹配即命中
    :param current_scene: 当前场景ID
    :param blacklist: 黑名单规则列表
    :return: 是否命中黑名单
    """
    # 空黑名单默认无命中
    if not blacklist:
        return False
    for rule in blacklist:
        if match_single_scene(current_scene, rule.strip()):
            return True
    return False
def match_scene_rules(current_scene: str, whitelist: List[str], blacklist: List[str]) -> bool:
    """
    整体场景匹配流程：先匹配白名单，再排除黑名单
    :param current_scene: 当前场景ID
    :param whitelist: 白名单规则列表
    :param blacklist: 黑名单规则列表
    :return: 是否允许使用该语料
    """
    # 白名单不匹配直接拒绝
    if not match_whitelist(current_scene, whitelist):
        return False
    # 命中黑名单直接拒绝
    if match_blacklist(current_scene, blacklist):
        return False
    # 全部通过
    return True
