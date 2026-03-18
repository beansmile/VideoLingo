# VideoLingo 宝塔面板 Docker 部署指南

> **适用环境**: CentOS 7.9 + 宝塔面板 + Docker，使用 Qwen API（无 GPU）

---

## 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | CentOS 7.9 |
| 面板 | 宝塔面板 7.9+ |
| Docker | 20.10+ |
| CPU | 4 核心以上 |
| 内存 | 8GB 以上 |
| 硬盘 | 100GB 以上 SSD |
| 网络 | 公网 IP，开放 80/443 端口 |

---

## 为什么使用 Docker？

| 对比项 | Docker 部署 ✅ | 宝塔 Python 部署 ❌ |
|--------|---------------|-------------------|
| **Python 版本** | 完全隔离，自带 Python 3.10 | 依赖系统版本，配置复杂 |
| **依赖管理** | 镜像包含所有依赖 | 需手动安装，容易冲突 |
| **环境隔离** | 完全隔离，不影响系统 | 可能影响系统环境 |
| **迁移方便** | 导出镜像即可迁移 | 需重新配置环境 |
| **版本管理** | 镜像版本控制 | 依赖配置文件 |

---

## 宝塔面板基础设置

### 1. 安装宝塔面板（如果未安装）

```bash
yum install -y wget && wget -O install.sh http://download.bt.cn/install/install_6.0.sh && sh install.sh
```

安装完成后记录：
- 面板地址
- 用户名
- 密码

### 2. 登录宝塔面板

访问 `http://你的服务器IP:8888`，使用记录的用户名密码登录。

### 3. 安装必要软件

在宝塔面板 **【软件商店】** 中安装：

| 软件 | 版本要求 | 说明 |
|------|----------|------|
| Nginx | 1.20+ | 必装 |
| Docker | 最新版 | 必装 |
| 防火墙 | - | 推荐 |

**注意**: 不需要安装 Python、PHP、MySQL 等软件。

---

## 部署步骤

### 步骤一：安装 Docker

#### 方法一：使用宝塔面板安装（推荐）

1. 在宝塔面板进入 **【软件商店】**
2. 搜索 **Docker**
3. 点击 **【安装】**
4. 等待安装完成

#### 方法二：命令行安装

在宝塔终端中执行：

```bash
# 卸载旧版本
yum remove -y docker docker-client docker-client-latest docker-common

# 安装依赖
yum install -y yum-utils device-mapper-persistent-data lvm2

# 添加 Docker 阿里云镜像源（国内加速）
yum-config-manager --add-repo https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo

# 安装 Docker
yum install -y docker-ce docker-ce-cli containerd.io

# 启动 Docker
systemctl enable --now docker

# 验证安装
docker --version
docker run hello-world
```

#### 配置 Docker 镜像加速（可选，国内推荐）

```bash
# 创建配置目录
mkdir -p /etc/docker

# 配置镜像加速
cat > /etc/docker/daemon.json <<EOF
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1panel.live",
    "https://hub.rat.dev"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}
EOF

# 重启 Docker
systemctl daemon-reload
systemctl restart docker
```

### 步骤二：创建项目目录

在宝塔面板中：

1. 进入 **【文件】**
2. 进入 `/www` 目录
3. 创建 `VideoLingo` 文件夹

或使用命令行：

```bash
mkdir -p /www/VideoLingo
cd /www/VideoLingo
```

### 步骤三：创建配置文件

#### 1. 创建 config.yaml

在宝塔面板中：

1. 进入 **【文件】**
2. 进入 `/www/VideoLingo` 目录
3. 点击 **【新建文件】**，命名为 `config.yaml`
4. 点击 **【编辑】**，填入以下内容：

```yaml
display_language: "zh-CN"

# 翻译 API
api:
  key: 'sk-your-api-key'           # 替换为你的 API Key
  base_url: 'https://yunwu.ai'
  model: 'gpt-4.1-2025-04-14'
  llm_support_json: false

max_workers: 4
target_language: '简体中文'
demucs: false

# ASR 配置（使用 Qwen-ASR）
whisper:
  model: 'large-v3'
  language: 'zh'
  runtime: 'qwen'
  qwen_api_key: 'sk-your-qwen-key'  # 阿里云 DashScope API Key

# TTS 配置（使用 Qwen-TTS）
tts_method: 'qwen_tts'
qwen_tts:
  api_key: 'sk-your-qwen-key'
  voice: 'Cherry'
  model: 'qwen3-tts-flash'
  region: 'cn'

# 其他配置
model_dir: './_model_cache'
burn_subtitles: true
ffmpeg_gpu: false
```

