FROM python:3.10

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ==============================================================================
# 国内镜像源配置 - 加速下载
# ==============================================================================

# 替换 Debian APT 源为阿里云镜像
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.ubuntu.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    curl \
    ffmpeg \
    fonts-noto \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 配置 pip 使用清华 PyPI 镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn

# Set working directory
WORKDIR /app

# 克隆项目（使用 beansmile 的 fork，分支 feat-support-new-asr）
RUN git clone --branch feat-support-new-asr https://github.com/beansmile/VideoLingo.git . && \
    rm -rf .git

# ==============================================================================
# 安装 PyTorch (CPU 版本)
# 根据 install.py，使用 PyTorch 2.8.0
# ==============================================================================
RUN pip install --no-cache-dir torch==2.8.0 torchaudio==2.8.0

# ==============================================================================
# 安装 Qwen API 相关依赖（dashscope）
# Qwen-ASR 和 Qwen-TTS 需要使用 dashscope SDK
# ==============================================================================
RUN pip install --no-cache-dir dashscope

# ==============================================================================
# 安装 demucs（使用 --no-deps 避免 torchaudio 冲突）
# 参考 install.py 第 201-209 行
# ==============================================================================
RUN pip install --no-cache-dir --no-deps "demucs[dev]@git+https://github.com/adefossez/demucs" && \
    pip install --no-cache-dir dora-search openunmix lameenc

# ==============================================================================
# 安装项目依赖
# 参考 install.py 第 211-212 行
# ==============================================================================
RUN pip install --no-cache-dir -e .

# ==============================================================================
# Spacy 模型 - 从本地文件夹复制
#
# 使用方法：
# 1. 本地下载模型（使用代理）：
#    - https://github.com/explosion/spacy-models/releases/download/en_core_web_md-3.8.0/en_core_web_md-3.8.0-py3-none-any.whl
#    - https://github.com/explosion/spacy-models/releases/download/zh_core_web_md-3.8.0/zh_core_web_md-3.8.0-py3-none-any.whl
# 2. 上传到服务器的 /www/VideoLingo/spacy_models/ 目录
# 3. 构建 Docker 镜像时会自动安装
# ==============================================================================
COPY spacy_models/ /tmp/spacy_models/
RUN pip install --no-cache-dir /tmp/spacy_models/*.whl && \
    rm -rf /tmp/spacy_models

# 创建必要的目录
RUN mkdir -p /app/output /app/_model_cache /app/logs

# 暴露端口
EXPOSE 8501

# 启动命令
CMD ["streamlit", "run", "st.py", "--server.port=8501", "--server.address=0.0.0.0"]
