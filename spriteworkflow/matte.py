from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def remove_background(frames=None, frames_dir=None, bg_color=None, tolerance=30, output_dir="matted"):
    """Remove background from frames via chroma-key (euclidean distance in RGB).

    Parameters
    ----------
    frames : list of Path or str, optional
        List of paths to individual frame images.
    frames_dir : Path or str, optional
        Directory containing PNG frames. Mutually exclusive with *frames*.
    bg_color : tuple of int, optional
        RGB triplet (0-255 each). If ``None`` it is auto-detected by
        averaging the four corner pixels of the first frame.
    tolerance : int
        Maximum euclidean distance from *bg_color* for a pixel to be
        considered background (made transparent). Default 30.
    output_dir : Path or str
        Directory where the processed RGBA PNGs are saved. Created if it
        does not exist. Default ``"matted"``.

    Returns
    -------
    list of Path
        Sorted list of paths to the generated RGBA PNG files.

    Raises
    ------
    ValueError
        If neither *frames* nor *frames_dir* is provided, if both are
        provided, if *frames_dir* points to an empty directory, or if
        *bg_color* is not a valid RGB triplet.
    FileNotFoundError
        If *frames_dir* does not exist.
    NotADirectoryError
        If *frames_dir* is a file, not a directory.
    """
    # ------------------------------------------------------------------
    # Validación de entrada (mismo estilo que create_spritesheet_lineal)
    # ------------------------------------------------------------------
    if frames is None and frames_dir is None:
        raise ValueError("Either 'frames' or 'frames_dir' must be provided.")

    if frames is not None and frames_dir is not None:
        raise ValueError("Only one of 'frames' or 'frames_dir' should be provided, not both.")

    if frames_dir is not None:
        frames_path = Path(frames_dir)

        if not frames_path.exists():
            raise FileNotFoundError(f"The directory '{frames_dir}' does not exist.")

        if not frames_path.is_dir():
            raise NotADirectoryError(f"The path '{frames_dir}' is not a directory.")

        frames = sorted(frames_path.glob("*.png"))

    if not frames:
        raise ValueError("No frames found to process for background removal.")

    # Normalise frame paths
    frame_paths = [Path(f) for f in frames]

    # ------------------------------------------------------------------
    # Color de fondo — autodetección o validación
    # ------------------------------------------------------------------
    if bg_color is None:
        bgr = cv2.imread(str(frame_paths[0]), cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError(f"Cannot read frame '{frame_paths[0]}' with OpenCV.")

        h, w = bgr.shape[:2]
        corners_bgr = [
            bgr[0, 0],
            bgr[0, w - 1],
            bgr[h - 1, 0],
            bgr[h - 1, w - 1],
        ]
        avg_bgr = np.mean(corners_bgr, axis=0).astype(int)
        bg_color = tuple(avg_bgr[::-1])  # BGR → RGB
    else:
        if not isinstance(bg_color, tuple) or len(bg_color) != 3:
            raise ValueError("bg_color must be a tuple of 3 integers (R, G, B).")

        if not all(isinstance(c, int) and 0 <= c <= 255 for c in bg_color):
            raise ValueError("bg_color values must be integers in the range 0-255.")

    # ------------------------------------------------------------------
    # Procesar cada frame
    # ------------------------------------------------------------------
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    bg_array = np.array(bg_color, dtype=np.uint8)  # RGB
    result_paths = []

    for frame_path in frame_paths:
        if not frame_path.exists():
            raise FileNotFoundError(f"The frame '{frame_path}' does not exist.")

        bgr = cv2.imread(str(frame_path), cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError(f"Cannot read frame '{frame_path}' with OpenCV.")

        # Convert BGR → RGB for the distance computation
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

        # Euclidean distance per pixel against bg_color
        diff = rgb.astype(np.float32) - bg_array.astype(np.float32)
        dist = np.sqrt(np.sum(diff ** 2, axis=2))

        # Alpha mask: 0 for background, 255 for foreground
        alpha = np.where(dist <= tolerance, 0, 255).astype(np.uint8)

        rgba = np.dstack([rgb, alpha])

        out_file = output_path / frame_path.name
        Image.fromarray(rgba, "RGBA").save(out_file)
        result_paths.append(out_file)

    return sorted(result_paths)
