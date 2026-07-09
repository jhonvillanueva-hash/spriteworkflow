# SpriteWorkflow

Biblioteca Python para convertir videos en spritesheets (hojas de sprites).
Extrae fotogramas de un video, opcionalmente remueve el fondo por chroma-key,
y los ensambla en un spritesheet lineal (horizontal) o en cuadrícula (grid).
Incluye un reporte de validación en formato JSON.

## Instalación

```bash
pip install spriteworkflow
```

Requiere **Python ≥ 3.10** y dependencias: `opencv-python`, `pillow`, `imageio-ffmpeg`.

### Dependencias de sistema

- **FFmpeg**: necesario para la extracción de fotogramas. La biblioteca lo
  localiza automáticamente con `imageio-ffmpeg`, pero si no está disponible
  puedes instalarlo manualmente:
  - Windows: `winget install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

---

## Funciones de la biblioteca

### `extract_frames(video_name, output_dir="temp")`

Extrae fotogramas de un video en archivos PNG numerados.

| Parámetro      | Tipo              | Default   | Descripción                              |
|----------------|-------------------|-----------|------------------------------------------|
| `video_name`   | `str` o `Path`    | —         | Ruta al archivo de video                 |
| `output_dir`   | `str` o `Path`    | `"temp"`  | Directorio de salida (se crea si no existe) |

- **Retorna**: `list[Path]` — rutas a los PNG extraídos, ordenados.
- **Excepciones**: `FileNotFoundError` (video no existe),
  `ValueError` (archivo inválido o vacío), `PermissionError` (sin permiso),
  `RuntimeError` (FFmpeg falla o no se extrajeron fotogramas).

### `remove_background(frames=None, frames_dir=None, bg_color=None, tolerance=30, feather=0, output_dir="matted")`

Elimina el fondo de fotogramas mediante chroma-key (distancia euclidiana en RGB).

| Parámetro     | Tipo              | Default     | Descripción                                    |
|---------------|-------------------|-------------|------------------------------------------------|
| `frames`      | `list[Path]`      | `None`      | Lista de rutas a los fotogramas PNG            |
| `frames_dir`  | `str` o `Path`    | `None`      | Directorio con PNG (alternativa a `frames`)    |
| `bg_color`    | `tuple[int,int,int]` | `None`   | RGB del chroma-key; auto-detectado si es `None`|
| `tolerance`   | `int`             | `30`        | Distancia euclídea máxima del color de fondo   |
| `feather`     | `int`             | `0`         | Ancho del difuminado lineal alrededor de `tolerance`|
| `output_dir`  | `str` o `Path`    | `"matted"`  | Directorio para los PNG con canal alpha        |

- **Retorna**: `list[Path]` — rutas a los PNG procesados (RGBA), ordenados.
- **Excepciones**: `ValueError` (parámetros inválidos),
  `FileNotFoundError` (`frames_dir` no existe),
  `NotADirectoryError` (`frames_dir` no es directorio).

### `create_spritesheet_lineal(frames=None, frames_dir=None, output_file="spritesheet.png")`

Ensambla fotogramas en un spritesheet horizontal (una fila).

| Parámetro      | Tipo              | Default              | Descripción                              |
|----------------|-------------------|----------------------|------------------------------------------|
| `frames`       | `list[Path]`      | `None`               | Lista de rutas a los fotogramas PNG      |
| `frames_dir`   | `str` o `Path`    | `None`               | Directorio con PNG (alternativa a `frames`)|
| `output_file`  | `str` o `Path`    | `"spritesheet.png"`  | Ruta del spritesheet generado            |

- **Retorna**: `Path` — ruta al archivo generado.
- **Excepciones**: `ValueError`, `FileNotFoundError`, `NotADirectoryError`.

### `create_spritesheet_grid(frames=None, frames_dir=None, columns=None, padding=0, background=(0,0,0,0), output_file="spritesheet_grid.png")`

Ensambla fotogramas en un spritesheet en cuadrícula (filas × columnas).

| Parámetro      | Tipo               | Default                    | Descripción                              |
|----------------|--------------------|----------------------------|------------------------------------------|
| `frames`       | `list[Path]`       | `None`                     | Lista de rutas a los fotogramas PNG      |
| `frames_dir`   | `str` o `Path`     | `None`                     | Directorio con PNG (alternativa a `frames`)|
| `columns`      | `int` o `None`     | `None`                     | N° de columnas; `None` = `ceil(sqrt(N))`|
| `padding`      | `int`              | `0`                        | Píxeles de espacio entre celdas         |
| `background`   | `tuple[int,int,int,int]` | `(0,0,0,0)`         | RGBA de relleno para celdas vacías       |
| `output_file`  | `str` o `Path`     | `"spritesheet_grid.png"`   | Ruta del spritesheet generado            |

- **Retorna**: `Path` — ruta al archivo generado.
- **Excepciones**: `ValueError`, `FileNotFoundError`, `NotADirectoryError`.

### `generate_report(frames=None, frames_dir=None, spritesheet_path=None, output_file="report.json")`

Inspecciona fotogramas y produce un reporte de validación JSON.

| Parámetro          | Tipo              | Default        | Descripción                              |
|--------------------|-------------------|----------------|------------------------------------------|
| `frames`           | `list[Path]`      | `None`         | Lista de rutas a los fotogramas PNG      |
| `frames_dir`       | `str` o `Path`    | `None`         | Directorio con PNG (alternativa)         |
| `spritesheet_path` | `str` o `Path`    | `None`         | Ruta al spritesheet (opcional)           |
| `output_file`      | `str` o `Path`    | `"report.json"`| Ruta del archivo JSON generado           |

- **Retorna**: `Path` — ruta al archivo JSON.
- **Excepciones**: `ValueError`, `FileNotFoundError`, `NotADirectoryError`.

El reporte incluye: `total_frames`, `frames[]` (archivo, ancho, alto),
`consistent_dimensions`, `reference_size`, `mismatched_frames`,
`spritesheet_path`, `spritesheet_size`, y `generated_at`.

---

## Ejemplo de uso (como biblioteca)

```python
from spriteworkflow import extract_frames, remove_background
from spriteworkflow import create_spritesheet_grid, generate_report

# 1. Extraer fotogramas de un video
frames = extract_frames("gameplay.mp4", output_dir="temp")
print(f"Extraídos {len(frames)} fotogramas")

# 2. Remover fondo verde (chroma-key)
frames_matted = remove_background(
    frames=frames,
    bg_color=(0, 255, 0),
    tolerance=40,
    output_dir="matted",
)

# 3. Crear spritesheet en grilla (3 columnas)
sheet = create_spritesheet_grid(
    frames=frames_matted,
    columns=3,
    padding=2,
    background=(0, 0, 0, 0),
    output_file="hoja_sprites.png",
)
print(f"Spritesheet guardado: {sheet}")

# 4. Generar reporte de validación
report = generate_report(
    frames=frames_matted,
    spritesheet_path=sheet,
    output_file="reporte.json",
)
print(f"Reporte guardado: {report}")
```

---

## Uso desde CLI

El paquete instala el comando `spriteworkflow` con un subcomando `build` que
encadena el pipeline completo:

```bash
spriteworkflow build <video> [opciones]
```

### Argumentos

| Argumento / Flag        | Descripción                                   | Default                 |
|-------------------------|-----------------------------------------------|-------------------------|
| `video`                 | Ruta al video de entrada (requerido)          | —                       |
| `--output`, `-o`        | Ruta del spritesheet generado                 | `spritesheet.png`       |
| `--layout`              | Lineal o grid (`lineal`, `grid`)              | `lineal`                |
| `--columns`             | Columnas para grilla (auto si no se indica)   | auto `ceil(sqrt(N))`    |
| `--padding`             | Píxeles de separación entre celdas            | `0`                     |
| `--matte`               | Activa remoción de fondo por chroma-key       | desactivado             |
| `--bg-color`            | RGB para chroma-key, ej: `--bg-color 0 255 0`| auto-detectado          |
| `--tolerance`           | Tolerancia euclídea de chroma-key             | `30`                    |
| `--feather`             | Difuminado del borde del chroma-key           | `0`                     |
| `--report-file`         | Ruta del reporte JSON de validación           | no se genera            |
| `--temp-dir`            | Directorio temporal para fotogramas extraídos | `temp`                  |

### Ejemplos

```bash
# Pipeline mínimo: extraer y ensamblar spritesheet lineal
spriteworkflow build partida.mp4

# Especificar ruta de salida
spriteworkflow build partida.mp4 -o assets/hoja.png

# Spritesheet en grilla de 4 columnas con padding
spriteworkflow build partida.mp4 --layout grid --columns 4 --padding 2

# Remover chroma-key verde, luego ensamblar spritesheet
spriteworkflow build partida.mp4 --matte --bg-color 0 255 0

# Pipeline completo con reporte
spriteworkflow build partida.mp4 \
    --layout grid --columns 4 --padding 2 \
    --matte --tolerance 40 \
    --report-file reporte.json
```

## Ejecutar pruebas

El proyecto usa `pytest`. Para ejecutar la suite completa:

```bash
pip install -e ".[test]"
pytest -v
```

Para ejecutar un archivo de pruebas específico:

```bash
pytest tests/cli_test.py -v
```

---

## Licencia

MIT
