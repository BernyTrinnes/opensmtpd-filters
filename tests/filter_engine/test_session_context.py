from opensmtpd_filters.filter_engine import SessionContext


class TestFilterSessionContext:
    """ Tests for the class ``SessionContext``. """
    
    def test_when_str_called_and_only_mandatory_parameters_set_then_correct_string_returned(self) -> None:
        filter_session = SessionContext("session_id")
        
        assert "SessionContext(session_id='session_id')" == str(filter_session)
    
    def test_when_str_called_and_all_parameters_set_then_correct_string_returned(self) -> None:
        filter_session = SessionContext("session_id", "localhost", "pass", "127.0.0.1", "127.0.0.2")
        expected_str = "session_id='session_id', rdns='localhost', fcrdns='pass', src='127.0.0.1', dest='127.0.0.2'"
        
        assert f"SessionContext({expected_str})" == str(filter_session)
    
    def test_when_str_called_and_some_parameters_set_then_correct_string_returned(self) -> None:
        filter_session = SessionContext("session_id", src="127.0.0.1", dest="127.0.0.2")
        expected_str = "session_id='session_id', src='127.0.0.1', dest='127.0.0.2'"
        
        assert f"SessionContext({expected_str})" == str(filter_session)
