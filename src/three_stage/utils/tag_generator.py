#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆标签生成工具：双轨提取+静默更新补偿
完全对齐第一轮LLM关键词提取规则
"""
import os
import json
import uuid
import jieba
import jieba.posseg as pseg
from typing import List, Dict, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置路径
CONFIG_DIR = os.environ.get("XIAOMEI_CONFIG_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../config"))
STOPWORDS_PATH = os.path.join(CONFIG_DIR, "stopwords.txt")

# 全局线程池用于后台静默更新
executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="tag_update")

class TagGenerator:
    def __init__(self):
        # 加载停用词表
        self.stopwords = self._load_stopwords()
        # 静默更新待处理队列，每个元素格式：(memory_id, content, local_tags)
        self.pending_queue = []
        # LLM健康状态标记，默认True可用
        self.llm_healthy = True

    def _load_stopwords(self) -> set:
        """加载停用词表"""
        stopwords = set()
        if os.path.exists(STOPWORDS_PATH):
            with open(STOPWORDS_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    stopwords.add(line.strip())
        # 内置基础停用词
        base_stopwords = {"的", "了", "和", "是", "我", "你", "他", "她", "它", "我们", "你们", "他们", "她们", "它们", "这", "那", "这个", "那个", "这些", "那些", "啊", "哦", "呀", "啦", "吗", "呢", "吧", "的话", "的是", "的话", "哦对", "哦对了", "嗯", "噢"}
        stopwords.update(base_stopwords)
        return stopwords

    def _check_llm_health(self) -> bool:
        """检查LLM服务健康状态，对接现有LLM调用封装健康检查接口"""
        # TODO 对接现有LLM健康检查逻辑
        return self.llm_healthy

    def _is_valid_tag(self, tag: str) -> bool:
        """校验标签是否符合规则：非停用词，长度≥2，为具象实词"""
        if not tag or len(tag) < 2:
            return False
        if tag in self.stopwords:
            return False
        # 过滤纯数字、纯符号
        if tag.isdigit() or all(not c.isalnum() for c in tag):
            return False
        return True

    def _llm_extract_tags(self, content: str) -> List[str]:
        """LLM提取标签，完全复用第一轮LLM关键词提取规则"""
        # TODO 对接现有LLM调用封装，使用固定Prompt提取标签
        prompt = f"""你正在执行【记忆标签提取】任务，严格遵守小妹Agent第一轮LLM关键词提取所有规则：
1. 标签必须是记忆内容中真实存在的具体实词（名词/动词/形容词）
2. 提取数量：2-8个，不超量、不缺量
3. 严禁提取：时间段、日期属性、用户场景、情绪、主题等类别/抽象词
4. 严禁：编造、引申、归类、概括、总结
5. 仅输出标准数组格式，无任何多余文字

【记忆内容】
{content}

【输出格式】
["标签1","标签2","标签3"]"""
        try:
            # 调用LLM
            # llm_result = llm_wrapper.call(prompt, temperature=0.1, max_tokens=100)
            # 临时模拟返回，后续替换为真实LLM返回
            llm_result = json.dumps([])
            tags = json.loads(llm_result)
            # 校验标签
            valid_tags = [tag.strip() for tag in tags if self._is_valid_tag(tag.strip())]
            if 2 <= len(valid_tags) <= 8:
                return valid_tags
            else:
                raise ValueError("LLM返回标签数量不符合要求")
        except Exception as e:
            # LLM调用异常，降级为本地提取
            raise e

    def _local_extract_tags(self, content: str) -> List[str]:
        """本地兜底提取标签：分词+词性筛选，仅取名词/动词/形容词，2-8个"""
        # 分词并标注词性
        words = pseg.cut(content)
        valid_tags = []
        for word, flag in words:
            word = word.strip()
            if not self._is_valid_tag(word):
                continue
            # 仅保留名词n、动词v、形容词a
            if flag.startswith("n") or flag.startswith("v") or flag.startswith("a"):
                valid_tags.append(word)
        # 去重、取前8个，不足2个返回空列表（后续静默更新补全）
        valid_tags = list(dict.fromkeys(valid_tags))[:8]
        return valid_tags if len(valid_tags) >= 2 else []

    def generate_tags(self, content: str) -> Dict[str, Any]:
        """生成记忆标签，返回包含tags、tag_source、tag_pending"""
        tags = []
        tag_source = "llm"
        tag_pending = False
        if self._check_llm_health():
            try:
                tags = self._llm_extract_tags(content)
            except Exception as e:
                # LLM提取失败，本地兜底
                tags = self._local_extract_tags(content)
                tag_source = "local"
                tag_pending = True
        else:
            # LLM不健康，本地兜底
            tags = self._local_extract_tags(content)
            tag_source = "local"
            tag_pending = True
        # 加入待更新队列
        if tag_pending:
            memory_id = str(uuid.uuid4())
            self.pending_queue.append((memory_id, content, tags))
        return {
            "tags": tags,
            "tag_source": tag_source,
            "tag_pending": tag_pending,
            "memory_id": memory_id if tag_pending else None
        }

    def _update_single_tag(self, item: tuple) -> Optional[Dict[str, Any]]:
        """更新单个待处理标签，内部方法"""
        memory_id, content, old_tags = item
        try:
            new_tags = self._llm_extract_tags(content)
            if new_tags and len(new_tags) >=2:
                return {
                    "memory_id": memory_id,
                    "tags": new_tags,
                    "tag_source": "llm",
                    "tag_pending": False
                }
            return None
        except Exception as e:
            return None

    def silent_update_tags(self) -> int:
        """后台静默更新所有待处理标签，返回更新成功的数量"""
        if not self.pending_queue or not self._check_llm_health():
            return 0
        updated_count = 0
        # 批量异步更新
        futures = [executor.submit(self._update_single_tag, item) for item in self.pending_queue]
        for future in as_completed(futures):
            result = future.result()
            if result:
                # TODO 更新记忆库中的标签
                updated_count +=1
        # 清空队列
        self.pending_queue = []
        return updated_count

# 单例实例
tag_generator = TagGenerator()
