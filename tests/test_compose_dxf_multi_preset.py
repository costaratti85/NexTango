"""Tests for multi-preset compose_dxf (PUNTO_PRESET_POR_FIGURA).

Covers:
- compose_dxf with selected_items (new style)
- compose_dxf_legacy backward compat wrapper
- entity_variants matching logic (bbox-center proximity)
"""
import sys
import os
import math
import tempfile
from pathlib import Path
import pytest

# Add erpnext app to path so we can import the vectorize modules directly
_ERPNEXT = Path(__file__).resolve().parents[2] / "Nextango-erpnext" / "apps" / "sistema_industrial"
if str(_ERPNEXT) not in sys.path:
    sys.path.insert(0, str(_ERPNEXT))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_manifest(presets):
    """Build a minimal manifest dict for testing."""
    return {"run_id": "test", "presets": presets}


def _preset(name, entities, transform_scale=1.0):
    return {"name": name, "transform_scale": transform_scale, "entities": entities}


def _entity(eid, d, bbox=None):
    return {"id": eid, "d": d, "bbox_approx": bbox or {"x": 0, "y": 0, "w": 10, "h": 10}}


# Minimal SVG path: a small square (LINE entities only, no splines)
_SQUARE_D = "M 0 0 L 10 0 L 10 10 L 0 10 Z"
_TRIANGLE_D = "M 0 0 L 5 8 L 10 0 Z"


# ---------------------------------------------------------------------------
# compose_dxf — new multi-preset style
# ---------------------------------------------------------------------------

class TestComposeDxfMultiPreset:

    def test_single_entity_single_preset(self, tmp_path):
        """compose_dxf with one item renders without error."""
        from sistema_industrial.vectorize.composer import compose_dxf
        manifest = _minimal_manifest([
            _preset("Fino", [_entity("e0", _SQUARE_D)]),
        ])
        out = tmp_path / "out.dxf"
        compose_dxf(manifest, [{"entity_id": "e0", "preset": "Fino"}], 1.0, out)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_two_entities_same_preset(self, tmp_path):
        """Two items, same preset — both entities included."""
        from sistema_industrial.vectorize.composer import compose_dxf
        import ezdxf
        manifest = _minimal_manifest([
            _preset("Fino", [
                _entity("e0", _SQUARE_D),
                _entity("e1", _TRIANGLE_D),
                _entity("e2", _SQUARE_D),
            ]),
        ])
        out = tmp_path / "out.dxf"
        compose_dxf(manifest, [
            {"entity_id": "e0", "preset": "Fino"},
            {"entity_id": "e1", "preset": "Fino"},
        ], 1.0, out)
        doc = ezdxf.readfile(str(out))
        msp = doc.modelspace()
        lines = [e for e in msp if e.dxftype() == "LINE"]
        # e0 has 4 lines (square), e1 has 3 lines (triangle) = 7 total
        assert len(lines) == 7

    def test_two_entities_different_presets(self, tmp_path):
        """Each entity uses its own preset — entities from correct presets."""
        from sistema_industrial.vectorize.composer import compose_dxf
        import ezdxf
        # Fino has square (4 line segments), Ultra-Fino has triangle (3 lines)
        manifest = _minimal_manifest([
            _preset("Fino",       [_entity("e0", _SQUARE_D)]),
            _preset("Ultra-Fino", [_entity("e0", _TRIANGLE_D)]),
        ])
        out = tmp_path / "out.dxf"
        compose_dxf(manifest, [
            {"entity_id": "e0", "preset": "Fino"},       # square
            {"entity_id": "e0", "preset": "Ultra-Fino"}, # triangle
        ], 1.0, out)
        doc = ezdxf.readfile(str(out))
        msp = doc.modelspace()
        lines = [e for e in msp if e.dxftype() == "LINE"]
        assert len(lines) == 7  # 4 (square) + 3 (triangle)

    def test_unknown_preset_skipped(self, tmp_path):
        """Item with nonexistent preset is silently skipped."""
        from sistema_industrial.vectorize.composer import compose_dxf
        import ezdxf
        manifest = _minimal_manifest([
            _preset("Fino", [_entity("e0", _SQUARE_D)]),
        ])
        out = tmp_path / "out.dxf"
        compose_dxf(manifest, [
            {"entity_id": "e0", "preset": "Fino"},
            {"entity_id": "e1", "preset": "NoExiste"},
        ], 1.0, out)
        doc = ezdxf.readfile(str(out))
        lines = [e for e in doc.modelspace() if e.dxftype() == "LINE"]
        assert len(lines) == 4  # only the square

    def test_unknown_entity_id_skipped(self, tmp_path):
        """Item with nonexistent entity_id in a valid preset is silently skipped."""
        from sistema_industrial.vectorize.composer import compose_dxf
        import ezdxf
        manifest = _minimal_manifest([
            _preset("Fino", [_entity("e0", _SQUARE_D)]),
        ])
        out = tmp_path / "out.dxf"
        compose_dxf(manifest, [
            {"entity_id": "e0", "preset": "Fino"},
            {"entity_id": "e99", "preset": "Fino"},
        ], 1.0, out)
        doc = ezdxf.readfile(str(out))
        lines = [e for e in doc.modelspace() if e.dxftype() == "LINE"]
        assert len(lines) == 4

    def test_scale_applied_per_preset(self, tmp_path):
        """Each item uses the transform_scale of its own preset."""
        from sistema_industrial.vectorize.composer import compose_dxf
        import ezdxf
        # Preset A: transform_scale=1.0, Preset B: transform_scale=2.0
        # Same path "M 0 0 L 10 0" → line endpoint at (10*scale*escala, 0)
        manifest = _minimal_manifest([
            _preset("A", [_entity("e0", "M 0 0 L 10 0")], transform_scale=1.0),
            _preset("B", [_entity("e0", "M 0 0 L 10 0")], transform_scale=2.0),
        ])
        out = tmp_path / "out.dxf"
        compose_dxf(manifest, [
            {"entity_id": "e0", "preset": "A"},
            {"entity_id": "e0", "preset": "B"},
        ], escala_display=1.0, output_path=out)
        doc = ezdxf.readfile(str(out))
        lines = sorted(
            [e for e in doc.modelspace() if e.dxftype() == "LINE"],
            key=lambda l: l.dxf.end.x
        )
        assert len(lines) == 2
        # Preset A produces line ending at x=10*1.0*1.0=10
        # Preset B produces line ending at x=10*2.0*1.0=20
        ends_x = sorted(l.dxf.end.x for l in lines)
        assert abs(ends_x[0] - 10.0) < 1e-6
        assert abs(ends_x[1] - 20.0) < 1e-6

    def test_empty_selected_items_produces_valid_dxf(self, tmp_path):
        """Empty selection → valid DXF with no entities."""
        from sistema_industrial.vectorize.composer import compose_dxf
        import ezdxf
        manifest = _minimal_manifest([_preset("Fino", [_entity("e0", _SQUARE_D)])])
        out = tmp_path / "out.dxf"
        compose_dxf(manifest, [], 1.0, out)
        doc = ezdxf.readfile(str(out))
        assert list(doc.modelspace()) == [] or all(
            e.dxftype() not in ("LINE", "ARC", "SPLINE")
            for e in doc.modelspace()
        )


