# 自动字幕管理器 (Subtitle Manager)

一个自动检测和下载中文字幕的 Docker 服务，专为 Unraid NAS 设计，可与 Plex 和 NASTools 配合使用。

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Docker](https://img.shields.io/badge/docker-supported-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

## 功能特性

- **自动检测**: 监控目录中的新电影文件，自动检测是否缺少中文字幕
- **智能搜索**: 从多个字幕源（SubHD、字幕库、OpenSubtitles）搜索匹配的字幕
- **自动下载**: 自动下载最匹配的中文字幕到电影目录
- **实时监控**: 支持目录监控，nastools 生成硬链接后立即处理
- **定时扫描**: 可配置定时扫描间隔，确保不遗漏任何文件
- **失败重试**: 下载失败自动重试，最多重试3次
- **并发处理**: 支持并发下载，提高效率
- **历史记录**: 保存处理历史，避免重复处理
- **Web 界面**: 苹果风格的现代化管理界面
- **批量上传**: 支持电视剧字幕批量上传（S01E01格式自动匹配）

## 支持的格式

### 视频格式
- MKV, MP4, AVI, MOV, WMV, FLV, M4V

### 字幕格式
- SRT, ASS, SSA, VTT, SUB

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    字幕管理器系统                            │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Web 界面   │  │   API 服务   │  │  目录监控    │       │
│  │  (Vue.js)    │  │  (FastAPI)   │  │  (Watcher)   │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                 │               │
│         └─────────────────┼─────────────────┘               │
│                           │                                 │
│              ┌────────────┴────────────┐                   │
│              │    字幕管理器核心        │                   │
│              │   (Subtitle Manager)     │                   │
│              └────────────┬────────────┘                   │
│                           │                                 │
│         ┌─────────────────┼─────────────────┐              │
│         │                 │                 │               │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐        │
│  │   SubHD     │  │   字幕库    │  │OpenSubtitles│        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 方法一：使用 PowerShell 部署脚本（推荐 Windows 用户）

```powershell
# 1. 进入项目目录
cd subtitle-manager

# 2. 构建 Docker 镜像
.\deploy.ps1 -Build

# 3. 启动服务
.\deploy.ps1 -Start

# 4. 访问 Web 界面
# http://localhost:8080
```

### 方法二：使用 Docker Compose

```bash
# 1. 克隆或下载项目
cd subtitle-manager

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置你的媒体目录

# 3. 构建并启动
docker-compose up -d --build

# 4. 查看日志
docker-compose logs -f
```

### 方法三：本地开发环境

```bash
# 1. 安装 Python 依赖
pip install -r requirements.txt

# 2. 安装前端依赖
cd web
npm install
npm run build
cd ..

# 3. 启动服务
python start_server.py
```

## 配置说明

### 环境变量

编辑 `.env` 文件配置系统：

```env
# 监控目录（多个目录用逗号分隔）
WATCH_DIRS=/movies,/tvshows

# 扫描间隔（分钟）
SCAN_INTERVAL=30

# 文件大小阈值（MB），小于此值的文件跳过
MIN_FILE_SIZE_MB=100

# 字幕源配置
SUBTITLE_SOURCES=subhd,zimuku,opensubtitles

# OpenSubtitles API 配置（可选）
OPENSUBTITLES_API_KEY=your_api_key
OPENSUBTITLES_USERNAME=your_username
OPENSUBTITLES_PASSWORD=your_password

# 是否启用自动下载
AUTO_DOWNLOAD=true

# 下载前是否备份原字幕
BACKUP_EXISTING_SUBTITLE=false

# 最大并发下载数
MAX_CONCURRENT_DOWNLOADS=3

# 日志级别
LOG_LEVEL=INFO
```

### Docker Compose 配置

```yaml
version: '3.8'

services:
  subtitle-manager:
    build: .
    container_name: subtitle-manager
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - WATCH_DIRS=/movies,/tvshows
      - SCAN_INTERVAL=30
      - AUTO_DOWNLOAD=true
    volumes:
      - /path/to/movies:/movies
      - /path/to/tvshows:/tvshows
      - ./logs:/app/logs
      - ./data:/app/data
```

## 使用指南

### Web 界面

启动服务后访问 http://localhost:8080

#### 1. 仪表盘
- 查看统计信息（电影/电视剧数量、字幕状态）
- 查看最近活动记录
- 查看任务队列状态

#### 2. 电影管理
- 浏览电影库
- 查看字幕状态
- 手动搜索字幕
- 下载字幕

#### 3. 电视剧管理
- 浏览电视剧库
- 按季查看剧集
- 查看每集字幕状态
- 批量上传字幕

#### 4. 批量上传字幕
1. 选择电视剧和季数
2. 上传字幕文件（文件名需包含 S01E01 格式）
3. 系统自动匹配字幕到对应剧集
4. 确认匹配结果并上传

#### 5. 设置
- 配置监控目录
- 设置扫描间隔
- 配置字幕源
- 配置 API 密钥

### API 接口

服务提供完整的 RESTful API：

```
GET  /api/stats              # 获取统计信息
GET  /api/movies             # 获取电影列表
POST /api/movies/{id}/search-subtitles  # 搜索字幕
POST /api/movies/{id}/download-subtitle # 下载字幕
GET  /api/tvshows            # 获取电视剧列表
POST /api/batch-upload-subtitles        # 批量上传字幕
GET  /api/settings           # 获取设置
POST /api/settings           # 更新设置
POST /api/scan               # 触发扫描
GET  /health                 # 健康检查
```

完整 API 文档访问：http://localhost:8080/docs

## 目录结构

```
subtitle-manager/
├── subtitle_sources/       # 字幕源实现
│   ├── __init__.py
│   ├── subhd.py           # SubHD 字幕源
│   ├── zimuku.py          # 字幕库
│   └── opensubtitles.py   # OpenSubtitles
├── web/                   # 前端项目
│   ├── src/
│   │   ├── components/    # Vue 组件
│   │   ├── router/        # 路由配置
│   │   ├── stores/        # Pinia 状态管理
│   │   └── views/         # 页面视图
│   ├── package.json
│   └── vite.config.js
├── api_server.py          # FastAPI 服务
├── config.py              # 配置管理
├── docker-compose.yml     # Docker 编排
├── Dockerfile             # Docker 镜像
├── main.py                # 主入口
├── requirements.txt       # Python 依赖
├── subtitle_manager.py    # 核心管理器
├── utils.py               # 工具函数
├── watcher.py             # 目录监控
├── deploy.ps1             # Windows 部署脚本
└── README.md              # 说明文档
```

## 与 NASTools 集成

1. 配置 NASTools 的硬链接目录
2. 将硬链接目录映射到字幕管理器的监控目录
3. 当 NASTools 下载新电影时，字幕管理器会自动检测并下载字幕

## 与 Plex 集成

1. 确保 Plex 的媒体库目录与字幕管理器的监控目录一致
2. 字幕管理器下载的字幕会自动保存到视频文件所在目录
3. Plex 会自动识别同目录下的字幕文件

## 故障排除

### Docker 服务无法启动

```bash
# 检查 Docker 日志
docker-compose logs

# 检查端口占用
netstat -ano | findstr :8080

# 重启服务
docker-compose restart
```

### 字幕搜索失败

1. 检查网络连接
2. 检查字幕源配置
3. 查看日志获取详细信息

### 前端无法访问

1. 检查后端服务是否正常运行
2. 检查端口映射配置
3. 检查防火墙设置

## 开发计划

- [x] 基础字幕检测和下载
- [x] Web 管理界面
- [x] 批量上传字幕功能
- [x] Docker 支持
- [ ] 更多字幕源支持
- [ ] 字幕翻译功能
- [ ] 字幕同步调整
- [ ] 移动端适配

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 致谢

- [FastAPI](https://fastapi.tiangolo.com/)
- [Vue.js](https://vuejs.org/)
- [Element Plus](https://element-plus.org/)
- [Docker](https://www.docker.com/)
