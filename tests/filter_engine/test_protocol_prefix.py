from datetime import datetime

from opensmtpd_filters.filter_engine import Event, ProtocolPrefix, Stream, Subsystem


class TestFilterProtocolPrefix:
    """ Tests for the class ``ProtocolPrefix``. """
    
    def test_when_str_called_and_only_mandatory_parameters_set_then_correct_string_returned(self) -> None:
        filter_protocol_prefix = ProtocolPrefix(Stream.REPORT, "1.0", datetime.fromisocalendar(2000, 1, 1),
                                                Subsystem.SMTP_IN, Event.EHLO, "session_id")
        expected_str = ("stream='report', protocol_version='1.0', timestamp='2000-01-03 00:00:00', "
                        "subsystem='smtp-in', event='ehlo', session_id='session_id'")
        
        assert f"ProtocolPrefix({expected_str})" == str(filter_protocol_prefix)
    
    def test_when_str_called_and_all_parameters_set_then_correct_string_returned(self) -> None:
        filter_protocol_prefix = ProtocolPrefix(Stream.REPORT, "1.0", datetime.fromisocalendar(2000, 1, 1),
                                                Subsystem.SMTP_IN, Event.EHLO, "session_id")
        filter_protocol_prefix.token = "token"
        expected_str = ("stream='report', protocol_version='1.0', timestamp='2000-01-03 00:00:00', "
                        "subsystem='smtp-in', event='ehlo', session_id='session_id', token='token'")
        
        assert f"ProtocolPrefix({expected_str})" == str(filter_protocol_prefix)
