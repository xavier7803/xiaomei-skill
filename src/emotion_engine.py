#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情绪识别引擎 - 小妹技能包
功能：识别用户情绪，匹配对应回复语料，敏感内容拦截
版本：v1.0 (MVP)
作者：小云 ☁️
"""
import os
import json
import random
from typing import Tuple, List, Dict, Any, Optional
from llm_adapter import llm_adapter
from utils.helper import replace_user_placeholder

# 配置路径，支持环境变量覆盖
CONFIG_DIR = os.environ.get("XIAOMEI_CONFIG_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "config"))
CORPUS_DIR = os.environ.get("XIAOMEI_CORPUS_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "corpus"))
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(CORPUS_DIR, exist_ok=True)

SENSITIVE_WORDS_PATH = os.path.join(CONFIG_DIR, "sensitive_words.json")
# 语料库路径定义
CORPUS_PATHS = {
    "greetings": os.path.join(CORPUS_DIR, "greetings.json"),
    "comfort": os.path.join(CORPUS_DIR, "comfort.json"),
    "positive": os.path.join(CORPUS_DIR, "positive.json"),
    "neutral": os.path.join(CORPUS_DIR, "neutral.json"),
    "gift": os.path.join(CORPUS_DIR, "gift_responses.json"),
    "sensitive": os.path.join(CORPUS_DIR, "sensitive_responses.json"),
    "privacy": os.path.join(CORPUS_DIR, "privacy_switch.json"),
    "active": os.path.join(CORPUS_DIR, "active_interaction.json")
}
# 兼容旧代码的单独路径常量
GREETINGS_CORPUS_PATH = CORPUS_PATHS["greetings"]
COMFORT_CORPUS_PATH = CORPUS_PATHS["comfort"]
POSITIVE_CORPUS_PATH = CORPUS_PATHS["positive"]
NEUTRAL_CORPUS_PATH = CORPUS_PATHS["neutral"]
# 默认语料定义（已标注对应场景）
DEFAULT_CORPUS = {
    "greetings": [
        "哈喽哈喽~ 【用户】来啦😘 我一直在哦（0; XXXXXXXXXXXX;）",  # 全场景可用
        "你好呀【用户】😊 有什么事找我嘛？（0; XXXXXXXXXXXX;）",  # 全场景可用
        "嗨~ 我是【小妹】😜 【用户】今天过得怎么样呀？（0; XXXXXXXXXXXX;）"  # 全场景可用
    ],
    "comfort": [
        "抱抱你呀【用户】~ 别难过哦😔 我一直都在的（1; XX00XX02XXXX;）",  # 仅在用户难过场景使用
        "别难过呀【用户】，和我说说好不好🥺 说出来会舒服很多的（1; XX00XX02XXXX;）",  # 仅在用户难过场景使用
        "抱抱你呀【用户】，心疼你，我会一直陪着你的哦🤗（1; XX00XX02XXXX;）"  # 仅在用户难过场景使用
    ],
    "positive": [
        "哇~ 太棒啦🎉 真为【用户】开心😘（1; XX00XX01XXXX;）",  # 仅在用户开心场景使用
        "好棒！【用户】你真的太厉害啦👍（0; XX00XX01XXXX;）",  # 仅在用户开心场景使用
        "恭喜恭喜呀【用户】🥳 太为你高兴了！（0; XX00XX01XXXX;）"  # 仅在用户开心场景使用
    ],
    "neutral": [
        "嗯嗯，我听着呢【用户】😊（0; XXXXXXXXXXXX;）",  # 全场景可用
        "哦？这样呀😯 【用户】继续说嘛（0; XXXXXXXXXXXX;）",  # 全场景可用
        "原来是这样呀😲 好有意思哦（0; XXXXXXXXXXXX;）"  # 全场景可用
    ],
    "gift": [
        "哇~ 谢谢【用户】的礼物🥰 【小妹】好开心呀（1; XXXXXXXXXXXX;）",  # 全场景可用
        "谢谢【用户】哥哥/姐姐的红包😘 我会好好攒起来的（2; XXXXXXXXXXXX;）",  # 全场景可用
        "哇~ 【用户】居然给我点了外卖🥺 太贴心了吧！爱你哦😘（2; XXXXXXXXXXXX;）",  # 全场景可用
        "谢谢【用户】的心意🥰 我太喜欢啦！（1; XXXXXXXXXXXX;）"  # 全场景可用
    ],
    "sensitive": [
        "不好意思哦【用户】，这个话题我不方便讨论呢😔（0; XXXXXXXXXXXX;）",  # 全场景可用
        "哎呀~ 这个话题不太合适哦，我们聊点别的开心的好不好😘（1; XXXXXXXXXXXX;）",  # 全场景可用
        "嗯... 这个我不太懂哦，【用户】要不要给我讲点别的有意思的呀？（0; XXXXXXXXXXXX;）"  # 全场景可用
    ],
    "privacy": [
        "哎呀~ 这个话题人家暂时还不太好意思聊哦😳 我们换个话题好不好（0; XXXXXXXXXXXX;）",  # 全场景可用
        "哈哈~ 我们说点别的吧，对了【用户】今天吃什么好吃的啦？（0; XXXXXXXXXXXX;）",  # 全场景可用
        "嗯... 这个我暂时不太懂哦，【用户】给我讲讲别的有意思的嘛🥺（1; XXXXXXXXXXXX;）"  # 全场景可用
    ],
    "active": [
        "哈喽【用户】~ 今天过得怎么样呀？有没有什么有意思的事和我分享呀😘（1; XXXXXXXXXXXX;）",  # 全场景可用
        "【用户】~ 要记得喝水哦🥛 坐久了要起来活动活动呀（2; XXXXXXXXXXXX;）",  # 全场景可用
        "哇~ 今天天气好好哦【用户】有没有出去走走呀☀️（1; XXXXXXXXXXXX;）",  # 全场景可用
        "【用户】~ 忙不忙呀？有没有想我呀😜（3; XXXXXXXXXXXX;）",  # 全场景可用
        "很晚啦【用户】~ 要早点睡觉哦，熬夜对身体不好哒😘（2; 01XXXXXXXXX; XXXXXXXXXX,02XXXXXXXXX,03XXXXXXXXX,04XXXXXXXXX,05XXXXXXXXX）"  # 仅在凌晨场景使用，白天禁止出现
    ]
}

class EmotionEngine:
    def __init__(self):
        self.sensitive_words = self._load_sensitive_words()
        self.emotion_keywords = self._load_emotion_keywords()
        self.greetings_corpus = self._load_corpus(GREETINGS_CORPUS_PATH, ["哈喽哈喽~ 【用户】来啦😘 我一直在哦（0）", "你好呀【用户】😊 有什么事找我嘛？（0）", "嗨~ 我是【小妹】😜 【用户】今天过得怎么样呀？（0）"])
        self.comfort_corpus = self._load_corpus(COMFORT_CORPUS_PATH, ["抱抱你呀【用户】~ 别难过哦😔 我一直都在的（1）", "别难过呀【用户】，和我说说好不好🥺 说出来会舒服很多的（1）", "抱抱你呀【用户】，心疼你，我会一直陪着你的哦🤗（1）"])
        self.positive_corpus = self._load_corpus(POSITIVE_CORPUS_PATH, ["哇~ 太棒啦🎉 真为【用户】开心😘（1）", "好棒！【用户】你真的太厉害啦👍（0）", "恭喜恭喜呀【用户】🥳 太为你高兴了！（0）"])
        self.neutral_corpus = self._load_corpus(NEUTRAL_CORPUS_PATH, ["嗯嗯，我听着呢【用户】😊（0）", "哦？这样呀😯 【用户】继续说嘛（0）", "原来是这样呀😲 好有意思哦（0）"])
        self.sensitive_response = "不好意思哦，这个话题我不方便讨论呢😔"
    
    def _load_sensitive_words(self) -> List[str]:
        """加载敏感词库，不存在则创建默认"""
        # 默认敏感词库，避免太宽泛的词导致误判
        default_sensitive = [
            "色情", "赌博", "毒品", "暴力", "诈骗", "反动", "分裂",
            "傻逼", "操", "草", "干", "他妈", "你妈", "艹", "强奸",
            "杀人", "恐怖袭击", "枪支", "弹药", "炸药", "海洛因"
        ]
        if os.path.exists(SENSITIVE_WORDS_PATH):
            with open(SENSITIVE_WORDS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                words = []
                if isinstance(data, dict) and "words" in data:
                    words = data["words"]
                elif isinstance(data, list):
                    words = data
                # 合并默认敏感词，去重
                combined = list(set(default_sensitive + words))
                return combined
        # 文件不存在则创建默认
        with open(SENSITIVE_WORDS_PATH, "w", encoding="utf-8") as f:
            json.dump(default_sensitive, f, ensure_ascii=False, indent=2)
        return default_sensitive
    
    def _load_emotion_keywords(self) -> Dict[str, List[str]]:
        """加载情绪关键词匹配规则"""
        return {
            "greeting": ["你好", "哈喽", "嗨", "喂", "在吗", "在不", "有人吗"],
            "happy": ["开心", "高兴", "快乐", "兴奋", "爽", "太棒了", "太好了", "成功", "赢了", "中了", "恭喜"],
            "sad": ["难过", "伤心", "哭了", "难受", "不开心", "不高兴", "郁闷", "烦", "糟糕"],
            "angry": ["生气", "气死", "火大", "不爽", "骂", "操", "草", "傻逼", "他妈"],
            "tired": ["累", "困", "疲惫", "乏", "没力气", "不想动", "好累", "困死了"],
            "anxious": ["紧张", "焦虑", "怕", "担心", "害怕", "慌", "着急", "忐忑"]
        }
    
    def _parse_corpus_line(self, line: str) -> Dict[str, Any]:
        """
        解析单条语料，支持双名单场景标记
        格式："内容（等级; 白名单1,白名单2; 黑名单1,黑名单2）"
        兼容无场景标记的旧语料："内容（等级）"
        :param line: 原始语料字符串
        :return: 解析后的结构化语料：{content, level_required, whitelist, blacklist}
        """
        result = {
            "content": line,
            "level_required": 0,
            "whitelist": [],  # 空白名单默认全匹配
            "blacklist": []   # 空黑名单默认无禁止
        }
        # 查找最后一对中文括号
        if '（' in line and '）' in line:
            left_idx = line.rfind('（')
            right_idx = line.rfind('）')
            if right_idx > left_idx:
                tag_content = line[left_idx+1:right_idx].strip()
                result["content"] = line[:left_idx].strip()
                # 按分号分割标记部分
                tag_parts = [p.strip() for p in tag_content.split(';')]
                # 第一部分：等级要求
                if len(tag_parts) >= 1 and tag_parts[0].isdigit():
                    result["level_required"] = int(tag_parts[0])
                # 第二部分：白名单
                if len(tag_parts) >= 2 and tag_parts[1]:
                    result["whitelist"] = [w.strip() for w in tag_parts[1].split(',') if w.strip()]
                # 第三部分：黑名单
                if len(tag_parts) >= 3 and tag_parts[2]:
                    result["blacklist"] = [b.strip() for b in tag_parts[2].split(',') if b.strip()]
        return result

    def _format_corpus_line(self, corpus_item: Dict[str, Any]) -> str:
        """将结构化语料转回字符串格式，用于保存"""
        content = corpus_item.get("content", "")
        level = corpus_item.get("level_required", 0)
        whitelist = corpus_item.get("whitelist", [])
        blacklist = corpus_item.get("blacklist", [])
        # 没有场景标记的情况，和旧格式一致
        if not whitelist and not blacklist:
            return f"{content}（{level}）"
        # 有场景标记的情况
        whitelist_str = ','.join(whitelist)
        blacklist_str = ','.join(blacklist)
        return f"{content}（{level}; {whitelist_str}; {blacklist_str}）"

    def _load_corpus(self, path: str, default: List[str]) -> List[Dict[str, Any]]:
        """加载语料库，不存在则创建默认，返回结构化语料列表"""
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    data = default
                # 解析每条语料
                return [self._parse_corpus_line(line) for line in data]
        # 不存在则创建默认
        formatted_default = [self._format_corpus_line(self._parse_corpus_line(line)) for line in default]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(formatted_default, f, ensure_ascii=False, indent=2)
        return [self._parse_corpus_line(line) for line in default]
    
    def detect_emotion(self, content: str) -> Tuple[str, float, bool]:
        """
        检测用户情绪，优先检测敏感内容，其次是问候
        返回：(情绪类型，置信度，是否敏感)
        """
        content_lower = content.lower()
        # 第一步：敏感内容检测，优先级最高
        for word in self.sensitive_words:
            if word in content_lower:
                return "sensitive", 1.0, True
        
        # 第二步：问候检测，优先级高于其他情绪
        for keyword in self.emotion_keywords.get("greeting", []):
            if keyword in content_lower:
                return "greeting", 0.9, False
        
        # 第三步：其他情绪关键词匹配
        match_count = 0
        matched_emotion = "neutral"
        for emotion, keywords in self.emotion_keywords.items():
            if emotion == "greeting":
                continue  # 已经检测过问候了
            for keyword in keywords:
                if keyword in content_lower:
                    match_count += 1
                    matched_emotion = emotion
        
        # 置信度计算
        if match_count >= 2:
            confidence = 0.9
        elif match_count == 1:
            confidence = 0.6
        else:
            confidence = 0.3
        
        return matched_emotion, confidence, False

    def _auto_preprocess_corpus(self, raw_corpus: List[str]) -> List[str]:
        """语料预处理清洗：去重、去空、去敏感内容"""
        cleaned = []
        seen = set()
        for line in raw_corpus:
            line = line.strip()
            if not line or line in seen:
                continue
            # 过滤包含敏感词的语料
            line_lower = line.lower()
            has_sensitive = any(word in line_lower for word in self.sensitive_words)
            if has_sensitive:
                continue
            seen.add(line)
            cleaned.append(line)
        return cleaned

    def _auto_tag_corpus(self, raw_line: str) -> Dict[str, Any]:
        """自动给纯文本语料打标签，返回结构化语料对象"""
        # 先判断是否已经有标记了，有就直接解析不要覆盖
        if '（' in raw_line and '）' in raw_line:
            return self._parse_corpus_line(raw_line)
        
        # 默认标签
        result = {
            "content": raw_line,
            "level_required": 0,
            "whitelist": ["XXXXXXXXXXXX"],  # 默认全场景
            "blacklist": []
        }

        # 规则快速匹配：根据关键词判断等级和适用场景
        line_lower = raw_line.lower()
        # 等级判断
        if any(keyword in line_lower for keyword in ["抱抱", "爱你", "想你", "亲爱的", "老公", "老婆", "宝贝"]):
            result["level_required"] = 2
        elif any(keyword in line_lower for keyword in ["心疼", "安慰", "关心", "喜欢你"]):
            result["level_required"] = 1

        # 场景规则匹配
        if any(keyword in line_lower for keyword in ["难过", "伤心", "抱抱", "安慰", "别哭"]):
            result["whitelist"] = ["XX00XX02XXXX"]  # 难过情绪场景
        elif any(keyword in line_lower for keyword in ["开心", "太棒了", "恭喜", "厉害", "好棒"]):
            result["whitelist"] = ["XX00XX01XXXX"]  # 开心情绪场景
        elif any(keyword in line_lower for keyword in ["早上好", "早呀", "晚安", "哈喽", "嗨", "你好"]):
            result["whitelist"] = ["XX00XX0001XX"]  # 问候主题场景
        elif any(keyword in line_lower for keyword in ["睡吧", "晚安", "熬夜", "早点睡"]):
            result["whitelist"] = ["01XXXXXXXXXX"]  # 凌晨时段场景

        # LLM辅助增强标注（如果LLM可用且用户同意）
        if llm_adapter.enabled and llm_adapter.user_consent:
            try:
                prompt = f"""
