from dataclasses import dataclass, field
from datetime import datetime

from .event import Event
from .stream import Stream
from .subsystem import Subsystem


@dataclass
class ProtocolPrefix:
    """
    Represents the prefix sent by the OpenSMTPd filter API protocol.
    
    This prefix is prepended to every report event, or filter request. Filter requests also include an additional
    opaque token, which must be included in every response.
    """
    
    stream: Stream
    """ The stream. """
    
    protocol_version: str
    """ The version of the protocol used by the OpenSMTPd filter API. """
    
    timestamp: datetime
    """ The timestamp. """
    
    subsystem: Subsystem
    """ The subsystem. """
    
    event: Event
    """ The event for the report stream, or the filtering phase for the filter stream. """
    
    session_id: str
    """ A unique session ID. """
    
    token: str | None = field(default=None, init=False, hash=False, compare=False)
    """ The opaque token sent only by filter requests. """
    
    def __str__(self) -> str:
        attributes = ", ".join(f"{attribute}='{value}'" for attribute, value in self.__dict__.items() if value is not
                               None)
        return f"{type(self).__name__}({attributes})"


@dataclass(init=False)
class ProtocolData:
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
