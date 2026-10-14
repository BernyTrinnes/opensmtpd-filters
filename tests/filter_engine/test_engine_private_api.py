import os
from datetime import datetime
from unittest.mock import call, Mock, patch

import pytest

from opensmtpd_filters.filter_engine import *


_CONFIG_READY = "config|ready"
_PROTOCOL_VERSION_1 = "0.1"
_PROTOCOL_VERSION_2 = "0.2"
_PROTOCOL_VERSION_3 = "0.3"
_PROTOCOL_VERSION_4 = "0.4"
_PROTOCOL_VERSION_5 = "0.5"
_PROTOCOL_VERSION_6 = "0.6"
_PROTOCOL_VERSION_7 = "0.7"
_PROTOCOL_VERSION_8 = "0.8"
_SESSION_ID = "82a3bd08e3a8db65"


def _make_protocol_prefix(event: Event, stream: Stream = Stream.REPORT,
        protocol_version: str = _PROTOCOL_VERSION_7) -> ProtocolPrefix:
    return ProtocolPrefix(
            stream=stream,
            protocol_version=protocol_version,
            timestamp=datetime.fromtimestamp(1577836800.0),
            subsystem=Subsystem.SMTP_IN,
            event=event,
            session_id=_SESSION_ID)


def _make_filter_protocol_data(event: Event, stream: Stream = Stream.REPORT, payload: str | None = None,
        protocol_version: str = _PROTOCOL_VERSION_7) -> ProtocolData:
    protocol_prefix = _make_protocol_prefix(event, stream, protocol_version)
    data = ProtocolData(
            stream=str(stream),
            protocol_version=protocol_version,
            timestamp="1577836800.0",
            subsystem=str(Subsystem.SMTP_IN),
            event=event.value if isinstance(event.value, str) else event.value[0],
            session_id=_SESSION_ID)
    data.protocol_prefix = protocol_prefix
    data.payload = payload
    return data


