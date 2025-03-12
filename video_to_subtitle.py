import json
import os
import logging
from faster_whisper import WhisperModel
from moviepy.editor import VideoFileClip
import subprocess

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

def save_subtitles(segments, output_path, subtitle_format):
    try:
        if subtitle_format == "srt":
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(segments, start=1):
                    start_time = segment.start
                    end_time = segment.end
                    text = segment.text
                    f.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")
        elif subtitle_format == "vtt":
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("WEBVTT\n\n")
                for segment in segments:
                    start_time = segment.start
                    end_time = segment.end
                    text = segment.text
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
        segments, info = model.transcribe(audio_path, language=args.language)
        save_subtitles(segments, output_path, subtitle_format)
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
    args = parser.parse_args()

    if not check_model_exists(args.model_path):
        logging.error(f"模型文件不存在于路径: {args.model_path}")
        return
    else:
        transcribe_video(args.video_path, args.output_path, args.subtitle_format, args)

if __name__ == "__main__":
    main()
