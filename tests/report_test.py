import json
from datetime import datetime
from pathlib import Path
from PIL import Image
import pytest

from spriteworkflow.report import generate_report
from tests.conftest import create_synthetic_frames


# ---------------------------------------------------------------------------
# Validación de parámetros de entrada
# ---------------------------------------------------------------------------

class TestInputValidation:
    def test_lanza_value_error_cuando_no_se_pasa_frames_ni_frames_dir(self):
        """Error si no se pasa ni 'frames' ni 'frames_dir'."""
        with pytest.raises(ValueError, match="Either 'frames' or 'frames_dir' must be provided"):
            generate_report()

    def test_lanza_value_error_cuando_se_pasan_ambos(self, tmp_path):
        """Error si se pasan 'frames' y 'frames_dir' simultáneamente."""
        frame = tmp_path / "dummy.png"
        frame.write_text("")
        with pytest.raises(ValueError, match="Only one"):
            generate_report(
                frames=[frame],
                frames_dir=str(tmp_path),
            )

    def test_lanza_file_not_found_cuando_frames_dir_no_existe(self, tmp_path):
        """Error si frames_dir no existe en disco."""
        inexistente = tmp_path / "no_existe"
        with pytest.raises(FileNotFoundError, match="does not exist"):
            generate_report(frames_dir=str(inexistente))

    def test_lanza_not_a_directory_cuando_frames_dir_es_un_archivo(self, tmp_path):
        """Error si frames_dir apunta a un archivo, no un directorio."""
        archivo = tmp_path / "archivo.txt"
        archivo.write_text("no soy un directorio")
        with pytest.raises(NotADirectoryError, match="not a directory"):
            generate_report(frames_dir=str(archivo))

    def test_lanza_value_error_cuando_directorio_esta_vacio(self, tmp_path):
        """Error si el directorio existe pero no contiene frames PNG."""
        vacio = tmp_path / "vacio"
        vacio.mkdir()
        with pytest.raises(ValueError, match="No frames found"):
            generate_report(frames_dir=str(vacio))

    def test_lanza_file_not_found_cuando_spritesheet_path_no_existe(self, tmp_path):
        """Error si spritesheet_path no existe en disco."""
        paths = create_synthetic_frames(tmp_path / "src", count=3, size=(64, 64))
        inexistente = tmp_path / "no_existe.png"
        with pytest.raises(FileNotFoundError, match="does not exist"):
            generate_report(frames=paths, spritesheet_path=str(inexistente))


# ---------------------------------------------------------------------------
# Contenido del reporte — frames consistentes
# ---------------------------------------------------------------------------

class TestConsistentFrames:
    def test_reporta_dimensiones_consistentes(self, tmp_path):
        """Todos los frames del mismo tamaño → consistent_dimensions=True."""
        paths = create_synthetic_frames(tmp_path / "src", count=3, size=(64, 64))
        out = generate_report(frames=paths, output_file=str(tmp_path / "report.json"))
        with open(out) as f:
            report = json.load(f)

        assert report["consistent_dimensions"] is True
        assert report["mismatched_frames"] == []
        assert report["reference_size"] == [64, 64]

    def test_cada_frame_tiene_sus_dimensiones_en_report(self, tmp_path):
        """'frames' debe contener una entrada por frame con file/width/height."""
        paths = create_synthetic_frames(tmp_path / "src", count=3, size=(64, 64),
                                         color=(255, 0, 0))
        paths += create_synthetic_frames(tmp_path / "src2", count=1, size=(32, 32),
                                          color=(0, 255, 0))

        all_paths = sorted(paths)
        out = generate_report(frames=all_paths, output_file=str(tmp_path / "report.json"))
        with open(out) as f:
            report = json.load(f)

        # Sólo verificar los 3 primeros (todos 64×64)
        for i in range(3):
            entry = report["frames"][i]
            assert entry["file"] == Path(all_paths[i]).name
            assert entry["width"] == 64
            assert entry["height"] == 64

    def test_total_frames_correcto(self, tmp_path):
        """total_frames debe coincidir con la cantidad de frames."""
        paths = create_synthetic_frames(tmp_path / "src", count=5, size=(64, 64))
        out = generate_report(frames=paths, output_file=str(tmp_path / "report.json"))
        with open(out) as f:
            report = json.load(f)
        assert report["total_frames"] == 5
        assert len(report["frames"]) == 5

    def test_reference_size_es_del_primer_frame(self, tmp_path):
        """reference_size debe ser el tamaño del primer frame."""
        paths = create_synthetic_frames(tmp_path / "src", count=2, size=(128, 64))
        # Agregar un frame distinto
        img = Image.new("RGBA", (64, 64), (0, 255, 0, 255))
        p = tmp_path / "src" / "frame_distinto.png"
        img.save(p)
        paths = sorted((tmp_path / "src").glob("*.png"))

        out = generate_report(frames=paths, output_file=str(tmp_path / "report.json"))
        with open(out) as f:
            report = json.load(f)
        assert report["reference_size"] == [128, 64]


# ---------------------------------------------------------------------------
# Contenido del reporte — frames inconsistentes (NO debe lanzar excepción)
# ---------------------------------------------------------------------------

