"""DashScope ASR 通用方法

所有使用 DashScope API 的 ASR 后端共享的通用逻辑。
"""
import json
import os
import time
import requests
from rich import print as rprint


def upload_and_get_url(api_key, file_path):
    """上传文件到 DashScope 并获取公网 URL

    Args:
        api_key: DashScope API Key
        file_path: 本地音频文件路径

    Returns:
        str: 文件的公网 URL
    """
    try:
        from dashscope import Files
    except ImportError:
        rprint("[red]❌ DashScope SDK not found. Please install: pip install dashscope[/red]")
        raise Exception("DashScope SDK is required. Please install: pip install dashscope")

    rprint("[yellow]📤 Uploading audio file to DashScope...[/yellow]")

    # 上传文件
    upload_result = Files.upload(
        file_path=file_path,
        purpose='inference',
        api_key=api_key
    )

    if upload_result.status_code != 200:
        raise Exception(f"Failed to upload file: {upload_result.message}")

    # 获取上传的文件信息
    uploaded_files = upload_result.output.get('uploaded_files', [])
    if not uploaded_files:
        raise Exception("No files were uploaded")

    file_id = uploaded_files[0]['file_id']
    rprint(f"[green]✓ File uploaded successfully, file_id: {file_id}[/green]")

    # 获取文件的公网 URL
    rprint("[yellow]📤 Getting file URL...[/yellow]")
    file_info_result = Files.get(file_id=file_id, api_key=api_key)

    if file_info_result.status_code != 200:
        raise Exception(f"Failed to get file info: {file_info_result.message}")

    file_url = file_info_result.output.get('url')
    if not file_url:
        raise Exception("No URL found for uploaded file")

    rprint(f"[green]✓ File URL obtained (length: {len(file_url)})[/green]")
    rprint(f"[dim]URL: {file_url[:80]}...[/dim]")

    # 验证 URL 格式
    if not file_url.startswith("http://") and not file_url.startswith("https://"):
        raise Exception(f"Invalid URL format: {file_url[:100]}")

    return file_url


def poll_task_status(task_api_url, task_id, api_key, query_method="GET", max_retries=120, retry_interval=3):
    """轮询任务状态直到完成

    Args:
        task_api_url: 任务 API 基础 URL
        task_id: 任务 ID
        api_key: DashScope API Key
        query_method: 查询方法 "GET" 或 "POST"
        max_retries: 最大重试次数
        retry_interval: 重试间隔（秒）

    Returns:
        str: 转录结果的下载 URL
    """
    rprint("[yellow]⏳ Waiting for task completion...[/yellow]")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    for attempt in range(max_retries):
        query_url = f"{task_api_url}/{task_id}"

        if query_method == "GET":
            query_response = requests.get(query_url, headers=headers)
        else:  # POST
            query_response = requests.post(query_url, headers=headers)

        if query_response.status_code != 200:
            raise Exception(f"Failed to get task status: {query_response.text}")

        query_result = query_response.json()
        task_status = query_result.get("output", {}).get("task_status")

        rprint(f"[yellow]⏳ Current status: {task_status}[/yellow]")

        if task_status == "SUCCEEDED":
            rprint("[green]✓ Task completed successfully[/green]")

            # 获取转录结果 URL
            # 格式1: result.transcription_url (qwen, fun)
            result = query_result.get("output", {}).get("result", {})
            if result.get("transcription_url"):
                return result["transcription_url"]

            # 格式2: results[0].transcription_url (paraformer)
            results = query_result.get("output", {}).get("results", [])
            if results and results[0].get("transcription_url"):
                return results[0]["transcription_url"]

            raise Exception("No transcription_url found in task response")

        elif task_status == "FAILED":
            error_message = query_result.get("output", {}).get("message", "Unknown error")
            raise Exception(f"ASR task failed: {error_message}")

        elif task_status in ["PENDING", "RUNNING"]:
            time.sleep(retry_interval)
        else:
            raise Exception(f"Unknown task status: {task_status}")

    raise Exception("Task timeout: exceeded maximum retry attempts")