# ---------------------------------------------------------------------------
# compose_dxf_legacy — backward compat
# ---------------------------------------------------------------------------

class TestComposeDxfLegacy:

    def test_legacy_wrapper_produces_same_output(self, tmp_path):
        """compose_dxf_legacy gives same result as compose_dxf with uniform preset."""
        from sistema_industrial.vectorize.composer import compose_dxf, compose_dxf_legacy
        import ezdxf
        manifest = _minimal_manifest([
            _preset("Fino", [
                _entity("e0", _SQUARE_D),
                _entity("e1", _TRIANGLE_D),
            ]),
        ])
        out_new = tmp_path / "new.dxf"
        out_leg = tmp_path / "leg.dxf"

        compose_dxf(manifest, [
            {"entity_id": "e0", "preset": "Fino"},
            {"entity_id": "e1", "preset": "Fino"},
        ], 1.0, out_new)

        compose_dxf_legacy(manifest, "Fino", ["e0", "e1"], 1.0, out_leg)

        def count_lines(path):
            return len([e for e in ezdxf.readfile(str(path)).modelspace()
                        if e.dxftype() == "LINE"])

        assert count_lines(out_new) == count_lines(out_leg)


# ---------------------------------------------------------------------------
# get_entity_variants — bbox-center matching logic
# ---------------------------------------------------------------------------

