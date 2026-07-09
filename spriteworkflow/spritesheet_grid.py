import math
from pathlib import Path

from PIL import Image


def create_spritesheet_grid(frames=None, frames_dir=None, columns=None, padding=0,
                             background=(0, 0, 0, 0), output_file="spritesheet_grid.png"):
    """Arrange frames into a grid spritesheet (rows × columns).

    Parameters
    ----------
    frames : list of Path or str, optional
        List of paths to individual frame images.
    frames_dir : Path or str, optional
        Directory containing PNG frames. Mutually exclusive with *frames*.
    columns : int, optional
        Number of columns in the grid. If ``None`` it is auto-calculated as
        ``ceil(sqrt(total_frames))``.
    padding : int
        Pixels of empty space between adjacent cells. Default 0.
    background : tuple of int
        RGBA quadruplet used to fill the background canvas and any unused
        cells. Default ``(0, 0, 0, 0)`` (fully transparent).
    output_file : Path or str
        Path for the generated spritesheet. Default ``"spritesheet_grid.png"``.

    Returns
    -------
    Path
        Path to the generated grid spritesheet.

    Raises
    ------
    ValueError
        If neither *frames* nor *frames_dir* is provided, if both are
        provided, if *frames_dir* points to an empty directory, if
        *columns* is not an integer ≥ 1, or if a frame has a different
        size than the first frame.
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
        raise ValueError("No frames found to create the spritesheet.")

    # ------------------------------------------------------------------
    # Validación de columns
    # ------------------------------------------------------------------
    if columns is None:
        columns = math.ceil(math.sqrt(len(frames)))
    elif not isinstance(columns, int) or columns < 1:
        raise ValueError("columns must be an integer >= 1.")

    # ------------------------------------------------------------------
    # Calcular dimensiones del grid
    # ------------------------------------------------------------------
    frame_paths = [Path(f) for f in frames]

    first_frame_path = frame_paths[0]
    if not first_frame_path.exists():
        raise FileNotFoundError(f"The frame '{first_frame_path}' does not exist.")

    first_frame = Image.open(first_frame_path)
    frame_width, frame_height = first_frame.size

    total_frames = len(frame_paths)
    rows = math.ceil(total_frames / columns)

    sheet_width = columns * frame_width + padding * (columns - 1)
    sheet_height = rows * frame_height + padding * (rows - 1)

    spritesheet = Image.new("RGBA", (sheet_width, sheet_height), background)

    # ------------------------------------------------------------------
    # Colocar frames en el grid
    # ------------------------------------------------------------------
    for index, frame_path in enumerate(frame_paths):
        frame_path = Path(frame_path)

        if not frame_path.exists():
            raise FileNotFoundError(f"The frame '{frame_path}' does not exist.")

        frame = Image.open(frame_path)

        if frame.size != (frame_width, frame_height):
            raise ValueError(f"Frame '{frame_path}' has a different size than the first frame.")

        col = index % columns
        row = index // columns
        x = col * (frame_width + padding)
        y = row * (frame_height + padding)

        spritesheet.paste(frame, (x, y))

    # ------------------------------------------------------------------
    # Guardar (mismo patrón que spritesheet_lineal)
    # ------------------------------------------------------------------
    output_path = Path(output_file)

    if output_path.suffix == "":
        output_path = output_path.with_suffix(".png")

    if output_path.exists():
        print(f"Warning: The file '{output_file}' already exists and will be overwritten.")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    spritesheet.save(output_path)

    return output_path