5. 点击 **【保存】**

#### 2. 使用项目提供的 Dockerfile

VideoLingo 项目提供了完整的 Dockerfile（参考 install.py 的安装流程）：

| 文件 | 说明 | 镜像大小 |
|------|------|----------|
| `Dockerfile` | 完整版，包含 PyTorch + demucs + 所有依赖 | ~3-4GB |

**Dockerfile 安装流程（参考 install.py）**：

1. 安装系统依赖（git, ffmpeg, fonts-noto）
2. 克隆项目（beansmile/VideoLingo，分支 feat-support-new-asr）
3. 安装 PyTorch 2.8.0（CPU 版本）
4. 安装 demucs（--no-deps 避免冲突）
5. 安装项目依赖（pip install -e .）

直接使用项目的 Dockerfile：

```bash
cd /www/VideoLingo
git clone --branch feat-support-new-asr https://github.com/beansmile/VideoLingo.git temp
cp temp/Dockerfile .
rm -rf temp

# 或者手动创建（使用完整版 Dockerfile）
cat > /www/VideoLingo/Dockerfile << 'EOF'
FROM python:3.10

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 替换为阿里云镜像源
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.ubuntu.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git curl ffmpeg fonts-noto \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 配置清华 PyPI 镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app

# 克隆项目
RUN git clone --branch feat-support-new-asr https://github.com/beansmile/VideoLingo.git . && \
    rm -rf .git

# 安装 PyTorch 2.8.0（CPU 版本）
RUN pip install --no-cache-dir torch==2.8.0 torchaudio==2.8.0

# 安装 demucs（--no-deps 避免 torchaudio 冲突）
RUN pip install --no-cache-dir --no-deps "demucs[dev]@git+https://github.com/adefossez/demucs" && \
    pip install --no-cache-dir dora-search openunmix lameenc

# 安装项目依赖
RUN pip install --no-cache-dir -e .

# 创建必要的目录
RUN mkdir -p /app/output /app/_model_cache /app/logs

EXPOSE 8501

CMD ["streamlit", "run", "st.py", "--server.port=8501", "--server.address=0.0.0.0"]
EOF
```

#### 3. 创建 .dockerignore

```bash
cat > /www/VideoLingo/.dockerignore << 'EOF'
.git
.gitignore
venv
__pycache__
*.pyc
output/
_model_cache/
logs/
*.log
.DS_Store
EOF
```

### 步骤四：构建 Docker 镜像

在宝塔终端中执行：

```bash
cd /www/VideoLingo

# 构建镜像
docker build -t videolingo:latest .

# 查看镜像
docker images | grep videolingo
```

### 步骤五：运行容器

```bash
# 创建必要的目录
mkdir -p /www/VideoLingo/output /www/VideoLingo/_model_cache

# 运行容器
docker run -d \
  --name videolingo \
  --restart unless-stopped \
  -p 8501:8501 \
  -v /www/VideoLingo/config.yaml:/app/config.yaml:ro \
  -v /www/VideoLingo/output:/app/output \
  -v /www/VideoLingo/_model_cache:/app/_model_cache \
  --memory="4g" \
  --cpus="2" \
  videolingo:latest

# 查看容器状态
docker ps | grep videolingo

# 查看日志
docker logs -f videolingo
```

**参数说明**：

| 参数 | 说明 |
|------|------|
| `-d` | 后台运行 |
| `--name videolingo` | 容器名称 |
| `--restart unless-stopped` | 自动重启 |
| `-p 8501:8501` | 端口映射 |
| `-v ...` | 挂载配置和输出目录 |
| `--memory="4g"` | 内存限制 4GB |
| `--cpus="2"` | CPU 限制 2 核 |

### 步骤六：配置 Nginx 反向代理

1. 在宝塔面板进入 **【网站】**
2. 点击 **【添加站点】**：

| 选项 | 值 |
|------|-----|
| 域名 | your-domain.com |
| 根目录 | /www/VideoLingo |
| FTP | 不创建 |
| 数据库 | 不创建 |
| PHP 版本 | 纯静态 |

