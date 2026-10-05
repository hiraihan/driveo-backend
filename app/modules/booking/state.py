from app.core.enums import BookingState, BookingEvent
from app.core.errors import InvalidTransition

TRANSITIONS: dict[tuple[BookingState, BookingEvent], BookingState] = {
    (BookingState.MENUNGGU_DP, BookingEvent.DP_PAID): BookingState.MENUNGGU_KONFIRMASI_RENTAL,
    (BookingState.MENUNGGU_DP, BookingEvent.CANCEL): BookingState.DIBATALKAN,
    (BookingState.MENUNGGU_DP, BookingEvent.EXPIRE): BookingState.DIBATALKAN,
    
    (BookingState.MENUNGGU_KONFIRMASI_RENTAL, BookingEvent.CONFIRM): BookingState.TERKONFIRMASI,
    (BookingState.MENUNGGU_KONFIRMASI_RENTAL, BookingEvent.REJECT): BookingState.DITOLAK,
    (BookingState.MENUNGGU_KONFIRMASI_RENTAL, BookingEvent.CANCEL): BookingState.DIBATALKAN,
    (BookingState.MENUNGGU_KONFIRMASI_RENTAL, BookingEvent.SLA_BREACH): BookingState.DIBATALKAN,
    
    (BookingState.TERKONFIRMASI, BookingEvent.CANCEL): BookingState.DIBATALKAN,
    (BookingState.TERKONFIRMASI, BookingEvent.HANDOVER): BookingState.BERJALAN,
    
    (BookingState.BERJALAN, BookingEvent.RETURN): BookingState.SELESAI,
}

def transition(booking, event: BookingEvent) -> BookingState:
    state = BookingState(booking.booking_state)
    key = (state, event)
    if key not in TRANSITIONS:
        raise InvalidTransition(state=state.value, event=event.value)
    
    new_state = TRANSITIONS[key]
    booking.booking_state = new_state.value
    return new_state
