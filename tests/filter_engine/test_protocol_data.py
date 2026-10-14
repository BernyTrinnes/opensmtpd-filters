from datetime import datetime

import pytest

from opensmtpd_filters.filter_engine import Event, FilterEngineException, ProtocolData, ProtocolPrefix, Stream, \
    Subsystem


class TestFilterProtocolPrefix:
    """ Tests for the class ``ProtocolPrefix``. """
    
    def test_when_str_called_and_only_mandatory_parameters_set_then_correct_string_returned(self) -> None:
        filter_protocol_prefix = ProtocolPrefix(Stream.REPORT, "1.0", datetime.fromisocalendar(2000, 1, 1),
                Subsystem.SMTP_IN, Event.EHLO, "session_id")
        expected_str = ("stream='report', protocol_version='1.0', timestamp='2000-01-03 00:00:00', "
                        "subsystem='smtp-in', event='ehlo', session_id='session_id'")
        
        assert str(filter_protocol_prefix) == f"ProtocolPrefix({expected_str})"
    
    def test_when_str_called_and_all_parameters_set_then_correct_string_returned(self) -> None:
        filter_protocol_prefix = ProtocolPrefix(Stream.REPORT, "1.0", datetime.fromisocalendar(2000, 1, 1),
                Subsystem.SMTP_IN, Event.EHLO, "session_id")
        filter_protocol_prefix.token = "token"
        expected_str = ("stream='report', protocol_version='1.0', timestamp='2000-01-03 00:00:00', "
                        "subsystem='smtp-in', event='ehlo', session_id='session_id', token='token'")
        
        assert str(filter_protocol_prefix) == f"ProtocolPrefix({expected_str})"


class TestProtocolData:
    """ Tests for the class ``ProtocolData``. """
    
    def test_when_timestamp_is_valid_string_then_converted_to_datetime(self) -> None:
        data = ProtocolData(Stream.FILTER, "1.0", "946684800", Subsystem.SMTP_IN, Event.EHLO, "session-1")
        
        assert data.protocol_prefix.timestamp == datetime.fromtimestamp(946684800.0)
    
    def test_when_timestamp_is_datetime_then_used_directly(self) -> None:
        expected = datetime.fromisocalendar(2000, 1, 1)
        data = ProtocolData(Stream.FILTER, "1.0", expected, Subsystem.SMTP_IN, Event.EHLO,"session-1")
        
        assert data.protocol_prefix.timestamp == expected
    
    def test_when_timestamp_is_invalid_string_then_raises_filter_engine_exception(self) -> None:
        with pytest.raises(FilterEngineException):
            ProtocolData(Stream.FILTER, "1.0", "not-a-timestamp", Subsystem.SMTP_IN, Event.EHLO, "session-1")
    
    def test_when_timestamp_overflows_then_raises_filter_engine_exception(self) -> None:
        with pytest.raises(FilterEngineException):
            ProtocolData(Stream.FILTER, "1.0", "99999999999999", Subsystem.SMTP_IN, Event.EHLO, "session-1")
