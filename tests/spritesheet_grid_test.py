import math
from pathlib import Path
from PIL import Image
import pytest

from spriteworkflow.spritesheet_grid import create_spritesheet_grid
from tests.conftest import create_synthetic_frames


# ---------------------------------------------------------------------------
# Validación de parámetros de entrada
# ---------------------------------------------------------------------------

class TestInputValidation:
    def test_lanza_value_error_cuando_no_se_pasa_frames_ni_frames_dir(self):
        """Error si no se pasa ni 'frames' ni 'frames_dir'."""
        with pytest.raises(ValueError, match="Either 'frames' or 'frames_dir' must be provided"):
            create_spritesheet_grid()

    def test_lanza_value_error_cuando_se_pasan_ambos(self, tmp_path):
        """Error si se pasan 'frames' y 'frames_dir' simultáneamente."""
        frame = tmp_path / "dummy.png"
        frame.write_text("")
        with pytest.raises(ValueError, match="Only one"):
            create_spritesheet_grid(
                frames=[frame],
                frames_dir=str(tmp_path),
            )

    def test_lanza_file_not_found_cuando_frames_dir_no_existe(self, tmp_path):
        """Error si frames_dir no existe en disco."""
        inexistente = tmp_path / "no_existe"
        with pytest.raises(FileNotFoundError, match="does not exist"):
            create_spritesheet_grid(frames_dir=str(inexistente))

    def test_lanza_not_a_directory_cuando_frames_dir_es_un_archivo(self, tmp_path):
        """Error si frames_dir apunta a un archivo, no un directorio."""
        archivo = tmp_path / "archivo.txt"
        archivo.write_text("no soy un directorio")
        with pytest.raises(NotADirectoryError, match="not a directory"):
            create_spritesheet_grid(frames_dir=str(archivo))

    def test_lanza_value_error_cuando_directorio_esta_vacio(self, tmp_path):
        """Error si el directorio existe pero no contiene frames PNG."""
        vacio = tmp_path / "vacio"
        vacio.mkdir()
        with pytest.raises(ValueError, match="No frames found"):
            create_spritesheet_grid(frames_dir=str(vacio))

    def test_lanza_value_error_si_frame_tiene_tamanio_distinto(self, tmp_path):
        """Error si un frame tiene tamaño diferente al del primer frame."""
        src = tmp_path / "src"
        src.mkdir()
        create_synthetic_frames(src, count=3, size=(64, 64), color=(255, 0, 0))
        img_bad = Image.new("RGBA", (32, 32), (0, 255, 0, 255))
        img_bad.save(src / "frame_distinto.png")

        with pytest.raises(ValueError, match="different size"):
            create_spritesheet_grid(frames_dir=str(src))

    def test_lanza_value_error_cuando_columns_no_es_entero_valido(self, tmp_path):
        """Error si columns no es int >= 1."""
        paths = create_synthetic_frames(tmp_path / "src", count=4, size=(64, 64))
        with pytest.raises(ValueError, match="columns must be an integer >= 1"):
            create_spritesheet_grid(frames=paths, columns=0)
        with pytest.raises(ValueError, match="columns must be an integer >= 1"):
            create_spritesheet_grid(frames=paths, columns=-1)
        with pytest.raises(ValueError, match="columns must be an integer >= 1"):
            create_spritesheet_grid(frames=paths, columns=2.5)


# ---------------------------------------------------------------------------
# Dimensiones del sheet
# ---------------------------------------------------------------------------

class TestDimensions:
    def test_4_frames_columns_2_dimensiones_correctas(self, tmp_path):
        """4 frames, columns=2, padding=0 → ancho=128, alto=128."""
        paths = create_synthetic_frames(tmp_path / "src", count=4, size=(64, 64))
        out = create_spritesheet_grid(frames=paths, columns=2, padding=0,
                                      output_file=str(tmp_path / "sheet.png"))
        sheet = Image.open(out)
        assert sheet.size == (128, 128)

    def test_6_frames_columns_3_dimensiones_correctas(self, tmp_path):
        """6 frames, columns=3, padding=0 → ancho=192, alto=128."""
        paths = create_synthetic_frames(tmp_path / "src", count=6, size=(64, 64))
        out = create_spritesheet_grid(frames=paths, columns=3, padding=0,
                                      output_file=str(tmp_path / "sheet.png"))
        sheet = Image.open(out)
        assert sheet.size == (192, 128)

    def test_columns_autocalculado_ceil_sqrt(self, tmp_path):
        """5 frames, columns=None → columns=ceil(sqrt(5))=3, rows=2."""
        paths = create_synthetic_frames(tmp_path / "src", count=5, size=(64, 64))
        out = create_spritesheet_grid(frames=paths, columns=None, padding=0,
                                      output_file=str(tmp_path / "sheet.png"))
        sheet = Image.open(out)
        expected_cols = math.ceil(math.sqrt(5))
        expected_rows = math.ceil(5 / expected_cols)
        assert sheet.size == (expected_cols * 64, expected_rows * 64)

    def test_9_frames_columns_none_cuadrado_perfecto(self, tmp_path):
        """9 frames, columns=None → 3×3 grid."""
        paths = create_synthetic_frames(tmp_path / "src", count=9, size=(64, 64))
        out = create_spritesheet_grid(frames=paths, columns=None,
                                      output_file=str(tmp_path / "sheet.png"))
        sheet = Image.open(out)
        assert sheet.size == (192, 192)


# ---------------------------------------------------------------------------
# Posiciones de los frames en el grid
# ---------------------------------------------------------------------------

