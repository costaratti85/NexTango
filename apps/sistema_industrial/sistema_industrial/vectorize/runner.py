"""Image-to-potrace multi-preset vectorizer — tile extraction model.

Pipeline per preset:
  1. Image (PNG/JPG) → threshold binarize (Pillow) → PBM tempfile
  2. potrace --svg → raw SVG
  3. Parse SVG via regex (avoids xml.etree DOCTYPE issues with potrace output)
  4. Build display SVG: paths styled as outlines, each with id="e{i}" and
     vector-effect="non-scaling-stroke" so strokes are always 2px on screen.
  5. Return manifest {run_id, presets: [{name, svg_full, entities, ...}]}

Run state: <site>/private/vectorize_runs/{run_id}/
  manifest.json       — full result including svg_full per preset
  {slug}.svg          — raw potrace SVG
"""
import json
import re
import subprocess
import tempfile
from pathlib import Path


PRESETS = [
    {"name": "Ultra-Fino",   "turdsize": 2,  "alphamax": 0.5, "opttolerance": 0.1, "threshold": 128},
    {"name": "Fino",         "turdsize": 5,  "alphamax": 0.8, "opttolerance": 0.2, "threshold": 128},
    {"name": "Medio",        "turdsize": 10, "alphamax": 1.0, "opttolerance": 0.3, "threshold": 128},
    {"name": "Grueso",       "turdsize": 20, "alphamax": 1.2, "opttolerance": 0.5, "threshold": 128},
    {"name": "Umbral-Claro", "turdsize": 5,  "alphamax": 0.8, "opttolerance": 0.2, "threshold": 200},
]


def _preset_slug(name):
    return re.sub(r"[^\w]", "_", name).lower()


def _binarize(image_path: Path, threshold: int, pbm_path: Path) -> None:
    """Convert image to 1-bit PBM for potrace input."""
    from PIL import Image
    img = Image.open(str(image_path)).convert("L")
    bw = img.point(lambda p: 0 if p < threshold else 255, "1")
    bw.save(str(pbm_path))


def _run_potrace(pbm_path: Path, svg_path: Path, preset: dict) -> None:
    """Run potrace binary with preset params, output SVG."""
    cmd = [
        "potrace", "--svg",
        f"--turdsize={preset['turdsize']}",
        f"--alphamax={preset['alphamax']}",
        f"--opttolerance={preset['opttolerance']}",
        "-o", str(svg_path),
        str(pbm_path),
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"potrace falló: {result.stderr.decode()}")


def _split_subpaths(d: str) -> list:
    """Split a compound SVG path d into individual closed subpaths (each M…Z).

    potrace emits compound paths for connected geometry: one <path> whose d
    attribute contains N subpaths joined as "M…Z M…Z M…Z" — the outer contour
    plus each hole. We split at every Z→M boundary so each contour becomes its
    own selectable entity.
    """
    parts = re.split(r'(?<=[Zz])\s*(?=[Mm])', d.strip())
    result = [p.strip() for p in parts if p.strip()]
    return result or [d.strip()]


def _parse_potrace_svg(svg_text: str) -> tuple:
    """Extract entities and metadata from potrace SVG text via regex.

    Returns (transform_scale, viewbox, path_ds):
      transform_scale: |sx| from group transform — typically 0.1 (path units × 0.1 = display units)
      viewbox: viewBox attribute string, e.g. "0 0 4800 4320"
      path_ds: list of individual subpath d strings (compound paths are split)
    """
    # viewBox
    m = re.search(r'viewBox="([^"]+)"', svg_text)
    viewbox = m.group(1) if m else "0 0 100 100"

    # Group transform: potrace uses translate(0,H) scale(sx,-sy)
    m = re.search(
        r'<g\b[^>]*transform="translate\([^,]+,[^)]+\)\s+scale\(([^,]+),([^)]+)\)',
        svg_text,
    )
    transform_scale = abs(float(m.group(1))) if m else 1.0

    # Extract all path d attributes; split compound paths into individual subpaths
    # so each closed contour (outer boundary or hole) is a separate selectable entity.
    path_ds = []
    for pm in re.finditer(r'<path\b[^>]*/>', svg_text):
        elem = pm.group(0)
        dm = re.search(r'\bd="([^"]*)"', elem)
        if not dm:
            continue
        d = dm.group(1).strip()
        if d:
            path_ds.extend(_split_subpaths(d))

    return transform_scale, viewbox, path_ds