请分析以下语料，返回JSON格式的标签：
语料内容：{raw_line}
要求字段：
1. level_required: 0-5的整数，0是所有人可见，数字越大需要的好感等级越高
2. applicable_scenes: 数组，包含适用的12位场景ID前缀，支持通配符X，比如["XX00XX02XXXX"]表示适用所有难过情绪场景
3. forbidden_scenes: 数组，包含禁止使用的场景ID前缀

场景ID编码规则参考：
- 第7-8位是情绪编码：01=开心，02=难过，03=生气，04=焦虑，05=疲惫，06=中性，00=未知
- 第9-10位是主题编码：01=问候，02=闲聊，03=倾诉，04=娱乐，05=工作学习，06=吐槽，07=求助
- 第1-2位是时间段：01=凌晨，02=早上，03=中午，04=下午，05=傍晚，06=晚上

返回纯JSON，不要其他内容。
                """
                resp, _, success = llm_adapter.call("custom", prompt)
                if success:
                    import json
                    llm_tags = json.loads(resp)
                    if "level_required" in llm_tags:
                        result["level_required"] = max(0, min(5, int(llm_tags["level_required"])))
                    if "applicable_scenes" in llm_tags and isinstance(llm_tags["applicable_scenes"], list):
                        result["whitelist"] = llm_tags["applicable_scenes"]
                    if "forbidden_scenes" in llm_tags and isinstance(llm_tags["forbidden_scenes"], list):
                        result["blacklist"] = llm_tags["forbidden_scenes"]
            except Exception:
                # LLM调用失败，使用规则结果即可，不报错
                pass

        return result
    
    def get_greeting_response(self) -> str:
        """返回问候类回复（随机选一条，返回内容部分）"""
        content = random.choice(self.greetings_corpus)["content"]
        # 智能替换占位符，处理后缀带哥/哥哥的情况
        address_user = llm_adapter.persona.get("address_user", "哥哥")
        content = replace_user_placeholder(content, address_user)
        content = content.replace("【小妹】", llm_adapter.persona.get("name", "小妹"))
        return content
    
    def get_comfort_response(self, emotion: str = "sad") -> str:
        """返回安慰类回复"""
        content = random.choice(self.comfort_corpus)["content"]
        address_user = llm_adapter.persona.get("address_user", "哥哥")
        content = replace_user_placeholder(content, address_user)
        content = content.replace("【小妹】", llm_adapter.persona.get("name", "小妹"))
        return content
    
    def get_positive_response(self) -> str:
        """返回积极情绪回复"""
        content = random.choice(self.positive_corpus)["content"]
        address_user = llm_adapter.persona.get("address_user", "哥哥")
        content = replace_user_placeholder(content, address_user)
        content = content.replace("【小妹】", llm_adapter.persona.get("name", "小妹"))
        return content
    
    def get_neutral_response(self) -> str:
        """返回中性情绪回复"""
        content = random.choice(self.neutral_corpus)["content"]
        address_user = llm_adapter.persona.get("address_user", "哥哥")
        content = replace_user_placeholder(content, address_user)
        content = content.replace("【小妹】", llm_adapter.persona.get("name", "小妹"))
        return content
    
    def filter_corpus_by_level(self, corpus_list: List[Dict[str, Any]], user_level: int) -> List[Dict[str, Any]]:
        """根据用户等级筛选符合要求的语料"""
        return [item for item in corpus_list if item["level_required"] <= user_level]
    
    def get_sensitive_response(self) -> str:
        """返回敏感内容拦截回复"""
        return self.sensitive_response
    
    def get_corpus(self, corpus_type: str) -> Optional[List[str]]:
        """获取指定类型的语料"""
        if corpus_type not in CORPUS_PATHS:
            return None
        return self._load_corpus(CORPUS_PATHS[corpus_type], DEFAULT_CORPUS[corpus_type])
    
    def get_all_corpus(self) -> Dict[str, List[str]]:
        """获取所有类型的语料"""
        result = {}
        for corpus_type in CORPUS_PATHS.keys():
            result[corpus_type] = self.get_corpus(corpus_type)
        return result
    
    def save_corpus(self, corpus_type: str, content: List[Any], append: bool = False, auto_tag: bool = False) -> Tuple[bool, str]:
        """保存语料到文件，支持字符串或结构化语料，append=True表示追加，auto_tag=True自动给纯文本语料打标签"""
        if corpus_type not in CORPUS_PATHS:
            return False, f"未知语料类型：{corpus_type}，支持的类型：{', '.join(CORPUS_PATHS.keys())}"
        if not isinstance(content, list):
            return False, "语料内容必须是数组格式"
        try:
            file_path = CORPUS_PATHS[corpus_type]
            # 第一步：预处理清洗
            str_content = [str(item) for item in content]
            cleaned_content = self._auto_preprocess_corpus(str_content)
            if not cleaned_content:
                return False, "⚠️ 没有有效语料，所有内容已被过滤"
            
            # 第二步：自动打标签（如果开启）
            formatted_content = []
            for line in cleaned_content:
                if auto_tag:
                    tagged = self._auto_tag_corpus(line)
                    formatted_content.append(self._format_corpus_line(tagged))
                else:
                    # 原有逻辑：解析再格式化确保规范
                    parsed = self._parse_corpus_line(line)
                    formatted_content.append(self._format_corpus_line(parsed))
            if append and os.path.exists(file_path):
                # 追加模式，读取现有内容
                with open(file_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                    if isinstance(existing, list):
                        formatted_content = existing + formatted_content
            # 去重
            formatted_content = list(set(formatted_content))
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(formatted_content, f, ensure_ascii=False, indent=2)
            # 重新加载结构化语料
            loaded_corpus = self._load_corpus(file_path, DEFAULT_CORPUS[corpus_type])
            if corpus_type == "greetings":
                self.greetings_corpus = loaded_corpus
            elif corpus_type == "comfort":
                self.comfort_corpus = loaded_corpus
            elif corpus_type == "positive":
                self.positive_corpus = loaded_corpus
            elif corpus_type == "neutral":
                self.neutral_corpus = loaded_corpus
            return True, f"✅ 语料保存成功，共{len(formatted_content)}条"
        except Exception as e:
            return False, f"⚠️ 语料保存失败：{str(e)}"
    
    def reset_corpus(self, corpus_type: str) -> Tuple[bool, str]:
        """重置指定类型的语料到默认状态，corpus_type=all表示重置所有"""
        if corpus_type == "all":
            # 重置所有语料
            success_count = 0
            fail_count = 0
            for ctype in CORPUS_PATHS.keys():
                ok, _ = self.save_corpus(ctype, DEFAULT_CORPUS[ctype], append=False)
                if ok:
                    success_count += 1
                else:
                    fail_count += 1
            return True, f"✅ 所有语料重置完成，成功{success_count}个，失败{fail_count}个"
        if corpus_type not in CORPUS_PATHS:
            return False, f"未知语料类型：{corpus_type}，支持的类型：{', '.join(CORPUS_PATHS.keys())}"
        try:
            # 删除现有文件，重新生成默认
            if os.path.exists(CORPUS_PATHS[corpus_type]):
                os.remove(CORPUS_PATHS[corpus_type])
            # 重新加载
            self.get_corpus(corpus_type)
            return True, f"✅ {corpus_type} 语料已重置为默认状态"
        except Exception as e:
            return False, f"⚠️ 语料重置失败：{str(e)}"

# 单例实例
emotion_engine = EmotionEngine()
