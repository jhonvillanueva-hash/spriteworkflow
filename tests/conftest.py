from pathlib import Path
from PIL import Image, ImageDraw
import pytest


def create_synthetic_frames(directory, count=3, size=(64, 64), color=(255, 0, 0)):
    """Create *count* solid-color PNG frames of *size* inside *directory*.

    Each frame is an RGBA image filled with *color*.
    Returns sorted list of Path objects.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for i in range(count):
        img = Image.new("RGBA", size, color + (255,))
        path = directory / f"frame_{i:04d}.png"
        img.save(path)
        paths.append(path)
    return sorted(paths)


def create_chroma_key_frames(directory, count=3, size=(64, 64),
                              bg_color=(0, 255, 0), subject_color=(255, 0, 0),
                              subject_radius=10):
    """Create frames with solid *bg_color* and a circle of *subject_color*.

    Useful for testing chroma-key / background-removal functions: the
    four corners are always *bg_color*, and the centre contains a
    *subject_color* circle so the alpha mask can be verified at both
    regions.
    Returns sorted list of Paths.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    cx, cy = size[0] // 2, size[1] // 2
    paths = []
    for i in range(count):
        img = Image.new("RGBA", size, bg_color + (255,))
        draw = ImageDraw.Draw(img)
        draw.ellipse(
            [cx - subject_radius, cy - subject_radius,
             cx + subject_radius, cy + subject_radius],
            fill=subject_color + (255,),
        )
        path = directory / f"frame_{i:04d}.png"
        img.save(path)
        paths.append(path)
    return sorted(paths)


@pytest.fixture
def frame_dir(tmp_path):
    """Path to a directory containing 3 synthetic 64x64 red frames."""
    d = tmp_path / "frames"
    create_synthetic_frames(d, count=3, size=(64, 64), color=(255, 0, 0))
    return d


@pytest.fixture
def frame_list(frame_dir):
    """Sorted list of Paths to 3 synthetic 64x64 red frames."""
    return sorted(Path(frame_dir).glob("*.png"))
