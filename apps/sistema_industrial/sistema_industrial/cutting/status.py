ALLOWED_PIECE_STATUSES = [
    "draft",
    "quoted",
    "ordered",
    "pending_cut",
    "batched",
    "sent_to_cypcut",
    "cut",
    "ready",
    "delivered",
    "cancelled",
]


def is_valid_piece_status(status: str) -> bool:
    return status in ALLOWED_PIECE_STATUSES
