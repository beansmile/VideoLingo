# ASR 后端配置文档

## 概述

本文档详细说明了如何配置和使用 VideoLingo 项目中的各种 ASR（自动语音识别）后端。

## 配置文件

配置主要通过 `core/utils/config_utils.py` 中的 `load_key()` 和 `update_key()` 函数进行管理。

## ASR 运行时配置

### 1. 选择 ASR 后端

在配置文件中设置 `whisper.runtime` 来选择要使用的 ASR 后端：

```python
# whisper.runtime 可选值:
# local, cloud, elevenlabs, qwen, paraformer, fun-asr
whisper.runtime = "qwen"  # 使用 Qwen-ASR
```

### 2. 语言配置

设置要识别的语言：

```python
# whisper.language 可选值:
# en, zh, auto, etc.
whisper.language = "zh"  # 中文
```

### 3. API 密钥配置

为云服务 ASR 后端设置 API 密钥：

```python
# Qwen-ASR API 密钥
whisper.qwen_api_key = "your_qwen_api_key_here"

# Paraformer API 密钥  
whisper.paraformer_api_key = "your_paraformer_api_key_here"

# Fun-ASR API 密钥
whisper.fun_asr_api_key = "your_fun_asr_api_key_here"

# ElevenLabs API 密钥
whisper.elevenlabs_api_key = "your_elevenlabs_api_key_here"
```

## 配置示例

### 示例 1: 使用 Qwen-ASR（中文）

```ini
[whisper]
runtime = "qwen"
language = "zh"
qwen_api_key = "your_qwen_api_key_here"
```

### 示例 2: 使用 Paraformer（多语种）

```ini
[whisper]
runtime = "paraformer"
language = "en"
paraformer_api_key = "your_paraformer_api_key_here"
```

### 示例 3: 使用 Fun-ASR（最新版本）

```ini
[whisper]
runtime = "fun-asr"
language = "auto"
fun_asr_api_key = "your_fun_asr_api_key_here"
```

### 示例 4: 使用 ElevenLabs（专业语音识别）

```ini
[whisper]
runtime = "elevenlabs"
language = "auto"
elevenlabs_api_key = "your_elevenlabs_api_key_here"
```

## 测试配置

### 测试模式

可以设置 `whisper.test_mode` 来启用测试模式，这将使用模拟数据而不是实际 API 调用：

```ini
[whisper]
test_mode = true
```

### 日志配置

可以配置日志级别和输出：

```ini
[logging]
level = "INFO"
file = "output/log/asr.log"
```

## 性能配置

### 批处理大小

对于本地 ASR 模型，可以配置批处理大小：

```ini
[whisper]
batch_size = 16  # 本地模型的批处理大小
```

### 并发限制

可以配置并发转录任务的数量：

```ini
[whisper]
max_concurrent = 4  # 最大并发任务数
```

## 错误处理配置

### 重试策略

配置重试次数和延迟：

```ini
[whisper]
max_retries = 3
retry_delay = 5  # 重试延迟（秒）
```

### 超时设置

配置 API 调用超时：

```ini
[whisper]
timeout = 30  # API 调用超时（秒）
```

## 部署配置

### 环境变量

可以通过环境变量设置配置：

```bash
export WHISPER_RUNTIME="qwen"
export WHISPER_LANGUAGE="zh"
export WHISPER_QWEN_API_KEY="your_api_key"
```

### Docker 配置

在 Docker 环境中，可以通过环境变量或配置文件挂载：

```dockerfile
ENV WHISPER_RUNTIME=qwen
ENV WHISPER_LANGUAGE=zh
ENV WHISPER_QWEN_API_KEY=your_api_key
```

## 监控配置

### 健康检查

配置健康检查间隔：

```ini
[monitoring]
health_check_interval = 60  # 健康检查间隔（秒）
```

### 性能监控

配置性能指标收集：

```ini
[monitoring]
collect_metrics = true
metrics_interval = 300  # 指标收集间隔（秒）
```

## 故障排除

### 常见问题

1. **API 密钥无效**
   - 检查 API 密钥是否正确
   - 确认密钥有足够的权限
   - 检查网络连接

2. **模型加载失败**
   - 检查模型文件是否存在
   - 确认 GPU 内存足够
   - 检查 PyTorch 版本兼容性

3. **音频处理错误**
   - 检查音频文件格式
   - 确认音频文件可读
   - 检查音频编码

4. **API 调用超时**
   - 增加超时设置
   - 检查网络连接
   - 确认 API 服务可用

### 调试模式

启用调试模式以获取详细日志：

```ini
[whisper]
debug = true
```

## 最佳实践

1. **测试配置**：在正式使用前测试所有配置
2. **错误处理**：实现适当的错误处理和重试机制
3. **性能监控**：监控 ASR 性能和资源使用
4. **安全**：保护 API 密钥，不要硬编码在代码中
5. **文档**：记录配置变更和最佳实践

--- 

*最后更新: 2026-03-17*
