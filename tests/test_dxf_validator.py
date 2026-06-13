"""Tests for the DXF entity validator."""

import shutil
import tempfile
from pathlib import Path

import ezdxf
import pytest

from sistema_industrial.presets.dxf_validator import (
    UnsupportedDXFEntitiesError,
    validate_dxf_entities,
)


def _tmp_dxf(msp_fn) -> Path:
    """Write a DXF built by msp_fn to a temp file, return the path."""
    doc = ezdxf.new()
    msp = doc.modelspace()
    msp_fn(msp)
    d = tempfile.mkdtemp()
    path = Path(d) / "test.dxf"
    doc.saveas(str(path))
    return path


def test_valid_dxf_passes():
    path = _tmp_dxf(lambda msp: (
        msp.add_line((0, 0), (10, 0)),
        msp.add_arc((5, 5), radius=3, start_angle=0, end_angle=90),
        msp.add_circle((0, 0), radius=5),
    ))
    validate_dxf_entities(path)  # no debe lanzar


def test_spline_raises():
    path = _tmp_dxf(lambda msp: (
        msp.add_line((0, 0), (10, 0)),
        msp.add_spline([(0, 0), (5, 5), (10, 0)]),
    ))
    with pytest.raises(UnsupportedDXFEntitiesError) as exc_info:
        validate_dxf_entities(path)

    msg = str(exc_info.value)
    assert "SPLINE" in msg
    assert "1" in msg
    assert "Inkscape" in msg


def test_ellipse_raises():
    path = _tmp_dxf(lambda msp: (
        msp.add_ellipse((10, 10), major_axis=(5, 0), ratio=0.5),
    ))
    with pytest.raises(UnsupportedDXFEntitiesError) as exc_info:
        validate_dxf_entities(path)

    assert "ELLIPSE" in str(exc_info.value)


def test_multiple_unsupported_types_listed():
    def build(msp):
        msp.add_spline([(0, 0), (5, 5), (10, 0)])
        msp.add_spline([(1, 1), (6, 6), (11, 1)])
        msp.add_spline([(2, 2), (7, 7), (12, 2)])
        msp.add_ellipse((10, 10), major_axis=(5, 0), ratio=0.5)

    path = _tmp_dxf(build)
    with pytest.raises(UnsupportedDXFEntitiesError) as exc_info:
        validate_dxf_entities(path)

    msg = str(exc_info.value)
    assert "SPLINE" in msg
    assert "ELLIPSE" in msg
    assert "3" in msg


def test_error_message_shows_overflow_suffix():
    def build(msp):
        for i in range(5):
            msp.add_spline([(i, 0), (i + 1, 1), (i + 2, 0)])

    path = _tmp_dxf(build)
    with pytest.raises(UnsupportedDXFEntitiesError) as exc_info:
        validate_dxf_entities(path)

    assert "y 2 más" in str(exc_info.value)


def test_found_attribute_carries_all_entities():
    def build(msp):
        msp.add_spline([(0, 0), (5, 5), (10, 0)])
        msp.add_ellipse((10, 10), major_axis=(5, 0), ratio=0.5)

    path = _tmp_dxf(build)
    with pytest.raises(UnsupportedDXFEntitiesError) as exc_info:
        validate_dxf_entities(path)

    types = {e.entity_type for e in exc_info.value.found}
    assert types == {"SPLINE", "ELLIPSE"}
