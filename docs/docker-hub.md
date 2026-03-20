# 字幕管理器 (Subtitle Manager)

[![Docker Pulls](https://img.shields.io/docker/pulls/qqzz007/subtitle-manager)](https://hub.docker.com/r/qqzz007/subtitle-manager)
[![Docker Stars](https://img.shields.io/docker/stars/qqzz007/subtitle-manager)](https://hub.docker.com/r/qqzz007/subtitle-manager)

一个功能强大的自动化中文字幕下载和管理工具，专为 NAS 和媒体服务器设计。

## ✨ 主要功能

- **🎬 多类型支持** - 支持电影、电视剧、动漫的字幕管理
- **🔍 智能搜索** - 集成多个字幕源（SubHD、射手网、OpenSubtitles、Assrt）
- **🤖 自动下载** - 监控目录变化，自动搜索并下载缺失字幕
- **📺 NASTool 对接** - 支持 NASTool Webhook，实现自动化字幕下载
- **🎯 智能匹配** - 基于文件名、TMDB 信息智能匹配最佳字幕
- **📝 多格式支持** - 支持 SRT、ASS、SSA、VTT 等主流字幕格式
- **🎨 现代界面** - 美观的 Web 管理界面，支持移动端访问
- **🔐 安全可控** - 支持 Webhook 安全令牌验证

## 🚀 快速开始

### Docker Compose（推荐）

```yaml
version: '3.8'

services:
  subtitle-manager:
    image: qqzz007/subtitle-manager:latest
    container_name: subtitle-manager
    restart: unless-stopped
    ports:
      - "18080:8080"
    environment:
      # 监控目录
      MOVIE_DIR: "/movies"
      TV_DIR: "/tvshows"
      ANIME_DIR: "/anime"
      # 字幕源配置
      SUBTITLE_SOURCES: "shooter,assrt,opensubtitles,subhd"
      # NASTool 对接（可选）
      NASTOOL_ENABLED: "false"
      NASTOOL_WEBHOOK_TOKEN: ""
      # API 配置（可选）
      TMDB_API_KEY: ""
      OPENSUBTITLES_API_KEY: ""
    volumes:
      - /path/to/movies:/movies
      - /path/to/tvshows:/tvshows
      - /path/to/anime:/anime
      - ./logs:/app/logs
      - ./data:/app/data
```

### Docker Run

```bash
docker run -d \
  --name subtitle-manager \
  --restart unless-stopped \
  -p 18080:8080 \
  -e MOVIE_DIR="/movies" \
  -e TV_DIR="/tvshows" \
  -e ANIME_DIR="/anime" \
  -e SUBTITLE_SOURCES="shooter,assrt,opensubtitles,subhd" \
  -v /path/to/movies:/movies \
  -v /path/to/tvshows:/tvshows \
  -v /path/to/anime:/anime \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  qqzz007/subtitle-manager:latest
```

## 📖 使用指南

### 1. 访问 Web 界面

打开浏览器访问：`http://your-server:18080`

### 2. 配置监控目录

在设置页面配置电影、电视剧、动漫的监控目录。

### 3. 选择字幕源

启用需要的字幕源：
- **SubHD** - 中文高清字幕
- **射手网** - 经典中文字幕
- **OpenSubtitles** - 国际字幕库
- **Assrt** - 日文字幕源

### 4. NASTool 对接（可选）

在 NASTool 中配置 Webhook：
- URL: `http://your-server:18080/api/webhook/nastool`
- 方法: POST
- 触发事件: 下载完成、媒体刮削完成

## ⚙️ 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `MOVIE_DIR` | 电影目录 | `/movies` |
| `TV_DIR` | 电视剧目录 | `/tvshows` |
| `ANIME_DIR` | 动漫目录 | `/anime` |
| `SUBTITLE_SOURCES` | 启用的字幕源 | `shooter,assrt,opensubtitles,subhd` |
| `SCAN_INTERVAL` | 扫描间隔（分钟） | `30` |
| `AUTO_DOWNLOAD` | 自动下载字幕 | `true` |
| `NASTOOL_ENABLED` | 启用 NASTool 对接 | `false` |
| `NASTOOL_WEBHOOK_TOKEN` | Webhook 安全令牌 | `` |
| `TMDB_API_KEY` | TMDB API 密钥（可选） | `` |
| `OPENSUBTITLES_API_KEY` | OpenSubtitles API 密钥（可选） | `` |

## 🔌 API 接口

### Webhook 接口

**POST** `/api/webhook/nastool`

接收 NASTool 通知，自动下载字幕。

请求示例：
```json
{
  "event": "download.completed",
  "title": "电影名称",
  "file_path": "/movies/电影/电影.mkv",
  "type": "movie"
}
```

### 其他 API

- **GET** `/api/movies` - 获取电影列表
- **GET** `/api/tvshows` - 获取电视剧列表
- **POST** `/api/movies/{id}/search-subtitles` - 搜索字幕
- **GET** `/api/settings` - 获取设置
- **POST** `/api/settings` - 更新设置

完整 API 文档访问：`http://your-server:18080/docs`

## 🛠️ 技术栈

- **后端**: Python 3.11 + FastAPI
- **前端**: Vue 3 + Element Plus
- **字幕源**: SubHD、射手网、OpenSubtitles、Assrt
- **容器**: Docker + Docker Compose

## 📝 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系

如有问题，请通过 GitHub Issues 联系。

---

**注意**: 本项目仅供学习交流使用，请尊重字幕作者的劳动成果。