def _bbox_from_d(d: str) -> dict:
    """Approximate bbox from raw numbers in path d — adequate for rubber-band hints."""
    nums = [float(n) for n in re.findall(
        r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", d
    )]
    if len(nums) < 4:
        return {"x": 0.0, "y": 0.0, "w": 0.0, "h": 0.0}
    xs = nums[0::2]
    ys = nums[1::2]
    return {
        "x": round(min(xs), 1), "y": round(min(ys), 1),
        "w": round(max(xs) - min(xs), 1), "h": round(max(ys) - min(ys), 1),
    }


def _build_display_svg(svg_text: str) -> str:
    """Modify potrace SVG for interactive entity display.

    Changes made:
    - <g fill="#000000" stroke="none"> → fill="none" stroke="#555555"
    - Each compound <path d="M…Z M…Z …"/> is split into N individual <path> elements,
      one per subpath, each with id="e{i}" and vector-effect="non-scaling-stroke".

    Splitting compound paths ensures each contour (outer boundary or hole) is an
    independent hit-target — the user can select individual lines, not filled regions.
    IDs are assigned in the same order as _parse_potrace_svg / _split_subpaths.
    """
    # Change group fill/stroke (handles both #000000 and #000 forms)
    result = re.sub(
        r'(<g\b[^>]*?)\bfill="#(?:000000|000)"\s+stroke="none"',
        r'\1fill="none" stroke="#555555"',
        svg_text,
    )

    idx = [0]

    def _expand_path(m):
        """Replace one <path .../> (possibly compound) with N individual <path> elements."""
        elem = m.group(0)
        dm = re.search(r'\bd="([^"]*)"', elem)
        if not dm or not dm.group(1).strip():
            return elem
        subpaths = _split_subpaths(dm.group(1).strip())
        parts = []
        for sub_d in subpaths:
            i = idx[0]
            idx[0] += 1
            parts.append(
                f'<path id="e{i}" d="{sub_d}" fill="none" stroke="#555555"'
                f' vector-effect="non-scaling-stroke" stroke-width="2"/>'
            )
        return "\n".join(parts)

    result = re.sub(r'<path\b[^>]*/>', _expand_path, result)
    return result


def _vectorize_preset(image_path: Path, run_dir: Path, preset: dict) -> dict:
    """Run one preset and return its manifest entry."""
    slug = _preset_slug(preset["name"])
    svg_path = run_dir / f"{slug}.svg"

    with tempfile.TemporaryDirectory() as tmp:
        pbm_path = Path(tmp) / "input.pbm"
        _binarize(image_path, preset["threshold"], pbm_path)
        _run_potrace(pbm_path, svg_path, preset)

    svg_text = svg_path.read_text(encoding="utf-8", errors="replace")
    transform_scale, viewbox, path_ds = _parse_potrace_svg(svg_text)

    entities = [
        {
            "id": f"e{i}",
            "d": d,
            "bbox_approx": _bbox_from_d(d),
            "nodes": len(re.findall(r"[MLCQmlcq]", d)),
        }
        for i, d in enumerate(path_ds)
    ]

    return {
        "name": preset["name"],
        "slug": slug,
        "transform_scale": transform_scale,
        "viewbox": viewbox,
        "entity_count": len(entities),
        "entities": entities,
        "svg_full": _build_display_svg(svg_text),
    }


def vectorize(image_path: Path, run_dir: Path, presets: list = None) -> dict:
    """Run multi-preset potrace vectorization. Saves manifest, returns it."""
    if presets is None:
        presets = PRESETS

    preset_results = []
    for preset in presets:
        try:
            preset_results.append(_vectorize_preset(image_path, run_dir, preset))
        except Exception as exc:
            preset_results.append({
                "name": preset["name"],
                "slug": _preset_slug(preset["name"]),
                "transform_scale": 0.1,
                "viewbox": "0 0 100 100",
                "entity_count": 0,
                "entities": [],
                "svg_full": "",
                "error": str(exc),
            })

    manifest = {
        "run_id": run_dir.name,
        "image_path": str(image_path),
        "presets": preset_results,
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest
