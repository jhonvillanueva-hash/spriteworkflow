"""SpriteWorkflow — convert video frames into linear spritesheets.

Provides :func:`extract_frames` (extract frames from video via FFmpeg),
:func:`create_spritesheet_lineal` (stitch frames into a horizontal
spritesheet), and :func:`remove_background` (chroma-key background
removal on frames).
"""

from .extractor import extract_frames
from .spritesheet_lineal import create_spritesheet_lineal
from .matte import remove_background

__all__ = [
    "extract_frames",
    "create_spritesheet_lineal",
    "remove_background",
]