class TestGetEntityVariants:
    """Test the bbox-center proximity matching used by get_entity_variants.

    We test the matching logic in isolation (no Frappe context needed).
    """

    @staticmethod
    def _find_best(entities, ref_cx, ref_cy, tol):
        """Replicate the matching logic from get_entity_variants."""
        best = None
        best_dist = float("inf")
        for e in entities:
            ebb = e.get("bbox_approx", {})
            cx = ebb.get("x", 0) + ebb.get("w", 0) / 2.0
            cy = ebb.get("y", 0) + ebb.get("h", 0) / 2.0
            dist = math.sqrt((cx - ref_cx) ** 2 + (cy - ref_cy) ** 2)
            if dist < best_dist:
                best_dist = dist
                best = e
        if best is not None and best_dist <= tol:
            return best, best_dist
        return None, best_dist

    def test_exact_center_match(self):
        """Entity with identical bbox-center is matched."""
        entities = [
            _entity("e0", "", {"x": 100, "y": 200, "w": 20, "h": 20}),
            _entity("e1", "", {"x": 200, "y": 300, "w": 20, "h": 20}),
        ]
        best, dist = self._find_best(entities, ref_cx=110, ref_cy=210, tol=5.0)
        assert best is not None
        assert best["id"] == "e0"
        assert dist < 1e-9  # exact

    def test_closest_wins(self):
        """When multiple entities are near, the closest one wins."""
        entities = [
            _entity("e0", "", {"x":  0, "y": 0, "w": 10, "h": 10}),   # center (5,5)
            _entity("e1", "", {"x": 20, "y": 0, "w": 10, "h": 10}),   # center (25,5)
        ]
        best, dist = self._find_best(entities, ref_cx=6, ref_cy=5, tol=20.0)
        assert best["id"] == "e0"

    def test_outside_tolerance_returns_none(self):
        """Entity outside tolerance is not returned."""
        entities = [
            _entity("e0", "", {"x": 100, "y": 100, "w": 10, "h": 10}),  # center (105,105)
        ]
        best, dist = self._find_best(entities, ref_cx=0, ref_cy=0, tol=5.0)
        assert best is None

    def test_tolerance_boundary(self):
        """Entity at exactly tol distance is included (<=)."""
        entities = [
            _entity("e0", "", {"x": 3, "y": 0, "w": 4, "h": 0}),  # center (5, 0)
        ]
        # ref at (0,0), entity center at (5,0), dist=5.0
        best, dist = self._find_best(entities, ref_cx=0, ref_cy=0, tol=5.0)
        assert best is not None
        assert abs(dist - 5.0) < 1e-9

    def test_size_similarity_tiebreak(self):
        """When two entities equidistant, test documents the first-wins behavior."""
        entities = [
            _entity("e0", "", {"x": 0, "y": 0, "w": 10, "h": 10}),   # center (5,5)
            _entity("e1", "", {"x": 0, "y": 0, "w": 10, "h": 10}),   # center (5,5) — same
        ]
        best, _ = self._find_best(entities, ref_cx=5, ref_cy=5, tol=1.0)
        assert best["id"] == "e0"  # first one wins when equidistant


# ---------------------------------------------------------------------------
# compose_dxf — bbox centering (PUNTO_ORIGEN_SIN_CENTRAR_COMPOSE_DXF)
# ---------------------------------------------------------------------------

