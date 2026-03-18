"""Qwen-TTS backend for VideoLingo

使用阿里云通义千问 TTS 服务进行语音合成。
支持基础 TTS 合成（系统音色），非流式输出。

文档: https://help.aliyun.com/zh/model-studio/qwen-tts
"""
import os
from pathlib import Path
from rich import print as rprint

from core.utils import load_key, except_handler

# 支持的音色列表（部分常用音色）
# 完整列表请参考: https://help.aliyun.com/zh/model-studio/qwen-tts
VOICE_LIST = [
    "Cherry",      # 芊悦 - 阳光积极、亲切自然小姐姐（女性）
    "Serena",      # 苏瑶 - 温柔小姐姐（女性）
    "Ethan",       # 晨煦 - 阳光、温暖、活力、朝气（男性）
    "Chelsie",     # 千雪 - 二次元虚拟女友（女性）
    "Momo",        # 茉兔 - 撒娇搞怪，逗你开心（女性）
    "Vivian",      # 十三 - 拽拽的、可爱的小暴躁（女性）
    "Moon",        # 月白 - 率性帅气的月白（男性）
    "Maia",        # 四月 - 知性与温柔的碰撞（女性）
    "Kai",         # 凯 - 耳朵的一场SPA（男性）
    "Nofish",      # 不吃鱼 - 不会翘舌音的设计师（男性）
]

# 支持的模型列表
MODEL_LIST = [
    "qwen3-tts-flash",              # 推荐用于基础 TTS
    "qwen3-tts-flash-2025-11-27",
    "qwen3-tts-instruct-flash",     # 支持指令控制
    "qwen3-tts-instruct-flash-2026-01-26",
]

# API 端点配置
# 北京地域（中国内地）
BASE_URL_CN = "https://dashscope.aliyuncs.com/api/v1"
# 新加坡地域（国际）
BASE_URL_INTL = "https://dashscope-intl.aliyuncs.com/api/v1"


@except_handler("Failed to generate audio using Qwen TTS", retry=3, delay=1)
def qwen_tts(text: str, save_as: str) -> bool:
    """使用 Qwen-TTS 生成语音

    Args:
        text: 要合成的文本
        save_as: 保存音频文件的路径

    Returns:
        bool: 成功返回 True，失败返回 False
    """
    try:
        import dashscope
    except ImportError:
        rprint("[red]❌ DashScope SDK not found. Please install: pip install dashscope[/red]")
        raise Exception("DashScope SDK is required. Please install: pip install dashscope")

    # 加载配置
    api_key = load_key("qwen_tts.api_key")
    voice = load_key("qwen_tts.voice")
    model = load_key("qwen_tts.model")
    region = load_key("qwen_tts.region")

    # 验证音色
    if voice not in VOICE_LIST:
        rprint(f"[yellow]⚠️  Warning: Voice '{voice}' not in common voice list.[/yellow]")
        rprint(f"[yellow]    Common voices: {', '.join(VOICE_LIST[:5])}...[/yellow]")

    # 设置 API 端点
    if region == "intl":
        dashscope.base_http_api_url = BASE_URL_INTL
    else:
        dashscope.base_http_api_url = BASE_URL_CN

    rprint(f"[cyan]🔊 Qwen-TTS: Generating audio...[/cyan]")
    rprint(f"[dim]    Model: {model}[/dim]")
    rprint(f"[dim]    Voice: {voice}[/dim]")
    rprint(f"[dim]    Text: {text[:50]}{'...' if len(text) > 50 else ''}[/dim]")

    # 创建输出目录
    speech_file_path = Path(save_as)
    speech_file_path.parent.mkdir(parents=True, exist_ok=True)

    # 调用 Qwen-TTS API
    response = dashscope.MultiModalConversation.call(
        model=model,
        api_key=api_key,
        text=text,
        voice=voice,
        stream=False  # 非流式输出，返回 URL
    )

    # 检查响应状态
    if response.status_code != 200:
        error_msg = f"Qwen-TTS API error: {response.status_code} - {response.message}"
        rprint(f"[red]❌ {error_msg}[/red]")
        raise Exception(error_msg)

    # 获取音频 URL
    audio_url = response.output.audio.url
    if not audio_url:
        error_msg = "No audio URL found in Qwen-TTS response"
        rprint(f"[red]❌ {error_msg}[/red]")
        raise Exception(error_msg)

    rprint(f"[green]✓ Audio URL received, downloading...[/green]")

    # 下载音频文件
    import requests
    audio_response = requests.get(audio_url, timeout=30)
    audio_response.raise_for_status()

    # 保存音频文件
    with open(speech_file_path, 'wb') as f:
        f.write(audio_response.content)

    rprint(f"[green]✓ Audio saved to {speech_file_path}[/green]")
    return True


def get_available_voices():
    """获取可用的音色列表

    Returns:
        list: 音色名称列表
    """
    return VOICE_LIST


def get_available_models():
    """获取可用的模型列表

    Returns:
        list: 模型名称列表
    """
    return MODEL_LIST


if __name__ == "__main__":
    # 测试代码
    test_text = "你好，我是通义千问的语音合成服务。今天天气真不错！"
    qwen_tts(test_text, "qwen_tts_test.wav")
    print("Test completed!")
