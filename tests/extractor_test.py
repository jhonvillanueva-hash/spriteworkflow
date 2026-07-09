from pathlib import Path
import subprocess
from PIL import Image
import pytest

from spriteworkflow.extractor import extract_frames


# ---------------------------------------------------------------------------
# Validación de entrada — no requieren mockear ffmpeg
# ---------------------------------------------------------------------------

class TestInputValidation:
    def test_lanza_file_not_found_cuando_video_no_existe(self, tmp_path):
        """Video path no existe en disco."""
        inexistente = tmp_path / "no_existe.mp4"
        with pytest.raises(FileNotFoundError, match="not found"):
            extract_frames(str(inexistente), output_dir=str(tmp_path))

    def test_lanza_value_error_cuando_path_es_directorio(self, tmp_path):
        """Video path es un directorio, no un archivo regular."""
        d = tmp_path / "un_directorio"
        d.mkdir()
        with pytest.raises(ValueError, match="not a valid file"):
            extract_frames(str(d), output_dir=str(tmp_path))

    def test_lanza_value_error_cuando_archivo_esta_vacio(self, tmp_path):
        """Archivo existe pero pesa 0 bytes."""
        vacio = tmp_path / "vacio.mp4"
        vacio.write_text("")
        with pytest.raises(ValueError, match="empty"):
            extract_frames(str(vacio), output_dir=str(tmp_path))


# ---------------------------------------------------------------------------
# Extracción exitosa y errores de ffmpeg — requieren monkeypatch
# ---------------------------------------------------------------------------

class TestExtraction:
    """Helper methods para preparar el escenario de mock."""

    @staticmethod
    def _crear_video_valido(tmp_path, nombre="video.mp4"):
        """Crea un archivo ficticio que pase las validaciones de extract_frames."""
        p = tmp_path / nombre
        p.write_text("fake video content")
        return p

    @staticmethod
    def _mockear_mkdtemp(monkeypatch, tmp_path, subdir="frames_mock"):
        """Hace que tempfile.mkdtemp devuelva una ruta predecible dentro de tmp_path."""
        fake_temp = tmp_path / subdir
        fake_temp.mkdir(exist_ok=True)
        monkeypatch.setattr(
            "tempfile.mkdtemp",
            lambda prefix="", dir=None: str(fake_temp),
        )
        return fake_temp

    @staticmethod
    def _mockear_subprocess_run(monkeypatch):
        """Mockea subprocess.run y retorna lista de (args, kwargs) por llamada."""
        captured = []
        monkeypatch.setattr(
            "subprocess.run",
            lambda *args, **kwargs: captured.append((args, kwargs)),
        )
        return captured

    @staticmethod
    def _assert_comando_ffmpeg(captured, ffmpeg_path, video_path, output_dir):
        """Verifica que subprocess.run fue llamado con el comando ffmpeg esperado."""
        assert len(captured) == 1, "Se esperaba exactamente 1 llamada a subprocess.run"
        call_args, call_kwargs = captured[0]
        cmd = call_args[0]

        assert cmd == [
            ffmpeg_path,
            "-v",
            "error",
            "-i",
            str(video_path),
            str(output_dir / "frame_%04d.png"),
        ]
        assert call_kwargs == {"check": True, "stderr": subprocess.PIPE, "text": True}

    # ------------------------------------------------------------------
    # Camino feliz
    # ------------------------------------------------------------------

    def test_extraccion_exitosa_retorna_frames_ordenados(self, tmp_path, monkeypatch):
        """FFmpeg simulado: crea frames PNG falsos, verifica comando y frames ordenados."""
        video = self._crear_video_valido(tmp_path)
        monkeypatch.setattr(
            "spriteworkflow.extractor.get_ffmpeg_path", lambda: "/fake/ffmpeg"
        )
        fake_temp = self._mockear_mkdtemp(monkeypatch, tmp_path)
        captured = self._mockear_subprocess_run(monkeypatch)

        # Crear frames esperados
        for i in range(4):
            img = Image.new("RGBA", (64, 64), (255, 0, 0, 255))
            img.save(fake_temp / f"frame_{i+1:04d}.png")

        frames = extract_frames(str(video), output_dir=str(tmp_path))

        # Verificar comando ffmpeg
        self._assert_comando_ffmpeg(captured, "/fake/ffmpeg", video, fake_temp)

        # Verificar frames devueltos
        assert len(frames) == 4
        for i, f in enumerate(frames):
            assert f.name == f"frame_{i+1:04d}.png", f"Frame {i} desordenado"
            assert f.exists()
        assert all(isinstance(f, Path) for f in frames)

    def test_extraccion_exitosa_con_un_solo_frame(self, tmp_path, monkeypatch):
        """Un solo frame también funciona; verifica comando ffmpeg."""
        video = self._crear_video_valido(tmp_path)
        monkeypatch.setattr(
            "spriteworkflow.extractor.get_ffmpeg_path", lambda: "/fake/ffmpeg"
        )
        fake_temp = self._mockear_mkdtemp(monkeypatch, tmp_path)
        captured = self._mockear_subprocess_run(monkeypatch)

        img = Image.new("RGBA", (32, 32), (0, 255, 0, 255))
        img.save(fake_temp / "frame_0001.png")

        frames = extract_frames(str(video), output_dir=str(tmp_path))

        # Verificar comando ffmpeg
        self._assert_comando_ffmpeg(captured, "/fake/ffmpeg", video, fake_temp)

        # Verificar frame único
        assert len(frames) == 1
        assert frames[0].name == "frame_0001.png"

    # ------------------------------------------------------------------
    # Errores de ffmpeg
    # ------------------------------------------------------------------

    def test_lanza_runtime_error_cuando_ffmpeg_falla(self, tmp_path, monkeypatch):
        """CalledProcessError de subprocess se relanza como RuntimeError."""
        video = self._crear_video_valido(tmp_path)
        monkeypatch.setattr(
            "spriteworkflow.extractor.get_ffmpeg_path", lambda: "/fake/ffmpeg"
        )

        def mock_run_fail(*args, **kwargs):
            raise subprocess.CalledProcessError(
                1, "ffmpeg", stderr="unknown decoder"
            )

        monkeypatch.setattr("subprocess.run", mock_run_fail)

        with pytest.raises(RuntimeError, match="FFmpeg failed"):
            extract_frames(str(video), output_dir=str(tmp_path))

    def test_lanza_runtime_error_cuando_ffmpeg_no_genera_frames(self, tmp_path, monkeypatch):
        """Si ffmpeg no produce ningún archivo PNG → RuntimeError."""
        video = self._crear_video_valido(tmp_path)
        monkeypatch.setattr(
            "spriteworkflow.extractor.get_ffmpeg_path", lambda: "/fake/ffmpeg"
        )
        self._mockear_mkdtemp(monkeypatch, tmp_path)
        # Usamos el helper de captura en vez del lambda ciego aunque no
        # verifiquemos asserts aquí — consistencia y mantenibilidad.
        self._mockear_subprocess_run(monkeypatch)

        # No creamos frames → glob vacío
        with pytest.raises(RuntimeError, match="No frames were extracted"):
            extract_frames(str(video), output_dir=str(tmp_path))