class TestFilterEnginePrivateAPIFilterStreamReport:
    """ Tests for the private API of the class ``FilterEngine``, method ``_filter_stream_report``. """
    
    channel_in: Mock
    filter_engine: FilterEngine
    
    @pytest.fixture(autouse=True)
    def _create_engine(self) -> None:
        self.channel_in.return_value.readline.return_value = _CONFIG_READY
        with self.suspend_capture:
            self.filter_engine = FilterEngine()
    
    @pytest.mark.parametrize("payload", [
        None, ""
    ])
    @patch.object(FilterEngine, "_call_processor")
    def test_when_invalid_payload_then_call_processor_with_no_args(self, mocked_call_processor: Mock,
            payload: str | None) -> None:
        filter_dataline = _make_filter_protocol_data(Event.LINK_CONNECT, payload=None)
        
        self.filter_engine._filter_stream_report(filter_dataline)
        
        mocked_call_processor.assert_called_once_with(self.filter_engine._result_processor_noop,
                filter_dataline.protocol_prefix)
    
    @patch.object(FilterEngine, "_call_processor")
    def test_when_payload_with_single_value_then_call_processor_with_one_arg(self, mocked_call_processor: Mock) -> None:
        payload = "single_value"
        filter_dataline = _make_filter_protocol_data(Event.LINK_DISCONNECT, payload=payload)
        
        self.filter_engine._filter_stream_report(filter_dataline)
        
        mocked_call_processor.assert_called_once_with(self.filter_engine._result_processor_noop,
                filter_dataline.protocol_prefix, payload)
    
    @patch.object(FilterEngine, "_call_processor")
    def test_when_payload_with_multiple_values_then_call_processor_with_multiple_args(self,
            mocked_call_processor: Mock) -> None:
        filter_dataline = _make_filter_protocol_data(Event.LINK_CONNECT,
                payload="localhost|pass|127.0.0.1:1234|127.0.0.1:25")
        
        self.filter_engine._filter_stream_report(filter_dataline)
        
        mocked_call_processor.assert_called_once_with(self.filter_engine._result_processor_noop,
                filter_dataline.protocol_prefix, "localhost", "pass", "127.0.0.1:1234", "127.0.0.1:25")
    
    @pytest.mark.parametrize("version", [
        _PROTOCOL_VERSION_1, _PROTOCOL_VERSION_2, _PROTOCOL_VERSION_3, _PROTOCOL_VERSION_4
    ])
    @patch.object(FilterEngine, "_call_processor")
    def test_when_tx_mail_old_protocol_three_args_then_swap_result_and_sender(self, mocked_call_processor: Mock,
            version: str) -> None:
        filter_dataline = _make_filter_protocol_data(Event.TX_MAIL, payload="arg0|result|sender",
                protocol_version=version)
        
        self.filter_engine._filter_stream_report(filter_dataline)
        
        mocked_call_processor.assert_called_once_with(self.filter_engine._result_processor_noop,
                filter_dataline.protocol_prefix, "arg0", "sender", "result")
    
    @patch.object(FilterEngine, "_call_processor")
    def test_when_tx_mail_new_protocol_then_no_swap(self, mocked_call_processor: Mock) -> None:
        filter_dataline = _make_filter_protocol_data(Event.TX_MAIL, payload="arg0|result|sender",
                protocol_version=_PROTOCOL_VERSION_5)
        
        self.filter_engine._filter_stream_report(filter_dataline)
        
        mocked_call_processor.assert_called_once_with(self.filter_engine._result_processor_noop,
                filter_dataline.protocol_prefix, "arg0", "result", "sender")
    
    @patch.object(FilterEngine, "_call_processor")
    def test_when_tx_mail_old_protocol_not_three_args_then_no_swap(self, mocked_call_processor: Mock) -> None:
        filter_dataline = _make_filter_protocol_data(Event.TX_MAIL, payload="arg0|result",
                protocol_version=_PROTOCOL_VERSION_4)
        
        self.filter_engine._filter_stream_report(filter_dataline)
        
        mocked_call_processor.assert_called_once_with(self.filter_engine._result_processor_noop,
                filter_dataline.protocol_prefix, "arg0", "result")
    
    @patch.object(FilterEngine, "_call_processor")
    def test_when_tx_mail_old_protocol_four_args_then_no_swap(self, mocked_call_processor: Mock) -> None:
        filter_dataline = _make_filter_protocol_data(Event.TX_MAIL, payload="arg0|result|sender|extra",
                protocol_version=_PROTOCOL_VERSION_4)
        
        self.filter_engine._filter_stream_report(filter_dataline)
        
        mocked_call_processor.assert_called_once_with(self.filter_engine._result_processor_noop,
                filter_dataline.protocol_prefix, "arg0", "result", "sender", "extra")
    
    @patch.object(FilterEngine, "_call_processor")
    def test_when_non_tx_mail_old_protocol_then_no_swap(self, mocked_call_processor: Mock) -> None:
        filter_dataline = _make_filter_protocol_data(Event.TX_RCPT, payload="arg0|result|recipient",
                protocol_version=_PROTOCOL_VERSION_4)
        
        self.filter_engine._filter_stream_report(filter_dataline)
        
        mocked_call_processor.assert_called_once_with(self.filter_engine._result_processor_noop,
                filter_dataline.protocol_prefix, "arg0", "result", "recipient")
    
    @patch.object(FilterEngine, "_call_processor")
    def test_when_tx_mail_with_pipe_in_address_then_args_split_by_pipe(self, mocked_call_processor: Mock) -> None:
        filter_dataline = _make_filter_protocol_data(Event.TX_MAIL, payload="ok|user|host|extra",
                protocol_version=_PROTOCOL_VERSION_7)
        
        self.filter_engine._filter_stream_report(filter_dataline)
        
        mocked_call_processor.assert_called_once_with(self.filter_engine._result_processor_noop,
                filter_dataline.protocol_prefix, "ok", "user", "host", "extra")
    
    @patch.object(FilterEngine, "_call_processor")
    def test_when_various_report_events_then_call_processor(self, mocked_call_processor: Mock) -> None:
        events_with_payloads = [
            (Event.LINK_GREETING, None),
            (Event.LINK_IDENTIFY, "client-hostname"),
            (Event.LINK_TLS, "certificate"),
            (Event.LINK_AUTH, "method|username"),
            (Event.TX_RESET, "reason"),
            (Event.TX_BEGIN, "info"),
            (Event.TX_ENVELOPE, "sender|recipient"),
            (Event.TX_DATA, "info|size"),
            (Event.TX_COMMIT, "info|path"),
            (Event.TX_ROLLBACK, "reason"),
            (Event.PROTOCOL_CLIENT, "command"),
            (Event.PROTOCOL_SERVER, "response"),
            (Event.FILTER_REPORT, "filter|token|message"),
            (Event.FILTER_RESPONSE, "filter|token|response"),
            (Event.TIMEOUT, None),
        ]
        
        for event, payload in events_with_payloads:
            filter_dataline = _make_filter_protocol_data(event, payload=payload)
            
            self.filter_engine._filter_stream_report(filter_dataline)
            
            if payload:
                args = payload.split("|")
                mocked_call_processor.assert_called_once_with(self.filter_engine._result_processor_noop,
                        filter_dataline.protocol_prefix, *args)
            else:
                mocked_call_processor.assert_called_once_with(self.filter_engine._result_processor_noop,
                        filter_dataline.protocol_prefix)
            
            mocked_call_processor.reset_mock()


