from pathlib import Path
from PIL import Image
import pytest

from spriteworkflow.spritesheet_lineal import create_spritesheet_lineal
from tests.conftest import create_synthetic_frames  # helper for parametrized tests


# ---------------------------------------------------------------------------
# Validación de parámetros de entrada
# ---------------------------------------------------------------------------

class TestInputValidation:
    def test_lanza_value_error_cuando_no_se_pasa_frames_ni_frames_dir(self):
        """Error si no se pasa ni 'frames' ni 'frames_dir'."""
        with pytest.raises(ValueError, match="Either 'frames' or 'frames_dir' must be provided"):
            create_spritesheet_lineal()

    def test_lanza_value_error_cuando_se_pasan_ambos(self, frame_list, tmp_path):
        """Error si se pasan 'frames' y 'frames_dir' simultáneamente."""
        with pytest.raises(ValueError, match="Only one"):
            create_spritesheet_lineal(
                frames=frame_list,
                frames_dir=str(tmp_path / "whatever"),
                output_file=str(tmp_path / "out.png"),
            )

    def test_lanza_file_not_found_cuando_frames_dir_no_existe(self, tmp_path):
        """Error si frames_dir no existe en disco."""
        inexistente = tmp_path / "no_existe"
        with pytest.raises(FileNotFoundError, match="does not exist"):
            create_spritesheet_lineal(
                frames_dir=str(inexistente),
                output_file=str(tmp_path / "out.png"),
            )

    def test_lanza_not_a_directory_cuando_frames_dir_es_un_archivo(self, tmp_path):
        """Error si frames_dir apunta a un archivo, no un directorio."""
        archivo = tmp_path / "archivo.txt"
        archivo.write_text("no soy un directorio")
        with pytest.raises(NotADirectoryError, match="not a directory"):
            create_spritesheet_lineal(
                frames_dir=str(archivo),
                output_file=str(tmp_path / "out.png"),
            )

    def test_lanza_value_error_cuando_directorio_esta_vacio(self, tmp_path):
        """Error si el directorio existe pero no contiene frames PNG."""
        vacio = tmp_path / "vacio"
        vacio.mkdir()
        with pytest.raises(ValueError, match="No frames found"):
            create_spritesheet_lineal(
                frames_dir=str(vacio),
                output_file=str(tmp_path / "out.png"),
            )

    def test_lanza_value_error_si_frame_tiene_tamanio_distinto(self, frame_dir, tmp_path):
        """Error si un frame tiene tamaño diferente al del primer frame."""
        # Añadir un frame de tamaño distinto al directorio
        img_bad = Image.new("RGBA", (32, 32), (0, 255, 0, 255))
        img_bad.save(frame_dir / "frame_distinto.png")

        with pytest.raises(ValueError, match="different size"):
            create_spritesheet_lineal(
                frames_dir=str(frame_dir),
                output_file=str(tmp_path / "out.png"),
            )


# ---------------------------------------------------------------------------
# Camino feliz — spritesheet desde lista de frames
# ---------------------------------------------------------------------------

class TestWithFramesList:
    def test_spritesheet_tiene_dimensiones_correctas(self, frame_list, tmp_path):
        """Ancho = frame_width * count, alto = frame_height."""
        output = create_spritesheet_lineal(
            frames=frame_list,
            output_file=str(tmp_path / "sheet.png"),
        )
        sheet = Image.open(output)
        assert sheet.size == (64 * 3, 64)

    def test_numero_de_frames_coincide(self, frame_list, tmp_path):
        """El spritesheet resultante debe contener todos los frames."""
        output = create_spritesheet_lineal(
            frames=frame_list,
            output_file=str(tmp_path / "sheet.png"),
        )
        sheet = Image.open(output)
        assert sheet.width == 64 * len(frame_list)
        assert sheet.height == 64

    @pytest.mark.parametrize("count", [1, 2, 5])
    def test_funciona_con_distinta_cantidad_de_frames(self, tmp_path, count):
        """Funciona con 1, 2 o 5 frames."""
        paths = create_synthetic_frames(
            tmp_path / f"set_{count}",
            count=count,
            size=(64, 64),
            color=(0, 120, 255),
        )
        output = create_spritesheet_lineal(
            frames=paths,
            output_file=str(tmp_path / f"sheet_{count}.png"),
        )
        sheet = Image.open(output)
        assert sheet.size == (64 * count, 64)

    def test_cada_frame_aparece_en_su_posicion_correcta(self, tmp_path):
        """Frames de distintos colores: verificar que cada uno está en su sitio."""
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        paths = []
        for i, c in enumerate(colors):
            img = Image.new("RGBA", (64, 64), c + (255,))
            p = tmp_path / "rainbow" / f"frame_{i:04d}.png"
            p.parent.mkdir(parents=True, exist_ok=True)
            img.save(p)
            paths.append(p)

        output = create_spritesheet_lineal(
            frames=paths,
            output_file=str(tmp_path / "rainbow_sheet.png"),
        )
        sheet = Image.open(output)

        for i, color in enumerate(colors):
            pixel = sheet.getpixel((i * 64 + 32, 32))
            assert pixel == color + (255,), f"Frame {i} no está en columna {i}"


# ---------------------------------------------------------------------------
# Camino feliz — spritesheet desde directorio
# ---------------------------------------------------------------------------

class TestWithFramesDir:
    def test_funciona_con_frames_dir(self, frame_dir, tmp_path):
        """create_spritesheet_lineal acepta frames_dir."""
        output = create_spritesheet_lineal(
            frames_dir=str(frame_dir),
            output_file=str(tmp_path / "from_dir.png"),
        )
        sheet = Image.open(output)
        assert sheet.size == (64 * 3, 64)

    def test_archivo_de_salida_se_crea_en_disco(self, frame_list, tmp_path):
        """Verifica que el archivo spritesheet se escribe realmente en disco."""
        output_path = tmp_path / "salida.png"
        result = create_spritesheet_lineal(
            frames=frame_list,
            output_file=str(output_path),
        )
        assert Path(result).exists()
        assert Path(result).stat().st_size > 0


# ---------------------------------------------------------------------------
# Comportamiento del archivo de salida
# ---------------------------------------------------------------------------

class TestOutputFile:
    def test_agrega_extension_png_si_no_tiene(self, frame_list, tmp_path):
        """Sin extensión en output_file, debe agregar .png automáticamente."""
        result = create_spritesheet_lineal(
            frames=frame_list,
            output_file=str(tmp_path / "noext"),
        )
        assert str(result).endswith(".png")
        assert Path(result).exists()
