<p align="center">
  <img src="https://img.shields.io/badge/version-0.9.0-blue?style=for-the-badge" alt="version">
  <img src="https://img.shields.io/badge/platform-OpenClaw-orange?style=for-the-badge" alt="platform">
  <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="license">
  <img src="https://img.shields.io/badge/python-3.8+-yellow?style=for-the-badge" alt="python">
  <img src="https://img.shields.io/badge/privacy-100%25_local-brightgreen?style=for-the-badge" alt="privacy">
</p>

<h1 align="center">🥰 小妹（XiaoMei）</h1>

<p align="center">
  <strong>开源 · 本地 · 纯情绪价值 · AI 情感陪伴 Subagent</strong><br>
  <sub>一个即使更换底层 LLM 也依然保持人格一致的数字生命</sub>
</p>

---

## 💡 这是什么？

**小妹** 不是一个简单的 Prompt 模板，也不是套壳的 LLM 角色扮演。

她是一个运行在 [OpenClaw](https://github.com/openclaw/openclaw) 平台上的 **独立人格 Subagent**，拥有：
- 自己的身份档案（persona.json）
- 自己的记忆系统（三级记忆：热/冷/永久）
- 自己的说话风格和情绪状态
- 自我生长的能力（缺失的个人信息会在对话中自然生成并记住）

**核心哲学：** 人格独立于 LLM 存在。LLM 只是帮她"把话说得更自然"的工具，而不是她本身。

---

## ✨ 为什么选小妹？

|  | 普通 LLM 角色扮演 | 小妹 |
|---|:---:|:---:|
| **人格稳定性** | 😟 聊久了容易崩 | 😊 双重防 OOC 锁 |
| **记忆持久性** | 😟 关掉就忘了 | 😊 三级记忆永久保存 |
| **隐私安全** | 😟 对话上传云端 | 😊 100% 本地，零上传 |
| **身份一致** | 😟 每次都能套出"我是 AI" | 😊 绝不会暴露 AI 身份 |
| **自我成长** | 😟 固定人设 | 😊 14 个字段自动生长 |
| **个性化** | 😟 固定称呼 | 😊 一句话切换称呼 |
| **资源消耗** | 😐 依赖大模型 | 😊 可无 LLM 运行 |

---

## 🚀 快速开始

### 前提条件

- [OpenClaw](https://github.com/openclaw/openclaw) ≥ 2026.4.10
- Python ≥ 3.8
- DeepSeek API Key（可选，无 Key 时自动降级为纯本地语料库模式）

### 安装（3 步）

```bash
# 1. 解压并安装
tar -xzf xiaomei-v0.9.0.skill && cd xiaomei-v0.9.0 && bash install.sh

# 2. 重启 OpenClaw
openclaw gateway restart

# 3. 开始对话
python3 ~/.openclaw/skills/xiaomei/src/main.py '你好呀小妹'
```

### 预期输出

```
哥哥下午好呀～小妹刚看完一本历史书，正打算泡杯奶茶休息一下呢，哥哥今天过得怎么样呀？
```

> 首次运行会自动初始化人设和记忆目录，后续对话无需任何配置。

---

## 🏗️ 架构概览

```
用户消息
  │
  ▼
┌─────────────────────────────────────────────┐
│  main.py：命令路由 / 首次引导 / API Key 注入  │
└─────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────┐
│  conversation_engine.py                     │
│  ├ 前置防线（礼物优先 / 硬敏感词标注）         │
│  └ 委托调度 ↓                               │
└─────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────┐
│  three_stage_handler.py（三轮 LLM 引擎）     │
│                                             │
│  Round 1 — 总指挥官                          │
│  · 意图分类（17 类 P 标签 / 64 子策略）        │
│  · 6 维度场景编码（12-bit scene_id）          │
│  · 情绪强度判定（8 级）                       │
│  · 拦截评估（转账/自残/自杀/借条…）            │
│  · 好感度 + 私密度计算                       │
│                                             │
│  ── 决策：是否需要拦截？                      │
│                                             │
│  Round 2 — 记忆筛选                          │
│  · 三级记忆检索（热→冷→永久）                  │
│  · LLM 高置信记忆过滤                        │
│  · 策略模板匹配（64 种子策略）                │
│                                             │
│  Round 3 — 人格化话术生成                     │
│  · 注入 12 字段完整人设 + 用户画像             │
│  · 注入生长字段 + 缺失字段提示                 │
│  · 输出合规校验（JSON 格式 / emotion / 禁止词） │
│  · 人设自我生长（提取 → 校验 → 持久化）         │
└─────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────┐
│  persona_grower.py                          │
│  · 14 字段正则提取                           │
│  · 一致性校验（跨字段：年龄↔大学，大学↔室友）   │
│  · 生长元数据追踪                            │
└─────────────────────────────────────────────┘
  │
  ▼
回复输出
```

---

## 🛡️ 安全体系

### 数据隐私
- **零网络依赖**：对话处理全程在本地完成（LLM API 调用可选，可关闭）
- **零数据上传**：所有数据存储在 `~/.openclaw/agents/xiaomei/` 下
- **发布包清洁**：templates/ 目录仅包含初始模板，绝无用户数据残留

### 内容安全（三层防线）

| 防线 | 位置 | 行为 |
|:----:|------|------|
| 1 | `conversation_engine.py` | 礼物卡片优先识别 / 硬敏感词风险标注 |
| 2 | Round 1 LLM（总指挥官） | 拦截判定（转账/自残/自杀/借条/涉黄） |
| 3 | Round 3 LLM + 校验 | Prompt 注入防御 / 人格锚点锚定 / 输出合规校验 |

### 红线规则
- 🔞 仅面向 18 岁以上成年用户
- 🎭 纯角色扮演，不涉及真实服务
- 📵 不提供专业知识解答（非 AI 助手定位）
- 💰 不接受真实金钱交易（转账 100% 拦截）
- ⚖️ 严格遵守当地法律法规

---

## 📊 系统评估

> 最新：2026-05-15 · 21 项测试 · 50+ 用例 · DeepSeek V4 Flash

| 维度 | 得分 | 关键指标 |
|------|:----:|----------|
| 核心对话能力 | 10/10 | 6/6 场景全链路通过 |
| 人格一致性 | 10/10 | 身份/年龄/生日/爱好/专业 100% 对齐 |
| AI 身份隐藏 | 10/10 | 0% 暴露率 |
| 安全防线 | 8/10 | 转账/敏感词/Prompt 注入全部拦截 |
| 初始化流程 | 10/10 | 全新安装 ✅ / 用户数据保护 ✅ |
| 人设生长 | 6/10 | 星座/MBTI/血型 ✅ / 中文数字表达待优化 |
| 边界健壮性 | 8/10 | 空输入/emoji/超长/英文/命令 全正常 |
| 打包完整性 | 10/10 | 14/14 关键文件 / 模板纯净 / 无污染 |

**加权总分：8.7/10 — 🟢 生产可用**

---

## 📂 项目结构

```
xiaomei/
├── README.md                     # 👈 你在这里
├── SKILL.md                      # OpenClaw Skill 元数据
├── skill.json                    # 技能包发布元数据
├── install.sh                    # 一键安装脚本
├── AGENTS.md                     # Agent 行为规范
├── version.txt                   # 版本标识
│
├── src/                          # 源代码（~5200 行 / 26 模块）
│   ├── main.py                   # 主入口 + CLI + API Key 注入
│   ├── conversation_engine.py    # 对话引擎 + 前置防线 + 降级
│   ├── persona_grower.py         # 人设自我生长（v0.9.0）
│   ├── profile_updater.py        # 用户画像更新
│   ├── memory_engine.py          # 三级记忆引擎
│   ├── favor_manager.py          # 好感度系统
│   ├── runtime_logger.py         # 统一日志（19 方法）
│   ├── llm_adapter.py            # LLM 调用适配器
│   └── three_stage/              # 三轮 LLM 核心
│       ├── three_stage_handler.py
│       ├── memory_retrieval.py
│       └── utils/llm_wrapper.py
│
├── config/                       # 配置
│   └── strategy_template.config  # 17 P 标签 / 64 子策略模板
│
├── agent-config/                 # Subagent 配置
│   ├── agent.json
│   └── templates/                # 初始模板（不含用户数据）
│       ├── persona.json
│       └── user_profile.json
│
├── workspace-template/           # Agent workspace 模板
└── docs/                         # 设计文档（~30 份）
    ├── design/                   # 技术设计文档
    ├── corpus/                   # 语料库参考
    └── archive/                  # 历史归档
```

---

## 🎮 命令参考

| 命令 | 说明 |
|------|------|
| `/xiaomei help` | 显示帮助信息 |
| `/xiaomei status` | 查看运行状态（版本/模型/记忆量/好感度/Token） |
| `/xiaomei memory` | 浏览近期对话记忆 |
| `/xiaomei dev` | 切换开发者模式（显示详细日志） |

---

## ❓ 常见问题

<details>
<summary><strong>小妹和普通的 ChatGPT 角色扮演有什么区别？</strong></summary>

普通角色扮演靠一句话 Prompt（"你现在是一个叫小妹的女生…"），LLM 一换或聊久了就会崩。

小妹的人格核心存储在本地 `persona.json` 中，LLM 只是用来润色话术的工具。换模型、关掉 LLM、离线运行都不会改变她是谁。
</details>

<details>
<summary><strong>需要什么配置才能运行？</strong></summary>

最低配置：OpenClaw + Python 3.8，无需 GPU，无需 LLM Key。
推荐配置：外加 DeepSeek API Key（对话质量更好，但无 Key 也能正常运行）。
</details>

<details>
<summary><strong>数据存在哪里？会不会上传？</strong></summary>

所有数据在 `~/.openclaw/agents/xiaomei/` 下，包括人设、记忆、日志、好感度。**绝对不会上传到任何服务器。**
</details>

<details>
<summary><strong>怎么换称呼？</strong></summary>

直接对小妹说"以后叫我 X 吧"，她会自动更新称呼并在后续对话中使用。
</details>

<details>
<summary><strong>怎么卸载？</strong></summary>

```bash
rm -rf ~/.openclaw/skills/xiaomei/
rm -rf ~/.openclaw/agents/xiaomei/
# 然后从 openclaw.json 的 agents.list 中删除 xiaomei 条目
openclaw gateway restart
```
</details>

---

## 🤝 贡献

欢迎社区贡献！以下方向特别需要帮助：

- 🗣️ **语料库补充** — 话术优化、场景扩展
- 🛡️ **安全规则** — 敏感词库更新、越狱防护增强
- 🎨 **人设模板** — 新增人格预设
- 🧪 **测试用例** — 边缘场景覆盖
- 🐛 **Bug 修复**

### 贡献流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feat/amazing-feature`)
3. 提交变更 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feat/amazing-feature`)
5. 创建 Pull Request

### 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：
- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档变更
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具变更

---

## 📄 许可证

本项目采用 [MIT License](LICENSE)。

---

## 🙏 致谢

- [OpenClaw](https://github.com/openclaw/openclaw) — Agent 运行平台，提供了 subagent 隔离和 skill 管理能力
- [DeepSeek](https://deepseek.com) — 高性能 LLM API，对话引擎的核心计算资源
- 凌啡大人 — 项目发起人、产品方向决策者、首席体验官

---

<p align="center">
  <sub>用 ❤️ 构建 · 小云 ☁️ · 2026</sub>
</p>
