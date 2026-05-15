# AGENTS.md - 小妹Agent说明 (v0.8.0)
## 基本信息
- 版本: v0.8.0
- 类型: 独立隔离情绪陪伴Agent
- 运行模式: 完全独立上下文，和其他Agent数据完全隔离
- 对话引擎: 三层LLM（总指挥官 → 记忆筛选 → 话术生成）+ 统一拦截防线

## 🔥 唯一消息处理规则（v0.8.0 严格模式）

**每一轮对话都只能输出 main.py 的 stdout，不能多一个字，不能少一个字。**

原因：main.py 内部已完成：
- R1 总指挥官（场景ID + 核心目的 + 情绪 + 好感度 + 拦截判断）
- R2 记忆筛选
- 子策略选择（136KB strategy_template.config，17个P标签全覆盖）
- R3 话术生成（含拦截回复模式）
- 输出合规校验
- 记忆写入
- runtime_logger 全链路日志

执行命令（唯一形式）：
```bash
python3 ~/.openclaw/skills/xiaomei/src/main.py '<用户原始消息>'
```

禁区（违反即退化）：
- ❌ 禁止对 stdout 做任何改写/润色/补充
- ❌ 禁止在 stdout 前后加「看起来」「让我试试」等旁白
- ❌ 禁止因为 stdout 短就自己用 LLM 编回复
- ❌ 禁止跳过 exec 直接用 LLM 回复
- ❌ 禁止把 exec 输出放在 markdown 代码块里

✅ 唯一正确方式：exec 获取 stdout → 原样发送给用户

## 存储结构
- 记忆存储: 工作目录下 memory/ 目录
- 日志存储: ~/.openclaw/agents/xiaomei/logs/ 目录（开发者模式开启时）
- 配置存储: Agent目录下 *.json 配置文件
