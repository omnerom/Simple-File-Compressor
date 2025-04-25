import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
import threading
import webbrowser

DEFAULT_SIZE_MB = 10
DEFAULT_RESOLUTION = "720p"


def get_video_duration(input_file):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", input_file],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def get_resolution(res_str):
    return {
        "480p": "854:480",
        "720p": "1280:720",
        "1080p": "1920:1080"
    }.get(res_str, "1280:720")


def generate_output_path(input_path, output_dir):
    base, ext = os.path.splitext(os.path.basename(input_path))
    output_path = os.path.join(output_dir, f"{base} - compressed{ext}")
    return output_path


def compress_video(input_file, target_size_mb, resolution_str, output_dir):
    duration = get_video_duration(input_file)
    target_size_kb = target_size_mb * 1024
    target_bitrate = ((target_size_kb * 8) / duration) - 128
    resolution = get_resolution(resolution_str)
    output_file = generate_output_path(input_file, output_dir)
    passlog = "ffmpeg2pass"

    subprocess.run([  # First pass
        "ffmpeg", "-y", "-i", input_file,
        "-b:v", f"{int(target_bitrate)}k", "-pass", "1",
        "-vf", f"scale={resolution}",
        "-an", "-f", "mp4", os.devnull
    ])

    subprocess.run([  # Second pass
        "ffmpeg", "-y", "-i", input_file,
        "-b:v", f"{int(target_bitrate)}k", "-pass", "2",
        "-vf", f"scale={resolution}",
        "-c:v", "libx264", "-preset", "slow",
        "-c:a", "aac", "-b:a", "128k",
        output_file
    ])

    # Clean up pass logs
    for file in [f"{passlog}-0.log", f"{passlog}-0.log.mbtree"]:
        if os.path.exists(file):
            os.remove(file)

    messagebox.showinfo("Done", f"Output saved as:\n{output_file}")


def browse_file(entry, output_dir_entry):
    file_path = filedialog.askopenfilename(filetypes=[("MP4 files", "*.mp4")])
    if file_path:
        entry.delete(0, tk.END)
        entry.insert(0, file_path)

        # Automatically set output folder to the input file's directory
        input_folder = os.path.dirname(file_path)
        output_dir_entry.delete(0, tk.END)
        output_dir_entry.insert(0, input_folder)


def browse_output_folder(output_dir_entry):
    folder_path = filedialog.askdirectory()
    if folder_path:
        output_dir_entry.delete(0, tk.END)
        output_dir_entry.insert(0, folder_path)


def start_compression(input_entry, size_entry, resolution_var, output_dir_entry):
    try:
        input_path = input_entry.get()
        size = int(size_entry.get())
        resolution = resolution_var.get()
        output_dir = output_dir_entry.get()

        threading.Thread(target=compress_video, args=(input_path, size, resolution, output_dir)).start()
    except Exception as e:
        messagebox.showerror("Error", str(e))


def open_github_repo():
    webbrowser.open("https://github.com/omnerom/")


def get_preset_for_length(duration):
    if duration < 300:  # Short video (under 5 minutes)
        return '480p', 1000  # 1 Mbps for smaller file size
    elif 300 <= duration < 1800:  # Medium video (5 - 30 minutes)
        return '720p', 2000  # 2 Mbps
    else:  # Long video (over 30 minutes)
        return '1080p', 4000  # 4 Mbps for larger, high-quality files


# --- GUI ---
root = tk.Tk()
root.title("Simple Video Compressor")
root.geometry("600x400")

# Input file field
input_label = tk.Label(root, text="Input File:")
input_label.grid(row=0, column=0, padx=10, pady=10)
input_entry = tk.Entry(root, width=60)
input_entry.grid(row=0, column=1)
input_button = tk.Button(root, text="Browse", command=lambda: browse_file(input_entry, output_dir_entry))
input_button.grid(row=0, column=2)

# Output folder field (with browse button)
output_folder_label = tk.Label(root, text="Output Folder:")
output_folder_label.grid(row=1, column=0, padx=10, pady=10)
output_dir_entry = tk.Entry(root, width=60)
output_dir_entry.grid(row=1, column=1)
output_button = tk.Button(root, text="Browse", command=lambda: browse_output_folder(output_dir_entry))
output_button.grid(row=1, column=2)

# Target size input
size_label = tk.Label(root, text="Target Size (MB):")
size_label.grid(row=2, column=0, padx=10, pady=10)
size_entry = tk.Entry(root)
size_entry.insert(0, str(DEFAULT_SIZE_MB))
size_entry.grid(row=2, column=1)

# Suggested resolution dropdown
resolution_label = tk.Label(root, text="Resolution:")
resolution_label.grid(row=3, column=0, padx=10, pady=10)
resolution_var = ttk.Combobox(root, values=["480p", "720p", "1080p"], state="readonly", width=15)
resolution_var.grid(row=3, column=1, padx=10, pady=10)
resolution_var.set("720p")  # Default resolution

# Start compression button
compress_button = tk.Button(root, text="Start Compression", command=lambda: start_compression(input_entry, size_entry, resolution_var, output_dir_entry))
compress_button.grid(row=4, column=1, padx=10, pady=20)

# GitHub link button
github_button = tk.Button(root, text="Visit GitHub Repo", command=open_github_repo)
github_button.grid(row=5, column=1, padx=10, pady=10)

root.mainloop()
