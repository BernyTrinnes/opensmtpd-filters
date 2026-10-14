import inspect
import os
import sys
from builtins import open as open_in, open as open_out
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from packaging.version import parse as version_parse

from .answer import Answer
from .event import Event
from .exception import FilterEngineException
from .protocol_prefix import ProtocolPrefix
from .session_context import SessionContext
from .stream import Stream
from .subsystem import Subsystem


@dataclass(init=False)
class _FilterProtocolData:
    """ A representation of a data line which is sent by the OpenSMTPd filter API. """
    protocol_prefix: ProtocolPrefix
    payload: str | None = None
    
    def __init__(self, stream: str, protocol_version: str, timestamp: str, subsystem: str, event: str, session_id: str):
        """
        Initialise the data representation.

        :param stream: The stream for which this data has been sent.
        :type stream: object
        :param protocol_version: The version of the protocol used by the OpenSMTPd filter API.
        :type protocol_version: object
        :param timestamp: The timestamp at which this data has been sent.
        :type timestamp: object
        :param subsystem: The subsystem for which this data has been sent.
        :type subsystem: object
        :param event: The event for which this data has been sent.
        :type event: object
        :param session_id: The unique session identifier.
        :type session_id: str
        """
        
        _stream = Stream(stream)
        _timestamp: datetime = timestamp if isinstance(timestamp, datetime) else datetime.fromtimestamp(
                float(str(timestamp)))
        _subsystem: Subsystem = subsystem if isinstance(subsystem, Subsystem) else Subsystem(str(subsystem))
        _event: Event = event if isinstance(event, Event) else Event(str(event))
        self.protocol_prefix = ProtocolPrefix(_stream, protocol_version, _timestamp, _subsystem, _event, session_id)