class TestComposeDxfCentering:

    def test_centered_on_origin_after_compose(self, tmp_path):
        """compose_dxf centers entity bbox on (0,0) before saving."""
        from sistema_industrial.vectorize.composer import compose_dxf
        import ezdxf
        # Square at (100,200)→(110,210) — center at (105,205), should move to (0,0)
        manifest = _minimal_manifest([
            _preset("Fino", [_entity("e0", "M 100 200 L 110 200 L 110 210 L 100 210 Z")]),
        ])
        out = tmp_path / "out.dxf"
        compose_dxf(manifest, [{"entity_id": "e0", "preset": "Fino"}], 1.0, out)
        doc = ezdxf.readfile(str(out))
        lines = [e for e in doc.modelspace() if e.dxftype() == "LINE"]
        xs = [l.dxf.start.x for l in lines] + [l.dxf.end.x for l in lines]
        ys = [l.dxf.start.y for l in lines] + [l.dxf.end.y for l in lines]
        cx = (min(xs) + max(xs)) / 2
        cy = (min(ys) + max(ys)) / 2
        assert abs(cx) < 1e-4, f"Expected bbox center x≈0, got {cx}"
        assert abs(cy) < 1e-4, f"Expected bbox center y≈0, got {cy}"

    def test_already_centered_unchanged(self, tmp_path):
        """compose_dxf does not alter a pattern already centered at origin."""
        from sistema_industrial.vectorize.composer import compose_dxf
        import ezdxf
        # Square symmetric around origin: (-5,-5)→(5,5)
        manifest = _minimal_manifest([
            _preset("Fino", [_entity("e0", "M -5 -5 L 5 -5 L 5 5 L -5 5 Z")]),
        ])
        out = tmp_path / "out.dxf"
        compose_dxf(manifest, [{"entity_id": "e0", "preset": "Fino"}], 1.0, out)
        doc = ezdxf.readfile(str(out))
        lines = [e for e in doc.modelspace() if e.dxftype() == "LINE"]
        xs = [l.dxf.start.x for l in lines] + [l.dxf.end.x for l in lines]
        ys = [l.dxf.start.y for l in lines] + [l.dxf.end.y for l in lines]
        assert abs(min(xs) + 5) < 1e-4
        assert abs(max(xs) - 5) < 1e-4

    def test_centering_preserves_geometry(self, tmp_path):
        """Centering translates but does not distort — width and height stay the same."""
        from sistema_industrial.vectorize.composer import compose_dxf
        import ezdxf
        # 30x20 rectangle at (1000, 500)
        manifest = _minimal_manifest([
            _preset("Fino", [_entity("e0", "M 1000 500 L 1030 500 L 1030 520 L 1000 520 Z")]),
        ])
        out = tmp_path / "out.dxf"
        compose_dxf(manifest, [{"entity_id": "e0", "preset": "Fino"}], 1.0, out)
        doc = ezdxf.readfile(str(out))
        lines = [e for e in doc.modelspace() if e.dxftype() == "LINE"]
        xs = [l.dxf.start.x for l in lines] + [l.dxf.end.x for l in lines]
        ys = [l.dxf.start.y for l in lines] + [l.dxf.end.y for l in lines]
        assert abs(max(xs) - min(xs) - 30) < 1e-4, "Width should be 30"
        assert abs(max(ys) - min(ys) - 20) < 1e-4, "Height should be 20"


# ---------------------------------------------------------------------------
# _bbox_from_d — relative commands (PUNTO_BBOX_APPROX_COMANDOS_RELATIVOS)
# ---------------------------------------------------------------------------

class TestBboxFromD:

    @staticmethod
    def _bbox(d):
        from sistema_industrial.vectorize.runner import _bbox_from_d
        return _bbox_from_d(d)

    def test_absolute_commands_unchanged(self):
        """Absolute commands: bbox matches direct coordinate min/max."""
        bb = self._bbox("M 10 20 L 50 20 L 50 60 L 10 60 Z")
        assert abs(bb["x"] - 10) < 0.2
        assert abs(bb["y"] - 20) < 0.2
        assert abs(bb["w"] - 40) < 0.2
        assert abs(bb["h"] - 40) < 0.2

    def test_relative_move_and_lines(self):
        """Relative m,l commands accumulate position correctly."""
        # m 100 200 l 10 0 l 0 10 z → square at (100,200)-(110,210)
        bb = self._bbox("m 100 200 l 10 0 l 0 10 z")
        assert abs(bb["x"] - 100) < 0.2, f"Expected x≈100, got {bb['x']}"
        assert abs(bb["y"] - 200) < 0.2, f"Expected y≈200, got {bb['y']}"
        assert abs(bb["w"] - 10) < 0.2, f"Expected w≈10, got {bb['w']}"
        assert abs(bb["h"] - 10) < 0.2, f"Expected h≈10, got {bb['h']}"

    def test_relative_cubic_bezier(self):
        """Relative c command: control points accumulated from current position."""
        # M 100 100 c 0 -50 100 -50 100 0 → a Bézier from (100,100) to (200,100)
        # control pts at (100,50) and (200,50)
        bb = self._bbox("M 100 100 c 0 -50 100 -50 100 0")
        # x range: 100..200, y range: 50..100
        assert bb["x"] <= 100.1
        assert bb["x"] + bb["w"] >= 199.9
        assert bb["y"] <= 50.1
        assert bb["y"] + bb["h"] >= 99.9

    def test_relative_path_far_from_origin(self):
        """Relative path at (500,300) gives correct bbox, not near-zero."""
        bb = self._bbox("M 500 300 l 20 0 l 0 15 l -20 0 z")
        assert bb["x"] >= 490, f"x should be ~500, got {bb['x']}"
        assert bb["y"] >= 290, f"y should be ~300, got {bb['y']}"
        assert abs(bb["w"] - 20) < 0.2
        assert abs(bb["h"] - 15) < 0.2

    def test_mixed_absolute_and_relative(self):
        """Path mixing absolute M with relative l commands."""
        # M 200 100 l 30 0 l 0 20 l -30 0 z → rect at (200,100) 30×20
        bb = self._bbox("M 200 100 l 30 0 l 0 20 l -30 0 z")
        assert abs(bb["x"] - 200) < 0.2
        assert abs(bb["y"] - 100) < 0.2
        assert abs(bb["w"] - 30) < 0.2
        assert abs(bb["h"] - 20) < 0.2

    def test_empty_d_returns_zero_bbox(self):
        """Empty path → zero bbox without error."""
        bb = self._bbox("")
        assert bb == {"x": 0.0, "y": 0.0, "w": 0.0, "h": 0.0}


