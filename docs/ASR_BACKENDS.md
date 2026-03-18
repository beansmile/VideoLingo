# ASR 后端集成文档

## 概述

本文档记录了 VideoLingo 项目中可用的 ASR（自动语音识别）后端，包括现有的和计划集成的阿里云百炼平台模型。

## 现有 ASR 后端

### 1. WhisperX Local
- **类型**: 本地部署
- **模型**: HuggingFace Whisper 模型
- **语言支持**: 多语言（通过模型选择）
- **特点**:
  - 支持离线使用
  - 可自定义模型
  - 支持语音对齐
- **配置**: 通过 `whisper.runtime=local` 启用
- **文件**: `core/asr_backend/whisperX_local.py`

### 2. WhisperX 302 Cloud
- **类型**: 云服务
- **提供商**: Whisper 302 API
- **语言支持**: 多语言
- **特点**:
  - 云端处理，无需本地 GPU
  - 稳定可靠
- **配置**: 通过 `whisper.runtime=cloud` 启用
- **文件**: `core/asr_backend/whisperX_302.py`

### 3. ElevenLabs ASR
- **类型**: 云服务
- **提供商**: ElevenLabs
- **语言支持**: 多语言
- **特点**:
  - 专业的语音识别服务
  - 支持说话人分离
  - OpenAI 兼容 API
- **配置**: 通过 `whisper.runtime=elevenlabs` 启用
- **文件**: `core/asr_backend/elevenlabs_asr.py`

## 计划集成的阿里云百炼 ASR 模型

### 1. Qwen-ASR
- **模型类型**: 千问系列 ASR
- **提供商**: 阿里云百炼
- **接入方式**:
  - 千问 3-ASR-Flash-Filetrans: 仅支持 DashScope 异步调用
  - 千问 3-ASR-Flash: 支持 OpenAI 兼容和 DashScope 同步调用
  - 千问 Audio ASR: 仅支持 DashScope 同步调用
- **语言支持**: 中文优化
- **API 类型**: OpenAI 兼容 API
- **特点**:
  - 中文语音识别优化
  - 多种模型选择
  - 灵活的调用方式

### 2. Paraformer
- **模型类型**: 专业录音文件识别
- **提供商**: 阿里云百炼
- **模型列表**:
  - paraformer-v2: 直播、会议等多语种识别
  - paraformer-8k-v2: 电话客服、语音信箱等中文识别
- **SDK 支持**: Python、Java、Android、iOS
- **API 类型**: RESTful API
- **特点**:
  - 专业场景优化
  - 多平台 SDK 支持
  - 中文专业识别

### 3. Fun-ASR
- **模型类型**: Fun-ASR 录音文件识别
- **提供商**: 阿里云百炼
- **版本**: fun-asr-2025-11-07（最新版本）
- **区域支持**: 中国内地和国际部署
- **SDK 支持**: Python、Java、Android、iOS
- **API 类型**: RESTful API
- **特点**:
  - 最新技术版本
  - 通用场景支持
  - 多平台集成

## 实施计划

### 阶段 1: 文档和准备 (1-2天)
1. 创建此文档
2. 研究阿里云百炼 API 文档
3. 获取 API 密钥和测试权限
4. 确定配置方案

### 阶段 2: Qwen-ASR 集成 (3-4天)
1. 创建 `qwen_asr.py` 后端文件
2. 实现 OpenAI 兼容 API 调用
3. 添加配置选项
4. 测试基本功能

### 阶段 3: Paraformer 集成 (2-3天)
1. 创建 `paraformer_asr.py` 后端文件
2. 实现 RESTful API 调用
3. 添加模型选择逻辑
4. 测试专业场景功能

### 阶段 4: Fun-ASR 集成 (2-3天)
1. 创建 `fun_asr.py` 后端文件
2. 实现 RESTful API 调用
3. 测试最新版本功能
4. 优化性能

### 阶段 5: 配置和测试 (2-3天)
1. 更新主配置系统
2. 添加运行时选择逻辑
3. 全面测试所有后端
4. 性能优化

### 阶段 6: 文档和部署 (1-2天)
1. 更新用户文档
2. 添加示例配置
3. 部署到生产环境
4. 监控和优化

## 技术实现方案

### 后端文件结构
```
core/asr_backend/
├── whisperX_local.py      # 现有
├── whisperX_302.py       # 现有  
├── elevenlabs_asr.py     # 现有
├── qwen_asr.py           # 待实现
├── paraformer_asr.py     # 待实现
└── fun_asr.py           # 待实现
```

### 主配置更新
在 `_2_asr.py` 中添加新的运行时选项：
```python
elif runtime == "qwen":
    from core.asr_backend.qwen_asr import transcribe_audio_qwen as ts
    rprint("[cyan]🎤 Transcribing audio with Qwen-ASR...[/cyan]")
elif runtime == "paraformer":
    from core.asr_backend.paraformer_asr import transcribe_audio_paraformer as ts
    rprint("[cyan]🎤 Transcribing audio with Paraformer...[/cyan]")
elif runtime == "fun-asr":
    from core.asr_backend.fun_asr import transcribe_audio_fun as ts
    rprint("[cyan]🎤 Transcribing audio with Fun-ASR...[/cyan]")
```

### 配置文件更新
在配置系统中添加新的 ASR 后端选项：
```python
# whisper.runtime 可选值:
# local, cloud, elevenlabs, qwen, paraformer, fun-asr
```

## 预期收益

1. **中文优化**: 所有阿里云模型都针对中文进行了优化，提升中文语音识别准确率
2. **多场景支持**: 不同模型适用于不同场景（直播、客服、通用等）
3. **灵活选择**: 用户可以根据需求选择最适合的 ASR 后端
4. **官方支持**: 获得阿里云官方技术支持和维护
5. **成本优化**: 可根据使用场景选择最经济的方案

## 风险评估

1. **API 限制**: 阿里云 API 可能有限制或配额
2. **成本不确定性**: 需要详细了解定价模型
3. **性能差异**: 不同模型的转录速度和准确率可能不同
4. **集成复杂度**: RESTful API 调用比 OpenAI 兼容 API 更复杂

## 下一步行动

1. 开始实现 Qwen-ASR 后端
2. 获取阿里云 API 密钥
3. 创建测试脚本
4. 进行初步性能测试

--- 

*最后更新: 2026-03-17*