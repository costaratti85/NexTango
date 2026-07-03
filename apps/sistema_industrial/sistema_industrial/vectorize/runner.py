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


def _parse_potrace_svg(svg_text: str) -> tuple:
    """Extract entities and metadata from potrace SVG text via regex.

    Returns (transform_scale, viewbox, path_ds):
      transform_scale: |sx| from group transform — typically 0.1 (path units × 0.1 = display units)
      viewbox: viewBox attribute string, e.g. "0 0 4800 4320"
      path_ds: list of closed-path d attribute strings
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

    # Extract closed path d attributes
    path_ds = []
    for pm in re.finditer(r'<path\b[^>]*/>', svg_text):
        elem = pm.group(0)
        dm = re.search(r'\bd="([^"]*)"', elem)
        if not dm:
            continue
        d = dm.group(1).strip()
        if d and "z" in d.lower():
            path_ds.append(d)

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
    - Each <path>: add id="e{i}", vector-effect="non-scaling-stroke", stroke-width="2"

    vector-effect="non-scaling-stroke" makes stroke always 2px on screen regardless
    of the SVG viewBox coordinates or any CSS scaling — solving the invisible-stroke bug.
    """
    # Change group fill/stroke (handles both #000000 and #000 forms)
    result = re.sub(
        r'(<g\b[^>]*?)\bfill="#(?:000000|000)"\s+stroke="none"',
        r'\1fill="none" stroke="#555555"',
        svg_text,
    )

    idx = [0]

    def _stamp_entity(m):
        elem = m.group(0)
        i = idx[0]
        idx[0] += 1
        attrs = f' id="e{i}" vector-effect="non-scaling-stroke" stroke-width="2"'
        # Insert before self-closing />
        return re.sub(r'\s*/>$', attrs + '/>', elem)

    result = re.sub(r'<path\b[^>]*/>', _stamp_entity, result)
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
