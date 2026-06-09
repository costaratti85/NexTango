from sistema_industrial.cutting.status import is_valid_piece_status
from sistema_industrial.security.portal_gate import public_portal_launch_allowed
from sistema_industrial.client_library.models import ClientPieceReference
from sistema_industrial.linear_cutting.models import LinearCutRequest


def test_piece_status_lifecycle_markers_exist():
    assert is_valid_piece_status("pending_cut")
    assert is_valid_piece_status("batched")
    assert is_valid_piece_status("cut")
    assert not is_valid_piece_status("unknown")


def test_public_portal_requires_security_review():
    assert public_portal_launch_allowed(False) is False
    assert public_portal_launch_allowed(True) is True


def test_client_piece_reference_preserves_customer_piece():
    piece = ClientPieceReference(
        customer_code="C001",
        piece_code="PANEL-REPEAT-01",
        description="Repeated decorative panel",
        material="CHAPA",
        thickness_mm=3.0,
    )
    assert piece.customer_code == "C001"
    assert piece.revision == "A"


def test_linear_cutting_request_is_explicit_domain():
    req = LinearCutRequest(
        item_code="TUBO-20X20",
        material="HIERRO",
        profile="20x20",
        required_length_mm=1200,
        quantity=4,
    )
    assert req.quantity == 4
    assert req.required_length_mm == 1200
