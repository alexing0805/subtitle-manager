# 发布检查清单

## 发布前必须确认

- `.env`、真实 API Key、Plex Token、NAS 用户名密码没有进入 Git 提交
- `data/`、`logs/`、`web/dist/` 没有进入 Git 提交
- 测试媒体、临时截图、调试脚本已经删除
- `README.md` 与当前目录结构一致
- `docker build` 可以成功
- `cd web && npm run build` 可以成功
- `python -m py_compile backend/api_server.py backend/subtitle_manager.py` 可以成功

## 建议检查

- Docker Hub 镜像名与 README 一致
- 文档中的 IP、共享名、路径都已经改成通用示例
- 没有遗留旧字幕源名或已删除模块说明
- 如果准备公开开源，补充合适的 License
