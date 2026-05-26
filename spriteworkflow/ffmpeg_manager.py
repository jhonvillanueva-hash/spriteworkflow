import imageio_ffmpeg

def get_ffmpeg_path():
    try:
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    except RuntimeError as e:
        raise RuntimeError("Failed to initialize FFmpeg automatically.") from e

    return ffmpeg_path