class TestInconsistentFrames:
    def test_no_lanza_excepcion_cuando_frames_tienen_distinto_tamano(self, tmp_path):
        """A diferencia de spritesheet_lineal/grid, NO debe lanzar ValueError."""
        paths = create_synthetic_frames(tmp_path / "src", count=2, size=(64, 64))
        img = Image.new("RGBA", (32, 32), (0, 255, 0, 255))
        img.save(tmp_path / "src" / "small.png")
        all_paths = sorted((tmp_path / "src").glob("*.png"))

        # No debe lanzar excepción
        generate_report(frames=all_paths, output_file=str(tmp_path / "report.json"))

    def test_reporta_dimensiones_inconsistentes(self, tmp_path):
        """Frame de tamaño distinto → consistent_dimensions=False, incluido en mismatched."""
        paths = create_synthetic_frames(tmp_path / "src", count=2, size=(64, 64))
        img = Image.new("RGBA", (32, 32), (0, 255, 0, 255))
        img.save(tmp_path / "src" / "small.png")
        all_paths = sorted((tmp_path / "src").glob("*.png"))

        out = generate_report(frames=all_paths, output_file=str(tmp_path / "report.json"))
        with open(out) as f:
            report = json.load(f)

        assert report["consistent_dimensions"] is False
        assert "small.png" in report["mismatched_frames"]
        assert len(report["mismatched_frames"]) == 1

    def test_multiple_inconsistentes(self, tmp_path):
        """Varios frames de tamaños distintos deben aparecer todos en mismatched."""
        src = tmp_path / "src"
        src.mkdir()

        # Primer frame 64×64 (referencia)
        Image.new("RGBA", (64, 64), (255, 0, 0, 255)).save(src / "frame_0000.png")
        Image.new("RGBA", (48, 48), (0, 255, 0, 255)).save(src / "frame_0001.png")
        Image.new("RGBA", (64, 64), (0, 0, 255, 255)).save(src / "frame_0002.png")
        Image.new("RGBA", (96, 64), (255, 255, 0, 255)).save(src / "frame_0003.png")

        all_paths = sorted(src.glob("*.png"))
        out = generate_report(frames=all_paths, output_file=str(tmp_path / "report.json"))
        with open(out) as f:
            report = json.load(f)

        assert report["consistent_dimensions"] is False
        assert sorted(report["mismatched_frames"]) == ["frame_0001.png", "frame_0003.png"]


# ---------------------------------------------------------------------------
# Spritesheet_path
# ---------------------------------------------------------------------------

class TestSpritesheetPath:
    def test_con_spritesheet_valido_incluye_path_y_size(self, tmp_path):
        """Al pasar spritesheet_path válido, se incluyen path y size."""
        paths = create_synthetic_frames(tmp_path / "src", count=4, size=(64, 64))
        sprite = tmp_path / "sheet.png"
        Image.new("RGBA", (128, 128), (0, 0, 0, 255)).save(sprite)

        out = generate_report(frames=paths, spritesheet_path=str(sprite),
                               output_file=str(tmp_path / "report.json"))
        with open(out) as f:
            report = json.load(f)

        assert report["spritesheet_path"] == str(sprite)
        assert report["spritesheet_size"] == [128, 128]

    def test_sin_spritesheet_campos_son_none(self, tmp_path):
        """Sin spritesheet_path → spritesheet_path=None, spritesheet_size=None."""
        paths = create_synthetic_frames(tmp_path / "src", count=3, size=(64, 64))
        out = generate_report(frames=paths, output_file=str(tmp_path / "report.json"))
        with open(out) as f:
            report = json.load(f)

        assert report["spritesheet_path"] is None
        assert report["spritesheet_size"] is None


# ---------------------------------------------------------------------------
# Entrada / salida
# ---------------------------------------------------------------------------

class TestIO:
    def test_funciona_con_frames_list(self, tmp_path):
        """Acepta lista de paths en 'frames'."""
        paths = create_synthetic_frames(tmp_path / "src", count=3, size=(64, 64))
        out = generate_report(frames=paths, output_file=str(tmp_path / "r.json"))
        assert out.exists()

    def test_funciona_con_frames_dir(self, tmp_path):
        """Acepta directorio en 'frames_dir'."""
        src = tmp_path / "src"
        create_synthetic_frames(src, count=3, size=(64, 64))
        out = generate_report(frames_dir=str(src), output_file=str(tmp_path / "r.json"))
        assert out.exists()

    def test_archivo_json_se_crea_en_disco_y_es_parseable(self, tmp_path):
        """El reporte se escribe en disco y es JSON válido."""
        paths = create_synthetic_frames(tmp_path / "src", count=3, size=(64, 64))
        out = generate_report(frames=paths, output_file=str(tmp_path / "report.json"))

        assert out.exists()
        assert out.stat().st_size > 0
        # Debe ser parseable sin error
        with open(out) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_agrega_extension_json_si_no_tiene(self, tmp_path):
        """Sin extensión en output_file, debe agregar .json automáticamente."""
        paths = create_synthetic_frames(tmp_path / "src", count=3, size=(64, 64))
        result = generate_report(frames=paths, output_file=str(tmp_path / "noext"))
        assert str(result).endswith(".json")
        assert result.exists()

    def test_generated_at_es_timestamp_iso_valido(self, tmp_path):
        """generated_at debe ser un timestamp ISO 8601 parseable."""
        paths = create_synthetic_frames(tmp_path / "src", count=3, size=(64, 64))
        out = generate_report(frames=paths, output_file=str(tmp_path / "report.json"))
        with open(out) as f:
            report = json.load(f)

        ts = report["generated_at"]
        assert isinstance(ts, str)
        # Debe ser parseable sin lanzar excepción
        parsed = datetime.fromisoformat(ts)
        assert parsed is not None
