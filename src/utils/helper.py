#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用工具函数
"""

def replace_user_placeholder(text: str, address_user: str) -> str:
    """
    智能替换【用户】占位符，自动处理后缀带哥/哥哥的情况，避免重复称谓
    :param text: 原始文本
    :param address_user: 用户设置的称谓
    :return: 替换后的文本
    """
    # 优先处理带后缀的情况
    if "【用户】哥哥" in text:
        # 判断用户称谓是否已经以哥哥结尾，避免重复
        if address_user.endswith("哥哥"):
            return text.replace("【用户】哥哥", address_user)
        else:
            # 其他情况都拼接哥哥，如凌哥 + 哥哥 = 凌哥哥，凌啡大人 + 哥哥 = 凌啡大人哥哥
            return text.replace("【用户】哥哥", address_user + "哥哥")
    elif "【用户】哥" in text:
        # 如果已经带哥或哥哥，直接用，避免重复
        if address_user.endswith("哥") or address_user.endswith("哥哥"):
            return text.replace("【用户】哥", address_user)
        else:
            return text.replace("【用户】哥", address_user + "哥")
    # 普通无后缀情况
    return text.replace("【用户】", address_user)
