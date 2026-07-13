# 历史项目记忆

> 这份文档保留了早期设计记录，可能与当前仓库结构不完全一致。当前目录结构请以 `README.md` 为准。

# 字幕管理器 (Subtitle Manager) - 项目记忆文档

> **版本**: 1.0.0  
> **最后更新**: 2026-03-14  
> **维护者**: alexwjxing  

---

## 📑 目录

1. [项目概述](#1-项目概述)
2. [项目结构](#2-项目结构)
3. [技术栈](#3-技术栈)
4. [架构设计](#4-架构设计)
5. [核心模块](#5-核心模块)
6. [API 接口](#6-api-接口)
7. [配置说明](#7-配置说明)
8. [部署指南](#8-部署指南)
9. [开发规范](#9-开发规范)
10. [已知问题](#10-已知问题)

---

## 1. 项目概述

### 1.1 项目简介

字幕管理器是一个自动化中文字幕下载和管理工具，专为 NAS 和媒体服务器设计。支持电影、电视剧、动漫的字幕自动搜索、下载和管理。

### 1.2 主要功能

- **多类型支持**: 电影、电视剧、动漫字幕管理
- **智能搜索**: 集成多个字幕源（SubHD、射手网、OpenSubtitles、Assrt）
- **自动下载**: 监控目录变化，自动搜索并下载缺失字幕
- **NASTool 对接**: 支持 NASTool Webhook，实现自动化字幕下载
- **智能匹配**: 基于文件名、TMDB 信息智能匹配最佳字幕
- **多格式支持**: SRT、ASS、SSA、VTT 等主流字幕格式
- **现代界面**: Vue 3 + Element Plus 构建的 Web 管理界面

### 1.3 项目状态

- **当前版本**: 1.0.0
- **Docker 镜像**: `alexwjxing/subtitle-manager:latest`
- **状态**: 稳定运行中

---

## 2. 项目结构

```
subtitle-manager/
├── 📁 web/                          # 前端项目
│   ├── 📁 src/
│   │   ├── 📁 views/               # 页面组件
│   │   │   ├── Movies.vue          # 电影管理页面
│   │   │   ├── TVShows.vue         # 电视剧管理页面
│   │   │   ├── Anime.vue           # 动漫管理页面
│   │   │   ├── Settings.vue        # 设置页面
│   │   │   ├── Dashboard.vue       # 仪表盘页面
│   │   │   └── BatchUpload.vue     # 批量上传页面
│   │   ├── 📁 components/          # 公共组件
│   │   │   └── Sidebar.vue         # 侧边栏导航
│   │   ├── App.vue                 # 根组件
│   │   └── main.js                 # 入口文件
│   ├── package.json                # 前端依赖
│   └── vite.config.js              # Vite 配置
│
├── 📁 subtitle_sources/            # 字幕源实现
│   ├── __init__.py                 # 字幕源管理器
│   ├── subhd.py                    # SubHD 字幕源
│   ├── shooter.py                  # 射手网字幕源
│   ├── opensubtitles.py            # OpenSubtitles 字幕源
│   ├── assrt.py                    # Assrt 字幕源
│   └── captcha_solver.py           # 验证码识别
│
├── 📄 api_server.py                # FastAPI 后端服务
├── 📄 subtitle_manager.py          # 字幕管理器核心
├── 📄 config.py                    # 配置管理
├── 📄 config_manager.py            # 配置持久化
├── 📄 tmdb_api.py                  # TMDB API 接口
├── 📄 nastool_webhook.py           # NASTool Webhook 处理
├── 📄 watcher.py                   # 目录监控
├── 📄 utils.py                     # 工具函数
├── 📄 nfo_parser.py                # NFO 文件解析
├── 📄 main.py                      # 主入口
│
├── 📄 Dockerfile                   # Docker 构建文件
├── 📄 docker-compose.yml           # Docker Compose 配置
├── 📄 docker-compose.unraid.yml    # Unraid 专用配置
├── 📄 requirements.txt             # Python 依赖
├── 📄 PROJECT_MEMORY.md            # 本文件
└── 📄 DOCKER_HUB_README.md         # Docker Hub 说明
```

---

## 3. 技术栈

### 3.1 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.11 | 编程语言 |
| **FastAPI** | >=0.104.0 | Web 框架 |
| **Uvicorn** | >=0.24.0 | ASGI 服务器 |
| **Pydantic** | >=2.0.0 | 数据验证 |
| **Pydantic-Settings** | >=2.0.0 | 配置管理 |
| **AIOHTTP** | >=3.8.0 | 异步 HTTP 客户端 |
| **BeautifulSoup4** | >=4.12.0 | HTML 解析 |
| **Loguru** | >=0.7.0 | 日志记录 |
| **Watchdog** | >=3.0.0 | 文件系统监控 |

### 3.2 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| **Vue** | 3.4.0 | 前端框架 |
| **Element Plus** | 2.5.0 | UI 组件库 |
| **Vue Router** | 4.2.0 | 路由管理 |
| **Pinia** | 2.1.0 | 状态管理 |
| **Axios** | 1.6.0 | HTTP 客户端 |
| **Vite** | 5.4.21 | 构建工具 |
| **Sass** | 1.70.0 | CSS 预处理器 |

### 3.3 部署技术栈

| 技术 | 用途 |
|------|------|
| **Docker** | 容器化 |
| **Docker Compose** | 容器编排 |
| **GitHub Actions** | CI/CD（可选） |

---

## 4. 架构设计

### 4.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户层                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Web 界面   │  │  NASTool   │  │   API 调用   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
└─────────┼────────────────┼────────────────┼────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                      API 服务层 (FastAPI)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  电影 API   │  │  电视剧 API  │  │  设置 API   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Webhook API │  │  字幕 API   │  │  状态 API   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     业务逻辑层                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              SubtitleManager (字幕管理器)            │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  目录监控   │  │  字幕搜索   │  │  字幕下载   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     数据源层                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │    SubHD    │  │   射手网    │  │OpenSubtitles│         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│  ┌─────────────┐  ┌─────────────┐                          │
│  │    Assrt    │  │    TMDB     │                          │
│  └─────────────┘  └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 数据流图

```
用户操作 → API 接口 → SubtitleManager → 字幕源 → 下载字幕 → 保存到磁盘
                ↓
            配置管理 → 持久化到 /app/data/.env.backup
```

### 4.3 核心组件关系

```
api_server.py
    ├── SubtitleManager (subtitle_manager.py)
    │       ├── 字幕源管理器 (subtitle_sources/__init__.py)
    │       │       ├── SubHDSource (subhd.py)
    │       │       ├── ShooterSource (shooter.py)
    │       │       ├── OpenSubtitlesSource (opensubtitles.py)
    │       │       └── AssrtSource (assrt.py)
    │       ├── TMDB API (tmdb_api.py)
    │       └── 配置管理 (config.py)
    ├── NASTool Webhook (nastool_webhook.py)
    └── 配置管理 (config.py)
```

---

## 5. 核心模块

### 5.1 api_server.py

**职责**: FastAPI 应用入口，提供 RESTful API 接口

**主要功能**:
- 启动 FastAPI 服务
- 注册路由和中间件
- 处理 HTTP 请求
- 静态文件服务

**关键类/函数**:
- `app`: FastAPI 应用实例
- `startup_event()`: 应用启动事件处理

### 5.2 subtitle_manager.py

**职责**: 字幕管理器核心逻辑

**主要功能**:
- 扫描媒体文件
- 搜索字幕
- 下载字幕
- 管理处理历史

**关键类**:
- `SubtitleManager`: 字幕管理器主类
  - `scan_movies()`: 扫描电影
  - `scan_tvshows()`: 扫描电视剧
  - `search_subtitles()`: 搜索字幕
  - `download_subtitle()`: 下载字幕
  - `update_settings()`: 更新设置

### 5.3 config.py

**职责**: 配置管理

**主要功能**:
- 加载环境变量
- 配置验证
- 配置持久化
- 配置热重载

**关键类/函数**:
- `Settings`: 配置类
- `load_settings()`: 加载配置
- `reload_settings()`: 重新加载配置
- `restore_config_from_backup()`: 从备份恢复

### 5.4 subtitle_sources/

**职责**: 字幕源实现

**模块列表**:
| 模块 | 功能 | 状态 |
|------|------|------|
| `subhd.py` | SubHD 字幕源 | ✅ 可用 |
| `shooter.py` | 射手网字幕源 | ✅ 可用 |
| `opensubtitles.py` | OpenSubtitles | ✅ 可用 |
| `assrt.py` | Assrt 字幕源 | ✅ 可用 |

**基类**:
- `SubtitleSource`: 字幕源基类
  - `search()`: 搜索字幕
  - `download()`: 下载字幕

### 5.5 tmdb_api.py

**职责**: TMDB API 接口

**主要功能**:
- 搜索电影/电视剧信息
- 获取元数据
- 匹配视频文件

**关键函数**:
- `init_tmdb_api()`: 初始化 API
- `search_movie()`: 搜索电影
- `search_tv_show()`: 搜索电视剧

### 5.6 nastool_webhook.py

**职责**: NASTool Webhook 处理

**主要功能**:
- 接收 NASTool 通知
- 解析事件数据
- 触发字幕下载

**关键类**:
- `NASToolWebhookHandler`: Webhook 处理器
  - `handle_webhook()`: 处理 Webhook 请求

### 5.7 watcher.py

**职责**: 目录监控

**主要功能**:
- 监控媒体目录变化
- 自动触发扫描
- 文件系统事件处理

---

## 6. API 接口

### 6.1 电影相关 API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/movies` | 获取电影列表 |
| GET | `/api/movies/{id}` | 获取电影详情 |
| POST | `/api/movies/{id}/search-subtitles` | 搜索字幕 |
| POST | `/api/movies/{id}/download-subtitle` | 下载字幕 |

### 6.2 电视剧相关 API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/tvshows` | 获取电视剧列表 |
| GET | `/api/tvshows/{id}` | 获取电视剧详情 |
| POST | `/api/tvshows/{id}/scan` | 扫描剧集 |
| POST | `/api/tvshows/{id}/search-subtitles` | 搜索字幕 |

### 6.3 动漫相关 API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/anime` | 获取动漫列表 |
| GET | `/api/anime/{id}` | 获取动漫详情 |

### 6.4 设置相关 API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/settings` | 获取设置 |
| POST | `/api/settings` | 更新设置 |
| POST | `/api/test-tmdb` | 测试 TMDB API |

### 6.5 Webhook API

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/webhook/nastool` | NASTool Webhook |
| GET | `/api/webhook/nastool/test` | 测试 Webhook |

### 6.6 其他 API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/stats` | 获取统计信息 |
| GET | `/api/status` | 获取服务状态 |
| GET | `/api/recent-activity` | 获取最近活动 |

---

## 7. 配置说明

### 7.1 环境变量

| 变量名 | 说明 | 默认值 | 可持久化 |
|--------|------|--------|----------|
| `MOVIE_DIR` | 电影目录 | `/movies` | ❌ |
| `TV_DIR` | 电视剧目录 | `/tvshows` | ❌ |
| `ANIME_DIR` | 动漫目录 | `/anime` | ❌ |
| `SCAN_INTERVAL` | 扫描间隔（分钟） | `30` | ✅ |
| `SUBTITLE_SOURCES` | 字幕源 | `shooter,assrt,opensubtitles,subhd` | ✅ |
| `AUTO_DOWNLOAD` | 自动下载 | `true` | ✅ |
| `TMDB_API_KEY` | TMDB API 密钥 | - | ✅ |
| `OPENSUBTITLES_API_KEY` | OpenSubtitles API 密钥 | - | ✅ |
| `NASTOOL_ENABLED` | 启用 NASTool | `false` | ✅ |
| `NASTOOL_WEBHOOK_TOKEN` | Webhook 令牌 | - | ✅ |

### 7.2 配置持久化机制

**配置优先级**:
1. 环境变量（最高优先级）
2. `.env` 文件
3. 默认值（最低优先级）

**持久化流程**:
```
用户修改设置 → 保存到 .env → 备份到 /app/data/.env.backup
                                    ↓
容器重启 → 从备份恢复 → 加载到 .env → 应用读取
```

**重要提示**:
- 不要在 `docker-compose.yml` 的 `environment` 中设置需要持久化的配置
- 这些配置应该通过 Web 界面设置

### 7.3 配置文件示例

```yaml
# docker-compose.yml
services:
  subtitle-manager:
    image: alexwjxing/subtitle-manager:latest
    environment:
      # 只设置不需要持久化的配置
      MOVIE_DIR: "/movies"
      TV_DIR: "/tvshows"
      ANIME_DIR: "/anime"
      SUBTITLE_SOURCES: "shooter,assrt,opensubtitles,subhd"
      # 不要在这里设置 TMDB_API_KEY 等需要持久化的配置！
    volumes:
      - ./data:/app/data  # 配置持久化目录
```

---

## 8. 部署指南

### 8.1 Docker 部署

**步骤 1**: 创建目录结构
```bash
mkdir -p /path/to/subtitle-manager/{data,logs}
cd /path/to/subtitle-manager
```

**步骤 2**: 创建 docker-compose.yml
```yaml
services:
  subtitle-manager:
    image: alexwjxing/subtitle-manager:latest
    container_name: subtitle-manager
    restart: unless-stopped
    ports:
      - "18080:8080"
    environment:
      MOVIE_DIR: "/movies"
      TV_DIR: "/tvshows"
      ANIME_DIR: "/anime"
      SUBTITLE_SOURCES: "shooter,assrt,opensubtitles,subhd"
    volumes:
      - /path/to/movies:/movies
      - /path/to/tvshows:/tvshows
      - /path/to/anime:/anime
      - ./data:/app/data
      - ./logs:/app/logs
```

**步骤 3**: 启动服务
```bash
docker-compose up -d
```

**步骤 4**: 访问 Web 界面
```
http://your-server:18080
```

### 8.2 Unraid 部署

**步骤 1**: 在 Unraid 上创建目录
```bash
mkdir -p /mnt/user/appdata/subtitle-manager/{data,logs}
```

**步骤 2**: 使用 Compose Manager 插件
- 安装 Compose Manager 插件
- 创建新的 Compose 项目
- 粘贴 docker-compose.yml 内容

**步骤 3**: 配置媒体目录映射
- 电影: `/mnt/user/movies:/movies`
- 电视剧: `/mnt/user/tvshows:/tvshows`
- 动漫: `/mnt/user/anime:/anime`

### 8.3 构建镜像

**本地构建**:
```bash
docker build -t subtitle-manager:latest .
```

**推送镜像**:
```bash
docker tag subtitle-manager:latest alexwjxing/subtitle-manager:latest
docker push alexwjxing/subtitle-manager:latest
```

---

## 9. 开发规范

### 9.1 代码风格

- **Python**: 遵循 PEP 8
- **Vue**: 使用 Composition API
- **命名**: 使用有意义的变量名
- **注释**: 关键逻辑必须注释

### 9.2 提交规范

```
<type>: <subject>

<body>

<footer>
```

**Type 类型**:
- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档
- `style`: 格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

### 9.3 目录规范

```
subtitle-manager/
├── web/              # 前端代码
├── subtitle_sources/ # 字幕源
├── *.py             # 后端模块
├── Dockerfile       # Docker 配置
└── *.md            # 文档
```

### 9.4 API 设计规范

- 使用 RESTful 风格
- 路径使用小写和连字符
- 返回统一格式:
```json
{
  "success": true,
  "data": {},
  "message": ""
}
```

---

## 10. 已知问题

### 10.1 当前问题

| 问题 | 状态 | 说明 |
|------|------|------|
| 配置持久化 | ⚠️ 已修复 | 重启后配置丢失问题已修复 |
| Zimuku 字幕源 | ❌ 已移除 | 网络连接不稳定 |
| Xunlei 字幕源 | ❌ 已移除 | 服务不可用 |

### 10.2 修复记录

**2026-03-14**: 修复配置持久化问题
- 问题: 容器重启后配置丢失
- 原因: 环境变量优先级高于 .env 文件
- 解决: 移除 docker-compose.yml 中的敏感配置，使用备份机制

**2026-03-13**: 添加 NASTool 对接
- 新增 Webhook 接口
- 支持自动字幕下载

**2026-03-12**: 移除不稳定字幕源
- 移除 Zimuku 和 Xunlei

### 10.3 待办事项

- [ ] 优化 SubHD 验证码识别
- [ ] 添加更多字幕源
- [ ] 支持字幕自动翻译
- [ ] 添加用户认证
- [ ] 支持多语言界面

---

## 附录

### A. 常用命令

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 更新镜像
docker-compose pull
docker-compose up -d

# 进入容器
docker-compose exec subtitle-manager bash
```

### B. 相关链接

- **Docker Hub**: https://hub.docker.com/r/alexwjxing/subtitle-manager
- **项目文档**: 本文档

### C. 联系方式

如有问题，请通过 GitHub Issues 联系。

---

**文档版本**: 1.0.0  
**最后更新**: 2026-03-14  
**维护者**: alexwjxing