# ---------------------------------------------------------------------------
# Corner-clipping at tangent discontinuities (PUNTO_ESQUINA_SIGUE_TORCIDA)
# ---------------------------------------------------------------------------

class TestVecAngleDeg:
    """Unit tests for _vec_angle_deg helper."""

    @staticmethod
    def _angle(v1, v2):
        from sistema_industrial.vectorize.composer import _vec_angle_deg
        return _vec_angle_deg(v1, v2)

    def test_parallel_vectors_zero_deg(self):
        assert abs(self._angle((1, 0), (2, 0))) < 1e-6

    def test_antiparallel_vectors_180_deg(self):
        assert abs(self._angle((1, 0), (-1, 0)) - 180.0) < 1e-6

    def test_perpendicular_vectors_90_deg(self):
        assert abs(self._angle((1, 0), (0, 1)) - 90.0) < 1e-6

    def test_45_deg(self):
        assert abs(self._angle((1, 0), (1, 1)) - 45.0) < 1e-3

    def test_degenerate_zero_vector_returns_zero(self):
        """Zero-length vector: angle = 0 (no clipping triggered)."""
        assert self._angle((0, 0), (1, 0)) == 0.0


class TestDeCasteljauSplit:
    """Unit tests for _de_casteljau_split."""

    @staticmethod
    def _split(p0, p1, p2, p3, t):
        from sistema_industrial.vectorize.composer import _de_casteljau_split
        return _de_casteljau_split(p0, p1, p2, p3, t)

    def test_split_at_zero_returns_degenerate_first(self):
        """t=0: first piece is a degenerate point, second is the full curve."""
        p0, p1, p2, p3 = (0, 0), (1, 0), (1, 1), (0, 1)
        first, second = self._split(p0, p1, p2, p3, 0.0)
        assert abs(first[0][0]) < 1e-9 and abs(first[0][1]) < 1e-9
        assert abs(first[3][0]) < 1e-9 and abs(first[3][1]) < 1e-9  # first is a point

    def test_split_at_one_returns_degenerate_second(self):
        """t=1: second piece is degenerate, first is the full curve."""
        p0, p1, p2, p3 = (0, 0), (1, 0), (1, 1), (0, 1)
        first, second = self._split(p0, p1, p2, p3, 1.0)
        assert abs(first[0][0]) < 1e-9
        assert abs(first[3][0] - 0) < 1e-9 and abs(first[3][1] - 1) < 1e-9

    def test_split_at_half_midpoint(self):
        """t=0.5: split point for a symmetric Bézier is at its midpoint."""
        # Symmetric cubic: P0=(0,0) P1=(0,1) P2=(1,1) P3=(1,0)
        # At t=0.5 the curve passes through (0.5, 0.75) for this symmetric case
        p0, p1, p2, p3 = (0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)
        first, second = self._split(p0, p1, p2, p3, 0.5)
        # Endpoints must be connected: first[3] == second[0]
        assert abs(first[3][0] - second[0][0]) < 1e-9
        assert abs(first[3][1] - second[0][1]) < 1e-9
        # Outer endpoints preserved
        assert abs(first[0][0] - p0[0]) < 1e-9
        assert abs(second[3][0] - p3[0]) < 1e-9

    def test_linear_bezier_split_point_on_line(self):
        """For a degenerate (linear) Bézier, split point lies on the line."""
        # P0=(0,0) P1=(1,0) P2=(2,0) P3=(3,0) — a straight line
        p0, p1, p2, p3 = (0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0)
        first, second = self._split(p0, p1, p2, p3, 0.87)
        # Split point should be at x = 3 * 0.87 = 2.61
        assert abs(first[3][0] - 3.0 * 0.87) < 1e-6
        assert abs(first[3][1]) < 1e-9