def download_transcription(transcription_url):
    """下载转录结果

    Args:
        transcription_url: 转录结果的下载 URL

    Returns:
        dict: 解析后的转录数据
    """
    rprint("[yellow]📥 Downloading transcription results...[/yellow]")

    result_response = requests.get(transcription_url)
    if result_response.status_code != 200:
        raise Exception(f"Failed to download transcription: {result_response.status_code}")

    return result_response.json()


def parse_words_with_punctuation(words_data, time_offset=0):
    """解析词级别数据，合并词语和标点符号

    Args:
        words_data: 原始 words 数据列表
        time_offset: 时间偏移量（秒）

    Returns:
        list: 解析后的 words 列表
    """
    sentence_words = []

    for word_data in words_data:
        word_text = word_data.get("text", "")
        word_punctuation = word_data.get("punctuation", "")
        # 合并词语和标点符号
        full_word = word_text + word_punctuation

        word_start = word_data.get("begin_time", 0) / 1000 + time_offset  # 毫秒转秒
        word_end = word_data.get("end_time", 0) / 1000 + time_offset

        # 跳过空词语
        if not full_word.strip():
            continue

        sentence_words.append({
            "word": full_word,
            "start": word_start,
            "end": word_end
        })

    return sentence_words


def parse_transcription_with_words(transcription_data, time_offset=0):
    """解析转录结果（包含词级别信息），转换为 WhisperX 格式

    适用于 Qwen-ASR 和 Fun-ASR

    Args:
        transcription_data: 下载的转录 JSON 数据
        time_offset: 时间偏移量（秒）

    Returns:
        dict: WhisperX 格式的结果
    """
    transcripts = transcription_data.get("transcripts", [])
    if not transcripts:
        raise Exception("No transcription results found")

    all_segments = []

    for transcript in transcripts:
        sentences = transcript.get("sentences", [])
        for sentence in sentences:
            sentence_text = sentence.get("text", "")
            sentence_start = sentence.get("begin_time", 0) / 1000 + time_offset
            sentence_end = sentence.get("end_time", 0) / 1000 + time_offset

            # 解析 words 字段
            sentence_words = parse_words_with_punctuation(
                sentence.get("words", []),
                time_offset=time_offset
            )

            all_segments.append({
                "text": sentence_text,
                "start": sentence_start,
                "end": sentence_end,
                "words": sentence_words,
            })

    return {"segments": all_segments}


def parse_transcription_simple(transcription_data, time_offset=0):
    """解析转录结果（简化版，无词级别信息），转换为 WhisperX 格式

    适用于 Paraformer（词级别信息放在 segment 外）

    Args:
        transcription_data: 下载的转录 JSON 数据
        time_offset: 时间偏移量（秒）

    Returns:
        dict: WhisperX 格式的结果
    """
    transcripts = transcription_data.get("transcripts", [])
    if not transcripts:
        raise Exception("No transcripts found")

    # 获取文本内容
    full_text = transcripts[0].get("text", "")

    # 获取句子级别的详细信息
    sentences = transcripts[0].get("sentences", [])

    # 构建 WhisperX 格式的结果
    segments = []
    words = []

    for sentence in sentences:
        begin_time = sentence.get("begin_time", 0) / 1000.0 + time_offset
        end_time = sentence.get("end_time", 0) / 1000.0 + time_offset

        segments.append({
            "text": sentence.get("text", ""),
            "start": begin_time,
            "end": end_time
        })

        # 收集词级别的信息
        for word in sentence.get("words", []):
            words.append({
                "word": word.get("text", ""),
                "start": word.get("begin_time", 0) / 1000.0 + time_offset,
                "end": word.get("end_time", 0) / 1000.0 + time_offset
            })

    parsed_result = {
        "segments": segments,
        "words": words if words else []
    }

    return parsed_result


def save_and_return_result(result, log_file):
    """保存结果到日志文件并返回

    Args:
        result: 要保存的结果字典
        log_file: 日志文件路径

    Returns:
        dict: 输入的结果
    """
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
    return result


def create_empty_result(start, end):
    """创建空的转录结果（用于错误情况）

    Args:
        start: 开始时间
        end: 结束时间

    Returns:
        dict: 空的 WhisperX 格式结果
    """
    return {
        "segments": [{
            "text": "",
            "start": start,
            "end": end,
            "words": []
        }]
    }
