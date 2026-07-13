# Contributing

感谢你愿意改进 Subtitle Manager。

## 开始之前

- 请先阅读 [README.md](/mnt/e/work/subtitle-manager/README.md)
- 涉及部署、NAS 或发布的内容，优先同步更新 [docs](/mnt/e/work/subtitle-manager/docs)
- 不要提交真实的 `.env`、Token、API Key、NAS 凭据或测试媒体文件

## 本地开发

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

也可以使用：

```bash
python scripts/start_server.py
```

## 提交前检查

```bash
python -m py_compile backend/api_server.py backend/subtitle_manager.py
cd web && npm run build
```

如果改了 Docker 相关内容，再补跑：

```bash
docker build -t subtitle-manager:local .
```

## 提交建议

- 一次提交只解决一类问题
- 配置、文档、功能修改尽量分开
- 如果改了目录结构或接口，请同步更新 README 和相关文档
- 如果删除了旧能力，请确认文档中没有遗留说明

## Issue / PR 建议内容

请尽量带上这些信息：

- 媒体类型：电影 / 电视剧 / 动漫
- 文件名样例
- 使用的字幕源
- 关键日志片段
- 是否通过 Docker 运行
- 是否启用了 Plex 或 NASTool 集成
