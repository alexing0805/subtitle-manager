# Subtitle Manager

[![Docker Pulls](https://img.shields.io/docker/pulls/alexwjxing/subtitle-manager)](https://hub.docker.com/r/alexwjxing/subtitle-manager)
[![Docker Image Size](https://img.shields.io/docker/image-size/alexwjxing/subtitle-manager/latest)](https://hub.docker.com/r/alexwjxing/subtitle-manager)

**为 NAS、Plex 与媒体服务器设计的中文字幕自动化控制台**

Subtitle Manager 聚焦一件事：把“找到字幕、下载字幕、整理字幕、让 Plex 真正识别字幕”这条链路收成一个长期可运行的容器服务。

## 它能做什么

- 统一管理电影、电视剧、动漫三类媒体
- 搜索 `SubHD`、`Shooter`、`Assrt`、`OpenSubtitles`
- 自动下载缺失字幕，并对结果做匹配重排
- 下载后整理为更适合 Plex 的外挂字幕命名
- 支持 Plex 刷新与路径映射
- 支持 NASTool Webhook 联动
- 提供桌面和移动端可用的 Web 管理界面

## 适合谁

如果你符合下面任一场景，这个镜像就很适合直接挂上去跑：

- 你有 NAS，媒体目录稳定，想自动补中文字幕
- 你用 Plex，希望字幕下载后尽量直接可见、可选
- 你用 NASTool，想在下载完成或转移完成后自动拉字幕
- 你不想维护一堆分散脚本，而是想要一个有 Web UI 的集中控制台

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

启动后访问：

- Web UI: `http://your-server:18080`
- API Docs: `http://your-server:18080/docs`
- Health: `http://your-server:18080/health`

## 推荐的首次配置顺序

1. 确认三类媒体目录挂载正确
2. 打开设置页，补上 `TMDB_API_KEY`
3. 如果你用 Plex，再填 `PLEX_SERVER_URL`、`PLEX_TOKEN` 和路径映射
4. 如果你用 NASTool，再开启 Webhook 和安全令牌
5. 按需启用自动下载和对应字幕源

注意：

- `TMDB`、`Plex`、`OpenSubtitles`、`NASTool Token` 这类配置建议通过 Web 设置页持久化
- 不建议把敏感配置长期直接写死在 `docker-compose.yml` 的 `environment` 中

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

## NASTool / Plex 集成

### NASTool Webhook

支持事件：

- `download.completed`
- `media.scraped`
- `subtitle.missing`
- `transfer.completed`

如果启用了令牌验证：

```text
http://your-server:18080/api/webhook/nastool?token=your_token
```

### Plex 联动

- 支持下载后刷新媒体项
- 支持路径映射
- 支持更适合 Plex 的外挂字幕命名格式

## 使用时你需要知道的事

- 这个项目只负责 **字幕搜索、下载、整理与集成**，不负责完整媒体刮削流程
- 某些字幕源会遇到验证码、限流或站点波动
- 图片字幕（如 `SUP`）体积通常比文本字幕大很多
- 最终可用性也会受到源站内容质量影响

## 项目地址

- GitHub: <https://github.com/alexing0805/subtitle-manager>
- Docker Hub: <https://hub.docker.com/r/alexwjxing/subtitle-manager>
