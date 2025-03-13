import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
import sys
import json
import threading
import time
import shutil
import requests
import zipfile
import io
import logging
from pathlib import Path
from faster_whisper import WhisperModel

# Function to load configuration
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    with open(config_path, "r") as config_file:
        config = json.load(config_file)
    return config

# Function to download the model
def download_model(model_path):
    model_url = "https://example.com/path/to/faster-whisper-large-v3-turbo.zip"
    response = requests.get(model_url)
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        z.extractall(model_path)

# Function to check if the model exists
def check_model_exists(model_path):
    return os.path.exists(model_path)

# Function to select video file
def select_video_file():
    video_file = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mkv *.mov *.flv *.wmv *.webm"), ("Audio files", "*.mp3 *.wav *.aac *.flac *.ogg")])
    video_file_entry.delete(0, tk.END)
    video_file_entry.insert(0, video_file)

# Function to select output directory
def select_output_directory():
    output_directory = filedialog.askdirectory()
    output_directory_entry.delete(0, tk.END)
    output_directory_entry.insert(0, output_directory)

# Function to select model path
def select_model_path():
    model_path = filedialog.askdirectory()
    model_path_entry.delete(0, tk.END)
    model_path_entry.insert(0, model_path)

# Function to select folder
def select_folder():
    folder = filedialog.askdirectory()
    folder_entry.delete(0, tk.END)
    folder_entry.insert(0, folder)

# Function to run transcription with model path
def run_transcription():
    video_file = video_file_entry.get()
    folder = folder_entry.get()
    output_directory = output_directory_entry.get()
    language = language_var.get()
    model_path = model_path_entry.get()

    if not output_directory:
        messagebox.showerror("Error", "Please select an output directory.")
        return

    if not model_path:
        messagebox.showerror("Error", "Please select a model path.")
        return

    if not check_model_exists(model_path):
        messagebox.showinfo("Info", "Model not found. Downloading model...")
        download_model(model_path)
        messagebox.showinfo("Info", "Model downloaded successfully.")

    # Change the current working directory to the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    if video_file:
        # Handle single video/audio file
        video_name = os.path.splitext(os.path.basename(video_file))[0]
        output_file = os.path.join(output_directory, f"{video_name}.srt")

        command = [
            "python", "video_to_subtitle.py", video_file, output_file,
            "--subtitle_format", "srt", "--language", language,
            "--model_path", model_path
        ]

        try:
            subprocess.run(command, check=True)
            messagebox.showinfo("Success", f"Transcription completed successfully for {os.path.basename(video_file)}.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Transcription failed for {os.path.basename(video_file)}: {e}")
    elif folder:
        # Handle folder of video/audio files
        for filename in os.listdir(folder):
            if filename.endswith((".mp4", ".avi", ".mkv", ".mov", ".flv", ".wmv", ".webm", ".mp3", ".wav", ".aac", ".flac", ".ogg")):
                video_file = os.path.join(folder, filename)
                video_name = os.path.splitext(os.path.basename(video_file))[0]
                output_file = os.path.join(output_directory, f"{video_name}.srt")

                command = [
                    "python", "video_to_subtitle.py", video_file, output_file,
                    "--subtitle_format", "srt", "--language", language,
                    "--model_path", model_path
                ]

                try:
                    subprocess.run(command, check=True)
                    messagebox.showinfo("Success", f"Transcription completed successfully for {filename}.")
                except subprocess.CalledProcessError as e:
                    messagebox.showerror("Error", f"Transcription failed for {filename}: {e}")
    else:
        messagebox.showerror("Error", "Please select a video/audio file or a folder.")

# Load configuration
config = load_config()

# Create the main window
root = tk.Tk()
root.title("Video/Audio to Subtitle")

# Video file selection
video_file_label = tk.Label(root, text="视频/音频文件:")
video_file_label.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
video_file_entry = tk.Entry(root, width=50)
video_file_entry.grid(row=0, column=1, padx=10, pady=10)
video_file_button = tk.Button(root, text="浏览", command=select_video_file)
video_file_button.grid(row=0, column=2, padx=10, pady=10)