3. 创建后，点击站点右侧的 **【设置】**
4. 进入 **【配置文件】**，替换为以下内容：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书
    ssl_certificate /www/server/panel/vhost/cert/your-domain.com/fullchain.pem;
    ssl_certificate_key /www/server/panel/vhost/cert/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # 上传和超时限制
    client_max_body_size 500M;
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
    client_body_timeout 3600s;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_connect_timeout 3600s;
    }

    # Streamlit 健康检查
    location /_stcore/health {
        proxy_pass http://127.0.0.1:8501/_stcore/health;
        access_log off;
    }
}
```

5. 点击 **【保存】**
6. 重启 Nginx：在宝塔面板进入 **【软件商店】** → 找到 Nginx → 点击 **【重启】**

### 步骤七：申请 SSL 证书

1. 在宝塔面板进入 **【网站】**
2. 找到你的站点，点击 **【设置】**
3. 进入 **【SSL】** 选项卡
4. 选择 **【Let's Encrypt】**
5. 填写邮箱
6. 点击 **【申请】**
7. 等待证书申请完成
8. 开启 **【强制 HTTPS】**

---

## 安全设置

### 1. 防火墙配置

在宝塔面板中：

1. 进入 **【安全】**
2. 确保只开放以下端口：

| 端口 | 说明 |
|------|------|
| 80 | HTTP |
| 443 | HTTPS |
| 8888 | 宝塔面板（建议使用完后关闭或改为其他端口） |
| 22 | SSH |

3. **删除** 8501 端口（不对外暴露）

### 2. 配置文件权限

```bash
# 设置配置文件权限
chmod 600 /www/VideoLingo/config.yaml

# 设置输出目录权限
chmod 755 /www/VideoLingo/output
```

### 3. Docker 容器安全

```bash
# 以非 root 用户运行容器（可选）
docker run -d \
  --name videolingo \
  --user 1000:1000 \
  --read-only \
  --tmpfs /tmp \
  ...
```

### 4. 宝塔面板安全

1. **修改面板端口**：
   - 进入 **【面板设置】**
   - 修改面板端口
   - 点击 **【保存】**

2. **修改面板用户名密码**：
   - 进入 **【面板设置】**
   - 修改为强密码

3. **绑定域名访问**：
   - 进入 **【面板设置】**
   - 绑定访问域名
   - 关闭 IP 访问

---

## 日常运维

### 查看日志

```bash
# 查看容器日志
docker logs -f videolingo

# 查看最近 100 行日志
docker logs --tail 100 videolingo

# 查看容器状态
docker ps -a | grep videolingo
```

在宝塔面板中：
1. 进入 **【Docker】**
2. 找到 videolingo 容器
3. 点击 **【日志】**

### 更新代码

```bash
# 停止并删除旧容器
docker stop videolingo
docker rm videolingo

# 拉取最新代码
cd /www/VideoLingo
git pull

# 重新构建镜像
docker build -t videolingo:latest .

# 运行新容器
docker run -d \
  --name videolingo \
  --restart unless-stopped \
  -p 8501:8501 \
  -v /www/VideoLingo/config.yaml:/app/config.yaml:ro \
  -v /www/VideoLingo/output:/app/output \
  -v /www/VideoLingo/_model_cache:/app/_model_cache \
  --memory="4g" \
  --cpus="2" \
  videolingo:latest
```

或使用宝塔面板：
1. 进入 **【Docker】**
2. 找到 videolingo 容器
3. 点击 **【重启】** 或 **【重建】**

### 进入容器调试

```bash
# 进入容器内部
docker exec -it videolingo bash

# 查看环境
python --version
pip list
```

### 备份配置

使用宝塔计划任务：

1. 进入 **【计划任务】**
2. 添加任务：

| 选项 | 值 |
|------|-----|
| 任务类型 | 备担网站 |
| 执行周期 | 每天 |
| 备份到 | 服务器磁盘 / 对象存储 |

3. 点击 **【提交】**

或手动备份：

```bash
# 备份配置和输出
tar czf /backup/videolingo-$(date +%Y%m%d).tar.gz /www/VideoLingo/config.yaml /www/VideoLingo/output

# 导出镜像
docker save videolingo:latest | gzip > /backup/videolingo-image-$(date +%Y%m%d).tar.gz
```

### 监控资源

在宝塔面板中：
1. 查看首页的 **CPU、内存、磁盘** 使用情况
2. 进入 **【Docker】** 查看容器资源占用

```bash
# 查看容器资源使用
docker stats videolingo
```

---

## 故障排查

### 1. 容器无法启动

```bash
# 查看容器日志
docker logs videolingo

# 查看容器详细信息
docker inspect videolingo

# 手动运行测试
docker run -it --rm \
  -p 8501:8501 \
  -v /www/VideoLingo/config.yaml:/app/config.yaml:ro \
  videolingo:latest
```

**常见问题**：
- 端口 8501 被占用：修改端口或停止占用进程
- 配置文件错误：检查 config.yaml 语法
- 内存不足：增加内存限制或减少并发

### 2. 502 Bad Gateway

```bash
# 检查容器是否运行
docker ps | grep videolingo

