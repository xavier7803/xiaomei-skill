#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场景ID生成器
遵循官方12位6维度编码标准，纯本地规则实现，零外部依赖
编码结构：[时间段(2)][日期属性(2)][用户场景(2)][用户情绪(2)][对话主题(2)][特殊标识(2)]
"""
import datetime
from typing import Tuple, Dict, List
class SceneGenerator:
    def __init__(self):
        # 对话主题关键词匹配规则，顺序越靠前优先级越高
        self.topic_keywords = {
            "01": ["你好", "哈喽", "嗨", "在吗", "喂", "早上好", "晚上好", "中午好"],  # 问候（优先级最高）
            "03": ["难过", "伤心", "委屈", "烦", "郁闷", "难受", "痛苦", "心情不好", "崩溃"],  # 情感倾诉
            "06": ["吐槽", "服了", "醉了", "气死", "傻逼", "坑", "垃圾", "无语", "过分"],  # 吐槽抱怨
            "07": ["问一下", "问个事", "怎么弄", "怎么办", "如何", "请教", "帮帮我", "求助"],  # 求助咨询
            "05": ["工作", "上班", "学习", "考试", "作业", "项目", "加班", "开会", "领导", "同事", "客户"],  # 工作学习
            "04": ["看剧", "电影", "综艺", "明星", "游戏", "玩什么", "好看的", "好听的", "视频", "抖音", "b站"],  # 娱乐讨论
            "02": ["今天", "昨天", "前天", "天气", "吃了吗", "干嘛呢", "在干嘛", "聊会", "聊天", "唠嗑"],  # 日常闲聊（优先级最低）
        }
        # 时间推断关键词
        self.time_infer_keywords = {
            "01": ["凌晨", "半夜", "深夜", "晚安", "还没睡", "睡不着"],  # 凌晨0-6点
            "02": ["早上", "早晨", "早上好", "早啊", "起床了", "吃早餐", "早饭"],  # 早上6-12点
            "03": ["中午", "午安", "吃午饭", "午休", "中饭"],  # 中午12-14点
            "04": ["下午", "午安", "下午茶", "上班中", "上课中"],  # 下午14-18点
            "05": ["傍晚", "黄昏", "下班了", "放学了", "吃晚饭"],  # 傍晚18-20点
            "06": ["晚上", "晚安", "吃夜宵", "看剧", "睡觉了"],  # 晚上20-24点
        }
        # 日期属性推断关键词
        self.date_infer_keywords = {
            "01": ["周一", "周二", "周三", "周四", "周五", "工作日", "上班", "上课"],  # 工作日
            "02": ["周六", "周日", "周末", "放假", "休息"],  # 周末
        }
        # 情绪编码映射，和emotion_engine的情绪类型对应
        self.emotion_code_map = {
            "sensitive": "00",
            "greeting": "00",
            "neutral": "06",
            "happy": "01",
            "sad": "02",
            "angry": "03",
            "anxious": "04",
            "tired": "05"
        }
    
    def _get_time_period_code(self, now: datetime.datetime) -> str:
        """获取时间段编码（2位）
        00=未知 01=凌晨(0-6点) 02=早上(6-12点) 03=中午(12-14点) 04=下午(14-18点) 05=傍晚(18-20点) 06=晚上(20-24点)
        """
        hour = now.hour
        if 0 <= hour < 6:
            return "01"
        elif 6 <= hour < 12:
            return "02"
        elif 12 <= hour < 14:
            return "03"
        elif 14 <= hour < 18:
            return "04"
        elif 18 <= hour < 20:
            return "05"
        elif 20 <= hour < 24:
            return "06"
        return "00"
    
    def _get_date_type_code(self, now: datetime.datetime) -> str:
        """获取日期属性编码（2位）
        00=未知 01=工作日 02=周末 03=法定节假日（MVP版本暂未实现，默认01/02）
        """
        weekday = now.weekday()  # 0=周一，4=周五，5=周六，6=周日
        if weekday < 5:
            return "01"
        else:
            return "02"
    
    def _get_user_scene_code(self, content: str, now: datetime.datetime) -> str:
        """获取用户场景编码（2位），MVP版本默认00，后续扩展
        00=未知 01=居家 02=工作/学习 03=通勤 04=聚会 05=户外
        """
        # MVP版本暂时默认返回00，后续根据时间、关键词等推断
        return "00"
    
    def _get_emotion_code(self, emotion_type: str) -> str:
        """获取用户情绪编码（2位），复用情绪识别结果"""
        return self.emotion_code_map.get(emotion_type, "00")
    
    def _get_topic_code(self, content: str) -> str:
        """获取对话主题编码（2位），关键词匹配"""
        content_lower = content.lower()
        # 优先级高的先匹配
        for topic_code, keywords in self.topic_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    return topic_code
        # 未匹配到默认是日常闲聊
        return "02"
    
    def _infer_time_from_content(self, content: str) -> str:
        """从用户输入内容上下文推断时间段，获取不到系统时间时兜底使用"""
        content_lower = content.lower()
        for time_code, keywords in self.time_infer_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    return time_code
        return "00"  # 推断失败返回未知

    def _infer_date_type_from_content(self, content: str) -> str:
        """从用户输入内容上下文推断日期属性，获取不到系统时间时兜底使用"""
        content_lower = content.lower()
        for date_code, keywords in self.date_infer_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    return date_code
        return "00"  # 推断失败返回未知

    def _get_special_flag_code(self, content: str, now: datetime.datetime = None) -> str:
        """获取特殊标识编码（2位），MVP版本默认00
        00=无 01=节日限定 02=首次对话 03=回归对话
        """
        return "00"
    
    def generate(self, user_content: str, emotion_type: str, now: datetime.datetime = None) -> Tuple[str, Dict[str, str]]:
        """
        生成12位场景ID
        优先级：传入now > 系统时间 > 上下文推断 > 未知00
        :param user_content: 用户输入消息
        :param emotion_type: 情绪识别结果（来自emotion_engine）
        :param now: 当前时间，不传则取系统当前时间
        :return: (12位场景ID字符串，各维度解析详情字典)
        """
        system_time_available = True
        if now is None:
            try:
                now = datetime.datetime.now()
            except Exception:
                    # 获取系统时间失败，降级使用上下文推断
                    system_time_available = False
        
        # 生成各维度编码
        if system_time_available:
            time_period = self._get_time_period_code(now)
            date_type = self._get_date_type_code(now)
        else:
            # 获取系统时间失败，从用户内容推断，推断失败返回00
            time_period = self._infer_time_from_content(user_content)
            date_type = self._infer_date_type_from_content(user_content)
        user_scene = self._get_user_scene_code(user_content, now)
        emotion = self._get_emotion_code(emotion_type)
        topic = self._get_topic_code(user_content)
        special_flag = self._get_special_flag_code(user_content, now)
        
        # 拼接成12位场景ID
        scene_id = f"{time_period}{date_type}{user_scene}{emotion}{topic}{special_flag}"
        
        # 返回详情字典，方便调试和展示
        detail = {
            "时间段": time_period,
            "日期属性": date_type,
            "用户场景": user_scene,
            "用户情绪": emotion,
            "对话主题": topic,
            "特殊标识": special_flag
        }
        
        return scene_id, detail

# 单例实例
scene_generator = SceneGenerator()