# Output directory selection
output_directory_label = tk.Label(root, text="输出目录:")
output_directory_label.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
output_directory_entry = tk.Entry(root, width=50)
output_directory_entry.grid(row=1, column=1, padx=10, pady=10)
output_directory_button = tk.Button(root, text="浏览", command=select_output_directory)
output_directory_button.grid(row=1, column=2, padx=10, pady=10)

# Folder selection
folder_label = tk.Label(root, text="音视频文件夹:")
folder_label.grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
folder_entry = tk.Entry(root, width=50)
folder_entry.grid(row=2, column=1, padx=10, pady=10)
folder_button = tk.Button(root, text="浏览", command=select_folder)
folder_button.grid(row=2, column=2, padx=10, pady=10)

# Model path selection
model_path_label = tk.Label(root, text="转录模型路径:")
model_path_label.grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
model_path_entry = tk.Entry(root, width=50)
model_path_entry.grid(row=3, column=1, padx=10, pady=10)
model_path_entry.insert(0, config["model_path"])  # Set default model path
model_path_button = tk.Button(root, text="浏览", command=select_model_path)
model_path_button.grid(row=3, column=2, padx=10, pady=10)

# Language selection
language_label = tk.Label(root, text="源文件语言:")
language_label.grid(row=4, column=0, padx=10, pady=10, sticky=tk.W)
language_var = tk.StringVar(value="auto")
language_options = ["auto", "en", "ja", "ko", "zh"]
language_menu = tk.OptionMenu(root, language_var, *language_options)
language_menu.grid(row=4, column=1, padx=10, pady=10)

# Run transcription button
run_button = tk.Button(root, text="转录字幕(源语言)", command=run_transcription)
run_button.grid(row=5, column=0, columnspan=3, pady=10)

def run_transcription_with_translation():
    video_file = video_file_entry.get()
    folder = folder_entry.get()
    output_directory = output_directory_entry.get()
    language = language_var.get()
    model_path = model_path_entry.get()
    target_language = language_var.get()  # Assuming target_language is the same as language for now

    if not output_directory:
        messagebox.showerror("Error", "Please select an output directory.")
        return

    if not model_path:
        messagebox.showerror("Error", "Please select a model path.")
        return

    if not check_model_exists(model_path):
        messagebox.showinfo("Info", "Model not found. Downloading model...")
        download_model(model_path)
        messagebox.showinfo("Info", "Model downloaded successfully.")

    # Change the current working directory to the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    if video_file:
        # Handle single video/audio file
        video_name = os.path.splitext(os.path.basename(video_file))[0]
        output_file = os.path.join(output_directory, f"{video_name}.srt")

        command = [
            "python", "video_to_subtitle.py", video_file, output_file,
            "--subtitle_format", "srt", "--language", language,
            "--model_path", model_path, "--translate", "--target_language", target_language
        ]

        try:
            subprocess.run(command, check=True)
            messagebox.showinfo("Success", f"Transcription completed successfully for {os.path.basename(video_file)}.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Transcription failed for {os.path.basename(video_file)}: {e}")
    elif folder:
        # Handle folder of video/audio files
        for filename in os.listdir(folder):
            if filename.endswith((".mp4", ".avi", ".mkv", ".mov", ".flv", ".wmv", ".webm", ".mp3", ".wav", ".aac", ".flac", ".ogg")):
                video_file = os.path.join(folder, filename)
                video_name = os.path.splitext(os.path.basename(video_file))[0]
                output_file = os.path.join(output_directory, f"{video_name}.srt")

                command = [
                    "python", "video_to_subtitle.py", video_file, output_file,
                    "--subtitle_format", "srt", "--language", language,
                    "--model_path", model_path, "--translate", "--target_language", target_language
                ]

                try:
                    subprocess.run(command, check=True)
                    messagebox.showinfo("Success", f"Transcription completed successfully for {filename}.")
                except subprocess.CalledProcessError as e:
                    messagebox.showerror("Error", f"Transcription failed for {filename}: {e}")
    else:
        messagebox.showerror("Error", "Please select a video/audio file or a folder.")

run_transcription_with_translation_button = tk.Button(root, text="转录字幕(双语)", command=run_transcription_with_translation)
run_transcription_with_translation_button.grid(row=6, column=0, columnspan=3, pady=10)

# Start the GUI event loop
root.mainloop()
