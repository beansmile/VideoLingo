import os
import json
import time
import requests
import tempfile
import librosa
import numpy as np
from rich import print as rprint
from core.utils import *
from core.asr_backend.dashscope_asr import (
    upload_and_get_url,
    poll_task_status,
    download_transcription,
    parse_transcription_simple,
    save_and_return_result,
)

# Paraformer 配置
PARAFORMER_SUBMIT_API = "https://dashscope.aliyuncs.com/api/v1/services/audio/asr/transcription"
PARAFORMER_TASK_API = "https://dashscope.aliyuncs.com/api/v1/tasks"
PARAFORMER_MODELS = {
    "paraformer-v2": "paraformer-v2",
    "paraformer-8k-v2": "paraformer-8k-v2"
}


def transcribe_audio_paraformer(raw_audio_path, vocal_audio_path, start=None, end=None):
    rprint(f"[cyan]🎤 Processing audio transcription with Paraformer, file path: {vocal_audio_path}[/cyan]")
    LOG_FILE = f"output/log/paraformer_transcribe_{start}_{end}.json"

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    # 默认时间范围
    if start is None:
        start = 0
    if end is None:
        end = start

    try:
        api_key = load_key("whisper.paraformer_api_key")

        rprint(f"[yellow]📤 Starting transcription process with DashScope...[/yellow]")
        start_time = time.time()

        # 步骤1: 上传文件并获取 URL
        file_url = upload_and_get_url(api_key, vocal_audio_path)

        # 步骤2: 提交异步识别任务
        rprint(f"[yellow]📤 Submitting recognition task...[/yellow]")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable"
        }

        # 选择模型（默认使用 paraformer-v2）
        model_name = PARAFORMER_MODELS.get("paraformer-v2")

        # Paraformer 使用 file_urls（数组）
        data = {
            "model": model_name,
            "input": {
                "file_urls": [file_url]
            },
            "parameters": {
                "channel_id": [0],
                # language_hints 仅适用于 paraformer-v2 模型
                "language_hints": [load_key("whisper.language")]
            }
        }

        response = requests.post(PARAFORMER_SUBMIT_API, headers=headers, json=data)

        rprint(f"[yellow]API request sent, status code: {response.status_code}[/yellow]")

        if response.status_code != 200:
            rprint(f"[red]❌ API Error: {response.text}[/red]")
            raise Exception(f"Paraformer API error: {response.text}")

        submit_result = response.json()
        task_id = submit_result.get("output", {}).get("task_id")

        if not task_id:
            raise Exception(f"Failed to get task_id from response: {submit_result}")

        rprint(f"[green]✓ Task submitted successfully, task_id: {task_id}[/green]")

        # 步骤3: 轮询等待任务完成（Paraformer 使用 POST）
        transcription_url = poll_task_status(
            PARAFORMER_TASK_API, task_id, api_key, query_method="POST"
        )

        # 步骤4: 下载并解析转录结果
        transcription_data = download_transcription(transcription_url)

        # 步骤5: 解析为 WhisperX 格式
        parsed_result = parse_transcription_simple(transcription_data, time_offset=start)

        rprint(f"[green]✓ Transcription completed in {time.time() - start_time:.2f} seconds[/green]")
        rprint(f"[green]✓ Transcribed text: {parsed_result['segments'][0]['text'][:100] if parsed_result['segments'] else ''}{'...' if parsed_result['segments'] and len(parsed_result['segments'][0]['text']) > 100 else ''}[/green]")

        return save_and_return_result(parsed_result, LOG_FILE)

    except Exception as e:
        rprint(f"[red]❌ Transcription failed: {e}[/red]")
        # 返回空结果或错误信息
        return {
            "segments": [{
                "text": "",
                "start": start,
                "end": end,
                "words": []
            }]
        }


# 测试函数
if __name__ == "__main__":
    file_path = input("Enter local audio file path (mp3 format): ")
    language = input("Enter language code for transcription (en or zh or other...): ")
    result = transcribe_audio_paraformer(file_path, file_path, start=0, end=1.0)
    print(result)

    # Save result to file
    with open("output/transcript.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
