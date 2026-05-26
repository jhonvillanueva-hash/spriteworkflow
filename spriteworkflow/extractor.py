from pathlib import Path
import subprocess
from spriteworkflow.ffmpeg_manager import get_ffmpeg_path
import tempfile

def extract_frames(video_name, output_dir="temp"):
    
    ffmpeg_path = get_ffmpeg_path()
    
    video_path = Path(video_name)
    
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_name}")
    
    if not video_path.is_file():
        raise ValueError(f"Path is not a valid file: {video_name}")
    
    if video_path.stat().st_size <= 0:
        raise ValueError(f"Video file is empty: {video_name}")
    
    try:
        with open(video_path, "rb"):
            pass
    except PermissionError as e:
        raise PermissionError(f"Video file is not readable: {video_name}") from e
        
    temp_root = Path(output_dir)
    temp_root.mkdir(parents=True, exist_ok=True)
    
    temp_dir = tempfile.mkdtemp(prefix="frames_", dir=temp_root)
    
    output_path = Path(temp_dir)
        
    frame_pattern = output_path / "frame_%04d.png"
    
    command = [
        ffmpeg_path,
        "-v",
        "error",
        "-i",
        str(video_path),
        str(frame_pattern)
    ]
    
    try:
        subprocess.run(command, check=True, stderr=subprocess.PIPE, text=True)
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip()
        raise RuntimeError(f"FFmpeg failed:\n{stderr}") from e

    frames = sorted(output_path.glob("*.png"))
    
    if not frames:
        raise RuntimeError(
            "No frames were extracted. "
            "Possible causes:\n"
            "- Corrupted video\n"
            "- Unsupported codec\n"
            "- Zero-duration video\n"
            "- FFmpeg decoding issue\n"
            "- Permission problems"
        )
    
    return frames