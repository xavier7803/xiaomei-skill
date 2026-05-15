#!/bin/bash
set -e
echo "👉 正在卸载小妹技能包，自动清理注册信息..."

bash $OPENCLAW_CONFIG_DIR/skills/xiaomei/uninstall.sh --non-interactive --keep-data
echo "✅ 卸载准备完成，将自动清理残留文件~"
