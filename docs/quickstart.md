# 字幕管理器快速启动指南

## 方法一：使用启动脚本（推荐）

### 1. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装前端依赖
cd web
npm install
cd ..
```

### 2. 启动服务

```bash
python scripts/start_server.py
```

启动后访问：
- **Web 界面**: http://localhost:5173
- **API 地址**: http://localhost:8080
- **API 文档**: http://localhost:8080/docs

## 方法二：手动启动

### 1. 只启动后端 API

```bash
# 安装依赖
pip install -r requirements.txt

# 启动后端
python -m uvicorn backend.api_server:app --host 0.0.0.0 --port 8080 --reload
```

访问 http://localhost:8080/docs 查看 API 文档

### 2. 只启动前端（开发模式）

```bash
cd web
npm install
npm run dev
```

访问 http://localhost:5173

## 方法三：Docker 部署

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置你的媒体目录
# MOVIE_DIR=/movies
# TV_DIR=/tvshows
# ANIME_DIR=/anime

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

访问 http://localhost:8080

## 常见问题

### 1. 端口被占用

如果 8080 端口被占用，可以修改端口：

```bash
# 后端使用其他端口
python -m uvicorn backend.api_server:app --host 0.0.0.0 --port 8081 --reload

# 或修改 docker-compose.yml 中的端口映射
```

### 2. 前端依赖安装失败

```bash
# 使用淘宝镜像
cd web
npm config set registry https://registry.npmmirror.com
npm install
```

### 3. Python 依赖安装失败

```bash
# 使用清华镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 配置说明

编辑 `.env` 文件配置系统：

```env
# 媒体目录
MOVIE_DIR=/movies
TV_DIR=/tvshows
ANIME_DIR=/anime

# 扫描间隔（分钟）
SCAN_INTERVAL=30

# 文件大小阈值（MB）
MIN_FILE_SIZE_MB=100

# 是否自动下载字幕
AUTO_DOWNLOAD=true
```

## 使用说明

1. **仪表盘**: 查看统计信息和最近活动
2. **电影**: 管理电影字幕，搜索和下载
3. **电视剧**: 管理电视剧字幕
4. **批量上传**: 为电视剧批量上传字幕文件（支持 S01E01 格式自动匹配）
5. **设置**: 配置系统参数

## 批量上传字幕步骤

1. 进入"批量上传"页面
2. 选择电视剧和季数
3. 上传字幕文件（文件名需包含 S01E01 格式）
4. 系统自动匹配字幕到对应剧集
5. 确认匹配结果并上传

## 停止服务

- 按 `Ctrl+C` 停止启动脚本
- 或运行 `docker-compose down` 停止 Docker 服务
