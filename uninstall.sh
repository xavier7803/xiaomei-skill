#!/bin/bash
set -e
NON_INTERACTIVE=0
KEEP_DATA=0
# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --non-interactive)
            NON_INTERACTIVE=1
            shift
            ;;
        --keep-data)
            KEEP_DATA=1
            shift
            ;;
        *)
            shift
            ;;
    esac
done
# 交互模式下询问用户
if [[ $NON_INTERACTIVE == 0 ]]; then
    echo "⚠️  即将卸载小妹技能包，请选择卸载模式："
    read -p "🤔 是否需要保留小妹的记忆、人设配置文件？(y/n，默认n完全清除)：" CHOICE
    CHOICE=${CHOICE:-n}
    if [[ $CHOICE =~ ^[Yy]$ ]]; then
        KEEP_DATA=1
        echo "✅ 已选择保留记忆和配置文件，仅卸载程序和注册信息~"
    else
        KEEP_DATA=0
        echo "⚠️  已选择完全卸载，所有记忆、配置、数据将被永久清除，不可恢复！"
        sleep 2
    fi
fi
# 停止可能运行的小妹相关进程
echo "👉 正在停止小妹Agent进程..."
pkill -f "xiaomei.*agent" || true
pkill -f "first_launch.py" || true
# 清理技能安装目录
echo "👉 正在清理技能程序文件..."
rm -rf /home/admin/.openclaw/skills/xiaomei/
# 清理独立Agent配置目录（运行时配置，不影响用户数据）
echo "👉 正在删除Agent注册配置..."
rm -rf /home/admin/.openclaw/agents/xiaomei/
# 清理独立工作目录（根据用户选择）
if [[ $KEEP_DATA == 0 ]]; then
    echo "👉 正在删除所有数据（记忆/日志/配置）..."
    rm -rf /home/admin/openclaw/workspace/xiaomei/
else
    echo "👉 已保留记忆和配置文件，工作目录数据不会删除~"
fi
# 从全局Agent列表中移除xiaomei
echo "👉 正在注销Agent注册信息..."
CONFIG_FILE="/home/admin/.openclaw/openclaw.json"
if [ -f "$CONFIG_FILE" ]; then
    python3 -c "
import json
with open('$CONFIG_FILE', 'r', encoding='utf-8') as f:
    config = json.load(f)
if 'agents' in config and 'list' in config['agents']:
    config['agents']['list'] = [item for item in config['agents']['list'] if item.get('id') != 'xiaomei']
with open('$CONFIG_FILE', 'w', encoding='utf-8') as f:
    json.dump(config, f, ensure_ascii=False, indent=2)
"
fi
# 清理可能残留的临时文件/标记
echo "👉 正在清理残留缓存文件..."
rm -rf /tmp/xiaomei_* || true
rm -rf /tmp/.xiaomei_* || true
echo ""
echo "✅ 小妹技能包卸载完成！"
if [[ $KEEP_DATA == 1 ]]; then
    echo "👉 记忆和配置文件已保留在：/home/admin/openclaw/workspace/xiaomei/"
fi
echo "👉 重启OpenClaw网关即可完全清除Agent列表中的小妹项~"
