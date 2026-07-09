"""Tests for the CLI module (:mod:`spriteworkflow.cli`).

Mocks the five public pipeline functions at the :mod:`spriteworkflow.cli` level
so no real video, ffmpeg, OpenCV, or disk I/O is needed.
"""

from pathlib import Path

import pytest

from spriteworkflow.cli import main, build_parser


# ============================================================================
# Argument parsing
# ============================================================================

class TestBuildParser:
    def test_minimal_invocation(self):
        """``spriteworkflow build video.mp4`` parses successfully."""
        parser = build_parser()
        args = parser.parse_args(["build", "video.mp4"])
        assert args.command == "build"
        assert args.video == "video.mp4"

    def test_all_options(self):
        """Every flag is parsed to the correct attribute."""
        parser = build_parser()
        argv = [
            "build", "video.mp4",
            "--output", "sheet.png",
            "--layout", "grid",
            "--columns", "4",
            "--padding", "8",
            "--matte",
            "--bg-color", "0", "255", "0",
            "--tolerance", "15",
            "--feather", "2",
            "--report-file", "report.json",
            "--temp-dir", "work",
        ]
        args = parser.parse_args(argv)
        assert args.output == "sheet.png"
        assert args.layout == "grid"
        assert args.columns == 4
        assert args.padding == 8
        assert args.matte is True
        assert args.bg_color == [0, 255, 0]
        assert args.tolerance == 15
        assert args.feather == 2
        assert args.report_file == "report.json"
        assert args.temp_dir == "work"

    def test_defaults(self):
        """Default values match those of the library functions."""
        parser = build_parser()
        args = parser.parse_args(["build", "video.mp4"])
        assert args.output == "spritesheet.png"
        assert args.layout == "lineal"
        assert args.columns is None
        assert args.padding == 0
        assert args.matte is False
        assert args.bg_color is None
        assert args.tolerance == 30
        assert args.feather == 0
        assert args.report_file is None
        assert args.temp_dir == "temp"


# ============================================================================
# Pipeline flow — all library functions mocked
# ============================================================================

class TestBuildFlow:
    VIDEO = "video.mp4"

    # ------------------------------------------------------------------
    # Helper: mock all 5 pipeline functions
    # ------------------------------------------------------------------

    @staticmethod
    def _mock_all(monkeypatch, tmp_path):
        """Replace every import in ``spriteworkflow.cli`` with a mock.

        Returns a list ``calls`` that records ``(name, args, kwargs)``
        tuples in call order.
        """
        calls = []

        def _factory(name, return_value):
            def _mock(*args, **kwargs):
                calls.append((name, args, kwargs))
                return return_value

            return _mock

        frame_dir = tmp_path / "frames"
        frame_dir.mkdir()
        frames = sorted(frame_dir / f"frame_{i:04d}.png" for i in range(3))
        sheet = tmp_path / "spritesheet.png"
        report = tmp_path / "report.json"

        monkeypatch.setattr(
            "spriteworkflow.cli.extract_frames",
            _factory("extract_frames", frames),
        )
        monkeypatch.setattr(
            "spriteworkflow.cli.remove_background",
            _factory("remove_background", frames),
        )
        monkeypatch.setattr(
            "spriteworkflow.cli.create_spritesheet_lineal",
            _factory("create_spritesheet_lineal", sheet),
        )
        monkeypatch.setattr(
            "spriteworkflow.cli.create_spritesheet_grid",
            _factory("create_spritesheet_grid", sheet),
        )
        monkeypatch.setattr(
            "spriteworkflow.cli.generate_report",
            _factory("generate_report", report),
        )

        return calls

    # ------------------------------------------------------------------
    # Pipeline ordering
    # ------------------------------------------------------------------

    def test_simple_lineal(self, tmp_path, monkeypatch):
        """build → extract_frames + create_spritesheet_lineal."""
        calls = self._mock_all(monkeypatch, tmp_path)
        main(["build", self.VIDEO])

        names = [c[0] for c in calls]
        assert names == ["extract_frames", "create_spritesheet_lineal"], names

    def test_with_matte(self, tmp_path, monkeypatch):
        """build --matte → extract, remove_background, lineal."""
        calls = self._mock_all(monkeypatch, tmp_path)
        main(["build", self.VIDEO, "--matte"])

        names = [c[0] for c in calls]
        assert names == [
            "extract_frames",
            "remove_background",
            "create_spritesheet_lineal",
        ], names

    def test_matte_receives_correct_args(self, tmp_path, monkeypatch):
        """--bg-color, --tolerance, --feather propagate correctly."""
        calls = self._mock_all(monkeypatch, tmp_path)
        main([
            "build", self.VIDEO, "--matte",
            "--bg-color", "0", "255", "0",
            "--tolerance", "15", "--feather", "2",
        ])

        matte_call = next(c for c in calls if c[0] == "remove_background")
        _name, _args, kwargs = matte_call
        assert kwargs["bg_color"] == (0, 255, 0)
        assert kwargs["tolerance"] == 15
        assert kwargs["feather"] == 2

    def test_matte_bg_color_default_none(self, tmp_path, monkeypatch):
        """Sin --bg-color → remove_background recibe bg_color=None."""
        calls = self._mock_all(monkeypatch, tmp_path)
        main(["build", self.VIDEO, "--matte"])

        matte_call = next(c for c in calls if c[0] == "remove_background")
        kwargs = matte_call[2]
        assert kwargs["bg_color"] is None

    def test_grid_flow(self, tmp_path, monkeypatch):
        """--layout grid → create_spritesheet_grid, not lineal."""
        calls = self._mock_all(monkeypatch, tmp_path)
        main(["build", self.VIDEO, "--layout", "grid"])

        names = [c[0] for c in calls]
        assert names == ["extract_frames", "create_spritesheet_grid"], names

    def test_grid_columns_and_padding(self, tmp_path, monkeypatch):
        """--columns y --padding llegan a create_spritesheet_grid."""
        calls = self._mock_all(monkeypatch, tmp_path)
        main([
            "build", self.VIDEO, "--layout", "grid",
            "--columns", "2", "--padding", "8",
        ])

        grid_call = next(c for c in calls if c[0] == "create_spritesheet_grid")
        kwargs = grid_call[2]
        assert kwargs["columns"] == 2
        assert kwargs["padding"] == 8

    def test_output_filename(self, tmp_path, monkeypatch):
        """--output cambia el output_file que recibe el builder."""
        calls = self._mock_all(monkeypatch, tmp_path)
        custom_out = tmp_path / "custom.png"
        main(["build", self.VIDEO, "--output", str(custom_out)])

        lineal_call = next(
            c for c in calls if c[0] == "create_spritesheet_lineal"
        )
        kwargs = lineal_call[2]
        assert str(kwargs["output_file"]) == str(custom_out)

    def test_report_flow(self, tmp_path, monkeypatch):
        """--report-file → generate_report recibe spritesheet_path y output_file."""
        calls = self._mock_all(monkeypatch, tmp_path)
        report_path = tmp_path / "my_report.json"
        main(["build", self.VIDEO, "--report-file", str(report_path)])

        names = [c[0] for c in calls]
        assert names == [
            "extract_frames",
            "create_spritesheet_lineal",
            "generate_report",
        ], names

        report_call = next(c for c in calls if c[0] == "generate_report")
        kwargs = report_call[2]
        assert str(kwargs["output_file"]) == str(report_path)
        assert kwargs["spritesheet_path"] is not None

    def test_full_pipeline(self, tmp_path, monkeypatch):
        """--matte --layout grid --report-file → 4 functions en orden."""
        calls = self._mock_all(monkeypatch, tmp_path)
        main([
            "build", self.VIDEO, "--matte",
            "--layout", "grid", "--columns", "3",
            "--report-file", str(tmp_path / "r.json"),
        ])
        names = [c[0] for c in calls]
        assert names == [
            "extract_frames",
            "remove_background",
            "create_spritesheet_grid",
            "generate_report",
        ], names


