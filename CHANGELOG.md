# 更新日志

所有值得注意的变更都记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，  
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [0.9.0] — 2026-05-15

### 🧪 新增
- 37 项纯本地单元测试覆盖 8 个模块（`test_v090_core.py`），无需网络/LLM/API Key
  - `persona_grower`（10 tests）— 字段生长/一致性校验/后处理
  - `profile_updater`（3 tests）— 地址变更检测
  - `memory_engine`（5 tests）— 添加/搜索/强度升级/计数
  - `favor_manager`（6 tests）— 信息键/互动方法/等级/解锁
  - `runtime_logger`（2 tests）— 单例模式/关键方法
  - `conversation_engine`（5 tests）— 敏感词检测/合规校验/兜底
  - `main`（3 tests）— 命令路由
  - CLI 端到端（2 tests）+ 平台兼容性检查（1 test）
- 旧版 v0.7.x 测试文件归档至 `tests/_archive/`

### 📝 文档
- 测试文件头部添加完整平台声明（已测试/未测试环境）
- 5 种跨平台失败场景详细说明

---

## [0.8.1] — 2026-05-15

### 🔧 修复
- 统一 `address_user=凌啡哥哥`（取代多版本不一致的称呼）
- 发布包清洁审计：移除运行时用户数据残留
- LICENSE + install.sh 纳入发布包
- SKILL.md / README.md 规范化

### 🏗️ 架构
- 安装目录标准化：`agents/xiaomei/`
- `active_interaction.py` 废弃模块移除（已无调用方）

---

## [0.8.0] — 2026-05-15

### ✨ 新增
- **三轮 LLM 对话引擎**（`three_stage_handler.py`）
  - Round 1 — 总指挥官：意图分类/场景编码/情绪判定/拦截评估
  - Round 2 — 记忆筛选 + 策略模板匹配
  - Round 3 — 人格化话术生成 + 合规校验
- **人设自我生长 v1.0**（`persona_grower.py`）— 14 字段正则提取
  - 星座/MBTI/血型/身高/体重/家乡/大学/专业/室友/特长/偶像/爱好/特别技能/秘密
- **用户画像更新**（`profile_updater.py`）— 称呼无感切换
- **64 策略模板** 批量收录（`strategy_template.config`，86KB）
  - 17 P 标签 / 64 子策略全覆盖
- **防线统一架构** — 策略选择前置，性能 3.6x 提升
- **可追溯日志系统**（`_handler_log`）— 每轮 LLM 输入/输出/决策完整记录

### 🔧 修复
- v0.7.5 5 项 Bug 修复（llm_wrapper 截断/tag_generator 括号/导入越界/json 误加载/logger 废弃）
- `reasoning_tokens` 无法禁用 → `max_tokens=2000` 兜底
- API Key 硬编码 → 自动从 `openclaw.json` 读取

### 🏗️ 架构
- v0.7.5 → v0.8.0：全线模块重写，~5200 行 / 26 模块
- `conversation_engine.py`：前置防线 + 三轮调度 + 降级兜底

---

## [0.7.x 系列] — 2026-04-28 ~ 2026-05-11

### [0.7.5]
- 对话生成引擎 8 步流程
- 12 位场景码设计（6 维度编码）
- 512 条内置语料标注完成

### [0.7.4]
- 命令系统改造（`/xiaomei *` 前缀）
- 版本号显示修复

### [0.7.0]
- 首次发布包（~152KB）
- 好感度系统 + 记忆引擎基础版

---

## [0.4.x ~ 0.6.x 系列] — 2026-04-27 ~ 2026-04-28

MVP 初期迭代，核心功能快速上线：
- 基础对话引擎 + 情绪系统
- 礼物互动模块
- 敏感词检测
- 首次启动引导

---

[0.9.0]: https://github.com/xavier7803/xiaomei-skill/releases/tag/v0.9.0
[0.8.1]: https://github.com/xavier7803/xiaomei-skill/releases/tag/v0.8.1
[0.8.0]: https://github.com/xavier7803/xiaomei-skill/releases/tag/v0.8.0
[0.7.5]: https://github.com/xavier7803/xiaomei-skill/releases/tag/v0.7.5
[0.7.4]: https://github.com/xavier7803/xiaomei-skill/releases/tag/v0.7.4
[0.7.0]: https://github.com/xavier7803/xiaomei-skill/releases/tag/v0.7.0
