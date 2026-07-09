from pathlib import Path
from PIL import Image
import pytest

from spriteworkflow.matte import remove_background
from tests.conftest import create_chroma_key_frames, create_synthetic_frames


# ---------------------------------------------------------------------------
# Validación de parámetros de entrada
# ---------------------------------------------------------------------------

class TestInputValidation:
    def test_lanza_value_error_cuando_no_se_pasa_frames_ni_frames_dir(self):
        """Error si no se pasa ni 'frames' ni 'frames_dir'."""
        with pytest.raises(ValueError, match="Either 'frames' or 'frames_dir' must be provided"):
            remove_background()

    def test_lanza_value_error_cuando_se_pasan_ambos(self, tmp_path):
        """Error si se pasan 'frames' y 'frames_dir' simultáneamente."""
        frame = tmp_path / "dummy.png"
        frame.write_text("")
        with pytest.raises(ValueError, match="Only one"):
            remove_background(
                frames=[frame],
                frames_dir=str(tmp_path),
                output_dir=str(tmp_path / "out"),
            )

    def test_lanza_file_not_found_cuando_frames_dir_no_existe(self, tmp_path):
        """Error si frames_dir no existe en disco."""
        inexistente = tmp_path / "no_existe"
        with pytest.raises(FileNotFoundError, match="does not exist"):
            remove_background(
                frames_dir=str(inexistente),
                output_dir=str(tmp_path / "out"),
            )

    def test_lanza_not_a_directory_cuando_frames_dir_es_un_archivo(self, tmp_path):
        """Error si frames_dir apunta a un archivo, no un directorio."""
        archivo = tmp_path / "archivo.txt"
        archivo.write_text("no soy un directorio")
        with pytest.raises(NotADirectoryError, match="not a directory"):
            remove_background(
                frames_dir=str(archivo),
                output_dir=str(tmp_path / "out"),
            )

    def test_lanza_value_error_cuando_directorio_esta_vacio(self, tmp_path):
        """Error si el directorio existe pero no contiene frames PNG."""
        vacio = tmp_path / "vacio"
        vacio.mkdir()
        with pytest.raises(ValueError, match="No frames found"):
            remove_background(
                frames_dir=str(vacio),
                output_dir=str(tmp_path / "out"),
            )

    def test_lanza_value_error_si_bg_color_no_es_tupla_rgb(self, tmp_path):
        """Error si bg_color no es una tupla RGB válida."""
        frame = tmp_path / "frame.png"
        Image.new("RGBA", (64, 64), (255, 0, 0, 255)).save(frame)

        # No es una tupla
        with pytest.raises(ValueError, match="bg_color must be a tuple"):
            remove_background(frames=[frame], bg_color="green", output_dir=str(tmp_path / "out"))

        # Tupla con valor fuera de rango
        with pytest.raises(ValueError, match="range 0-255"):
            remove_background(frames=[frame], bg_color=(1, 2, 300), output_dir=str(tmp_path / "out"))

        # Tupla con longitud incorrecta
        with pytest.raises(ValueError, match="bg_color must be a tuple"):
            remove_background(frames=[frame], bg_color=(1, 2), output_dir=str(tmp_path / "out"))


# ---------------------------------------------------------------------------
# Chroma-key — comportamiento del algoritmo
# ---------------------------------------------------------------------------