class TestFilterEnginePrivateAPICallProcessor:
    """ Tests for the private API of the class ``FilterEngine``, method ``_call_processor``. """
    
    channel_in: Mock
    channel_out: Mock
    channel_err: Mock
    filter_engine: FilterEngine
    
    @pytest.fixture(autouse=True)
    def _create_engine(self) -> None:
        self.channel_in.return_value.readline.return_value = _CONFIG_READY
        with self.suspend_capture:
            self.filter_engine = FilterEngine()
    
    def test_when_no_processor_registered_then_returns_early(self) -> None:
        protocol_prefix = _make_protocol_prefix(Event.CONNECT, Stream.FILTER, "token|127.0.0.1")
        result_processor = Mock()
        
        self.filter_engine._call_processor(result_processor, protocol_prefix, "127.0.0.1")
        
        result_processor.assert_not_called()
    
    def test_when_called_with_registered_processor_then_calls_it(self) -> None:
        processor = Mock(return_value=str(Decision.PROCEED))
        self.filter_engine.register_processor(Stream.FILTER, Event.CONNECT, processor)
        
        protocol_prefix = _make_protocol_prefix(Event.CONNECT, Stream.FILTER, "token|127.0.0.1")
        result_processor = Mock()
        
        self.filter_engine._call_processor(result_processor, protocol_prefix, "127.0.0.1")
        
        processor.assert_called_once_with(_SESSION_ID, "127.0.0.1")
        result_processor.assert_called_once_with(str(Decision.PROCEED))
    
    def test_when_called_with_session_context_then_uses_context_object(self) -> None:
        processor = Mock(return_value=str(Decision.PROCEED))
        self.filter_engine.register_processor(Stream.FILTER, Event.CONNECT, processor)
        self.filter_engine._session_contexts = {
            _SESSION_ID: SessionContext(_SESSION_ID, "localhost", "pass", "127.0.0.1", "127.0.0.1:25")
        }
        
        protocol_prefix = _make_protocol_prefix(Event.CONNECT, Stream.FILTER)
        result_processor = Mock()
        
        self.filter_engine._call_processor(result_processor, protocol_prefix, "127.0.0.1")
        
        call_args = processor.call_args[0]
        assert isinstance(call_args[0], SessionContext)
        assert call_args[0].session_id == _SESSION_ID
        assert call_args[1] == "127.0.0.1"
    
    def test_when_called_with_session_context_then_on_link_connect_uses_session_id(self) -> None:
        processor = Mock(return_value=None)
        self.filter_engine.register_processor(Stream.REPORT, Event.LINK_CONNECT, processor)
        self.filter_engine._session_contexts = {
            _SESSION_ID: SessionContext(_SESSION_ID, "localhost", "pass", "127.0.0.1", "127.0.0.1:25")
        }
        
        protocol_prefix = _make_protocol_prefix(Event.LINK_CONNECT)
        result_processor = Mock()
        
        self.filter_engine._call_processor(result_processor, protocol_prefix, "localhost", "pass", "127.0.0.1:1234",
                "127.0.0.1:25")
        
        assert processor.call_args[0][0] == _SESSION_ID
    
    def test_when_called_with_varargs_processor_then_passes_all_args(self) -> None:
        processor = Mock(return_value=str(Decision.PROCEED))
        self.filter_engine.register_processor(Stream.FILTER, Event.CONNECT, processor)
        
        protocol_prefix = _make_protocol_prefix(Event.CONNECT, Stream.FILTER)
        result_processor = Mock()
        
        self.filter_engine._call_processor(result_processor, protocol_prefix, "127.0.0.1", "extra", "data")
        
        processor.assert_called_once_with(_SESSION_ID, "127.0.0.1", "extra", "data")
    
    def test_when_called_with_exact_args_then_no_rejoin(self) -> None:
        received_args = []
        
        def my_processor(session: str, arg1: str, arg2: str):
            received_args.append((session, arg1, arg2))
            return str(Decision.PROCEED)
        
        self.filter_engine.register_processor(Stream.FILTER, Event.CONNECT, my_processor)
        
        protocol_prefix = _make_protocol_prefix(Event.CONNECT, Stream.FILTER)
        result_processor = Mock()
        
        self.filter_engine._call_processor(result_processor, protocol_prefix, "first", "second")
        
        assert received_args[0][0] == _SESSION_ID
        assert received_args[0][1] == "first"
        assert received_args[0][2] == "second"
        result_processor.assert_called_once_with(str(Decision.PROCEED))
    
    def test_when_called_with_fewer_data_items_then_rejoins_pipe_data(self) -> None:
        received_args = []
        
        def my_processor(session: str, arg1: str, arg2: str):
            received_args.append((session, arg1, arg2))
            return str(Decision.PROCEED)
        
        self.filter_engine.register_processor(Stream.FILTER, Event.CONNECT, my_processor)
        
        protocol_prefix = _make_protocol_prefix(Event.CONNECT, Stream.FILTER)
        result_processor = Mock()
        
        # Processor expects 2 data args (3 params - 1 session = 2)
        # Pass only 1 data item -> 1 < 2, so rejoin triggers
        # processor_data becomes (("first",), '')
        self.filter_engine._call_processor(result_processor, protocol_prefix, "first")
        
        assert received_args[0][0] == _SESSION_ID
        assert received_args[0][1] == ("first",)
        assert received_args[0][2] == ""
        result_processor.assert_called_once_with(str(Decision.PROCEED))
    
    def test_when_raises_exception_then_prints_to_stderr(self) -> None:
        def failing_processor(_session: str, _address: str):
            raise ValueError("Test error")
        
        self.filter_engine.register_processor(Stream.FILTER, Event.CONNECT, failing_processor)
        
        protocol_prefix = _make_protocol_prefix(Event.CONNECT, Stream.FILTER)
        result_processor = Mock()
        
        self.filter_engine._call_processor(result_processor, protocol_prefix, "127.0.0.1")
        
        self.channel_err.return_value.write.assert_has_calls([
            call("Could not start the registered processor for key 'filter|connect'."),
            call(os.linesep),
            call("Test error"),
            call(os.linesep)
        ])
        result_processor.assert_not_called()
    
    def test_when_called_with_empty_session_then_contexts_uses_session_id(self) -> None:
        processor = Mock(return_value=str(Decision.PROCEED))
        self.filter_engine.register_processor(Stream.FILTER, Event.CONNECT, processor)
        self.filter_engine._session_contexts = { }
        
        protocol_prefix = _make_protocol_prefix(Event.CONNECT, Stream.FILTER)
        result_processor = Mock()
        
        self.filter_engine._call_processor(result_processor, protocol_prefix, "127.0.0.1")
        
        processor.assert_called_once_with(_SESSION_ID, "127.0.0.1")


class TestFilterEnginePrivateAPIFilterStreamFilter:
    """ Tests for the private API of the class ``FilterEngine``, method ``_filter_stream_filter``. """
    
    channel_in: Mock
    channel_out: Mock
    filter_engine: FilterEngine
    
    @pytest.fixture(autouse=True)
    def _create_engine(self) -> None:
        self.channel_in.return_value.readline.return_value = _CONFIG_READY
        with self.suspend_capture:
            self.filter_engine = FilterEngine()
    
    def test_when_non_data_line_then_no_payload(self) -> None:
        processor = Mock(return_value=Decision.PROCEED)
        self.filter_engine.register_processor(Stream.FILTER, Event.CONNECT, processor)
        filter_dataline = _make_filter_protocol_data(Event.CONNECT, Stream.FILTER)
        
        self.filter_engine._filter_stream_filter(filter_dataline)
        
        processor.assert_called_once_with(_SESSION_ID)
    
    def test_when_non_data_line_payload_with_pipe_then_split_data_line(self) -> None:
        processor = Mock(return_value=str(Decision.PROCEED))
        self.filter_engine.register_processor(Stream.FILTER, Event.CONNECT, processor)
        filter_dataline = _make_filter_protocol_data(Event.CONNECT, Stream.FILTER, "abc123|127.0.0.1")
        
        self.filter_engine._filter_stream_filter(filter_dataline)
        
        assert filter_dataline.protocol_prefix.token == "abc123"
        assert filter_dataline.payload == "127.0.0.1"
        processor.assert_called_once_with(_SESSION_ID, "127.0.0.1")
    
    def test_when_non_data_line_payload_without_pipe_then_payload_is_none(self) -> None:
        processor = Mock(return_value=str(Decision.PROCEED))
        self.filter_engine.register_processor(Stream.FILTER, Event.CONNECT, processor)
        filter_dataline = _make_filter_protocol_data(Event.CONNECT, Stream.FILTER, "abc123")
        
        self.filter_engine._filter_stream_filter(filter_dataline)
        
        assert filter_dataline.protocol_prefix.token == "abc123"
        assert filter_dataline.payload is None
        processor.assert_called_once_with(_SESSION_ID)
    
    def test_when_filter_data_line_event_then_data_line_callback_processed(self) -> None:
        dataline_callback_received = []
        processor_call_args = []
        
        def data_line_processor(session: str, line: str, send_dataline):
            dataline_callback_received.append(send_dataline)
            processor_call_args.append((session, line, send_dataline))
            return None
        
        self.filter_engine.register_processor(Stream.FILTER, Event.DATA_LINE, data_line_processor)
        filter_dataline = _make_filter_protocol_data(Event.DATA_LINE, Stream.FILTER, "abc123|Hello World")
        
        self.filter_engine._filter_stream_filter(filter_dataline)
        
        assert filter_dataline.protocol_prefix.token == "abc123"
        assert filter_dataline.payload == "Hello World"
        assert len(processor_call_args) == 1
        assert processor_call_args[0][0] == _SESSION_ID
        assert processor_call_args[0][1] == "Hello World"
        assert processor_call_args[0][2] is dataline_callback_received[0]
    
    def test_when_dataline_event_and_response_is_sent_then_response_is_written(self) -> None:
        dataline_callback_received = []
        
        def data_line_processor(_session: str, _line: str, send_dataline):
            dataline_callback_received.append(send_dataline)
            return None
        
        self.filter_engine.register_processor(Stream.FILTER, Event.DATA_LINE, data_line_processor)
        filter_dataline = _make_filter_protocol_data(Event.DATA_LINE, Stream.FILTER, "abc123|Hello World")
        
        self.filter_engine._filter_stream_filter(filter_dataline)
        
        # Invoke the callback
        dataline_callback_received[0]("Modified Line")
        
        self.channel_out.return_value.write.assert_has_calls([
            call(f"{str(Answer.FILTER_DATALINE)}|{_SESSION_ID}|abc123|Modified Line"),
            call(os.linesep)
        ])
    
    def test_when_non_data_line_event_then_filter_response_is_sent(self) -> None:
        processor = Mock(return_value=Decision.decision(Decision.REJECT, NegativeReturnCode.E_550, "some reason"))
        self.filter_engine.register_processor(Stream.FILTER, Event.CONNECT, processor)
        
        filter_dataline = _make_filter_protocol_data(Event.CONNECT, Stream.FILTER, "abc123|127.0.0.1")
        
        self.filter_engine._filter_stream_filter(filter_dataline)
        
        self.channel_out.return_value.write.assert_has_calls([
            call(f"{str(Answer.FILTER_RESULT)}|{_SESSION_ID}|abc123|reject|550 some reason"),
            call(os.linesep)
        ])
    
    def test_when_no_registered_processor_then_no_response(self) -> None:
        filter_dataline = _make_filter_protocol_data(Event.CONNECT, Stream.FILTER, "abc123|127.0.0.1")
        
        initial_call_count = self.channel_out.call_count
        self.filter_engine._filter_stream_filter(filter_dataline)
        
        assert self.channel_out.call_count == initial_call_count
    
    def test_when_multiple_payload_values_then_separate_args_passed(self) -> None:
        processor = Mock(return_value=str(Decision.PROCEED))
        self.filter_engine.register_processor(Stream.FILTER, Event.MAIL_FROM, processor)
        filter_dataline = _make_filter_protocol_data(Event.MAIL_FROM, Stream.FILTER, "abc123|sender@example.com|extra")
        
        self.filter_engine._filter_stream_filter(filter_dataline)
        
        assert filter_dataline.protocol_prefix.token == "abc123"
        processor.assert_called_once_with(_SESSION_ID, "sender@example.com", "extra")


class TestFilterEnginePrivateAPISendFilterResponse:
    """ Tests for the private API of the class ``FilterEngine``, method ``_send_filter_response``. """
    
    channel_in: Mock
    channel_out: Mock
    filter_engine: FilterEngine
    
    @pytest.fixture(autouse=True)
    def _create_engine(self) -> None:
        self.channel_in.return_value.readline.return_value = _CONFIG_READY
        with self.suspend_capture:
            self.filter_engine = FilterEngine()
    
    def test_when_no_token_then_returns_early(self) -> None:
        protocol_prefix = _make_protocol_prefix(Event.CONNECT, Stream.FILTER)
        
        initial_call_count = self.channel_out.call_count
        self.filter_engine._send_filter_response(Answer.FILTER_RESULT, protocol_prefix, str(Decision.PROCEED))
        
        assert self.channel_out.call_count == initial_call_count
    
    def test_when_old_protocol_version_then_switch_field_order(self) -> None:
        protocol_prefix = _make_protocol_prefix(Event.CONNECT, Stream.FILTER, _PROTOCOL_VERSION_4)
        protocol_prefix.token = "abc123"
        
        self.filter_engine._send_filter_response(Answer.FILTER_RESULT, protocol_prefix, str(Decision.PROCEED))
        
        self.channel_out.return_value.write.assert_has_calls([
            call(f"{str(Answer.FILTER_RESULT)}|abc123|{_SESSION_ID}|{str(Decision.PROCEED)}"),
            call(os.linesep)
        ])
    
    def test_when_new_protocol_version_then_fields_in_order(self) -> None:
        protocol_prefix = _make_protocol_prefix(Event.CONNECT, Stream.FILTER, _PROTOCOL_VERSION_7)
        protocol_prefix.token = "abc123"
        
        self.filter_engine._send_filter_response(Answer.FILTER_RESULT, protocol_prefix, str(Decision.PROCEED))
        
        self.channel_out.return_value.write.assert_has_calls([
            call(f"{str(Answer.FILTER_RESULT)}|{_SESSION_ID}|abc123|{str(Decision.PROCEED)}"),
            call(os.linesep)
        ])
    
    def test_when_send_with_filter_dataline_then_correct_answer(self) -> None:
        protocol_prefix = _make_protocol_prefix(Event.DATA_LINE, Stream.FILTER)
        protocol_prefix.token = "abc123"
        
        self.filter_engine._send_filter_response(Answer.FILTER_DATALINE, protocol_prefix, "Modified Line")
        
        self.channel_out.return_value.write.assert_has_calls([
            call(f"{str(Answer.FILTER_DATALINE)}|{_SESSION_ID}|abc123|Modified Line"),
            call(os.linesep)
        ])
    
    def test_when_send_with_reject_decision_then_payload_contains_message(self) -> None:
        """Sending a reject decision includes the full message in payload."""
        protocol_prefix = _make_protocol_prefix(Event.CONNECT, Stream.FILTER)
        protocol_prefix.token = "abc123"
        
        self.filter_engine._send_filter_response(Answer.FILTER_RESULT, protocol_prefix,
                Decision.decision(Decision.REJECT, NegativeReturnCode.E_550, "Access denied"))
        
        self.channel_out.return_value.write.assert_has_calls([
            call(f"{str(Answer.FILTER_RESULT)}|{_SESSION_ID}|abc123|reject|550 Access denied"),
            call(os.linesep)
        ])
    
    @pytest.mark.parametrize("version", [
        _PROTOCOL_VERSION_1, _PROTOCOL_VERSION_2, _PROTOCOL_VERSION_3, _PROTOCOL_VERSION_4
    ])
    def test_when_old_protocol_versions_then_use_old_order(self, version: str) -> None:
        protocol_prefix = _make_protocol_prefix(Event.CONNECT, Stream.FILTER, version)
        protocol_prefix.token = "abc123"
        
        self.filter_engine._send_filter_response(Answer.FILTER_RESULT, protocol_prefix, str(Decision.PROCEED))
        
        self.channel_out.return_value.write.assert_has_calls([
            call(f"{str(Answer.FILTER_RESULT)}|abc123|{_SESSION_ID}|{str(Decision.PROCEED)}"),
            call(os.linesep)
        ])
    
    @pytest.mark.parametrize("version", [
        _PROTOCOL_VERSION_5, _PROTOCOL_VERSION_6, _PROTOCOL_VERSION_7, _PROTOCOL_VERSION_8
    ])
    def test_when_new_protocol_versions_then_use_new_order(self, version: str) -> None:
        protocol_prefix = _make_protocol_prefix(Event.CONNECT, Stream.FILTER, version)
        protocol_prefix.token = "abc123"
        
        self.filter_engine._send_filter_response(Answer.FILTER_RESULT, protocol_prefix, str(Decision.PROCEED))
        
        self.channel_out.return_value.write.assert_has_calls([
            call(f"{str(Answer.FILTER_RESULT)}|{_SESSION_ID}|abc123|{str(Decision.PROCEED)}"),
            call(os.linesep)
        ])


