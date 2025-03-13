import json
import os
import logging
import requests
from faster_whisper import WhisperModel
from moviepy.editor import VideoFileClip
import subprocess

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def translate_text(text, target_lang="中文", model="qwen:14b"):
    """
    使用本地 Ollama 模型进行文本翻译
    参数：
        text: 要翻译的文本
        target_lang: 目标语言（默认：中文）
        model: 使用的模型名称（默认：llama2）
    """
    # Ollama 的 API 地址（默认本地地址）
    OLLAMA_URL = "http://localhost:11434/api/generate"
    
    # 构造翻译指令
    prompt = f"""请将以下文本翻译成中文，保持专业准确，不要添加任何额外内容，仅忠实的反映原文的意思：
    
    {text}
    
    翻译结果："""
    
    # 请求数据
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3  # 控制生成结果的随机性
        }
    }
    
    try:
        response = requests.post(
            OLLAMA_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(data)
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["response"].strip()
        else:
            return f"请求失败，状态码：{response.status_code}"
            
    except Exception as e:
        return f"发生异常：{str(e)}"

# 从命令行参数中获取 model_path
# model_path = None
# local_files_only = False

# 模型加载将在 transcribe_video 函数中进行

def extract_audio(video_path, audio_path):
    try:
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path, codec='pcm_s16le')
        logging.info(f"音频已成功提取到 {audio_path}")
    except Exception as e:
        logging.error(f"提取音频时出错: {e}")
        raise

def transcribe_audio(audio_path, model, language):
    try:
        segments, _ = model.transcribe(audio_path, language=language)
        logging.info("语音转录已完成")
        return segments
    except Exception as e:
        logging.error(f"语音转录时出错: {e}")
        raise

def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def save_subtitles(segments, output_path, subtitle_format, translate=False, target_language="中文"):
    try:
        if subtitle_format == "srt":
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(segments, start=1):
                    start_time = format_timestamp(segment.start)
                    end_time = format_timestamp(segment.end)
                    text = segment.text
                    if translate:
                        translated_text = translate_text(text, target_language)
                        f.write(f"{i}\n{start_time} --> {end_time}\n{text}\n{translated_text}\n\n")
                    else:
                        f.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")
        elif subtitle_format == "vtt":
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("WEBVTT\n\n")
                for segment in segments:
                    start_time = format_timestamp(segment.start)
                    end_time = format_timestamp(segment.end)
                    text = segment.text
                    if translate:
                        translated_text = translate_text(text, target_language)
                        f.write(f"{start_time} --> {end_time}\n{text}\n{translated_text}\n\n")
                    else:
                        f.write(f"{start_time} --> {end_time}\n{text}\n\n")
        else:
            logging.error(f"不支持的字幕格式: {subtitle_format}")
            raise ValueError(f"不支持的字幕格式: {subtitle_format}")
        logging.info(f"字幕已成功保存到 {output_path}")
    except Exception as e:
        logging.error(f"保存字幕时出错: {e}")
        raise

def transcribe_video(video_path, output_path, subtitle_format, args):
    audio_path = "temp_audio.wav"
    try:
        extract_audio(video_path, audio_path)
        model = WhisperModel(args.model_path, device="cuda", compute_type="int8_float16")
        segments, info = model.transcribe(audio_path, language=args.language, beam_size=5, vad_filter=True)
        save_subtitles(segments, output_path, subtitle_format, translate=args.translate, target_language=args.target_language)
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)
            logging.info(f"临时音频文件 {audio_path} 已删除")

import argparse

def check_model_exists(model_path):
    return os.path.exists(model_path)

def main():
    parser = argparse.ArgumentParser(description="将视频中的语音提取并转化为字幕")
    parser.add_argument("video_path", type=str, help="视频文件路径")
    parser.add_argument("output_path", type=str, help="输出字幕文件路径")
    parser.add_argument("--subtitle_format", type=str, default="srt", help="字幕格式 (srt, vtt)")
    parser.add_argument("--language", type=str, default="auto", help="语言 (auto, en, ja, ko, zh)")
    parser.add_argument("--model_path", type=str, required=True, help="模型路径")
    parser.add_argument("--translate", action="store_true", help="是否翻译字幕")
    parser.add_argument("--target_language", type=str, default="中文", help="目标语言 (默认：中文)")
    args = parser.parse_args()

    if not check_model_exists(args.model_path):
        logging.error(f"模型文件不存在于路径: {args.model_path}")
        return

    base_output_path, ext = os.path.splitext(args.output_path)
    counter = 1
    while os.path.exists(args.output_path):
        args.output_path = f"{base_output_path}-{counter}{ext}"
        counter += 1

    transcribe_video(args.video_path, args.output_path, args.subtitle_format, args)

if __name__ == "__main__":
    main()
