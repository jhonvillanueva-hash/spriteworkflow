"""SpriteWorkflow CLI — build spritesheets from video via the command line.

Usage::

    spriteworkflow build <video> [options]

Subcommands
-----------
build       Extract frames (optionally remove background), assemble into a
            spritesheet, and optionally produce a validation report.
"""

import argparse
import sys
from pathlib import Path

from spriteworkflow import (
    extract_frames,
    remove_background,
    create_spritesheet_lineal,
    create_spritesheet_grid,
    generate_report,
)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the ``build`` subcommand.

    Returns
    -------
    argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="spriteworkflow",
        description="Convert video frames into linear or grid spritesheets.",
    )

    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="Build a spritesheet from a video")

    # Positional
    build.add_argument(
        "video",
        help="Path to the input video file",
    )

    # Output
    build.add_argument(
        "--output", "-o",
        default="spritesheet.png",
        help="Output spritesheet path (default: %(default)s)",
    )

    # Layout
    build.add_argument(
        "--layout",
        choices=("lineal", "grid"),
        default="lineal",
        help="Spritesheet layout (default: %(default)s)",
    )
    build.add_argument(
        "--columns",
        type=int,
        default=None,
        help="Grid columns — auto-calculated as ceil(sqrt(N)) when not set. "
             "Only relevant with --layout=grid.",
    )
    build.add_argument(
        "--padding",
        type=int,
        default=0,
        help="Padding pixels between grid cells (default: %(default)s). "
             "Only relevant with --layout=grid.",
    )

    # Chroma-key (matte)
    build.add_argument(
        "--matte",
        action="store_true",
        default=False,
        help="Enable chroma-key background removal between extraction and "
             "spritesheet assembly",
    )
    build.add_argument(
        "--bg-color",
        nargs=3,
        type=int,
        default=None,
        metavar=("R", "G", "B"),
        help="RGB triplet for chroma-key color, e.g. --bg-color 0 255 0. "
             "Auto-detected from corner pixels when not set.",
    )
    build.add_argument(
        "--tolerance",
        type=int,
        default=30,
        help="Chroma-key euclidean tolerance (default: %(default)s)",
    )
    build.add_argument(
        "--feather",
        type=int,
        default=0,
        help="Chroma-key feather width in pixels (default: %(default)s)",
    )

    # Report
    build.add_argument(
        "--report-file",
        default=None,
        help="Path for JSON validation report (omitted when not set)",
    )

    # Internal
    build.add_argument(
        "--temp-dir",
        default="temp",
        help="Temporary directory for extracted frames (default: %(default)s)",
    )

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv=None) -> None:
    """CLI entry point.

    Parameters
    ----------
    argv : list of str, optional
        Command-line arguments.  If ``None`` (default), ``sys.argv[1:]`` is
        read.  Passing an explicit list enables testing without I/O.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # argparse requires a subcommand — safety net for edge cases
    if args.command != "build":
        parser.print_help()
        sys.exit(2)

    try:
        # ---- Step 1 : Extract frames ------------------------------------
        print("> Extracting frames from video...")
        frames = extract_frames(args.video, output_dir=args.temp_dir)
        print(f"  {len(frames)} frames extracted.")

        # ---- Step 2 (optional) : Remove background ----------------------
        if args.matte:
            print("> Removing background via chroma-key...")
            bg = tuple(args.bg_color) if args.bg_color else None
            frames = remove_background(
                frames=frames,
                bg_color=bg,
                tolerance=args.tolerance,
                feather=args.feather,
                output_dir=str(Path(args.temp_dir) / "matted"),
            )
            print(f"  {len(frames)} frames processed.")

        # ---- Step 3 : Build spritesheet ---------------------------------
        print(f"> Building {args.layout} spritesheet...")

        if args.layout == "grid":
            sheet = create_spritesheet_grid(
                frames=frames,
                columns=args.columns,
                padding=args.padding,
                output_file=args.output,
            )
        else:
            sheet = create_spritesheet_lineal(
                frames=frames,
                output_file=args.output,
            )

        print(f"  -> Spritesheet saved: {sheet}")

        # ---- Step 4 (optional) : Generate report ------------------------
        if args.report_file:
            print("> Generating validation report...")
            report = generate_report(
                frames=frames,
                spritesheet_path=sheet,
                output_file=args.report_file,
            )
            print(f"  -> Report saved: {report}")

    except (ValueError, FileNotFoundError, NotADirectoryError,
            RuntimeError, PermissionError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
