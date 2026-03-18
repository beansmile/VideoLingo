import json
import os
import time
from pathlib import Path

import requests
from rich import print as rprint

from core.utils import *
from core.asr_backend.dashscope_asr import (
    upload_and_get_url,
    poll_task_status,
    download_transcription,
    parse_transcription_with_words,
    save_and_return_result,
)

# Qwen-ASR 配置
QWEN_MODEL = "qwen3-asr-flash-filetrans"
QWEN_SUBMIT_API = "https://dashscope.aliyuncs.com/api/v1/services/audio/asr/transcription"
QWEN_TASK_API = "https://dashscope.aliyuncs.com/api/v1/tasks"


def transcribe_audio_qwen(raw_audio_path, vocal_audio_path, start=None, end=None):
    rprint(
        f"[cyan]🎤 Processing audio transcription with Qwen-ASR, file path: {vocal_audio_path}[/cyan]"
    )
    LOG_FILE = f"output/log/qwen_transcribe_{start}_{end}.json"

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    # 验证文件存在
    if not os.path.exists(vocal_audio_path):
        rprint(f"[red]❌ Audio file not found: {vocal_audio_path}[/red]")
        raise FileNotFoundError(f"Audio file not found: {vocal_audio_path}")

    # 默认时间范围
    if start is None:
        start = 0
    if end is None:
        end = start

    try:
        # 加载 API Key
        api_key = load_key("whisper.qwen_api_key")

        rprint(
            f"[yellow]📤 Starting transcription process with DashScope SDK...[/yellow]"
        )
        start_time = time.time()

        # 步骤1: 上传文件并获取 URL
        file_url = upload_and_get_url(api_key, vocal_audio_path)

        # 步骤2: 提交异步转录任务
        rprint("[yellow]📤 Submitting async transcription task...[/yellow]")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }

        # Qwen-ASR 使用 file_url（单数）
        payload = {
            "model": QWEN_MODEL,
            "input": {
                "file_url": file_url
            },
            "parameters": {
                "channel_id": [0],
                "enable_itn": False,
                "enable_words": True,
            },
        }

        rprint(f"[dim]Payload file_url length: {len(payload['input']['file_url'])}[/dim]")

        submit_response = requests.post(QWEN_SUBMIT_API, headers=headers, json=payload)

        if submit_response.status_code != 200:
            rprint(f"[red]❌ Submit failed with status {submit_response.status_code}[/red]")
            rprint(f"[dim]Response: {submit_response.text[:500]}[/dim]")
            raise Exception(f"Failed to submit task: {submit_response.text}")

        submit_result = submit_response.json()
        task_id = submit_result["output"]["task_id"]
        rprint(f"[green]✓ Task submitted successfully, task_id: {task_id}[/green]")

        # 步骤3: 轮询等待任务完成
        transcription_url = poll_task_status(
            QWEN_TASK_API, task_id, api_key, query_method="GET"
        )

        # 步骤4: 下载并解析转录结果
        transcription_data = download_transcription(transcription_url)

        # 步骤5: 解析为 WhisperX 格式
        parsed_result = parse_transcription_with_words(transcription_data, time_offset=start)

        rprint(
            f"[green]✓ Transcription completed in {time.time() - start_time:.2f} seconds[/green]"
        )

        return save_and_return_result(parsed_result, LOG_FILE)

    except Exception as e:
        rprint(f"[red]❌ Failed to transcribe audio: {e}[/red]")
        raise


# 测试函数
if __name__ == "__main__":
    file_path = input("Enter local audio file path: ")
    result = transcribe_audio_qwen(file_path, file_path)
    print(f"Transcription result: {result}")

    # Save result to file
    os.makedirs("output", exist_ok=True)
    with open("output/transcript.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
