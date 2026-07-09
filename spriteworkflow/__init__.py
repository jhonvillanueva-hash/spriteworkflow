"""SpriteWorkflow — convert video frames into linear spritesheets.

Provides :func:`extract_frames` (extract frames from video via FFmpeg)
and :func:`create_spritesheet_lineal` (stitch frames into a horizontal
spritesheet).
"""

from .extractor import extract_frames
from .spritesheet_lineal import create_spritesheet_lineal

__all__ = [
    "extract_frames",
    "create_spritesheet_lineal",
]
