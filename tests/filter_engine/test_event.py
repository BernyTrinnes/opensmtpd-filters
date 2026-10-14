import pytest
from opensmtpd_filters.filter_engine import Event, Stream


class TestEvent:
    """ Tests for the class ``Event``. """
    
    def test_when_bool_then_correct_value_returned(self) -> None:
        assert not bool(Event.UNKNOWN)
        assert bool(Event.TX_MAIL)
    
    def test_when_str_then_correct_string_returned(self) -> None:
        for event in Event:
            assert event.name.lower().replace("_", "-") == str(event)
    
    def test_when_repr_then_correct_representation_returned(self) -> None:
        for event in Event:
            assert f"Event.{event.name}" ==  repr(event)
    
    def test_when_missing_then_correct_member_returned(self) -> None:
        assert Event.PROTOCOL_CLIENT == Event("protocol-client")
        assert Event.TIMEOUT == Event("TIMEOUT")
        assert Event.UNKNOWN == Event("event")
        assert Event.UNKNOWN == Event(5)
    
    @pytest.mark.parametrize("stream, event_numbers", [
        (None, 0),
        (Stream.UNKNOWN, 0),
        (Stream.CONFIG, 0),
        (Stream.REPORT, 19),
        (Stream.FILTER, 10)
    ])
    def test_when_all_events_then_return_event_list(self, stream: Stream, event_numbers: int) -> None:
        assert event_numbers == len(Event.all_events(stream))
