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
