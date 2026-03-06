[app]
# 应用名称（英文）
title = Sangong

# 包名（唯一标识）
package.name = sangong
package.domain = org.example

# 源文件
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,txt,mp3,ttf

# 版本
version = 0.1
version.regex = __version__ = ['"](.*)['"]
version.filename = %(source.dir)s/main.py

# 需求库（重要！）
requirements = python3,kivy,requests,websocket-client

# 应用图标和启动画面（可选）
# icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/splash.png

# 权限（需要网络）
android.permissions = INTERNET

# 支持的架构（默认armeabi-v7a即可）
android.archs = armeabi-v7a, arm64-v8a

# 语言和编码
android.accept_sdk_license = True
osx.python_version = 3
osx.kivy_version = 2.1.0

# 资源文件（字体、图片等会自动包含，但可额外指定）
# 无需额外设置，只要文件在source.dir内且扩展名在source.include_exts中即可

[buildozer]
log_level = 2
warn_on_root = 1