class TestSplitAtCorners:
    """Integration tests for corner detection and clipping pipeline."""

    @staticmethod
    def _split(d, scale=1.0):
        from sistema_industrial.vectorize.composer import (
            _parse_path_segments, _split_at_corners
        )
        segs = _parse_path_segments(d, scale)
        return _split_at_corners(segs)

    def _count(self, d, scale=1.0):
        segs = self._split(d, scale)
        cubics = sum(1 for s in segs if s[0] == "cubic")
        lines  = sum(1 for s in segs if s[0] == "line")
        return cubics, lines

    def test_smooth_join_no_clip(self):
        """Two Béziers meeting at <25° are NOT clipped — count unchanged."""
        # Two very similar Béziers meeting with ~0° angle (tangent-continuous)
        # Segment 1: P0=(0,0) P1=(1,0) P2=(2,0) P3=(3,0) — horizontal exit
        # Segment 2: P3=(3,0) P4=(4,0) P5=(5,0) P6=(6,0) — horizontal entry
        d = "M 0 0 C 1 0 2 0 3 0 C 4 0 5 0 6 0"
        cubics, lines = self._count(d)
        assert cubics == 2  # both intact
        assert lines == 0

    def test_right_angle_corner_produces_stubs(self):
        """Two Béziers with 90° junction → each gets a LINE stub at the corner."""
        # Segment 1: exit tangent pointing right  (+x)
        # Segment 2: entry tangent pointing down   (-y) — 90° difference
        # P0=(0,0) P1=(1,0) P2=(2,0) P3=(3,0) | P4=(3,-1) P5=(3,-2) P6=(3,-3)
        d = "M 0 0 C 1 0 2 0 3 0 C 3 -1 3 -2 3 -3"
        cubics, lines = self._count(d)
        assert cubics == 2     # main body of each Bézier survives as SPLINE
        assert lines == 2      # one stub per side of the corner

    def test_sharp_corner_stub_endpoints_at_junction(self):
        """The LINE stubs both touch the junction point P3."""
        # Same 90° corner path
        d = "M 0 0 C 1 0 2 0 3 0 C 3 -1 3 -2 3 -3"
        segs = self._split(d)
        lines = [s for s in segs if s[0] == "line"]
        assert len(lines) == 2
        # Stub of segment 1 (tail): its endpoint (p1) should be near (3,0)
        tail_stub = lines[0]
        assert abs(tail_stub[2][0] - 3.0) < 0.1  # near P3.x
        assert abs(tail_stub[2][1] - 0.0) < 0.1  # near P3.y
        # Stub of segment 2 (head): its startpoint (p0) should be near (3,0)
        head_stub = lines[1]
        assert abs(head_stub[1][0] - 3.0) < 0.1
        assert abs(head_stub[1][1] - 0.0) < 0.1

    def test_three_segments_two_corners(self):
        """Three Béziers with two 90° corners → 4 stubs total."""
        # Seg1: right, Seg2: down, Seg3: left — L-shape with two 90° corners
        d = (
            "M 0 0 C 1 0 2 0 3 0 "    # seg1: exit →
            "C 3 -1 3 -2 3 -3 "        # seg2: entry ↓, exit ↓
            "C 2 -3 1 -3 0 -3"         # seg3: entry ←
        )
        cubics, lines = self._count(d)
        assert cubics == 3
        assert lines == 4  # tail+head at first corner, tail+head at second

    def test_line_between_cubics_breaks_adjacency(self):
        """A LINE between two cubics means they are NOT adjacent → no clipping."""
        from sistema_industrial.vectorize.composer import (
            _parse_path_segments, _split_at_corners
        )
        # Build segments manually: cubic, LINE, cubic with 90° that would trigger
        segs = [
            ("cubic", (0.0,0.0), (1.0,0.0), (2.0,0.0), (3.0,0.0)),
            ("line",  (3.0,0.0), (3.0,0.5)),   # intervening line breaks chain
            ("cubic", (3.0,0.5), (3.0,-0.5), (3.0,-1.5), (3.0,-3.0)),
        ]
        result = _split_at_corners(segs)
        cubics = sum(1 for s in result if s[0] == "cubic")
        lines  = sum(1 for s in result if s[0] == "line")
        assert cubics == 2
        assert lines == 1   # only the original intervening line
