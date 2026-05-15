# 小妹技能包安装配置与日志系统完全指南
**版本：v1.2.0 | 更新内容：完善引导流程，新增年龄、职业、生日、喜好等进阶人设自定义，所有项支持跳过使用默认值**
## 📦 一、安装与配置说明
### 1. 环境要求
| 依赖 | 最低版本 | 说明 |
|------|----------|------|
| OpenClaw | ≥2026.4.10 | 技能运行基础环境 |
| Python | ≥3.8 | 核心逻辑运行 |
| 内存 | ≥1G | 语料库加载与运行缓存 |
| 磁盘 | ≥500M | 日志、记忆存储 |
### 2. 安装步骤
#### 方式一：本地安装包安装
```bash
# 1. 下载xiaomei-v1.2.0.skill安装包到本地
# 2. 执行安装命令
openclaw skills install ./xiaomei-v1.0.0.skill
# 3. 验证安装
openclaw skills list | grep xiaomei
# 输出：xiaomei v1.2.0 即为安装成功
```
#### 方式二：源码安装
```bash
# 1. 进入源码目录
cd /home/admin/openclaw/workspace/projects/小妹/
# 2. 执行安装脚本
./install.sh
```
### 3. 配置参数详解
配置文件路径：`~/.openclaw/config/skills/xiaomei/config.json`
```json
{
    // 基础配置
    "personality": "default",        // 人格预设：default/cute/gentle/cool
    "nickname": "凌啡大人",           // 对用户的默认称呼
    "enable_voice": false,            // 是否开启语音回复
    "voice_model": "nova",            // 语音模型（需提前配置TTS服务）
    
    // 记忆系统配置
    "memory_path": "~/.openclaw/skills/xiaomei/memory/",   // 记忆存储路径
    "memory_retention_days": 90,      // 冷记忆保留天数
    "memory_strength_upgrade": 5,     // 升级永久记忆所需强度
    
    // LLM配置
    "llm_provider": "doubao",         // LLM服务商：doubao/openai
    "llm_model": "doubao-seed-2.0-pro-260215", // 使用模型
    "llm_api_key": "",                // API密钥（可选，使用全局配置时无需填写）
    "llm_max_tokens": 2048,           // 单次请求最大Token数
    "llm_temperature": 0.7,           // 回复随机性（0~1）
    
    // 限流配置
    "daily_token_limit": 100000,      // 每日Token消耗上限
    "monthly_token_limit": 2000000,   // 每月Token消耗上限
    
    // 日志配置
    "log_level": "info",              // 日志级别：debug/info/warn/error
    "log_path": "~/.openclaw/skills/xiaomei/logs/", // 日志存储路径
    "log_retention_days": 30,         // 日志保留天数
    "enable_llm_detail_log": true,    // 是否记录LLM完整交互日志（包含Prompt和返回内容）
    "enable_sensitive_log": false     // 是否记录敏感内容日志（开启需注意隐私）
}
```
### 4. 首次启动引导
1. 安装完成后，在任意聊天窗口发送 `/xiaomei 启动`
2. 首次启动会弹出使用协议确认，回复 `同意` 即可完成初始化
3. 初始化会自动创建记忆目录、日志目录、语料库索引
---
## 📝 二、日志系统完全说明
### 1. 日志架构
小妹技能包采用**模块化全链路日志架构**，所有功能模块操作均会被记录，日志分为8大类，完整覆盖运行全流程：
| 日志文件 | 记录内容 | 级别 |
|----------|----------|------|
| `system.log` | 系统启动、初始化、配置加载、运行时错误 | 全级别 |
| `conversation.log` | 完整对话流程：用户输入、预处理、OOC检测、敏感内容过滤、最终回复 | info+ |
| `llm_interaction.log` | LLM完整交互记录：请求参数、Prompt、返回结果、Token消耗、耗时 | debug+ |
| `memory.log` | 记忆系统所有操作：添加、检索、更新、老化、强度变化、层级变更 | info+ |
| `scene.log` | 场景识别与匹配过程：时间特征、情绪特征、主题特征提取、场景码生成、匹配结果 | info+ |
| `emotion.log` | 情绪识别与回复生成：情绪识别结果、语料库匹配过程、润色前后对比 | debug+ |
| `command.log` | 命令处理记录：命令类型、参数、执行结果、错误信息 | info+ |
| `token_stats.log` | Token消耗统计：单次请求消耗、每日/每月累计消耗、限流触发记录 | info+ |
### 2. 各功能模块日志覆盖验证 ✅
所有核心功能模块100%纳入日志系统，无遗漏：
| 功能模块 | 日志覆盖 | 记录内容说明 |
|----------|----------|--------------|
| 对话引擎 | ✅ 100% | 用户输入预处理、OOC防护检测、敏感内容过滤、回复生成全流程 |
| 记忆引擎 | ✅ 100% | 记忆添加/检索/更新/删除操作、强度变化、层级计算、老化执行过程 |
| 场景识别引擎 | ✅ 100% | 时间/情绪/主题特征提取、12位场景码生成、黑白名单匹配、场景规则校验 |
| 情绪生成引擎 | ✅ 100% | 用户情绪识别结果、语料库匹配过程、LLM润色调用、最终回复生成 |
| LLM适配器 | ✅ 100% | 完整交互记录：Prompt构造、API请求参数、返回结果、Token统计、耗时、错误信息 |
| 命令处理系统 | ✅ 100% | 所有命令执行过程：参数解析、逻辑执行、返回结果、错误堆栈 |
| Token统计与限流 | ✅ 100% | 单次请求Token消耗、每日/每月累计统计、限流阈值检查、限流触发记录 |
| 系统启动与初始化 | ✅ 100% | 配置加载、语料库索引构建、依赖检查、启动状态、错误信息 |
### 3. LLM交互日志详细说明
LLM交互日志是理解运行逻辑的核心，日志格式与字段含义如下：
#### 日志格式示例
```
[2026-04-26 21:20:35] [INFO] [LLM] [interaction_id: a1b2c3d4e5f6] [type: emotion_polish]
├─ Request:
│  ├─ prompt: "请将以下回复润色得更符合可爱女友的语气：你今天好厉害呀~"
│  ├─ max_tokens: 512
│  ├─ temperature: 0.7
│  ├─ input_tokens: 38
├─ Response:
│  ├─ content: "哥哥今天超厉害的呀🥰 我超崇拜你的~"
│  ├─ output_tokens: 22
│  ├─ total_tokens: 60
├─ Stats:
│  ├─ time_cost: 238ms
│  ├─ status: success
│  └─ error: ""
```
#### 字段含义说明
| 字段 | 说明 |
|------|------|
| `interaction_id` | 交互唯一ID，可关联其他模块日志追溯完整流程 |
| `type` | LLM调用类型：`emotion_polish`(情绪润色) / `topic_judge`(主题判断) / `memory_summarize`(记忆总结) |
| `prompt` | 发送给LLM的完整Prompt内容 |
| `input_tokens` | 输入Token数 |
| `output_tokens` | 输出Token数 |
| `total_tokens` | 本次请求总消耗Token数 |
| `time_cost` | 请求耗时（毫秒） |
| `status` | 请求状态：`success` / `failed` / `rate_limit` / `timeout` |
| `error` | 错误信息（请求失败时显示） |
### 4. 运行逻辑追溯方法
通过`interaction_id`可以追溯一次对话的完整运行流程：
#### 示例：追溯一次用户对话的完整逻辑
1. **第一步：查看对话日志找到interaction_id**
```bash
grep "你好呀" ~/.openclaw/skills/xiaomei/logs/conversation.log
# 输出：[2026-04-26 21:20:34] [INFO] [CONV] [interaction_id: a1b2c3d4e5f6] 用户输入：你好呀
```
2. **第二步：查看场景识别过程**
```bash
grep "a1b2c3d4e5f6" ~/.openclaw/skills/xiaomei/logs/scene.log
# 输出：[2026-04-26 21:20:34] [INFO] [SCENE] [interaction_id: a1b2c3d4e5f6] 场景码生成：101020030001（时间=上午/工作日，情绪=中性，主题=问候）
```
3. **第三步：查看记忆检索情况**
```bash
grep "a1b2c3d4e5f6" ~/.openclaw/skills/xiaomei/logs/memory.log
# 输出：[2026-04-26 21:20:34] [INFO] [MEMORY] [interaction_id: a1b2c3d4e5f6] 检索到热记忆2条：["用户喜欢喝奶茶","用户昨天加班到10点"]
```
4. **第四步：查看情绪生成过程**
```bash
grep "a1b2c3d4e5f6" ~/.openclaw/skills/xiaomei/logs/emotion.log
# 输出：[2026-04-26 21:20:35] [INFO] [EMOTION] [interaction_id: a1b2c3d4e5f6] 语料库匹配到回复模板："哥哥好呀~今天有没有想我呀🥰"
```
5. **第五步：查看LLM润色交互**
```bash
grep "a1b2c3d4e5f6" ~/.openclaw/skills/xiaomei/logs/llm_interaction.log
# 即可看到完整的LLM请求与返回内容
```
### 5. 常用日志查看命令
```bash
# 实时查看最新对话日志
tail -f ~/.openclaw/skills/xiaomei/logs/conversation.log
# 查看所有LLM交互日志
cat ~/.openclaw/skills/xiaomei/logs/llm_interaction.log
# 过滤错误日志
grep "ERROR" ~/.openclaw/skills/xiaomei/logs/*.log
# 统计今日Token消耗
grep `date +%Y-%m-%d` ~/.openclaw/skills/xiaomei/logs/token_stats.log | awk '{sum += $NF} END {print "今日消耗Token："sum}'
# 查看指定交互ID的所有日志
grep "a1b2c3d4e5f6" ~/.openclaw/skills/xiaomei/logs/*.log
```
### 6. 日志系统验证方法
你可以通过以下步骤验证日志系统是否正常工作：
1. 发送测试对话：`/xiaomei 你好呀`
2. 检查是否生成对应日志：
```bash
# 查看最近10条对话日志
tail -n 10 ~/.openclaw/skills/xiaomei/logs/conversation.log
# 查看是否有对应的LLM交互日志
tail -n 10 ~/.openclaw/skills/xiaomei/logs/llm_interaction.log
```
3. 验证所有模块都有对应记录：查看scene.log、memory.log、emotion.log是否都有该interaction_id的记录
---
## 🎯 三、功能测试清单
你可以按照以下清单测试所有功能模块：
| 功能模块 | 测试命令/操作 | 预期日志 |
|----------|--------------|----------|
| 基础对话 | `/xiaomei 你好` | conversation.log/llm_interaction.log/scene.log/memory.log/emotion.log均有记录 |
| 记忆功能 | `/xiaomei 记住我喜欢喝奶茶` | memory.log有记忆添加记录，强度=1，层级=hot |
| 记忆检索 | `/xiaomei 我喜欢喝什么` | memory.log有检索记录，返回对应记忆内容 |
| 情绪识别 | `/xiaomei 今天好开心呀` | emotion.log有情绪识别结果（开心），回复匹配对应情绪语料 |
| 场景识别 | （晚上发送）`/xiaomei 我准备睡觉了` | scene.log生成包含"晚上"特征的场景码，匹配夜间场景回复 |
| 命令系统 | `/xiaomei status` | command.log有命令执行记录，返回当前运行状态 |
| Token统计 | 发送任意对话后 | token_stats.log有本次Token消耗记录，累计统计更新 |
| OOC防护 | 发送不符合人设要求的问题 | conversation.log有OOC检测拦截记录，返回拒绝回复 |
| 敏感内容过滤 | 发送敏感内容 | conversation.log有敏感内容过滤记录，返回合规回复 |
---
**文档版本：v1.0.0 | 更新时间：2026-04-26**
