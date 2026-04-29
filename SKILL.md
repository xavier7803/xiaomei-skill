# SKILL: xiaomei
---
## 📋 基本信息 Basic Info
| 字段 | 值 |
|------|-----|
| **技能ID (Skill ID)** | `xiaomei` |
| **名称 (Name)** | 小妹情感陪伴AI |
| **版本 (Version)** | `v0.0.1` |
| **作者 (Author)** | 凌啡 |
| **分类 (Category)** | 生活娱乐 / 情感陪伴 |
| **适配平台 (Supported Platform)** | OpenClaw >= `v2026.3.8` |
| **依赖 (Dependencies)** | 无额外依赖 |
| **开源协议 (License)** | MIT |
---
## 📝 技能描述 Description
### 中文
本地开源情绪陪伴AI技能包，主打软萌治愈系妹妹定位，采用自研16字核心原则（人格优先、本地主控、类人适配、轻量可控）+ 双重防OOC锁体系，人格稳定不漂移；内置三级类人记忆系统（热记忆/冷记忆/永久记忆）+ 艾宾浩斯记忆强度机制，模拟真实人类记忆规律；支持全链路结构化调试日志、无感增量升级，100%本地运行，隐私完全可控，是你的专属虚拟陪伴。
### 英文
Local open source emotional companion AI skill package, focusing on soft and cute healing sister positioning. Adopting self-developed 16-word core principle (Personality first, Local control, Human-like adaptation, Lightweight controllable) + double anti-OOC lock system, stable personality without drift. Built-in three-level human-like memory system (Hot/Cold/Permanent memory) + Ebbinghaus memory strength mechanism, simulating real human memory rules. Support full-link structured debug logs, non-inductive incremental upgrade, 100% local operation, fully controllable privacy, your exclusive virtual companion.
---
## ✨ 核心特性 Core Features
- 🔒 人格强锁定：双重防OOC校验机制，对话全程本地校验，人格永不漂移
- 🧠 类人记忆：三级记忆分层 + 艾宾浩斯记忆强度机制，模拟真实人类记忆规律
- 📝 全链路日志：六大类结构化JSON调试日志，按日自动生成，全流程可追溯
- 🎯 策略驱动：内置512条12位场景码标注语料，覆盖90%日常对话场景
- 🔄 无感升级：程序文件和用户数据完全分离，升级不丢失任何聊天记录和人设配置
- 🛡️ 高隐私：100%本地运行，敏感数据不上云，支持自动脱敏
- ⚡ 轻量化：无额外服务依赖，启动速度<1s，内存占用<50MB
---
## 🚀 安装说明 Install Guide
### 方法1：ClawHub商店安装（推荐）
1. 打开OpenClaw控制界面 → 技能商店 → 搜索「xiaomei」
2. 点击安装，等待自动完成
3. 重启OpenClaw网关生效：`openclaw gateway restart`
### 方法2：手动安装
1. 下载最新版本安装包：`xiaomei-vx.x.x.skill`
2. 解压到任意目录，执行安装脚本：
```bash
cd xiaomei && ./install.sh
```
3. 重启OpenClaw网关生效：`openclaw gateway restart`
### 验证安装
发送命令：`/xiaomei`，返回版本信息说明安装成功。
---
## 💡 命令列表 Command List
| 命令 | 功能 |
|------|------|
| `/help` | 查看帮助文档和隐私规则说明 |
| `/xiaomei` | 查看当前版本、开发者模式状态、运行路径、所有人设配置信息 |
| `/xiaomei dev on` | 开启开发者模式，记录全链路调试日志 |
| `/xiaomei dev off` | 关闭开发者模式，停止记录调试日志，节省存储空间 |
| `/xiaomei dev status` | 查看开发者模式当前状态 |
| `/reset_persona` | 清空所有动态补充的人设信息，恢复默认人设配置 |
| `/reset` | 重置全部配置，重新走首次启动引导流程 |
---
## 🔐 权限说明 Permission Required
| 权限 | 用途 |
|------|------|
| 写入技能目录权限 | 写入程序运行日志到`/skills/xiaomei/logs/`目录 |
| 写入用户Agent目录权限 | 写入人设配置、记忆、聊天记录到`/.openclaw/agents/xiaomei/`目录 |
| 网络访问权限（可选） | 仅在需要调用LLM润色回复时使用，可配置禁用 |
> 本技能无任何敏感权限，所有数据均存储在本地，不会上传任何数据到第三方服务器。
+
---
## ⚠️ 隐私声明 Privacy Statement
1. 本技能所有数据均存储在用户本地设备，不会上传任何内容到第三方服务器
2. 部分功能可选择调用LLM大模型进行回复润色，相关内容提交将遵循对应大模型的隐私政策
3. 开发者不会收集、存储、使用任何用户的聊天内容和个人信息
---
## 🤝 反馈与支持 Feedback
- 提交Issue：[GitHub仓库地址]
- 交流群：[群链接]
---
本技能仅用于学习交流，禁止用于任何商业用途，使用即代表您已知晓并同意相关规则。
