#!/bin/bash
# Ubuntu 系统一键设置中文语言脚本（适用于 20.04 ~ 25.10）

set -e  # 遇到错误立即退出

echo "=== 开始设置 Ubuntu 系统语言为中文 ==="

# 检查是否有 root 权限
if [ "$EUID" -ne 0 ]; then 
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

# 更新软件源
apt update

# 安装中文语言包
echo "安装中文语言包..."
apt install -y language-pack-zh-hans

# 安装语言支持工具（如果尚未安装）
apt install -y language-selector-common

# 生成中文 locale
echo "生成中文 locale..."
locale-gen zh_CN.UTF-8

# 设置系统默认语言
echo "配置系统默认语言..."
update-locale LANG=zh_CN.UTF-8 LANGUAGE=zh_CN:zh LC_ALL=zh_CN.UTF-8

# 可选：安装中文字体（防止显示方块）
apt install -y fonts-noto-cjk

# 配置语言支持（自动选择汉语）
if command -v language-selector > /dev/null; then
    language-selector set-language 汉语
fi

echo "✅ 语言设置完成！"
echo "⚠️ 请重启系统（或注销重新登录）使更改生效。"