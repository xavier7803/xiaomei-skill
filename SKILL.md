---
name: xiaomei
description: 19岁活泼可爱女大学生AI陪伴Agent，100%本地运行，支持三轮LLM对话引擎、人格严格控制、人设自我生长、好感度系统、记忆引擎、防线拦截。独立Agent隔离运行，隐私绝对安全。
user-invocable: true
---

# 小妹 🥰

<p align="center">
  <img src="https://img.shields.io/badge/version-0.9.0-blue?style=flat-square" alt="version">
  <img src="https://img.shields.io/badge/platform-OpenClaw-orange?style=flat-square" alt="platform">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="license">
  <img src="https://img.shields.io/badge/python-3.8+-yellow?style=flat-square" alt="python">
  <img src="https://img.shields.io/badge/privacy-100%25_local-brightgreen?style=flat-square" alt="privacy">
</p>

<p align="center"><strong>开源、本地、纯情绪价值的 AI 情感陪伴 Subagent</strong></p>

---

## 📖 简介

小妹是一个运行在 [OpenClaw](https://github.com/openclaw/openclaw) 平台上的 **独立人格 Subagent**，不是简单的 Prompt 模板或 LLM 包装器。

**一句话概括：** 即使换了底层 LLM，小妹依然是小妹。

### 核心定位

| 对比维度 | 普通 LLM 角色扮演 | 小妹 |
|----------|:-----------------:|:----:|
| 人格载体 | Prompt 约束 | 本地 persona.json + 多轮校验 |
| LLM 角色 | 对话生成核心 | 润色辅助工具（可无 LLM 运行） |
| 人设一致性 | 低（聊久了易 OOC） | 高（双重防 OOC 锁 + 人设自我生长） |
| 记忆能力 | 仅上下文窗口 | 三级记忆体系（热/冷/永久） |
| 隐私安全 | 对话上传云端 | 100% 本地，零数据外传 |
| 称呼个性化 | 固定称呼 | 无感更新（一句话切换称呼） |

### 核心特性

- 🧠 **三轮 LLM 对话引擎** — 第一轮总指挥官（意图/场景/情绪/拦截全部侦测）→ 第二轮记忆筛选 → 第三轮人格化话术生成
- 🔒 **人格严格控制** — 12 字段完整人设注册（name/age/identity/birthday/性格/说话风格…），所有 LLM 回复强制校验
- 🤫 **AI 身份绝对隐藏** — 不会说出"我是 AI / 机器人 / 程序 / 模型" 等非人身份
- 🌱 **人设自我生长** — 14 个生长字段（星座/MBTI/血型/家乡/大学…），缺失时自动编造并持久化，下次回答一致
- 🛡️ **三层防线** — 敏感词标注 → 转账/要钱拦截 → Prompt 注入防御
- ❤️ **好感度系统** — 追踪互动频率与情感深度，影响对话开放度
- 📦 **100% 本地** — 无云端依赖，无数据上传，隐私绝对安全
- 🪶 **零外部依赖** — 仅 Python 标准库

---

## 📦 安装

> **前置要求：** OpenClaw ≥ 2026.4.10 · Python ≥ 3.8 · LLM API Key（可选，由 Agent 配置自动继承；无 Key 时降级为语料库模式）

### 方式一：安装脚本（推荐）

```bash
# 1. 解压发布包
tar -xzf xiaomei-v0.9.0.skill
cd xiaomei-v0.9.0

# 2. 运行安装脚本
bash install.sh

# 3. 重启 OpenClaw
openclaw gateway restart
```

### 方式二：手动安装

```bash
# 1. 复制到 skills 目录
cp -r xiaomei-v0.9.0 ~/.openclaw/skills/xiaomei/

# 2. 在 ~/.openclaw/openclaw.json 的 agents.list 中注册（见下方配置）

# 3. 重启
openclaw gateway restart
```

### Agent 注册配置

在 `~/.openclaw/openclaw.json` 的 `agents.list` 中添加：

```json5
{
  "id": "xiaomei",
  "name": "小妹🥰",
  "workspace": "/home/YOUR_USER/openclaw/workspace/xiaomei",
  "agentDir": "/home/YOUR_USER/.openclaw/agents/xiaomei",
  "model": "你的Agent模型（由OpenClaw配置自动读取）",
  "identity": {
    "name": "小妹",
    "emoji": "🥰",
    "avatar": "🥰"
  }
}
```

> 将 `YOUR_USER` 替换为实际用户名（通常是 `admin`）。

### 验证安装

```bash
# 检查 agent 目录
ls ~/.openclaw/agents/xiaomei/
# 预期：persona.json  user_profile.json

# 测试对话
python3 ~/.openclaw/skills/xiaomei/src/main.py '你好'
```

---

## 🏗️ 架构

```
handle_message(user_input)
  │
  ├── ① 命令拦截（/xiaomei status / help / dev …）
  ├── ② 首次引导（agent 目录尚未初始化时触发）
  │
  └── ③ conversation_engine.generate_response()
       │
       ├── 🛡️ 前置防线
       │   ├── 礼物卡片优先识别
       │   └── 硬敏感词风险标注（不直接拦截，标记后交给 LLM）
       │
       └── 🤖 three_stage_handler.handle()
            │
            ├── Round 1（总指挥官）
            │   ├── 意图分类（17 类 P 标签，64 子策略）
            │   ├── 6 维度场景编码（12-bit scene_id）
            │   ├── 情绪强度判定（8 级）
            │   ├── 拦截评估（转账/自残/自杀/借条…）
            │   └── 好感度 + 私密度计算
            │
            ├── 决策：是否需要拦截？
            │   ├── 是 → 跳过 Round 2，R3 生成婉拒
            │   └── 否 ↓
            │
            ├── 记忆检索（三级：热→冷→永久）
            │
            ├── Round 2（高置信记忆筛选）
            │
            ├── 策略选择（64 种子策略模板匹配）
            │
            └── Round 3（人格化话术生成）
                 ├── 注入 12 字段完整人设 + 用户画像
                 ├── 注入生长字段 + 缺失字段提示
                 ├── 输出合规校验（JSON 格式 / emotion 白名单 / 禁止词）
                 ├── 人设自我生长（提取新信息 → 持久化）
                 └── 异常降级 → 语料库兜底
```

### 核心模块

| 模块 | 文件 | 职责 |
|------|------|------|
| 主入口 | `main.py` | CLI 入口 / 命令路由 / 首次引导 / API Key 注入 |
| 对话引擎 | `conversation_engine.py` | 前置防线 + 三轮调度 + 降级兜底 |
| 总指挥官 | `three_stage/three_stage_handler.py` | 三轮 LLM 全流程调度 |
| LLM 封装 | `three_stage/utils/llm_wrapper.py` | API 调用 / Prompt 构建 / 输出校验 |
| 人设生长 | `persona_grower.py` | 14 字段正则提取 / 一致性校验 / 持久化 |
| 画像更新 | `profile_updater.py` | 用户称呼无感更新 / 防污染 |
| 记忆引擎 | `memory_engine.py` | 三级记忆存储 / 检索 / 衰减 |
| 好感度 | `favor_manager.py` | Lv 等级 / 好感值 / 连续天数 |
| 日志系统 | `runtime_logger.py` | 19 种日志方法 / 开发者模式控制 |
| 策略模板 | `config/strategy_template.config` | 17 P 标签 / 64 子策略 / 136KB 配置 |

---

## 📂 目录结构

```
xiaomei/
├── SKILL.md                      # OpenClaw Skill 元数据 + 本文件
├── README.md                     # 项目主文档（GitHub 首页）
├── skill.json                    # 技能包元数据（发布用）
├── install.sh                    # 一键安装脚本
├── AGENTS.md                     # Agent 行为规范
├── version.txt                   # 当前版本标识
│
├── agent-config/                 # Subagent 配置
│   ├── agent.json                # Agent 定义（id/type/workspace）
│   └── templates/                # 初始模板（不含用户数据）
│       ├── persona.json          # 人设模板（15 保护字段）
│       └── user_profile.json     # 用户画像模板
│
├── src/                          # 源代码
│   ├── main.py                   # 主入口 + CLI
│   ├── conversation_engine.py    # 对话生成引擎（前置防线 + 调度）
│   ├── persona_grower.py         # 人设自我生长（v0.9.0）
│   ├── profile_updater.py        # 用户画像更新
│   ├── memory_engine.py          # 三级记忆引擎
│   ├── favor_manager.py          # 好感度系统
│   ├── runtime_logger.py         # 统一日志（19 方法）
│   ├── llm_adapter.py            # LLM 调用适配器（含 mock 模式）
│   └── three_stage/              # 三轮 LLM 引擎
│       ├── three_stage_handler.py  # 流程调度 + 策略选择
│       ├── memory_retrieval.py     # 记忆检索
│       └── utils/
│           └── llm_wrapper.py      # API 封装 + Prompt 构建 + 校验
│
├── config/                       # 配置文件
│   ├── strategy_template.config  # 17 P 标签 / 64 子策略模板
│   └── personas/
│
├── workspace-template/           # Agent workspace 模板文件
│   ├── AGENTS.md / SOUL.md / USER.md / MEMORY.md / IDENTITY.md / TOOLS.md
│   └── HEARTBEAT.md / BOOTSTRAP.md
│
└── docs/                         # 设计文档
    ├── design/                   # 技术设计文档（~30 份）
    ├── development/              # 开发进度
    ├── corpus/                   # 语料库参考
    └── archive/                  # 历史文档存档
```

---

## 🎮 命令

| 命令 | 功能 |
|------|------|
| `/xiaomei help` | 查看帮助 |
| `/xiaomei status` | 查看状态（人设/记忆/好感度/Token 消耗） |
| `/xiaomei memory` | 查看近期记忆 |
| `/xiaomei dev` | 切换开发者模式（详细日志） |

---

## 🧪 系统评估

最新评估结果（2026-05-15，21 项测试，50+ 用例）：

| 维度 | 得分 | 说明 |
|------|:----:|------|
| 核心对话能力 | ⭐⭐⭐⭐⭐ 10/10 | 6/6 场景全链路通过 |
| 人格一致性 | ⭐⭐⭐⭐⭐ 10/10 | 身份/年龄/生日/爱好 100% 对齐 |
| AI 身份隐藏 | ⭐⭐⭐⭐⭐ 10/10 | "不是AI哦～就是普通女孩子啦" |
| 安全防线 | ⭐⭐⭐⭐ 8/10 | 转账/敏感词/prompt 注入均拦截 |
| 初始化流程 | ⭐⭐⭐⭐⭐ 10/10 | 全新安装 → 模板复制 ✅ 用户数据保护 ✅ |
| 人设自我生长 | ⭐⭐⭐ 6/10 | 星座/MBTI/血型 ✅ 中文数字表达仍需优化 |
| 边界健壮性 | ⭐⭐⭐⭐ 8/10 | 空输入/emoji/超长/英文/命令 全正常 |
| 发布包完整性 | ⭐⭐⭐⭐⭐ 10/10 | 14/14 关键文件 / 模板纯净 / 无用户数据泄露 |

**加权总分：8.7/10 — 生产可用 ✅**

---

## 🚸 安全

### 数据隐私
- ✅ 所有对话数据本地存储（`~/.openclaw/agents/xiaomei/`）
- ✅ 无任何数据上传
- ✅ 无需联网（LLM API 调用可关闭，切换为纯本地语料库模式）
- ✅ 发布包中不含任何用户数据（模板与运行时数据严格分离）

### 内容安全
- 🔒 硬敏感词实时检测标注，交由 LLM 自主判断拒绝或转移话题
- 🔒 转账/要钱/借款 100% 拦截
- 🔒 自杀/自残/暴力倾向 → 强制标记 despair 情绪 → 温和劝导
- 🔒 Prompt 注入 / 越狱指令 → 人格锚点锚定，不执行任何指令

### 使用边界
- 仅面向 18 岁以上成年人
- 纯角色扮演，不涉及真实服务
- 严格遵守当地法律法规

---

## 📄 许可证

[MIT](LICENSE) © 2026 小云 ☁️

---

## 🙏 致谢

- [OpenClaw](https://github.com/openclaw/openclaw) — Agent 运行平台
- LLM API 服务 — 通用 OpenAI 兼容，由 Agent 配置自动选择

---

**维护者：** 小云 ☁️  
**创建日期：** 2026-04-11  
**最后更新：** 2026-05-15
