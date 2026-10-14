from opensmtpd_filters.filter_engine import SessionContext


class TestFilterSessionContext:
    """ Tests for the class ``SessionContext``. """
    
    def test_when_str_called_and_only_mandatory_parameters_set_then_correct_string_returned(self) -> None:
        filter_session = SessionContext("session_id")
        
        assert str(filter_session) == "SessionContext(session_id='session_id')"
    
    def test_when_str_called_and_all_parameters_set_then_correct_string_returned(self) -> None:
        filter_session = SessionContext("session_id", "localhost", "pass", "127.0.0.1", "127.0.0.2")
        expected_str = "session_id='session_id', rdns='localhost', fcrdns='pass', src='127.0.0.1', dest='127.0.0.2'"
        
        assert str(filter_session) == f"SessionContext({expected_str})"
    
    def test_when_str_called_and_some_parameters_set_then_correct_string_returned(self) -> None:
        filter_session = SessionContext("session_id", src="127.0.0.1", dest="127.0.0.2")
        expected_str = "session_id='session_id', src='127.0.0.1', dest='127.0.0.2'"
        
        assert str(filter_session) == f"SessionContext({expected_str})"
    
    def test_when_context_data_initialized_then_empty_dict(self) -> None:
        filter_session = SessionContext("session_id")
        
        assert filter_session.context_data == {}
        assert isinstance(filter_session.context_data, dict)
    
    def test_when_context_data_set_then_value_retrieved(self) -> None:
        filter_session = SessionContext("session_id")
        filter_session.context_data["key"] = "value"
        
        assert filter_session.context_data["key"] == "value"
    
    def test_when_context_data_set_multiple_keys_then_all_preserved(self) -> None:
        filter_session = SessionContext("session_id")
        filter_session.context_data["key1"] = "value1"
        filter_session.context_data["key2"] = 42
        filter_session.context_data["key3"] = ["a", "b"]
        
        assert filter_session.context_data["key1"] == "value1"
        assert filter_session.context_data["key2"] == 42
        assert filter_session.context_data["key3"] == ["a", "b"]
    
    def test_when_context_data_deleted_then_key_removed(self) -> None:
        filter_session = SessionContext("session_id")
        filter_session.context_data["key"] = "value"
        del filter_session.context_data["key"]
        
        assert "key" not in filter_session.context_data
    
    def test_when_context_data_modified_then_str_excludes_it(self) -> None:
        filter_session = SessionContext("session_id", rdns="localhost")
        filter_session.context_data["key"] = "value"
        
        assert str(filter_session) == "SessionContext(session_id='session_id', rdns='localhost')"
        assert "context_data" not in str(filter_session)
        assert "key" not in str(filter_session)
