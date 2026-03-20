# 字幕管理器 (Subtitle Manager)

[![Docker Pulls](https://img.shields.io/docker/pulls/alexwjxing/subtitle-manager)](https://hub.docker.com/r/alexwjxing/subtitle-manager)
[![Docker Image Size](https://img.shields.io/docker/image-size/alexwjxing/subtitle-manager/latest)](https://hub.docker.com/r/alexwjxing/subtitle-manager)

一个面向 NAS 和媒体服务器的中文字幕下载与管理工具，提供 Web 界面、自动扫描、手动搜索、Plex 刷新和 NASTool Webhook 对接。

## 主要功能

- 支持电影、电视剧、动漫三类媒体
- 集成 `SubHD`、`Shooter`、`Assrt`、`OpenSubtitles`
- 自动搜索并下载缺失字幕
- 下载后自动整理为更适合 Plex 的外挂字幕命名
- 支持 Plex 刷新、路径映射和 NASTool Webhook
- 提供桌面和移动端可用的 Web 管理界面

## 快速开始

### Docker Compose

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
      NASTOOL_ENABLED: "false"
    volumes:
      - /path/to/movies:/movies
      - /path/to/tvshows:/tvshows
      - /path/to/anime:/anime
      - ./logs:/app/logs
      - ./data:/app/data
```

启动后访问：

- Web UI: `http://your-server:18080`
- API Docs: `http://your-server:18080/docs`
- Health: `http://your-server:18080/health`

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
  alexwjxing/subtitle-manager:latest
```

## 首次使用建议

1. 打开 Web 界面
2. 在设置页填写 `TMDB_API_KEY`、`Plex`、`NASTool` 等可选配置
3. 确认媒体目录挂载正确
4. 根据需要启用自动下载和对应字幕源

注意：

- `TMDB`、`Plex`、`OpenSubtitles`、`NASTool Token` 这类需要持久化的配置，建议通过 Web 设置页保存
- 不建议把敏感配置长期写死在 `docker-compose.yml` 的 `environment` 中

## 常用环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `MOVIE_DIR` | 电影目录 | `/movies` |
| `TV_DIR` | 电视剧目录 | `/tvshows` |
| `ANIME_DIR` | 动漫目录 | `/anime` |
| `SUBTITLE_SOURCES` | 启用的字幕源 | `shooter,assrt,opensubtitles,subhd` |
| `SCAN_INTERVAL` | 扫描间隔（分钟） | `30` |
| `AUTO_DOWNLOAD` | 自动下载字幕 | `true` |
| `AUTO_DOWNLOAD_DELAY_MIN_SECONDS` | 自动请求最小延迟 | `6` |
| `AUTO_DOWNLOAD_DELAY_MAX_SECONDS` | 自动请求最大延迟 | `14` |
| `NASTOOL_ENABLED` | 启用 NASTool 对接 | `false` |
| `NASTOOL_WEBHOOK_TOKEN` | Webhook 安全令牌 | 空 |
| `TMDB_API_KEY` | TMDB API Key | 空 |
| `OPENSUBTITLES_API_KEY` | OpenSubtitles API Key | 空 |
| `PLEX_SERVER_URL` | Plex 地址 | 空 |
| `PLEX_TOKEN` | Plex Token | 空 |

## NASTool Webhook

Webhook 地址：

```text
POST /api/webhook/nastool
```

如果设置了安全令牌，使用：

```text
http://your-server:18080/api/webhook/nastool?token=your_token
```

支持事件：

- `download.completed`
- `media.scraped`
- `subtitle.missing`
- `transfer.completed`

## 注意事项

- 本项目只处理字幕，不管理媒体刮削或媒体库本体
- 某些字幕源可能存在验证码、限流或站点不稳定的情况
- 图片字幕（如 `SUP`）文件体积可能明显大于文本字幕
- 请尊重字幕作者与字幕站点的使用规则

## 项目地址

- GitHub: <https://github.com/alexing0805/subtitle-manager>
- Docker Hub: <https://hub.docker.com/r/alexwjxing/subtitle-manager>
