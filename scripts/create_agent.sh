#!/bin/bash
echo "👉 正在创建小妹独立Agent实例..."
# 自动添加到Agent列表
python3 - <<PY
import json
import os
config_path = os.path.join(os.environ.get('OPENCLAW_CONFIG_DIR', '/home/admin/.openclaw'), 'openclaw.json')
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)
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
echo "✅ 小妹Agent创建成功！重启网关生效~"
