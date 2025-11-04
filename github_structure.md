# GitHub 项目结构说明

这个文档说明了如何将Pexels 4K视频下载器项目托管到GitHub上。

## 项目文件结构

```
Pexels/
├── .gitignore              # Git忽略文件
├── CONTRIBUTING.md         # 贡献指南
├── LICENSE                 # MIT许可证
├── README.md               # 项目说明文档
├── enhanced_pexels_downloader.py  # 主程序文件
├── launch.bat              # 简化版启动脚本
├── python/                 # 内置Python环境
│   ├── python.exe          # Python解释器
│   ├── Lib/                # 标准库
│   └── ...                 # 其他Python文件
├── requirements.txt        # Python依赖包列表
└── start.bat               # 完整版启动脚本
```

## 托管到GitHub的步骤

1. 在GitHub上创建一个新的仓库
2. 克隆仓库到本地：
   ```bash
   git clone https://github.com/yourusername/pexels-4k-video-downloader.git
   ```
3. 将项目文件复制到仓库目录中
4. 添加文件到Git：
   ```bash
   git add .
   ```
5. 提交更改：
   ```bash
   git commit -m "Initial commit: Pexels 4K Video Downloader"
   ```
6. 推送到GitHub：
   ```bash
   git push origin main
   ```

## 注意事项

- 由于内置Python环境较大，首次推送可能需要较长时间
- 建议在GitHub Release中提供预编译的可执行文件版本
- 可以使用GitHub Actions来自动化构建过程