# 检查端口是否监听
netstat -tulpn | grep 8501

# 检查 Nginx 配置
nginx -t
```

### 3. 容器不断重启

```bash
# 查看重启原因
docker logs videolingo

# 禁用自动重启调试
docker update --restart=no videolingo

# 手动启动
docker start videolingo
```

### 4. 镜像构建失败

```bash
# 清理 Docker 缓存
docker system prune -a

# 重新构建
docker build --no-cache -t videolingo:latest .
```

### 5. API 调用失败

```bash
# 进入容器测试网络
docker exec -it videolingo bash
curl -v https://dashscope.aliyuncs.com

# 检查配置文件
docker exec videolingo cat /app/config.yaml
```

---

## Docker 常用命令

```bash
# 镜像操作
docker images                    # 查看镜像列表
docker rmi <image_id>           # 删除镜像
docker save -o image.tar videolingo:latest  # 导出镜像
docker load -i image.tar        # 导入镜像

# 容器操作
docker ps                       # 查看运行中的容器
docker ps -a                    # 查看所有容器
docker start/stop/restart videolingo  # 启动/停止/重启
docker rm videolingo            # 删除容器
docker exec -it videolingo bash # 进入容器

# 日志操作
docker logs videolingo          # 查看日志
docker logs -f videolingo       # 实时查看日志
docker logs --tail 100 videolingo  # 查看最后100行

# 资源管理
docker stats                    # 查看资源使用
docker system df                # 查看磁盘使用
docker system prune -a          # 清理未使用的资源
```

---

## 使用 Docker Compose（推荐）

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  videolingo:
    build: .
    container_name: videolingo
    restart: unless-stopped
    ports:
      - "8501:8501"
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./output:/app/output
      - ./_model_cache:/app/_model_cache
    environment:
      - TZ=Asia/Shanghai
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
        reservations:
          memory: 2G
          cpus: '1'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"
```

使用 Docker Compose 部署：

```bash
# 安装 Docker Compose（如果未安装）
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 启动服务
cd /www/VideoLingo
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 更新服务
docker-compose pull
docker-compose up -d --build
```

---

## 宝塔部署目录结构

```
/www/VideoLingo/
├── config.yaml           # 配置文件
├── Dockerfile            # Docker 镜像构建文件
├── docker-compose.yml    # Docker Compose 配置（可选）
├── .dockerignore         # Docker 忽略文件
├── output/               # 输出文件目录
├── _model_cache/         # 模型缓存目录
└── backup/               # 备份目录
```

---

## 完整 config.yaml 示例

```yaml
display_language: "zh-CN"

# 翻译 API
api:
  key: 'sk-your-api-key'
  base_url: 'https://yunwu.ai'
  model: 'gpt-4.1-2025-04-14'
  llm_support_json: false

max_workers: 4
target_language: '简体中文'
demucs: false

# ASR - Qwen
whisper:
  model: 'large-v3'
  language: 'zh'
  detected_language: 'zh'
  runtime: 'qwen'
  qwen_api_key: 'sk-your-qwen-key'

# TTS - Qwen
tts_method: 'qwen_tts'
qwen_tts:
  api_key: 'sk-your-qwen-key'
  voice: 'Cherry'
  model: 'qwen3-tts-flash'
  region: 'cn'

# 其他
model_dir: './_model_cache'
burn_subtitles: true
ffmpeg_gpu: false
```

---

## 优化建议

### 1. 使用多阶段构建进一步减小镜像体积（可选）

如果需要更小的镜像，可以使用多阶段构建：

```dockerfile
FROM python:3.10-slim as builder

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    git gcc g++ \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --branch feat-support-new-asr https://github.com/beansmile/VideoLingo.git .

# 只安装核心依赖到用户目录
RUN pip install --user --no-cache-dir \
    streamlit requests rich pyyaml json-repair \
    dashscope openai yt-dlp google-api-python-client \
    pysrt chardet

FROM python:3.10-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg curl fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 从构建阶段复制依赖和代码
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app

ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN mkdir -p /app/output /app/_model_cache /app/logs

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

EXPOSE 8501

CMD ["streamlit", "run", "st.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 2. 设置日志轮转

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "100m"
    max-file: "3"
```

### 3. 资源限制

根据服务器配置调整：
- 小型 VPS（2核4G）：`--memory="2g" --cpus="1"`
- 中型 VPS（4核8G）：`--memory="4g" --cpus="2"`
- 大型 VPS（8核16G）：`--memory="8g" --cpus="4"`

---

**文档版本**: v4.0.0 (宝塔 Docker 版)
**最后更新**: 2025-03-18
