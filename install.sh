#!/bin/bash
# 小妹技能包 v0.8.1 安装脚本
# 用途：将发布包安装到 OpenClaw 技能目录，注册 subagent，初始化 agent 目录
set -e

SKILL_NAME="xiaomei"
SKILL_DIR="${HOME}/.openclaw/skills/${SKILL_NAME}"
AGENT_DIR="${HOME}/.openclaw/agents/${SKILL_NAME}"
CONFIG_PATH="${HOME}/.openclaw/openclaw.json"
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🥰 小妹技能包 v0.8.1 安装中..."
echo ""

# ── 步骤1：复制发布包到 skills 目录 ──
echo "📦 步骤1/4：复制技能包到 ${SKILL_DIR} ..."
if [ "$SRC_DIR" != "$SKILL_DIR" ]; then
    mkdir -p "$SKILL_DIR"
    rsync -av --delete \
        --exclude='__pycache__' --exclude='*.pyc' \
        --exclude='.brv' --exclude='Release_Versions' \
        "$SRC_DIR/" "$SKILL_DIR/" 2>&1 | tail -1
    echo "   ✅ 已复制"
else
    echo "   ✅ 已在目标目录，跳过"
fi

# ── 步骤2：注册 agent（如未注册） ──
echo "🔧 步骤2/4：检查 agent 注册 ..."
if [ -f "$CONFIG_PATH" ]; then
    if ! python3 -c "
import json, sys
with open('$CONFIG_PATH') as f:
    cfg = json.load(f)
agents = cfg.get('agents', {}).get('list', [])
if any(a.get('id') == '$SKILL_NAME' for a in agents):
    sys.exit(1)
" 2>/dev/null; then
        echo "   ✅ 已注册"
    else
        echo "   ⚠️  未在 openclaw.json 中注册。请手动添加 agent 条目（参见 SKILL.md）"
    fi
else
    echo "   ⚠️  openclaw.json 不存在，请先安装 OpenClaw"
fi

# ── 步骤3：初始化 agent 目录 ──
echo "📋 步骤3/4：初始化 agent 数据目录 ..."
mkdir -p "$AGENT_DIR"
TEMPLATE_DIR="${SKILL_DIR}/agent-config/templates"
if [ -f "${TEMPLATE_DIR}/persona.json" ] && [ ! -f "${AGENT_DIR}/persona.json" ]; then
    cp "${TEMPLATE_DIR}/persona.json" "${AGENT_DIR}/persona.json"
    echo "   ✅ persona.json 已从模板初始化"
else
    echo "   ✅ persona.json 已存在或模板不可用，跳过"
fi
if [ -f "${TEMPLATE_DIR}/user_profile.json" ] && [ ! -f "${AGENT_DIR}/user_profile.json" ]; then
    cp "${TEMPLATE_DIR}/user_profile.json" "${AGENT_DIR}/user_profile.json"
    echo "   ✅ user_profile.json 已从模板初始化"
else
    echo "   ✅ user_profile.json 已存在或模板不可用，跳过"
fi

# ── 步骤4：验证 ──
echo "🧪 步骤4/4：验证安装 ..."
if python3 -c "import json; json.load(open('${AGENT_DIR}/persona.json'))" 2>/dev/null; then
    echo "   ✅ persona.json 可正常解析"
else
    echo "   ❌ persona.json 解析失败"
fi

echo ""
echo "═══════════════════════════════════"
echo "  🥰 小妹技能包 v0.8.1 安装完成！"
echo "═══════════════════════════════════"
echo ""
echo "  下一步："
echo "    1. 确保已在 ~/.openclaw/openclaw.json 中注册 agent"
echo "    2. 重启 OpenClaw 网关：openclaw gateway restart"
echo "    3. 在控制面板找到「小妹🥰」开始对话"