class TestChromaKey:
    BG = (0, 255, 0)       # green screen
    SUBJECT = (255, 0, 0)  # red subject

    def test_con_bg_color_explicito_fondo_se_vuelve_transparente(self, tmp_path):
        """Con bg_color explícito: fondo alpha=0, sujeto alpha=255."""
        paths = create_chroma_key_frames(
            tmp_path / "src", count=1, size=(64, 64),
            bg_color=self.BG, subject_color=self.SUBJECT, subject_radius=10,
        )
        out = remove_background(frames=paths, bg_color=self.BG, tolerance=30,
                                output_dir=str(tmp_path / "out"))
        result = Image.open(out[0])

        # Esquina superior izquierda → fondo verde → alpha=0
        assert result.getpixel((0, 0))[3] == 0, "bg pixel should be transparent"

        # Centro → sujeto rojo → alpha=255
        assert result.getpixel((32, 32))[3] == 255, "subject pixel should be opaque"

    def test_autodeteccion_bg_color_desde_esquinas(self, tmp_path):
        """Sin bg_color explícito: debe autodetectar desde las esquinas."""
        paths = create_chroma_key_frames(
            tmp_path / "src", count=1, size=(64, 64),
            bg_color=self.BG, subject_color=self.SUBJECT, subject_radius=10,
        )
        out_auto = remove_background(frames=paths, tolerance=30,
                                     output_dir=str(tmp_path / "auto"))
        out_explicit = remove_background(frames=paths, bg_color=self.BG, tolerance=30,
                                         output_dir=str(tmp_path / "explicit"))

        auto_img = Image.open(out_auto[0])
        explicit_img = Image.open(out_explicit[0])

        # Same alpha mask (autodetect should match explicit bg_color)
        for y in range(64):
            for x in range(64):
                assert auto_img.getpixel((x, y)) == explicit_img.getpixel((x, y)), \
                    f"autodetect mismatch at ({x},{y})"

    def test_tolerance_controla_que_pixeles_cercanos_sean_transparentes(self, tmp_path):
        """Con tolerance=30 un pixel cercano al bg es transparente; con tolerance=0 es opaco."""
        bg = (0, 255, 0)
        near_bg = (0, 254, 0)   # distance = 1
        far = (255, 0, 0)       # distance ≈ 360

        size = (64, 64)
        img = Image.new("RGBA", size, bg + (255,))
        img.putpixel((10, 10), near_bg + (255,))
        img.putpixel((20, 20), far + (255,))

        frame = tmp_path / "tol_frame.png"
        img.save(frame)
        frames = [frame]

        # tolerance=30 → near_bg dentro del rango → transparente
        out_high = remove_background(frames=frames, bg_color=bg, tolerance=30,
                                     output_dir=str(tmp_path / "out_high"))
        r_high = Image.open(out_high[0])
        assert r_high.getpixel((10, 10))[3] == 0, "near_bg debe ser transparente con tol=30"
        assert r_high.getpixel((20, 20))[3] == 255, "far debe ser opaco con tol=30"
        assert r_high.getpixel((0, 0))[3] == 0, "bg debe ser transparente con tol=30"

        # tolerance=0 → near_bg fuera del rango → opaco
        out_low = remove_background(frames=frames, bg_color=bg, tolerance=0,
                                    output_dir=str(tmp_path / "out_low"))
        r_low = Image.open(out_low[0])
        assert r_low.getpixel((10, 10))[3] == 255, "near_bg debe ser opaco con tol=0"
        assert r_low.getpixel((20, 20))[3] == 255, "far debe ser opaco con tol=0"
        assert r_low.getpixel((0, 0))[3] == 0, "bg debe ser transparente con tol=0"

    def test_colores_rgb_se_conservan_en_pixeles_opacos(self, tmp_path):
        """Los canales RGB del sujeto deben preservarse (no alterarse)."""
        paths = create_chroma_key_frames(
            tmp_path / "src", count=1, size=(64, 64),
            bg_color=self.BG, subject_color=self.SUBJECT, subject_radius=10,
        )
        out = remove_background(frames=paths, bg_color=self.BG, tolerance=30,
                                output_dir=str(tmp_path / "out"))
        result = Image.open(out[0])

        # Centro del sujeto → RGB original preservado
        subject_pixel = result.getpixel((32, 32))
        assert subject_pixel[:3] == self.SUBJECT, \
            f"Subject RGB should be {self.SUBJECT}, got {subject_pixel[:3]}"


# ---------------------------------------------------------------------------
# Comportamiento de entrada / salida
# ---------------------------------------------------------------------------

class TestIO:
    def test_funciona_con_frames_list(self, tmp_path):
        """Acepta lista de paths en 'frames'."""
        paths = create_chroma_key_frames(
            tmp_path / "src", count=2, size=(64, 64),
        )
        out = remove_background(frames=paths, bg_color=(0, 255, 0), tolerance=30,
                                output_dir=str(tmp_path / "out"))
        assert len(out) == 2

    def test_funciona_con_frames_dir(self, tmp_path):
        """Acepta directorio en 'frames_dir'."""
        src = tmp_path / "src"
        create_chroma_key_frames(src, count=3, size=(64, 64))
        out = remove_background(frames_dir=str(src), bg_color=(0, 255, 0), tolerance=30,
                                output_dir=str(tmp_path / "out"))
        assert len(out) == 3

    def test_archivos_de_salida_se_crean_en_output_dir(self, tmp_path):
        """Los archivos procesados se escriben en output_dir con el nombre original."""
        paths = create_chroma_key_frames(
            tmp_path / "src", count=2, size=(64, 64),
        )
        out_dir = tmp_path / "processed"
        out = remove_background(frames=paths, bg_color=(0, 255, 0), tolerance=30,
                                output_dir=str(out_dir))

        assert out_dir.exists()
        for i, p in enumerate(out):
            assert p.parent == out_dir
            assert p.name == f"frame_{i:04d}.png"
            assert p.exists()
            assert p.stat().st_size > 0

    def test_retorna_lista_ordenada_de_paths(self, tmp_path):
        """El valor de retorno es una lista ordenada de Path."""
        paths = create_chroma_key_frames(
            tmp_path / "src", count=3, size=(64, 64),
        )
        out = remove_background(frames=paths, bg_color=(0, 255, 0), tolerance=30,
                                output_dir=str(tmp_path / "out"))
        assert isinstance(out, list)
        assert all(isinstance(p, Path) for p in out)
        assert out == sorted(out)
