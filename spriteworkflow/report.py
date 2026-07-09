import json
from datetime import datetime
from pathlib import Path

from PIL import Image


def generate_report(frames=None, frames_dir=None, spritesheet_path=None, output_file="report.json"):
    """Inspect frames and produce a JSON validation report.

    Use this function *after* creating a spritesheet to detect issues
    such as mismatched frame dimensions, verify the output file, and
    produce a portable metadata record.

    Unlike :func:`create_spritesheet_lineal` and
    :func:`create_spritesheet_grid`, this function **does not** raise
    when frames have different sizes — mismatches are recorded in the
    report instead, which is the whole point of validation.

    Parameters
    ----------
    frames : list of Path or str, optional
        List of paths to individual frame images.
    frames_dir : Path or str, optional
        Directory containing PNG frames. Mutually exclusive with *frames*.
    spritesheet_path : Path or str, optional
        Path to a spritesheet file to include its dimensions in the report.
    output_file : Path or str
        Path for the generated JSON report. Default ``"report.json"``.

    Returns
    -------
    Path
        Path to the generated JSON report file.

    Raises
    ------
    ValueError
        If neither *frames* nor *frames_dir* is provided, if both are
        provided, or if *frames_dir* points to an empty directory.
    FileNotFoundError
        If *frames_dir* or *spritesheet_path* does not exist.
    NotADirectoryError
        If *frames_dir* is a file, not a directory.
    """
    # ------------------------------------------------------------------
    # Validación de entrada (mismo estilo que spritesheet_lineal)
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
        raise ValueError("No frames found to report.")

    # ------------------------------------------------------------------
    # Validación de spritesheet_path
    # ------------------------------------------------------------------
    if spritesheet_path is not None:
        sprite_path = Path(spritesheet_path)
        if not sprite_path.exists():
            raise FileNotFoundError(f"The spritesheet '{spritesheet_path}' does not exist.")
        if not sprite_path.is_file():
            raise ValueError(f"The path '{spritesheet_path}' is not a valid file.")

    # ------------------------------------------------------------------
    # Procesar frames
    # ------------------------------------------------------------------
    frame_paths = [Path(f) for f in frames]

    frame_entries = []
    mismatched = []
    reference_size = None

    for idx, frame_path in enumerate(frame_paths):
        img = Image.open(frame_path)
        w, h = img.size

        frame_entries.append({
            "file": frame_path.name,
            "width": w,
            "height": h,
        })

        if idx == 0:
            reference_size = [w, h]
        elif [w, h] != reference_size:
            mismatched.append(frame_path.name)

    # ------------------------------------------------------------------
    # Información del spritesheet (opcional)
    # ------------------------------------------------------------------
    spritesheet_size = None
    sprite_path_str = None

    if spritesheet_path is not None:
        sprite_path = Path(spritesheet_path)
        sprite_img = Image.open(sprite_path)
        spritesheet_size = list(sprite_img.size)
        sprite_path_str = str(sprite_path)

    # ------------------------------------------------------------------
    # Construir y guardar el reporte
    # ------------------------------------------------------------------
    report = {
        "total_frames": len(frame_paths),
        "frames": frame_entries,
        "consistent_dimensions": len(mismatched) == 0,
        "reference_size": reference_size,
        "mismatched_frames": mismatched,
        "spritesheet_path": sprite_path_str,
        "spritesheet_size": spritesheet_size,
        "generated_at": datetime.now().isoformat(),
    }

    output_path = Path(output_file)

    if output_path.suffix == "":
        output_path = output_path.with_suffix(".json")

    if output_path.exists():
        print(f"Warning: The file '{output_file}' already exists and will be overwritten.")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return output_path