class TestFramePositions:
    FRAME_SIZE = 64

    def test_cada_frame_en_su_celda_correcta(self, tmp_path):
        """Frames de colores distintos en grid 2×2 → verificar centro de cada celda."""
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
        paths = []
        for i, c in enumerate(colors):
            p = tmp_path / "src" / f"frame_{i:04d}.png"
            p.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGBA", (self.FRAME_SIZE, self.FRAME_SIZE), c + (255,)).save(p)
            paths.append(p)

        out = create_spritesheet_grid(frames=paths, columns=2, padding=0,
                                      output_file=str(tmp_path / "grid.png"))
        sheet = Image.open(out)

        # Celda (col,row) → centro = (col*64 + 32, row*64 + 32)
        cases = [
            ((0, 0), (255, 0, 0)),     # frame 0
            ((1, 0), (0, 255, 0)),     # frame 1
            ((0, 1), (0, 0, 255)),     # frame 2
            ((1, 1), (255, 255, 0)),   # frame 3
        ]
        for (col, row), expected_rgb in cases:
            cx = col * self.FRAME_SIZE + self.FRAME_SIZE // 2
            cy = row * self.FRAME_SIZE + self.FRAME_SIZE // 2
            pixel = sheet.getpixel((cx, cy))
            assert pixel[:3] == expected_rgb, \
                f"celda ({col},{row}) esperaba {expected_rgb}, obtuvo {pixel[:3]}"

    def test_celdas_vacias_quedan_con_background(self, tmp_path):
        """5 frames en grid 2×3 → 6 celdas, la última vacía debe ser transparente."""
        paths = create_synthetic_frames(tmp_path / "src", count=5, size=(64, 64))
        bg = (0, 0, 0, 0)  # completamente transparente
        out = create_spritesheet_grid(frames=paths, columns=2, padding=0,
                                      background=bg,
                                      output_file=str(tmp_path / "grid.png"))
        sheet = Image.open(out)

        # Celda (col=1, row=2) está vacía
        empty_cx = 1 * self.FRAME_SIZE + self.FRAME_SIZE // 2
        empty_cy = 2 * self.FRAME_SIZE + self.FRAME_SIZE // 2
        pixel = sheet.getpixel((empty_cx, empty_cy))
        assert pixel == (0, 0, 0, 0), \
            f"C elda vacía debería ser transparente, obtuve {pixel}"


# ---------------------------------------------------------------------------
# Padding entre celdas
# ---------------------------------------------------------------------------

class TestPadding:
    FRAME_SIZE = 64
    PADDING = 8

    def test_padding_entre_celdas_se_respeta(self, tmp_path):
        """Con padding=8, la zona entre dos celdas debe tener el color de fondo."""
        paths = create_synthetic_frames(
            tmp_path / "src", count=2, size=(self.FRAME_SIZE, self.FRAME_SIZE),
            color=(255, 0, 0),
        )
        bg = (0, 0, 0, 0)
        out = create_spritesheet_grid(frames=paths, columns=2, padding=self.PADDING,
                                      background=bg,
                                      output_file=str(tmp_path / "grid.png"))
        sheet = Image.open(out)

        # Frame 0 ocupa x en [0, 64); Frame 1 ocupa x en [72, 136)
        # Padding zone: x en [64, 72), y en [0, 64)
        pad_x = self.FRAME_SIZE + self.PADDING // 2  # 68
        pad_y = self.FRAME_SIZE // 2  # 32
        pixel = sheet.getpixel((pad_x, pad_y))
        assert pixel == bg, f"padding zone debe ser background {bg}, obtuvo {pixel}"

    def test_padding_con_una_sola_columna_sin_espacio_extra(self, tmp_path):
        """1 columna → no debe haber padding horizontal."""
        paths = create_synthetic_frames(
            tmp_path / "src", count=4, size=(self.FRAME_SIZE, self.FRAME_SIZE),
        )
        bg = (0, 0, 0, 0)
        out = create_spritesheet_grid(frames=paths, columns=1, padding=self.PADDING,
                                      background=bg,
                                      output_file=str(tmp_path / "grid.png"))
        sheet = Image.open(out)
        # ancho = 1*64 + 8*0 = 64 (sin padding horizontal)
        assert sheet.width == self.FRAME_SIZE


# ---------------------------------------------------------------------------
# Comportamiento de entrada / salida
# ---------------------------------------------------------------------------

class TestIO:
    def test_funciona_con_frames_list(self, tmp_path):
        """Acepta lista de paths en 'frames'."""
        paths = create_synthetic_frames(tmp_path / "src", count=4, size=(64, 64))
        out = create_spritesheet_grid(frames=paths, columns=2,
                                      output_file=str(tmp_path / "sheet.png"))
        assert out.exists()

    def test_funciona_con_frames_dir(self, tmp_path):
        """Acepta directorio en 'frames_dir'."""
        src = tmp_path / "src"
        create_synthetic_frames(src, count=4, size=(64, 64))
        out = create_spritesheet_grid(frames_dir=str(src), columns=2,
                                      output_file=str(tmp_path / "sheet.png"))
        assert out.exists()

    def test_agrega_extension_png_si_no_tiene(self, tmp_path):
        """Sin extensión en output_file, debe agregar .png automáticamente."""
        paths = create_synthetic_frames(tmp_path / "src", count=4, size=(64, 64))
        result = create_spritesheet_grid(frames=paths, columns=2,
                                         output_file=str(tmp_path / "noext"))
        assert str(result).endswith(".png")
        assert result.exists()
