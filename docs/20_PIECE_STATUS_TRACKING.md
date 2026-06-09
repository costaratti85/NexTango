# Piece Status Tracking

Every manufactured or cut piece must have a traceable lifecycle.

Minimum states:
- draft
- quoted
- ordered
- pending_cut
- batched
- sent_to_cypcut
- cut
- ready
- delivered
- cancelled

The system must be able to answer:
- Is this piece already cut?
- Is it pending?
- Which batch includes it?
- Which order/customer generated it?
