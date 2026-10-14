import os
from typing import Generator
from unittest.mock import ANY, call, Mock, patch

import pytest
from pytest_mock import MockerFixture

from opensmtpd_filters.filter_engine import Event, FilterEngine, FilterEngineException, Stream


@pytest.fixture(scope="class")
def suspend_capture(pytestconfig):
    class suspend_guard:
        def __init__(self):
            self.capmanager = pytestconfig.pluginmanager.getplugin('capturemanager')

        def __enter__(self):
            self.capmanager.suspend_global_capture(in_=True)
            pass

        def __exit__(self, _1, _2, _3):
            self.capmanager.resume_global_capture()

    yield suspend_guard()


@pytest.fixture
def mocked_channel_in(mocker: MockerFixture) -> Generator[Mock, None, None]:
    _mocked_channel_in = mocker.patch("opensmtpd_filters.filter_engine.engine.open_in", new_callable=mocker.mock_open)
    yield _mocked_channel_in
    mocker.stop(_mocked_channel_in)


@pytest.fixture
def mocked_channel_out(mocker: MockerFixture) -> Generator[Mock, None, None]:
    _mocked_channel_out = mocker.patch("opensmtpd_filters.filter_engine.engine.open_out", new_callable=mocker.mock_open)
    yield _mocked_channel_out
    mocker.stop(_mocked_channel_out)


@pytest.fixture
def mocked_filter_stream_report(mocker: MockerFixture) -> Generator[Mock, None, None]:
    _mocked_filter_stream_report = mocker.patch.object(FilterEngine, "_filter_stream_report")
    yield _mocked_filter_stream_report
    mocker.stop(_mocked_filter_stream_report)


@pytest.fixture
def mocked_filter_stream_filter(mocker: MockerFixture) -> Generator[Mock, None, None]:
    _mocked_filter_stream_filter = mocker.patch.object(FilterEngine, "_filter_stream_filter")
    yield _mocked_filter_stream_filter
    mocker.stop(_mocked_filter_stream_filter)


