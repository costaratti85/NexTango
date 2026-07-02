"""Image-to-potrace multi-preset vectorizer.

Pipeline:
  1. Image (PNG/JPG) → binarize with threshold (Pillow) → PBM tempfile
  2. potrace --svg → SVG per preset
  3. Parse SVG: extract closed <path> elements → compute bbox
  4. Match figures across presets by bbox-center proximity
  5. Return manifest dict (also saved to run_dir/manifest.json)

Run state stored in:
  <site>/private/vectorize_runs/{run_id}/
    manifest.json         — full result
    {preset_slug}.svg     — raw SVG from potrace
"""
import json
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
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
    """Convert image to 1-bit PBM using Pillow (potrace native input)."""
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


def _parse_svg_paths(svg_path: Path):
    """Extract closed path elements from potrace SVG.

    Returns list of dicts: {d, bbox, nodes}.
    Numbers are extracted from d to approximate bbox (adequate for figure matching).
    """
    tree = ET.parse(str(svg_path))
    root = tree.getroot()

    paths = []
    for elem in root.iter("{http://www.w3.org/2000/svg}path"):
        d = elem.get("d", "").strip()
        if not d or "z" not in d.lower():
            continue  # only closed paths

        nums = [float(n) for n in re.findall(
            r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", d
        )]
        if len(nums) < 4:
            continue

        xs = nums[0::2]
        ys = nums[1::2]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        w, h = max_x - min_x, max_y - min_y
        if w < 1 or h < 1:
            continue

        bbox = {"x": round(min_x, 2), "y": round(min_y, 2),
                "w": round(w, 2), "h": round(h, 2)}
        nodes = len(re.findall(r"[MLCQmlcq]", d))
        paths.append({"d": d, "bbox": bbox, "nodes": nodes})

    return paths


def _bbox_center(bbox):
    return bbox["x"] + bbox["w"] / 2, bbox["y"] + bbox["h"] / 2


def _bboxes_match(b1, b2, tol_factor=0.35):
    """True if bboxes are likely the same figure across presets."""
    cx1, cy1 = _bbox_center(b1)
    cx2, cy2 = _bbox_center(b2)
    dist = ((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2) ** 0.5
    diag1 = (b1["w"] ** 2 + b1["h"] ** 2) ** 0.5
    diag2 = (b2["w"] ** 2 + b2["h"] ** 2) ** 0.5
    tol = tol_factor * (diag1 + diag2) / 2
    return dist < tol


def _make_svg_preview(d: str, bbox: dict) -> str:
    pad = max(bbox["w"], bbox["h"]) * 0.08
    vb = (
        f"{bbox['x'] - pad:.1f} {bbox['y'] - pad:.1f} "
        f"{bbox['w'] + 2*pad:.1f} {bbox['h'] + 2*pad:.1f}"
    )
    d_safe = d.replace('"', "&quot;")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" '
        f'width="100" height="100">'
        f'<path d="{d_safe}" fill="none" stroke="currentColor" stroke-width="1"/>'
        f'</svg>'
    )


def _match_figures(preset_results: list) -> list:
    """Group path results across presets into figures with per-preset variantes.

    preset_results: [(preset_name, [path_dicts]), ...]
    Returns: [{figura_id, bbox, variantes: [{preset, svg_preview, d, metrics}]}]
    """
    preset_names = [p for p, _ in preset_results]
    groups = []  # [{bbox, members: {preset_name: path_dict}}]

    for preset_name, paths in preset_results:
        for path in paths:
            best_g = None
            best_dist = float("inf")
            for g in groups:
                if preset_name in g["members"]:
                    continue
                if _bboxes_match(path["bbox"], g["bbox"]):
                    cx1, cy1 = _bbox_center(path["bbox"])
                    cx2, cy2 = _bbox_center(g["bbox"])
                    d = ((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2) ** 0.5
                    if d < best_dist:
                        best_g, best_dist = g, d
            if best_g is not None:
                best_g["members"][preset_name] = path
            else:
                groups.append({"bbox": path["bbox"], "members": {preset_name: path}})

    figuras = []
    for i, g in enumerate(groups):
        variantes = []
        for preset_name in preset_names:
            if preset_name in g["members"]:
                p = g["members"][preset_name]
                variantes.append({
                    "preset": preset_name,
                    "d": p["d"],
                    "svg_preview": _make_svg_preview(p["d"], p["bbox"]),
                    "metrics": {
                        "nodes": p["nodes"],
                        "area_approx": round(p["bbox"]["w"] * p["bbox"]["h"], 1),
                    },
                })
            else:
                variantes.append({
                    "preset": preset_name,
                    "d": None,
                    "svg_preview": None,
                    "metrics": None,
                })
        figuras.append({
            "figura_id": f"fig_{i}",
            "bbox": g["bbox"],
            "variantes": variantes,
        })

    return figuras


def vectorize(image_path: Path, run_dir: Path, presets: list = None) -> dict:
    """Run multi-preset potrace vectorization and save manifest.

    Returns the manifest dict.
    """
    if presets is None:
        presets = PRESETS

    preset_results = []

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        for preset in presets:
            slug = _preset_slug(preset["name"])
            pbm_path = tmp_dir / f"{slug}.pbm"
            svg_path = run_dir / f"{slug}.svg"
            try:
                _binarize(image_path, preset["threshold"], pbm_path)
                _run_potrace(pbm_path, svg_path, preset)
                paths = _parse_svg_paths(svg_path)
            except Exception:
                paths = []
            preset_results.append((preset["name"], paths))

    figuras = _match_figures(preset_results)

    manifest = {
        "run_id": run_dir.name,
        "image_path": str(image_path),
        "preset_names": [p["name"] for p in presets],
        "figura_count": len(figuras),
        "figuras": figuras,
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest
