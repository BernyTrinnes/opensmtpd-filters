import os
from unittest.mock import ANY, call, Mock, patch

import pytest

from opensmtpd_filters.filter_engine import Event, FilterEngine, FilterEngineException, Stream


class TestFilterEnginePublicAPI:
    """ Tests for the public API of the class ``FilterEngine``. """
    
    CONFIG_READY = "config|ready"
    REGISTER_READY = "register|ready"
    
    channel_in: Mock
    channel_out: Mock
    filter_stream_report: Mock
    filter_stream_filter: Mock
    
    @pytest.fixture(autouse=True)
    def _prepare_filter_stream_mocks(self, mocked_filter_stream_report: Mock,
            mocked_filter_stream_filter: Mock) -> None:
        self.filter_stream_report = mocked_filter_stream_report
        self.filter_stream_filter = mocked_filter_stream_filter
    
    def test_when_filterengine_init_then_protocol_configurations_read(self) -> None:
        self.channel_in.return_value.readline.side_effect = [
            "config|smtpd-version|version\r",
            "config|smtp-session-timeout|600\n",
            "config|subsystem|smtp-in\r\n",
            self.CONFIG_READY
        ]
        
        with self.suspend_capture:
            filter_engine = FilterEngine()
        
        assert len(filter_engine.get_protocol_configurations().items()) == 3
        assert ("smtpd-version", "version") in filter_engine.get_protocol_configurations().items()
        assert ("smtp-session-timeout", "600") in filter_engine.get_protocol_configurations().items()
        assert ("subsystem", "smtp-in") in filter_engine.get_protocol_configurations().items()
        assert ("config", "ready") not in filter_engine.get_protocol_configurations().items()
        self.filter_stream_report.assert_not_called()
        self.filter_stream_filter.assert_not_called()
        assert self.channel_in.return_value.readline.call_count == 4
        self.channel_out.return_value.write.assert_not_called()
    
    @pytest.mark.parametrize("line", [
        None, ""
    ])
    def test_when_receive_and_line_invalid_then_exception_is_raised(self, line: str) -> None:
        self.channel_in.return_value.readline.side_effect = [
            self.CONFIG_READY,
            line
        ]
        
        with pytest.raises(FilterEngineException) as context:
            with self.suspend_capture:
                filter_engine = FilterEngine()
                filter_engine.receive()
        
        assert isinstance(context.value, FilterEngineException)
        assert str(context.value) == "No more input received."
        self.filter_stream_report.assert_not_called()
        self.filter_stream_filter.assert_not_called()
        assert self.channel_in.return_value.readline.call_count == 2
        self.channel_out.return_value.write.assert_not_called()
    
    @pytest.mark.parametrize("line, expected", [
        ("line1\r", "line1"),
        ("line2\n", "line2"),
        ("line3\r\n", "line3"),
        ("line4\n\r", "line4"),
        ("line5", "line5"),
    ])
    def test_when_receive_and_line_valid_then_receive(self, line: str, expected: str) -> None:
        self.channel_in.return_value.readline.side_effect = [
            self.CONFIG_READY,
            line
        ]
        
        with self.suspend_capture:
            filter_engine = FilterEngine()
            line_received = filter_engine.receive()
        
        assert line_received == expected
        self.filter_stream_report.assert_not_called()
        self.filter_stream_filter.assert_not_called()
        assert self.channel_in.return_value.readline.call_count == 2
        self.channel_out.return_value.write.assert_not_called()
    
    @pytest.mark.parametrize("line", [
        None, ""
    ])
    def test_when_send_and_line_invalid_then_exception_is_raised(self, line: str) -> None:
        self.channel_in.return_value.readline.return_value = self.CONFIG_READY
        
        with pytest.raises(FilterEngineException) as context:
            with self.suspend_capture:
                filter_engine = FilterEngine()
                filter_engine.send(line)
        
        assert isinstance(context.value, FilterEngineException)
        assert str(context.value) == "No line to send."
        self.filter_stream_report.assert_not_called()
        self.filter_stream_filter.assert_not_called()
        assert self.channel_in.return_value.readline.call_count == 1
        self.channel_out.return_value.write.assert_not_called()
    
    def test_when_send_then_line_is_sent(self) -> None:
        self.channel_in.return_value.readline.return_value = self.CONFIG_READY
        
        with self.suspend_capture:
            filter_engine = FilterEngine()
            filter_engine.send("line1")
            filter_engine.send("line2")
            filter_engine.send(".")
        
        self.filter_stream_report.assert_not_called()
        self.filter_stream_filter.assert_not_called()
        assert self.channel_in.return_value.readline.call_count == 1
        assert self.channel_out.return_value.write.call_count == 6
        self.channel_out.return_value.write.assert_has_calls([
            call("line1"), call(os.linesep),
            call("line2"), call(os.linesep),
            call("."), call(os.linesep)
        ])
    
    @pytest.mark.parametrize("stream, event", [
        (None, Event.AUTH),
        (Stream.UNKNOWN, Event.AUTH),
        (Stream.CONFIG, None),
        (Stream.CONFIG, Event.UNKNOWN),
        (Stream.FILTER, Event.LINK_CONNECT),
        (Stream.REPORT, Event.CONNECT)
    ])
    def test_when_register_processor_with_invalid_stream_or_event_called_then_exception_raised(self, stream: Stream,
            event: Event) -> None:
        self.channel_in.return_value.readline.return_value = self.CONFIG_READY
        
        with pytest.raises(FilterEngineException) as context:
            with self.suspend_capture:
                filter_engine = FilterEngine()
                filter_engine.register_processor(stream, event, lambda _: _)
        
        if not stream:
            expected_message = "Can not register a processor for the stream 'UNKNOWN'."
        elif not event:
            expected_message = "Can not register a processor for the event 'UNKNOWN'."
        else:
            expected_message = f"The event '{event}' can't be registered for the stream '{stream}'."
        
        assert isinstance(context.value, FilterEngineException)
        assert str(context.value) == expected_message
        self.filter_stream_report.assert_not_called()
        self.filter_stream_filter.assert_not_called()
        assert self.channel_in.return_value.readline.call_count == 1
        self.channel_out.return_value.write.assert_not_called()
    
    def test_when_register_processor_with_valid_parameters_then_processor_registered(self) -> None:
        self.channel_in.return_value.readline.return_value = self.CONFIG_READY
        
        with self.suspend_capture:
            filter_engine = FilterEngine()
            filter_engine.register_processor(Stream.REPORT, Event.LINK_CONNECT, lambda _: _)
        
        assert len(filter_engine._processors.items()) == 1
        assert "report|link-connect" in filter_engine._processors
        self._assert_register_processor_for_link_connect()
    
    def _assert_register_processor_for_link_connect(self) -> None:
        self.filter_stream_report.assert_not_called()
        self.filter_stream_filter.assert_not_called()
        assert self.channel_in.return_value.readline.call_count == 1
        assert self.channel_out.return_value.write.call_count == 2
        self.channel_out.return_value.write.assert_has_calls([
            call("register|report|smtp-in|link-connect"), call(os.linesep)
        ])
    
    def test_when_register_processor_with_already_registered_stream_or_event_called_then_exception_raised(self) -> None:
        self.channel_in.return_value.readline.return_value = self.CONFIG_READY
        
        with pytest.raises(FilterEngineException) as context:
            with self.suspend_capture:
                filter_engine = FilterEngine()
                filter_engine.register_processor(Stream.REPORT, Event.LINK_CONNECT, lambda _: _)
                filter_engine.register_processor(Stream.REPORT, Event.LINK_CONNECT, lambda _: _)
        
        assert isinstance(context.value, FilterEngineException)
        assert str(context.value) == "A processor for 'report|link-connect' is already registered."
        self._assert_register_processor_for_link_connect()
    
    def test_when_filter_loop_and_line_invalid_then_nothing_processed(self) -> None:
        self.channel_in.return_value.readline.side_effect = [
            self.CONFIG_READY,
            "garbage",
            "garbage|garbage",
            "garbage|garbage|garbage",
            "garbage|garbage|garbage|garbage",
            "garbage|garbage|garbage|garbage|garbage",
            InterruptedError("test invalid protocol")
        ]
        
        with pytest.raises(InterruptedError) as context:
            with self.suspend_capture:
                filter_engine = FilterEngine()
                filter_engine.filter_loop()
        
        assert isinstance(context.value, InterruptedError)
        assert str(context.value) == "test invalid protocol"
        self.filter_stream_report.assert_not_called()
        self.filter_stream_filter.assert_not_called()
        assert self.channel_in.return_value.readline.call_count == 7
        assert self.channel_out.return_value.write.call_count == 2
        self.channel_out.return_value.write.assert_has_calls([
            call(self.REGISTER_READY), call(os.linesep)
        ])
    
    def test_when_filter_loop_then_unexpected_stream_is_not_processed(self) -> None:
        self.channel_in.return_value.readline.side_effect = [
            self.CONFIG_READY,
            "config|0.7|1577836800.000030|smtp-in|event|82a3bd08e3a8db65",
            "stream|0.7|1577836800.300000|smtp-in|unknown|82a3bd08e3a8db65|82a3bd08e3a8db66",
            InterruptedError("test invalid stream")
        ]
        
        with pytest.raises(InterruptedError) as context:
            with self.suspend_capture:
                filter_engine = FilterEngine()
                filter_engine.filter_loop()
        
        assert isinstance(context.value, InterruptedError)
        assert str(context.value) == "test invalid stream"
        self.filter_stream_report.assert_not_called()
        self.filter_stream_filter.assert_not_called()
        assert self.channel_in.return_value.readline.call_count == 4
        assert self.channel_out.return_value.write.call_count == 2
        self.channel_out.return_value.write.assert_has_calls([
            call(self.REGISTER_READY), call(os.linesep)
        ])
    
    def test_when_filter_loop_then_stream_report_is_processed(self) -> None:
        self.channel_in.return_value.readline.side_effect = [
            self.CONFIG_READY,
            "report|0.7|1577836800.000010|smtp-in|link-connect|82a3bd08e3a8db65|localhost|pass|127.0.0.1:1234|127.0.0"
            ".1:25",
            "report|0.7|1577836800.100000|smtp-in|link-disconnect|82a3bd08e3a8db65",
            InterruptedError("test report stream")
        ]
        
        with pytest.raises(InterruptedError) as context:
            with self.suspend_capture:
                filter_engine = FilterEngine()
                filter_engine.filter_loop()
        
        assert isinstance(context.value, InterruptedError)
        assert str(context.value) == "test report stream"
        assert self.filter_stream_report.call_count == 2
        self.filter_stream_filter.assert_not_called()
        assert self.channel_in.return_value.readline.call_count == 4
        assert self.channel_out.return_value.write.call_count == 2
        self.channel_out.return_value.write.assert_has_calls([
            call(self.REGISTER_READY),
            call(os.linesep)
        ])
    
    def test_when_filter_loop_then_stream_filter_is_processed(self) -> None:
        self.channel_in.return_value.readline.side_effect = [
            self.CONFIG_READY,
            "filter|0.7|1577836800.000020|smtp-in|connect|82a3bd08e3a8db65|82a3bd08e3a8db66|localhost|127.0.0.1:1234",
            "filter|0.7|1577836800.200000|smtp-in|junk|82a3bd08e3a8db65|82a3bd08e3a8db66",
            InterruptedError("test filter stream")
        ]
        
        with pytest.raises(InterruptedError) as context:
            with self.suspend_capture:
                filter_engine = FilterEngine()
                filter_engine.filter_loop()
        
        assert isinstance(context.value, InterruptedError)
        assert str(context.value) == "test filter stream"
        self.filter_stream_report.assert_not_called()
        assert self.filter_stream_filter.call_count == 2
        assert self.channel_in.return_value.readline.call_count == 4
        assert self.channel_out.return_value.write.call_count == 2
        self.channel_out.return_value.write.assert_has_calls([
            call(self.REGISTER_READY), call(os.linesep)
        ])
    
    @patch.object(FilterEngine, "register_processor")
    def test_when_track_context_and_session_context_set_then_do_nothing(self, mocked_register_processor: Mock) -> None:
        self.channel_in.return_value.readline.side_effect = [
            self.CONFIG_READY,
            InterruptedError("test session context set")
        ]
        
        with pytest.raises(InterruptedError) as context:
            with self.suspend_capture:
                filter_engine = FilterEngine()
                filter_engine._session_contexts = { 'test': "123456" }
                filter_engine.track_session_context()
                filter_engine.filter_loop()
        
        assert isinstance(context.value, InterruptedError)
        assert str(context.value) == "test session context set"
        mocked_register_processor.assert_not_called()
        self._assert_default_mock_calls()
    
    def _assert_default_mock_calls(self) -> None:
        self.filter_stream_report.assert_not_called()
        self.filter_stream_filter.assert_not_called()
        assert self.channel_in.return_value.readline.call_count == 2
        assert self.channel_out.return_value.write.call_count == 2
        self.channel_out.return_value.write.assert_has_calls([
            call(self.REGISTER_READY),
            call(os.linesep)
        ])
    
    @patch.object(FilterEngine, "register_processor")
    def test_when_track_context_and_session_context_not_set_then_track_context(self,
            mocked_register_processor: Mock) -> None:
        self.channel_in.return_value.readline.side_effect = [
            self.CONFIG_READY,
            InterruptedError("test session context unset")
        ]
        
        with pytest.raises(InterruptedError) as context:
            with self.suspend_capture:
                filter_engine = FilterEngine()
                filter_engine.track_session_context()
                filter_engine.filter_loop()
        
        assert isinstance(context.value, InterruptedError)
        assert str(context.value) == "test session context unset"
        mocked_register_processor.assert_has_calls([
            call(Stream.REPORT, Event.LINK_CONNECT, ANY),
            call(Stream.REPORT, Event.LINK_DISCONNECT, ANY)
        ])
        self._assert_default_mock_calls()
    
    @patch.object(FilterEngine, "track_session_context")
    @patch.object(FilterEngine, "register_processor")
    def test_when_register_message_body_filter_then_register_processor(self, mocked_register_processor: Mock,
            mocked_track_session_context: Mock) -> None:
        self.channel_in.return_value.readline.side_effect = [
            self.CONFIG_READY,
            InterruptedError("test register message body filter")
        ]
        
        with pytest.raises(InterruptedError) as context:
            with self.suspend_capture:
                filter_engine = FilterEngine()
                filter_engine.register_message_body_filter(lambda _: _)
                filter_engine.filter_loop()
        
        assert isinstance(context.value, InterruptedError)
        assert str(context.value) == "test register message body filter"
        mocked_track_session_context.assert_called_once()
        mocked_register_processor.assert_has_calls([
            call(Stream.FILTER, Event.DATA_LINE, ANY),
            call(Stream.FILTER, Event.COMMIT, ANY)
        ])
        self._assert_default_mock_calls()