class TestFilterEnginePublicAPI:
    """ Tests for the public API of the class ``FilterEngine``. """
    
    CONFIG_READY = "config|ready"
    REGISTER_READY = "register|ready"
    
    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def _suspend_capture(cls, suspend_capture) -> None:
        cls._suspend_capture = suspend_capture

    @pytest.fixture(autouse=True)
    def _mocked_channel_in(self, mocked_channel_in: Mock) -> None:
        self._mocked_stdin: Mock = mocked_channel_in

    @pytest.fixture(autouse=True)
    def _mocked_channel_out(self, mocked_channel_out: Mock) -> None:
        self._mocked_stdout: Mock = mocked_channel_out

    @pytest.fixture(autouse=True)
    def _mocked_filter_stream_report(self, mocked_filter_stream_report: Mock) -> None:
        self._mocked_filter_stream_report: Mock = mocked_filter_stream_report

    @pytest.fixture(autouse=True)
    def _mocked_filter_stream_filter(self, mocked_filter_stream_filter: Mock) -> None:
        self._mocked_filter_stream_filter: Mock = mocked_filter_stream_filter
    
    def test_when_filterengine_init_then_protocol_configurations_read(self) -> None:
        self._mocked_stdin.return_value.readline.side_effect = [
            "config|smtpd-version|version\r",
            "config|smtp-session-timeout|600\n",
            "config|subsystem|smtp-in\r\n",
            "config|admd|host-name\n\r",
            self.CONFIG_READY
        ]
        
        with self._suspend_capture:
            filter_engine = FilterEngine()
        
        assert 4 == len(filter_engine.get_protocol_configurations().items())
        assert ("smtpd-version", "version") in filter_engine.get_protocol_configurations().items()
        assert ("smtp-session-timeout", "600") in filter_engine.get_protocol_configurations().items()
        assert ("subsystem", "smtp-in") in filter_engine.get_protocol_configurations().items()
        assert ("admd", "host-name") in filter_engine.get_protocol_configurations().items()
        assert ("config", "ready") not in filter_engine.get_protocol_configurations().items()
        self._mocked_filter_stream_report.assert_not_called()
        self._mocked_filter_stream_filter.assert_not_called()
        assert 5 == self._mocked_stdin.return_value.readline.call_count
        self._mocked_stdout.return_value.write.assert_not_called()
    
    @pytest.mark.parametrize("line", [
        None, ""
    ])
    def test_when_receive_and_line_invalid_then_exception_is_raised(self, line: str) -> None:
        self._mocked_stdin.return_value.readline.side_effect = [
            self.CONFIG_READY,
            line
        ]
        
        with pytest.raises(FilterEngineException) as context:
            with self._suspend_capture:
                filter_engine = FilterEngine()
                filter_engine.receive()
        
        assert isinstance(context.value, FilterEngineException)
        assert "No more input received." == str(context.value)
        self._mocked_filter_stream_report.assert_not_called()
        self._mocked_filter_stream_filter.assert_not_called()
        assert 2 == self._mocked_stdin.return_value.readline.call_count
        self._mocked_stdout.return_value.write.assert_not_called()
    
    @pytest.mark.parametrize("line, expected", [
        ("line1\r", "line1"),
        ("line2\n", "line2"),
        ("line3\r\n", "line3"),
        ("line4\n\r", "line4"),
        ("line5", "line5"),
    ])
    def test_when_receive_and_line_valid_then_receive(self, line: str, expected: str) -> None:
        self._mocked_stdin.return_value.readline.side_effect = [
            self.CONFIG_READY,
            line
        ]
        
        with self._suspend_capture:
            filter_engine = FilterEngine()
            line_received = filter_engine.receive()
        
        assert expected == line_received
        self._mocked_filter_stream_report.assert_not_called()
        self._mocked_filter_stream_filter.assert_not_called()
        assert 2 == self._mocked_stdin.return_value.readline.call_count
        self._mocked_stdout.return_value.write.assert_not_called()
    
    @pytest.mark.parametrize("line", [
        None, ""
    ])
    def test_when_send_and_line_invalid_then_exception_is_raised(self, line: str) -> None:
        self._mocked_stdin.return_value.readline.return_value = self.CONFIG_READY
        
        with pytest.raises(FilterEngineException) as context:
            with self._suspend_capture:
                filter_engine = FilterEngine()
                filter_engine.send(line)
        
        assert isinstance(context.value, FilterEngineException)
        assert "No line to send." == str(context.value)
        self._mocked_filter_stream_report.assert_not_called()
        self._mocked_filter_stream_filter.assert_not_called()
        assert 1 == self._mocked_stdin.return_value.readline.call_count
        self._mocked_stdout.return_value.write.assert_not_called()
    
    def test_when_send_then_line_is_sent(self) -> None:
        self._mocked_stdin.return_value.readline.return_value = self.CONFIG_READY
        
        with self._suspend_capture:
            filter_engine = FilterEngine()
            filter_engine.send("line1")
            filter_engine.send("line2")
            filter_engine.send(".")

        self._mocked_filter_stream_report.assert_not_called()
        self._mocked_filter_stream_filter.assert_not_called()
        assert 1 == self._mocked_stdin.return_value.readline.call_count
        self._mocked_stdout.return_value.write.assert_has_calls([
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
        self._mocked_stdin.return_value.readline.return_value = self.CONFIG_READY
        
        with pytest.raises(FilterEngineException) as context:
            with self._suspend_capture:
                filter_engine = FilterEngine()
                filter_engine.register_processor(stream, event, lambda _: _)
        
        if not stream:
            expected_message = "Can not register a processor for the stream 'UNKNOWN'."
        elif not event:
            expected_message = "Can not register a processor for the event 'UNKNOWN'."
        else:
            expected_message = f"The event '{event}' can't be registered for the stream '{stream}'."
        
        assert isinstance(context.value, FilterEngineException)
        assert expected_message == str(context.value)
        self._mocked_filter_stream_report.assert_not_called()
        self._mocked_filter_stream_filter.assert_not_called()
        assert 1 == self._mocked_stdin.return_value.readline.call_count
        self._mocked_stdout.return_value.write.assert_not_called()
    
    def test_when_register_processor_with_valid_parameters_then_processor_registered(self) -> None:
        self._mocked_stdin.return_value.readline.return_value = self.CONFIG_READY
        
        with self._suspend_capture:
            filter_engine = FilterEngine()
            filter_engine.register_processor(Stream.REPORT, Event.LINK_CONNECT, lambda _: _)
        
        assert 1 == len(filter_engine._processors.items())
        assert "report|link-connect" in filter_engine._processors
        self._mocked_filter_stream_report.assert_not_called()
        self._mocked_filter_stream_filter.assert_not_called()
        assert 1 == self._mocked_stdin.return_value.readline.call_count
        self._mocked_stdout.return_value.write.assert_has_calls([
            call("register|report|smtp-in|link-connect"),
            call(os.linesep)
        ])
    
    def test_when_register_processor_with_already_registered_stream_or_event_called_then_exception_raised(self) -> None:
        self._mocked_stdin.return_value.readline.return_value = self.CONFIG_READY
        
        with pytest.raises(FilterEngineException) as context:
            with self._suspend_capture:
                filter_engine = FilterEngine()
                filter_engine.register_processor(Stream.REPORT, Event.LINK_CONNECT, lambda _: _)
                filter_engine.register_processor(Stream.REPORT, Event.LINK_CONNECT, lambda _: _)
        
        assert isinstance(context.value, FilterEngineException)
        assert "A processor for 'report|link-connect' is already registered." == str(context.value)
        self._mocked_filter_stream_report.assert_not_called()
        self._mocked_filter_stream_filter.assert_not_called()
        assert 1 == self._mocked_stdin.return_value.readline.call_count
        self._mocked_stdout.return_value.write.assert_has_calls([
            call("register|report|smtp-in|link-connect"),
            call(os.linesep)
        ])
    
    def test_when_filter_loop_and_line_invalid_then_nothing_processed(self) -> None:
        self._mocked_stdin.return_value.readline.side_effect = [
            self.CONFIG_READY,
            "garbage",
            "garbage|garbage",
            "garbage|garbage|garbage",
            "garbage|garbage|garbage|garbage",
            "garbage|garbage|garbage|garbage|garbage",
            InterruptedError("test invalid protocol")
        ]
        
        with pytest.raises(InterruptedError) as context:
            with self._suspend_capture:
                filter_engine = FilterEngine()
                filter_engine.filter_loop()
        
        assert isinstance(context.value, InterruptedError)
        assert "test invalid protocol" == str(context.value)
        self._mocked_filter_stream_report.assert_not_called()
        self._mocked_filter_stream_filter.assert_not_called()
        assert 7 == self._mocked_stdin.return_value.readline.call_count
        self._mocked_stdout.return_value.write.assert_has_calls([
            call(self.REGISTER_READY),
            call(os.linesep)
        ])
    
    def test_when_filter_loop_then_unexpected_stream_is_not_processed(self) -> None:
        self._mocked_stdin.return_value.readline.side_effect = [
            self.CONFIG_READY,
            "config|0.7|1577836800.000030|smtp-in|event|82a3bd08e3a8db65",
            "stream|0.7|1577836800.300000|smtp-in|unknown|82a3bd08e3a8db65|82a3bd08e3a8db66",
            InterruptedError("test invalid stream")
        ]
        
        with pytest.raises(InterruptedError) as context:
            with self._suspend_capture:
                filter_engine = FilterEngine()
                filter_engine.filter_loop()
        
        assert isinstance(context.value, InterruptedError)
        assert "test invalid stream" == str(context.value)
        self._mocked_filter_stream_report.assert_not_called()
        self._mocked_filter_stream_filter.assert_not_called()
        assert 4 == self._mocked_stdin.return_value.readline.call_count
        self._mocked_stdout.return_value.write.assert_has_calls([
            call(self.REGISTER_READY),
            call(os.linesep)
        ])
    
    def test_when_filter_loop_then_stream_report_is_processed(self) -> None:
        self._mocked_stdin.return_value.readline.side_effect = [
            self.CONFIG_READY,
            "report|0.7|1577836800.000010|smtp-in|link-connect|82a3bd08e3a8db65|localhost|pass|127.0.0.1:1234|127.0.0.1:25",
            "report|0.7|1577836800.100000|smtp-in|link-disconnect|82a3bd08e3a8db65",
            InterruptedError("test report stream")
        ]
        
        with pytest.raises(InterruptedError) as context:
            with self._suspend_capture:
                filter_engine = FilterEngine()
                filter_engine.filter_loop()
        
        assert isinstance(context.value, InterruptedError)
        assert "test report stream" == str(context.value)
        assert 2 == self._mocked_filter_stream_report.call_count
        self._mocked_filter_stream_filter.assert_not_called()
        assert 4 == self._mocked_stdin.return_value.readline.call_count
        self._mocked_stdout.return_value.write.assert_has_calls([
            call(self.REGISTER_READY),
            call(os.linesep)
        ])
    
    def test_when_filter_loop_then_stream_filter_is_processed(self) -> None:
        self._mocked_stdin.return_value.readline.side_effect = [
            self.CONFIG_READY,
            "filter|0.7|1577836800.000020|smtp-in|connect|82a3bd08e3a8db65|82a3bd08e3a8db66|localhost|127.0.0.1:1234",
            "filter|0.7|1577836800.200000|smtp-in|junk|82a3bd08e3a8db65|82a3bd08e3a8db66",
            InterruptedError("test filter stream")
        ]
        
        with pytest.raises(InterruptedError) as context:
            with self._suspend_capture:
                filter_engine = FilterEngine()
                filter_engine.filter_loop()
        
        assert isinstance(context.value, InterruptedError)
        assert "test filter stream" == str(context.value)
        self._mocked_filter_stream_report.assert_not_called()
        assert 2 == self._mocked_filter_stream_filter.call_count
        assert 4 == self._mocked_stdin.return_value.readline.call_count
        self._mocked_stdout.return_value.write.assert_has_calls([
            call(self.REGISTER_READY),
            call(os.linesep)
        ])
    
    @patch.object(FilterEngine, 'register_processor')
    def test_when_track_context_and_session_context_set_then_do_nothing(self, mocked_register_processor: Mock) -> None:
        self._mocked_stdin.return_value.readline.side_effect = [
            self.CONFIG_READY,
            InterruptedError("test session context set")
        ]
        
        with pytest.raises(InterruptedError) as context:
            with self._suspend_capture:
                filter_engine = FilterEngine()
                filter_engine._session_contexts = {'test': "123456"}
                filter_engine.track_session_context()
                filter_engine.filter_loop()
        
        assert isinstance(context.value, InterruptedError)
        assert "test session context set" == str(context.value)
        mocked_register_processor.assert_not_called()
        self._mocked_filter_stream_report.assert_not_called()
        self._mocked_filter_stream_filter.assert_not_called()
        assert 2 == self._mocked_stdin.return_value.readline.call_count
        self._mocked_stdout.return_value.write.assert_has_calls([
            call(self.REGISTER_READY),
            call(os.linesep)
        ])
    
    @patch.object(FilterEngine, 'register_processor')
    def test_when_track_context_and_session_context_not_set_then_track_context(self,
                                                                               mocked_register_processor: Mock) -> None:
        self._mocked_stdin.return_value.readline.side_effect = [
            self.CONFIG_READY,
            InterruptedError("test session context unset")
        ]
        
        with pytest.raises(InterruptedError) as context:
            with self._suspend_capture:
                filter_engine = FilterEngine()
                filter_engine.track_session_context()
                filter_engine.filter_loop()
        
        assert isinstance(context.value, InterruptedError)
        assert "test session context unset" == str(context.value)
        mocked_register_processor.assert_has_calls([
            call(Stream.REPORT, Event.LINK_CONNECT, ANY),
            call(Stream.REPORT, Event.LINK_DISCONNECT, ANY)
        ])
        self._mocked_filter_stream_report.assert_not_called()
        self._mocked_filter_stream_filter.assert_not_called()
        assert 2 == self._mocked_stdin.return_value.readline.call_count
        self._mocked_stdout.return_value.write.assert_has_calls([
            call(self.REGISTER_READY),
            call(os.linesep)
        ])
