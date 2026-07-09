"""SpriteWorkflow — convert video frames into linear spritesheets.

Provides :func:`extract_frames` (extract frames from video via FFmpeg),
:func:`create_spritesheet_lineal` (stitch frames into a horizontal
spritesheet), :func:`remove_background` (chroma-key background removal
on frames), :func:`create_spritesheet_grid` (arrange frames in a
rows × columns grid), and :func:`generate_report` (inspect frames and
produce a JSON validation report).
"""

from .extractor import extract_frames
from .spritesheet_lineal import create_spritesheet_lineal
from .matte import remove_background
from .spritesheet_grid import create_spritesheet_grid
from .report import generate_report

__all__ = [
    "extract_frames",
    "create_spritesheet_lineal",
    "remove_background",
    "create_spritesheet_grid",
    "generate_report",
]
