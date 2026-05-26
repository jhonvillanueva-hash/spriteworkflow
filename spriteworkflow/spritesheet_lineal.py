from pathlib import Path
from PIL import Image

def create_spritesheet_lineal(frames=None, frames_dir=None, output_file="spritesheet.png"):
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

    first_frame_path = Path(frames[0])
    
    if not first_frame_path.exists():
        raise FileNotFoundError(f"The frame '{frames[0]}' does not exist.")

    first_frame = Image.open(first_frame_path)
    frame_width, frame_height = first_frame.size
    
    total_frames = len(frames)

    sheet_width = frame_width * total_frames
    sheet_height = frame_height
    
    spritesheet = Image.new("RGBA", (sheet_width, sheet_height))

    for index, frame_path in enumerate(frames):
        frame_path = Path(frame_path)
        
        if not frame_path.exists():
            raise FileNotFoundError(f"The frame '{frame_path}' does not exist.")
        
        frame = Image.open(frame_path)
        
        if frame.size != (frame_width, frame_height):
            raise ValueError(f"Frame '{frame_path}' has a different size than the first frame.")
        
        x_position = index * frame_width
        y_position = 0
        
        spritesheet.paste(frame, (x_position, y_position))

    output_path = Path(output_file)
    
    if output_path.suffix == "":
        output_path = output_path.with_suffix(".png")
    
    if output_path.exists():
        print(f"Warning: The file '{output_file}' already exists and will be overwritten.")
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    spritesheet.save(output_path)
    
    return output_path
