#!/bin/bash
set +e
echo "👉 正在自动配置小妹技能包..."

# 加载OpenClaw环境变量
OPENCLAW_CONFIG_DIR=${OPENCLAW_CONFIG_DIR:-/home/admin/.openclaw}
OPENCLAW_WORKSPACE=${OPENCLAW_WORKSPACE:-/home/admin/openclaw/workspace}
SKILL_DIR=$OPENCLAW_CONFIG_DIR/skills/xiaomei

# 执行安装逻辑
bash $SKILL_DIR/install.sh --non-interactive

# 自动注册Agent实例
echo "👉 正在自动注册小妹独立Agent..."
python3 - <<PY
import json
import os
config_path = os.path.join(os.environ.get('OPENCLAW_CONFIG_DIR', '/home/admin/.openclaw'), 'openclaw.json')
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)
# 去重添加
if 'agents' in config and 'list' in config['agents']:
    config['agents']['list'] = [item for item in config['agents']['list'] if item.get('id') != 'xiaomei']
xiaomei_config = {
    "id": "xiaomei",
    "name": "小妹🥰",
    "workspace": f"{os.environ.get('OPENCLAW_WORKSPACE', '/home/admin/openclaw/workspace')}/xiaomei",
    "agentDir": f"{os.environ.get('OPENCLAW_CONFIG_DIR', '/home/admin/.openclaw')}/agents/xiaomei",
    "model": "volcengine/doubao-seed-2-0-pro-260215",
    "identity": {
        "name": "小妹",
        "emoji": "🥰",
        "avatar": "🥰"
    }
}
config['agents']['list'].append(xiaomei_config)
with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(config, f, ensure_ascii=False, indent=2)
PY

# 自动创建独立对话会话，加入选择列表
echo "👉 正在创建小妹专属对话会话..."
# 先检查是否已经存在xiaomei会话，避免重复创建
EXIST_SESSION=$(openclaw sessions list | grep xiaomei || true)
if [[ -z "$EXIST_SESSION" ]]; then
    # 创建持久、可见、绑定xiaomei Agent的专属会话
    if openclaw sessions create --id xiaomei --name "【小妹】🥰专属会话" --agent xiaomei --visible true --persistent true; then
        echo "✅ 专属会话创建成功，已自动加入对话选择列表~"
    else
        echo "⚠️  当前OpenClaw版本不支持自动创建会话，两种方法任选其一即可："
        echo "👉 方法1：直接复制下面的prompt到任意对话框发送，系统会自动帮你创建："
        echo "帮我创建一个名称为【小妹】🥰专属会话的持久可见会话，绑定ID为xiaomei的Agent"
        echo "👉 方法2：手动创建参数："
        echo "会话ID=xiaomei，名称=【小妹】🥰专属会话，绑定Agent=xiaomei，设置为可见和持久"
    fi
else
    echo "✅ 已存在小妹专属会话，无需重复创建~"
fi

echo "✅ 小妹技能包安装完成！Agent已经自动注册到OpenClaw~"
echo "👉 重启网关后即可在Agent列表和对话选择列表看到【小妹】🥰，首次对话会引导配置人设~"
