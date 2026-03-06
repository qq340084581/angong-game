vboxuser@Kivy-Builder:/media/sf_sangong$ cat > fix.sh << 'EOF'
#!/bin/bash
# 修复权限问题
sudo chmod -R 755 /media/sf_sangong
# 创建本地缓存目录
mkdir -p ~/.buildozer
# 确保可以使用共享文件夹中的文件
find /media/sf_sangong -type f -name "*.py" -exec chmod 644 {} \;
find /media/sf_sangong -type f -name "*.png" -exec chmod 644 {} \;
find /media/sf_sangong -type f -name "*.jpg" -exec chmod 644 {} \;
find /media/sf_sangong -type f -name "*.mp3" -exec chmod 644 {} \;
echo "权限修复完成"
EOF

chmod +x fix.sh
./fix.sh