import pytest
from app.modules.booking.state import transition, TRANSITIONS
from app.core.enums import BookingState, BookingEvent
from app.core.errors import InvalidTransition

class DummyBooking:
    def __init__(self, state):
        self.booking_state = state

def test_transition_table_length():
    assert len(TRANSITIONS) == 10

@pytest.mark.parametrize("state", list(BookingState))
@pytest.mark.parametrize("event", list(BookingEvent))
def test_all_transitions(state, event):
    booking = DummyBooking(state.value)
    
    key = (state, event)
    if key in TRANSITIONS:
        expected_state = TRANSITIONS[key]
        new_state = transition(booking, event)
        assert new_state == expected_state
        assert booking.booking_state == expected_state.value
    else:
        with pytest.raises(InvalidTransition) as exc_info:
            transition(booking, event)
        assert booking.booking_state == state.value
        assert exc_info.value.details == {"state": state.value, "event": event.value}
