# NAS 媒体访问与部署指南

这份文档提供几种常见的 NAS 接入方式。文中的主机名、共享名、用户名和密码都请替换成你自己的环境，不要直接照抄到公开仓库或提交历史里。

## 方案一：WSL2 中挂载 SMB，再给 Docker 使用

```bash
sudo apt-get update
sudo apt-get install -y cifs-utils
sudo mkdir -p /mnt/nas-video
sudo mount -t cifs //<nas-host>/<share-name> /mnt/nas-video \
  -o username=<nas-user>,password=<nas-password>,vers=3.0,ro
```

然后在 `docker-compose.nas.yml` 中映射：

```yaml
volumes:
  - /mnt/nas-video:/video:ro
```

## 方案二：Windows 先挂载，再给 Docker 使用

可以使用 [scripts/mount-nas.ps1](/mnt/e/work/subtitle-manager/scripts/mount-nas.ps1) 交互式挂载，也可以自行用资源管理器或 `net use` 挂载网络盘。

示例：

```powershell
.\scripts\mount-nas.ps1 -NasHost nas.local -Share "Video\Link" -MountLetter Z:
```

## 方案三：NAS / Unraid 直接部署

如果媒体和容器都在 NAS 上，推荐直接部署，避免额外挂载层。

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
      AUTO_DOWNLOAD: "true"
      NASTOOL_ENABLED: "false"
    volumes:
      - /mnt/user/Video/Link/MOVIES:/movies
      - /mnt/user/Video/Link/TVSHOWS:/tvshows
      - /mnt/user/Video/Link/ANIMES:/anime
      - /mnt/user/appdata/subtitle-manager/logs:/app/logs
      - /mnt/user/appdata/subtitle-manager/data:/app/data
```

## 安全建议

- 不要把 NAS 用户名、密码、Token、API Key 写进公开仓库
- `.env` 只保留模板，不提交真实值
- 如果必须写示例，请使用 `<nas-host>`、`<token>` 这类占位符
- 如果历史提交里出现过敏感信息，公开前应当改写历史或更换凭据
