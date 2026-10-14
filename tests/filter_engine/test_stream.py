from opensmtpd_filters.filter_engine import Stream


class TestStream:
    """ Tests for the class ``Stream``. """
    
    def test_when_bool_then_correct_value_returned(self) -> None:
        assert not bool(Stream.UNKNOWN)
        assert bool(Stream.FILTER)
    
    def test_when_str_called_then_correct_string_returned(self) -> None:
        for stream in Stream:
            assert stream.name.lower().replace("_", "-") == str(stream)
    
    def test_when_repr_called_then_correct_representation_returned(self) -> None:
        for stream in Stream:
            assert f"Stream.{stream.name}" == repr(stream)
    
    def test_when_missing_called_then_correct_member_returned(self) -> None:
        assert Stream.REPORT == Stream("report")
        assert Stream.CONFIG == Stream("CONFIG")
        assert Stream.UNKNOWN == Stream("stream")
        assert Stream.UNKNOWN == Stream(5)
