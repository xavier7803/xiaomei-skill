# 小妹技能包 OpenClaw 一键安装指引
## 方式一：后台控制面板安装（推荐）
1. 打开OpenClaw控制后台 → 技能商店 → 上传技能
2. 选择 `xiaomei-v1.4.0.skill` 安装包上传
3. 点击「安装」，系统会自动完成所有配置、Agent注册
4. 重启OpenClaw网关，在「我的Agent」列表即可看到「小妹🥰」
5. 首次和小妹对话，会自动触发引导流程配置人设

## 方式二：命令行一键安装
```bash
# 上传安装包到服务器后执行
openclaw skills install ./xiaomei-v1.4.0.skill
# 重启网关生效
openclaw gateway restart
```

## 方式三：手动安装
```bash
# 解压安装包
tar -xzf xiaomei-v1.4.0.skill
cd xiaomei-v1.4.0
# 执行安装脚本
bash install.sh
# 重启网关
openclaw gateway restart
```

## 验证安装
安装完成后执行：
```bash
openclaw skills list | grep xiaomei
openclaw agents list | grep xiaomei
```
看到小妹的信息说明安装成功！

## 卸载
```bash
# 后台控制面板直接点击卸载即可
# 或者命令行卸载
openclaw skills uninstall xiaomei
```
