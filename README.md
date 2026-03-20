# Subtitle Manager

一个面向 NAS 和媒体服务器的中文字幕管理工具，提供 Web 界面、手动搜索下载、自动扫描、Plex 刷新和 NASTool Webhook 对接。

## 特性

- 电影、电视剧、动漫统一管理
- 支持 `SubHD`、`Shooter`、`Assrt`、`OpenSubtitles`
- 自动搜索和下载缺失中文字幕
- 下载后统一整理为 Plex 更友好的外挂字幕命名
- 支持 Plex 刷新和路径映射
- 支持 NASTool Webhook 触发下载
- Vue 3 前端管理界面，适配桌面和移动端

## 目录结构

```text
subtitle-manager/
├── backend/                 # FastAPI 后端与字幕处理逻辑
│   ├── api_server.py
│   ├── subtitle_manager.py
│   ├── config.py
│   ├── nastool_webhook.py
│   ├── nfo_parser.py
│   ├── tmdb_api.py
│   ├── utils.py
│   └── subtitle_sources/
├── web/                     # Vue 3 前端
├── docs/                    # 补充文档
├── scripts/                 # 本地启动/部署辅助脚本
├── Dockerfile
├── docker-compose.yml
├── docker-compose.nas.yml
├── docker-compose.unraid.yml
├── requirements.txt
└── .env.example
```

## 快速开始

### Docker

```bash
cp .env.example .env
docker compose up -d
```

默认访问：

- Web UI: `http://localhost:18080`
- API: `http://localhost:18080/api/...`
- 健康检查: `http://localhost:18080/health`

### 本地开发

后端：

```bash
pip install -r requirements.txt
python -m uvicorn backend.api_server:app --host 0.0.0.0 --port 8080 --reload
```

前端：

```bash
cd web
npm install
npm run dev
```

或者直接用：

```bash
python scripts/start_server.py
```

## 配置说明

核心环境变量：

- `MOVIE_DIR`：电影目录
- `TV_DIR`：电视剧目录
- `ANIME_DIR`：动漫目录
- `SUBTITLE_SOURCES`：字幕源顺序，默认 `shooter,assrt,opensubtitles,subhd`
- `AUTO_DOWNLOAD`：是否自动下载
- `TMDB_API_KEY`：TMDB API Key
- `OPENSUBTITLES_API_KEY`：OpenSubtitles API Key
- `PLEX_SERVER_URL`：Plex 地址，例如 `http://plex.local:32400`
- `PLEX_TOKEN`：Plex Token
- `NASTOOL_ENABLED`：是否启用 NASTool Webhook
- `NASTOOL_WEBHOOK_TOKEN`：NASTool Webhook Token

需要持久化的配置建议通过 Web 设置页保存，不要长期写死在 `docker-compose.yml` 的 `environment` 中。

## NASTool / Plex

- Plex：支持下载后刷新媒体项，并支持路径映射
- NASTool：支持 `download.completed`、`media.scraped`、`subtitle.missing`、`transfer.completed`
- 当挂载路径不一致时，可在设置页填写 `from=to` 格式的路径映射

## 常用命令

```bash
# 构建前端
cd web && npm run build

# 本地验证后端语法
python -m py_compile backend/api_server.py backend/subtitle_manager.py

# Docker 构建
docker build -t subtitle-manager:latest .
```

## 文档

- [快速开始](docs/quickstart.md)
- [NAS 部署](docs/nas-setup.md)
- [Docker Hub 发布说明](docs/docker-hub.md)
- [项目记忆文档（历史参考，可能滞后）](docs/project-memory.md)
- [发布检查清单](docs/release-checklist.md)
- [贡献指南](CONTRIBUTING.md)
- [安全说明](SECURITY.md)

## 许可证

本项目当前使用 [MIT License](LICENSE)。

## 发布建议

发到 GitHub 前建议确认：

- `.env` 没有提交
- `data/`、`logs/`、`web/dist/` 没有提交
- 本地测试媒体和调试脚本已移除
- `docker build` 和 `npm run build` 都通过