class FilterEngine:
    """ The filter engine communicates with the OpenSMTPd filter API via ``stdin`` and ``stdout``. """
    
    def __init__(self):
        """ Initialise the communication with the OpenSMTd server. """
        
        self._CONFIGURATION_READY = f"{Stream.CONFIG}|{Event.READY}"
        self._REPORT_LINK_CONNECT = f"{Stream.REPORT}|{Event.LINK_CONNECT}"
        self._ANSWER_REGISTER_READY = f"{Answer.REGISTER}|{Event.READY}"
        
        self._channel_in = open_in(sys.stdin.fileno(), "rt", 1, "iso-8859-1")
        self._channel_out = open_out(sys.stdout.fileno(), "wt", 1, "iso-8859-1")
        self._stderr = os.fdopen(sys.stderr.fileno(), 'w', encoding='latin-1', buffering=1)
        self._processors: dict[str, Callable] = {}
        self._session_contexts: dict[str, Any] = {}
        
        self._protocol_configurations: dict[str, str] = {}
        self._read_protocol_configurations()
    
    def _read_protocol_configurations(self) -> None:
        """ Loop through the configuration data sent by the server and record it. """
        
        while True:
            config_entry = self.receive()
            if self._CONFIGURATION_READY == config_entry:
                break
            config_event, config_key, config_value = config_entry.split("|", 2)
            self._protocol_configurations[config_key] = config_value
    
    def get_protocol_configurations(self) -> dict[str, str]:
        """
        Return the general configuration information of the OpenSMTPd filter API protocol.
        
        :return: A dictionary containing the general configuration information, empty if the information has not been
        sent during the initial handshake.
        :rtype: dict[str, str]
        """
        
        return self._protocol_configurations
    
    def receive(self) -> str:
        """
        Receive one line sent by the OpenSMTPd filter API.
        
        :return: The received line, without line endings.
        :rtype: str
        :raise FilterEngineException If the OpenSMTPd filter API did not send data while trying to receive it.
        """
        
        line = self._channel_in.readline()
        if not line:
            raise FilterEngineException("No more input received.")
        return line.rstrip("\r\n")
    
    def send(self, line: str) -> None:
        """
        Send the given line to the OpenSMTPd filter API.
        
        :param line: The line to send, should not be empty.
        :type line:str
        :raise FilterEngineException: If the line to send is not valid.
        """
        
        if not line:
            raise FilterEngineException("No line to send.")
        print(line, file=self._channel_out)
    
    def register_processor(self, stream: Stream, event: Event, processor: Callable) -> None:
        """
        Register a processor for the given stream and event. The processor registration **must** be done before
        ``filter_loop()`` is called.
        
        Processors for the config stream will receive the config key and value as parameters, no response is expected.
        Processors for the report stream will receive session ID and phase-specific parameters as arguments, also no
        response is expected. Processors for most filter streams will receive the same parameters, but have to return a
        result like ``proceed`` or ``reject|550 Spam``. Processors for 'data-line' filter will receive an additional
        send_dataline processor as last parameter which can be called any number of times to send lines to the
        OpenSMTPd filter API.
        
        :param stream: The valid stream for which the processor is being registered.
        :type stream: Stream
        :param event: The valid event for which the processor is being registered.
        :type event: Event
        :param processor: A function which is called, when the registered stream and event are sent from the OpenSMTPd
        filter API.
        :type processor: Callable
        :raise FilterEngineException: If the stream or event are not valid, or an event is registered for a stream it is
        not intended to.
        """
        
        if not stream:
            raise FilterEngineException("Can not register a processor for the stream 'UNKNOWN'.")
        if not event:
            raise FilterEngineException("Can not register a processor for the event 'UNKNOWN'.")
        if event.stream != stream:
            raise FilterEngineException(f"The event '{event}' can't be registered for the stream '{stream}'.")
        
        processor_key = f"{stream}|{event}"
        if processor_key in self._processors:
            raise FilterEngineException(f"A processor for '{processor_key}' is already registered.")
        self._processors[processor_key] = processor
        self.send(f"{Answer.REGISTER}|{stream}|{Subsystem.SMTP_IN}|{event}")
    
    def filter_loop(self) -> None:
        """ Process the data coming from the OpenSMTPd filter API in an endless loop. """
        
        self.send(self._ANSWER_REGISTER_READY)
        while True:
            filter_dataline = self._split_protocol_line(self.receive())
            if not filter_dataline:
                continue
            
            match filter_dataline.protocol_prefix.stream:
                case Stream.REPORT:
                    self._filter_stream_report(filter_dataline)
                case Stream.FILTER:
                    self._filter_stream_filter(filter_dataline)
                case _:
                    print(f"Unexpected stream '{filter_dataline.protocol_prefix.stream}' received.", file=sys.stderr)
    
    @classmethod
    def _split_protocol_line(cls, filter_line: str) -> _FilterProtocolData | None:
        """
        Split the line sent by the OpenSMTPd filter API in the protocol prefix and the payload, which can also be
        ``None``.

        :param filter_line: The line as sent by the filter API.
        :type filter_line: str
        :return: The processed line, split in the protocol prefix and the payload.
        :rtype: _FilterProtocolData
        """
        
        filter_line_split = filter_line.split("|", 6)
        if len(filter_line_split) < 6:
            return None
        
        filter_protocol_data = _FilterProtocolData(*filter_line_split[:6])
        if len(filter_line_split) > 6:
            filter_protocol_data.payload = filter_line_split[6]
        return filter_protocol_data
    
    def _filter_stream_report(self, filter_dataline: _FilterProtocolData) -> None:
        """
        Process the line sent by the filter API for the report stream.
        
        :param filter_dataline: The data of the line which will be processed.
        :type filter_dataline: _FilterProtocolData
        """
        
        processor_arguments = []
        if filter_dataline.payload:
            processor_arguments = filter_dataline.payload.split('|')
        if (Event.TX_MAIL == filter_dataline.protocol_prefix.event and
                self._is_old_protocol_version(filter_dataline.protocol_prefix.protocol_version) and
                3 == len(processor_arguments)):
            # In older protocol versions, result and sender were in reversed order
            processor_arguments[1], processor_arguments[2] = (processor_arguments[2], processor_arguments[1])
        self._call_processor(self._result_processor_noop, filter_dataline.protocol_prefix, *processor_arguments)
        
    @classmethod
    def _is_old_protocol_version(cls, protocol_version: str) -> bool:
        """
        Check if the given protocol version is an old protocol version (<= 0.4).
        
        :param protocol_version: The protocol version to check.
        :type protocol_version: str
        :return: ``True`` if the given protocol version is an old protocol version (<= 0.4), ``False`` otherwise.
        """
        _protocol_version = version_parse(protocol_version)
        return _protocol_version <= version_parse("0.4")
    
    def _call_processor(self, result_processor: Callable, protocol_data: ProtocolPrefix, *processor_data):
        """
        Call the processor which has been registered for a given stream and event.
        
        :param result_processor: The internal processor for handling the data returned by the registered processor.
        :type result_processor: Callable
        :param protocol_data: The OpenSMTPd filter API protocol data.
        :type protocol_data: ProtocolPrefix
        :param processor_data: The payload which will be given to the processor.
        :type processor_data: string tuple of variable length
        """
        
        processor_key = '{}|{}'.format(protocol_data.stream, protocol_data.event)
        if processor_key not in self._processors:
            return
        
        try:
            session = protocol_data.session_id
            if self._session_contexts and self._REPORT_LINK_CONNECT != processor_key:
                session = self._session_contexts[protocol_data.session_id]
            
            processor = self._processors[processor_key]
            expected_processor_arguments = inspect.signature(processor).parameters.values()
            if any(inspect.Parameter.VAR_POSITIONAL == param.kind for param in expected_processor_arguments):
                # Processor function accepts a variable number of positional arguments
                expected_processor_arguments_number = len(processor_data)
            else:
                expected_processor_arguments_number = len(list(filter(
                        lambda parameter: parameter.kind in (inspect.Parameter.POSITIONAL_ONLY,
                                                             inspect.Parameter.POSITIONAL_OR_KEYWORD),
                        expected_processor_arguments))) - 1
            
            if len(processor_data) < expected_processor_arguments_number:
                # Processor function expects fewer positional arguments then the ones determined.
                # This could happen if e.g. an email address contains a pipe symbol.
                processor_data = (processor_data[:expected_processor_arguments_number - 1],
                                  '|'.join(processor_data[expected_processor_arguments_number - 1:]))
            result_processor(processor(session, *processor_data))
        except Exception as exception:
            print(f"Could not start the registered processor for key '{processor_key}'.", file=sys.stderr)
            print(exception, file=sys.stderr)
    
    def _result_processor_noop(self, result: str) -> None:
        """
        A processor for results which do not need further processing.
        
        :param result: The result which should be processed, ignored here.
        :type result: str
        """
        
        pass
    
    def _filter_stream_filter(self, filter_dataline: _FilterProtocolData) -> None:
        """
        Process the line sent by the filter API for the filter stream.
        
        :param filter_dataline: The data of the line which will be processed.
        :type filter_dataline: _FilterProtocolData
        """
        
        def _result_processor_filter_response(filter_response: str) -> None:
            if not filter_dataline:
                return
            self._send_filter_response(Answer.FILTER_RESULT, filter_dataline.protocol_prefix, filter_response)
        
        def _result_processor_filter_dataline(dataline: str) -> None:
            if not filter_dataline:
                return
            self._send_filter_response(Answer.FILTER_DATALINE, filter_dataline.protocol_prefix, dataline)
        
        if filter_dataline.payload and "|" in filter_dataline.payload:
            _token, _payload = filter_dataline.payload.split('|', 1)
        else:
            _token = filter_dataline.payload
            _payload = None
        filter_dataline.protocol_prefix.token = _token
        filter_dataline.payload = _payload
        
        if Event.DATA_LINE == filter_dataline.protocol_prefix.event:
            self._call_processor(self._result_processor_noop, filter_dataline.protocol_prefix, filter_dataline.payload,
                                 _result_processor_filter_dataline)
        else:
            processor_arguments = []
            if filter_dataline.payload:
                processor_arguments = filter_dataline.payload.split('|')
            self._call_processor(_result_processor_filter_response, filter_dataline.protocol_prefix, *processor_arguments)
    
    def _send_filter_response(self, answer: Answer, protocol_prefix: ProtocolPrefix, payload: str) -> None:
        """
        Send a filter response with the given data.
        
        :param answer: The answer which should be sent.
        :type answer: Answer
        :param protocol_prefix: The protocol prefix which is processed for the answer.
        :type protocol_prefix: ProtocolPrefix
        :param payload: The payload of the answer.
        :type payload: str
        """
        
        if not protocol_prefix.token:
            return
        
        if self._is_old_protocol_version(protocol_prefix.protocol_version):
            self.send('|'.join([str(answer), protocol_prefix.token, protocol_prefix.session_id, payload]))
        else:
            self.send('|'.join([str(answer), protocol_prefix.session_id, protocol_prefix.token, payload]))
    
    def track_session_context(self):
        """
        Calling this method before ``filter_loop()`` ensures that the first parameter passed to all processors will
        be the session context rather than just the session ID.
        
        The session context is a ``SessionContext`` object containing the data which the ``link-connect`` report event
        supplies. Processors can add and modify context object at will.
        
        **Note:** this will register the events ``link-connect`` and ``link-disconnect`` for the ``report`` stream.
        """
        
        if self._session_contexts:
            return
        
        def _handle_link_connect(session: str, rdns: str, fcrdns: str, src: str, dest: str):
            self._session_contexts[session] = SessionContext(session, rdns, fcrdns, src, dest)
        
        def _handle_link_disconnect(session_context: str | SessionContext):
            if isinstance(session_context, SessionContext):
                session_id = session_context.session_id
            else:
                session_id = str(session_context)
            
            if session_id not in self._session_contexts:
                return
            del self._session_contexts[session_id]
        
        self._session_contexts = {}
        self.register_processor(Stream.REPORT, Event.LINK_CONNECT, _handle_link_connect)
        self.register_processor(Stream.REPORT, Event.LINK_DISCONNECT, _handle_link_disconnect)
    
    def register_message_body_filter(self, message_processor: Callable):
        """
        Helper method allowing to filter message bodies without registering multiple event processors. The processor
        will be called with the session context and a list of message lines. It has to return a filtered list of
        lines.
        
        **Note:** this will call ``track_session_context()``.
        
        :param message_processor: A function which is called when the message body has been fully received.
        :type message_processor: Callable
        """
        
        def _escape_line(line: str):
            return "." + line if line.startswith('.') else line
        
        def _unescape_line(line: str):
            return line[1:] if line.startswith('..') else line
        
        def _process_dataline(session_context: SessionContext, data_line: str, send_dataline: Callable):
            try:
                if "." != data_line:
                    session_context.context_data.setdefault("message_lines", []).append(_unescape_line(data_line))
                else:
                    data_lines = message_processor(session_context, session_context.context_data.get('message_lines', []))
                    for line in data_lines:
                        send_dataline(_escape_line(line))
                    send_dataline('.')
                    session_context.pop('message_lines', None)
            except:
                send_dataline('.')
                session_context['message_error'] = True
                session_context.pop('message_lines', None)
                raise
        
        def _process_commit(context, *args):
            if 'message_error' in context:
                del context['message_error']
                return 'reject|451 Internal server error'
            else:
                return 'proceed'
        
        self.track_session_context()
        self.register_processor(Stream.FILTER, Event.DATA_LINE, _process_dataline)
        self.register_processor(Stream.FILTER, Event.COMMIT, _process_commit)