# ============================================================================
# Error handling
# ============================================================================

class TestErrorHandling:
    def test_file_not_found_in_extract(self, tmp_path, monkeypatch, capsys):
        """FileNotFoundError en extract → exit 1 + mensaje en stderr."""
        def _mock(*_a, **_kw):
            raise FileNotFoundError("Archivo no encontrado")

        monkeypatch.setattr("spriteworkflow.cli.extract_frames", _mock)

        with pytest.raises(SystemExit) as exc:
            main(["build", "missing.mp4"])

        assert exc.value.code == 1
        _out, err = capsys.readouterr()
        assert "Archivo no encontrado" in err

    def test_value_error_in_matte(self, tmp_path, monkeypatch, capsys):
        """ValueError en remove_background → exit 1 + stderr."""
        monkeypatch.setattr(
            "spriteworkflow.cli.extract_frames",
            lambda *_a, **_kw: [tmp_path / "f.png"],
        )

        def _mock(*_a, **_kw):
            raise ValueError("bg_color inválido")

        monkeypatch.setattr("spriteworkflow.cli.remove_background", _mock)

        with pytest.raises(SystemExit) as exc:
            main(["build", "v.mp4", "--matte"])

        assert exc.value.code == 1
        _out, err = capsys.readouterr()
        assert "bg_color inválido" in err

    def test_runtime_error_in_build(self, tmp_path, monkeypatch, capsys):
        """RuntimeError en create_spritesheet_lineal → exit 1 + stderr."""
        monkeypatch.setattr(
            "spriteworkflow.cli.extract_frames",
            lambda *_a, **_kw: [tmp_path / "f.png"],
        )

        def _mock(*_a, **_kw):
            raise RuntimeError("Error interno del builder")

        monkeypatch.setattr(
            "spriteworkflow.cli.create_spritesheet_lineal", _mock,
        )

        with pytest.raises(SystemExit) as exc:
            main(["build", "v.mp4"])

        assert exc.value.code == 1
        _out, err = capsys.readouterr()
        assert "Error interno del builder" in err

    def test_exit_code_2_without_subcommand(self, capsys):
        """Sin subcommand → parser muestra usage y sale con código 2."""
        with pytest.raises(SystemExit) as exc:
            main([])

        assert exc.value.code == 2