class TestFilterEnginePrivateAPITrackSessionContext:
    """ Tests for the private API of the class ``FilterEngine``, internal methods of ``track_session_context``. """
    
    channel_in: Mock
    channel_out: Mock
    filter_engine: FilterEngine
    
    @pytest.fixture(autouse=True)
    def _create_engine(self) -> None:
        self.channel_in.return_value.readline.return_value = _CONFIG_READY
        with self.suspend_capture:
            self.filter_engine = FilterEngine()
    
    def test_when_called_with_link_connect_then_creates_session(self) -> None:
        self.filter_engine.track_session_context()
        
        filter_dataline = _make_filter_protocol_data(Event.LINK_CONNECT,
                payload="localhost|pass|127.0.0.1:1234|127.0.0.1:25", )
        
        self.filter_engine._filter_stream_report(filter_dataline)
        
        assert _SESSION_ID in self.filter_engine._session_contexts
        session_context = self.filter_engine._session_contexts[_SESSION_ID]
        assert isinstance(session_context, SessionContext)
        assert session_context.session_id == _SESSION_ID
        assert session_context.rdns == "localhost"
        assert session_context.fcrdns == "pass"
        assert session_context.src == "127.0.0.1:1234"
        assert session_context.dest == "127.0.0.1:25"
    
    def test_when_called_with_link_disconnect_and_session_context_then_removes_session(self) -> None:
        self.filter_engine.track_session_context()
        
        # Create session
        connect_dataline = _make_filter_protocol_data(Event.LINK_CONNECT,
                payload="localhost|pass|127.0.0.1:1234|127.0.0.1:25", )
        self.filter_engine._filter_stream_report(connect_dataline)
        assert _SESSION_ID in self.filter_engine._session_contexts
        
        # Process link-disconnect
        disconnect_dataline = _make_filter_protocol_data(Event.LINK_DISCONNECT)
        self.filter_engine._filter_stream_report(disconnect_dataline)
        
        assert _SESSION_ID not in self.filter_engine._session_contexts
    
    def test_when_called_with_link_disconnect_and_session_context_then_do_nothing(self) -> None:
        self.filter_engine.track_session_context()
        
        # Create session
        connect_dataline = _make_filter_protocol_data(Event.LINK_CONNECT,
                payload="localhost|pass|127.0.0.1:1234|127.0.0.1:25", )
        self.filter_engine._filter_stream_report(connect_dataline)
        assert len(self.filter_engine._session_contexts) == 1
        assert _SESSION_ID in self.filter_engine._session_contexts
        assert "nonexisting_session" not in self.filter_engine._session_contexts
        
        # Process link-disconnect with non-existing session
        handler = self.filter_engine._processors[f"{Stream.REPORT}|{Event.LINK_DISCONNECT}"]
        handler("nonexistent_session")
        
        assert len(self.filter_engine._session_contexts) == 1
        assert _SESSION_ID in self.filter_engine._session_contexts
        assert "nonexisting_session" not in self.filter_engine._session_contexts
    
    def test_when_called_with_link_disconnect_and_session_id_then_removes_session(self) -> None:
        self.filter_engine.track_session_context()
        
        # Manually insert a SessionContext
        handler = self.filter_engine._processors[f"{Stream.REPORT}|{Event.LINK_DISCONNECT}"]
        self.filter_engine._session_contexts["string_session"] = "some_value"
        assert "string_session" in self.filter_engine._session_contexts
        
        # Call the handler directly
        handler("string_session")
        
        assert "string_session" not in self.filter_engine._session_contexts
    
    @patch.object(FilterEngine, "register_processor")
    def test_when_track_session_context_called_twice_then_returns_early(self, mocked_register_processor: Mock) -> None:
        # Pre-populate _session_contexts
        self.filter_engine._session_contexts["preexisting"] = "value"
        
        self.filter_engine.track_session_context()
        
        # No processors should be registered because _session_contexts was non-empty
        mocked_register_processor.assert_not_called()


class TestFilterEnginePrivateAPIRegisterMessageBodyFilter:
    """
    Tests for the private API of the class ``FilterEngine``, internal methods of ``register_message_body_filter``.
    """
    
    channel_in: Mock
    filter_engine: FilterEngine
    
    @pytest.fixture(autouse=True)
    def _create_engine(self) -> None:
        self.channel_in.return_value.readline.return_value = _CONFIG_READY
        with self.suspend_capture:
            self.filter_engine = FilterEngine()
    
    @patch.object(FilterEngine, "register_processor")
    @patch.object(FilterEngine, "track_session_context")
    def test_when_called_then_track_session_context_is_called(self, mocked_track_session_context: Mock,
            mocked_register_processor: Mock) -> None:
        self.filter_engine.register_message_body_filter(lambda s, l: l)
        
        mocked_track_session_context.assert_called_once()
        assert mocked_register_processor.call_count == 2
    
    def test_when_called_then_dataline_and_commit_processors_are_registered(self) -> None:
        self.filter_engine.register_message_body_filter(lambda s, l: l)
        
        assert f"{Stream.FILTER}|{Event.DATA_LINE}" in self.filter_engine._processors
        assert f"{Stream.FILTER}|{Event.COMMIT}" in self.filter_engine._processors
    
    def test_when_line_starts_with_dot_then_dot_prefix_added(self) -> None:
        self.filter_engine.register_message_body_filter(lambda _session, _lines: ["."])
        handler = self.filter_engine._processors[f"{Stream.FILTER}|{Event.DATA_LINE}"]
        
        session_ctx = SessionContext(_SESSION_ID)
        send_dataline = Mock()
        session_ctx.context_data["message_lines"] = ["Hello"]
        
        handler(session_ctx, ".", send_dataline)
        
        assert send_dataline.call_count == 2
        send_dataline.assert_has_calls([
            call(".."), call(".")
        ])
    
    def test_when_line_not_starts_with_dot_then_line_not_modified(self) -> None:
        self.filter_engine.register_message_body_filter(lambda _session, _lines: ["Hello World"])
        handler = self.filter_engine._processors[f"{Stream.FILTER}|{Event.DATA_LINE}"]
        
        session_ctx = SessionContext(_SESSION_ID)
        send_dataline = Mock()
        session_ctx.context_data["message_lines"] = ["Original"]
        
        handler(session_ctx, ".", send_dataline)
        
        assert send_dataline.call_count == 2
        send_dataline.assert_has_calls([
            call("Hello World"), call(".")
        ])
    
    def test_when_line_starts_with_double_dot_then_leading_dot_is_removed(self) -> None:
        self.filter_engine.register_message_body_filter(lambda _session, lines: lines)
        handler = self.filter_engine._processors[f"{Stream.FILTER}|{Event.DATA_LINE}"]
        
        session_ctx = SessionContext(_SESSION_ID)
        send_dataline = Mock()
        
        handler(session_ctx, "..hidden", send_dataline)
        
        assert session_ctx.context_data["message_lines"] == [".hidden"]
    
    def test_when_normal_line_then_line_unchanged(self) -> None:
        self.filter_engine.register_message_body_filter(lambda _session, lines: lines)
        handler = self.filter_engine._processors[f"{Stream.FILTER}|{Event.DATA_LINE}"]
        
        session_ctx = SessionContext(_SESSION_ID)
        send_dataline = Mock()
        
        handler(session_ctx, "Hello World", send_dataline)
        
        assert session_ctx.context_data["message_lines"] == ["Hello World"]
    
    def test_when_data_line_is_not_dot_then_lines_accumulated_until_dot(self) -> None:
        self.filter_engine.register_message_body_filter(lambda _session, lines: lines)
        handler = self.filter_engine._processors[f"{Stream.FILTER}|{Event.DATA_LINE}"]
        
        session_ctx = SessionContext(_SESSION_ID)
        send_dataline = Mock()
        
        handler(session_ctx, "Line 1", send_dataline)
        handler(session_ctx, "Line 2", send_dataline)
        
        assert session_ctx.context_data["message_lines"] == ["Line 1", "Line 2"]
        send_dataline.assert_not_called()
    
    def test_when_data_line_is_dot_then_processes_message_on_dot_delimiter(self) -> None:
        received_lines = []
        
        def message_processor(_session, lines):
            received_lines.extend(lines)
            return lines
        
        self.filter_engine.register_message_body_filter(message_processor)
        handler = self.filter_engine._processors[f"{Stream.FILTER}|{Event.DATA_LINE}"]
        
        session_ctx = SessionContext(_SESSION_ID)
        send_dataline = Mock()
        session_ctx.context_data["message_lines"] = ["Line 1", "Line 2"]
        
        handler(session_ctx, ".", send_dataline)
        
        assert received_lines == ["Line 1", "Line 2"]
    
    def test_when_data_line_is_processed_then_escaped_lines_and_dot_sent_on_completion(self) -> None:
        self.filter_engine.register_message_body_filter(lambda _session, _lines: ["Modified Line"])
        handler = self.filter_engine._processors[f"{Stream.FILTER}|{Event.DATA_LINE}"]
        
        session_ctx = SessionContext(_SESSION_ID)
        send_dataline = Mock()
        session_ctx.context_data["message_lines"] = ["Original"]
        
        handler(session_ctx, ".", send_dataline)
        
        assert send_dataline.call_count == 2
        send_dataline.assert_has_calls([
            call("Modified Line"), call(".")
        ])
    
    def test_when_data_line_is_processed_then_message_lines_cleared_after_processing(self) -> None:
        self.filter_engine.register_message_body_filter(lambda _session, lines: lines)
        handler = self.filter_engine._processors[f"{Stream.FILTER}|{Event.DATA_LINE}"]
        
        session_ctx = SessionContext(_SESSION_ID)
        send_dataline = Mock()
        session_ctx.context_data["message_lines"] = ["Line 1"]
        
        handler(session_ctx, ".", send_dataline)
        
        assert "message_lines" not in session_ctx.context_data
    
    def test_when_data_line_is_processed_and_no_message_lines_then_empty_list_used(self) -> None:
        received_lines = []
        
        def message_processor(_session, lines):
            received_lines.append(lines)
            return []
        
        self.filter_engine.register_message_body_filter(message_processor)
        handler = self.filter_engine._processors[f"{Stream.FILTER}|{Event.DATA_LINE}"]
        
        session_ctx = SessionContext(_SESSION_ID)
        send_dataline = Mock()
        
        handler(session_ctx, ".", send_dataline)
        
        assert received_lines == [[]]
    
    def test_when_exception_then_dot_sent_and_error_flag_set(self) -> None:
        def failing_processor(_session, _lines):
            raise ValueError("Processing failed")
        
        self.filter_engine.register_message_body_filter(failing_processor)
        handler = self.filter_engine._processors[f"{Stream.FILTER}|{Event.DATA_LINE}"]
        
        session_ctx = SessionContext(_SESSION_ID)
        send_dataline = Mock()
        session_ctx.context_data["message_lines"] = ["Line 1"]
        
        with pytest.raises(FilterEngineException):
            handler(session_ctx, ".", send_dataline)
        
        send_dataline.assert_called_once_with(".")
        assert session_ctx.context_data["message_error"] is True
        assert "message_lines" not in session_ctx.context_data
    
    def test_when_no_message_lines_then_exception(self) -> None:
        def failing_processor(_session, _lines):
            raise RuntimeError("Unexpected error")
        
        self.filter_engine.register_message_body_filter(failing_processor)
        handler = self.filter_engine._processors[f"{Stream.FILTER}|{Event.DATA_LINE}"]
        
        session_ctx = SessionContext(_SESSION_ID)
        send_dataline = Mock()
        
        with pytest.raises(FilterEngineException):
            handler(session_ctx, ".", send_dataline)
        
        send_dataline.assert_called_once_with(".")
        assert session_ctx.context_data["message_error"] is True
    
    def test_when_data_line_processed_then_session_context_is_passed_to_processor(self) -> None:
        received_session = []
        
        def message_processor(session, lines):
            received_session.append(session)
            return lines
        
        self.filter_engine.register_message_body_filter(message_processor)
        handler = self.filter_engine._processors[f"{Stream.FILTER}|{Event.DATA_LINE}"]
        
        session_ctx = SessionContext(_SESSION_ID, rdns="localhost")
        send_dataline = Mock()
        session_ctx.context_data["message_lines"] = ["test"]
        
        handler(session_ctx, ".", send_dataline)
        
        assert len(received_session) == 1
        assert received_session[0] is session_ctx
        assert received_session[0].rdns == "localhost"
    
    def test_when_data_line_processed_then_lines_modified(self) -> None:
        def filter_processor(_session, lines):
            return [line.upper() for line in lines]
        
        self.filter_engine.register_message_body_filter(filter_processor)
        handler = self.filter_engine._processors[f"{Stream.FILTER}|{Event.DATA_LINE}"]
        
        session_ctx = SessionContext(_SESSION_ID)
        send_dataline = Mock()
        session_ctx.context_data["message_lines"] = ["hello", "world"]
        
        handler(session_ctx, ".", send_dataline)
        
        assert send_dataline.call_count == 3
        send_dataline.assert_has_calls([
            call("HELLO"), call("WORLD"), call(".")
        ])
    
    def test_when_processor_returns_empty_lines_then_dot_is_sent(self) -> None:
        self.filter_engine.register_message_body_filter(lambda _session, _lines: [])
        handler = self.filter_engine._processors[f"{Stream.FILTER}|{Event.DATA_LINE}"]
        
        session_ctx = SessionContext(_SESSION_ID)
        send_dataline = Mock()
        session_ctx.context_data["message_lines"] = ["Line 1"]
        
        handler(session_ctx, ".", send_dataline)
        
        assert send_dataline.call_count == 1
        send_dataline.assert_has_calls([
            call(".")
        ])
    
    def test_when_message_error_set_then_reject(self) -> None:
        self.filter_engine.register_message_body_filter(lambda _session, lines: lines)
        handler = self.filter_engine._processors[f"{Stream.FILTER}|{Event.COMMIT}"]
        
        session_ctx = SessionContext(_SESSION_ID)
        session_ctx.context_data["message_error"] = True
        
        result = handler(session_ctx)
        
        assert result == Decision.decision(Decision.REJECT, NegativeReturnCode.E_451, "Internal server error")
    
    def test_when_commit_then_message_error_flag_cleared(self) -> None:
        self.filter_engine.register_message_body_filter(lambda _session, lines: lines)
        handler = self.filter_engine._processors[f"{Stream.FILTER}|{Event.COMMIT}"]
        
        session_ctx = SessionContext(_SESSION_ID)
        session_ctx.context_data["message_error"] = True
        
        handler(session_ctx)
        
        assert "message_error" not in session_ctx.context_data
    
    def test_when_commit_and_no_message_error_then_proceed(self) -> None:
        self.filter_engine.register_message_body_filter(lambda _session, lines: lines)
        handler = self.filter_engine._processors[f"{Stream.FILTER}|{Event.COMMIT}"]
        
        session_ctx = SessionContext(_SESSION_ID)
        
        result = handler(session_ctx)
        
        assert result == Decision.decision(Decision.PROCEED)
    
    def test_when_commit_with_empty_context_data_then_proceed(self) -> None:
        self.filter_engine.register_message_body_filter(lambda _session, lines: lines)
        handler = self.filter_engine._processors[f"{Stream.FILTER}|{Event.COMMIT}"]
        
        session_ctx = SessionContext(_SESSION_ID)
        
        result = handler(session_ctx)
        
        assert result == Decision.decision(Decision.PROCEED)
    
    def test_when_commit_then_message_error_removed_other_context_data_preserved(self) -> None:
        self.filter_engine.register_message_body_filter(lambda _session, lines: lines)
        handler = self.filter_engine._processors[f"{Stream.FILTER}|{Event.COMMIT}"]
        
        session_ctx = SessionContext(_SESSION_ID)
        session_ctx.context_data["message_error"] = True
        session_ctx.context_data["other_key"] = "other_value"
        
        handler(session_ctx)
        
        assert "message_error" not in session_ctx.context_data
        assert session_ctx.context_data["other_key"] == "other_value"
