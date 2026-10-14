from dataclasses import dataclass, field
from datetime import datetime

from .event import Event
from .exception import FilterEngineException
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
        """
        Retrieve the string representation of this protocol prefix.
        
        :return: A string containing the non-None attributes of the protocol prefix.
        :rtype: str
        """
        
        attributes = ", ".join(f"{attribute}='{value}'" for attribute, value in self.__dict__.items() if value is not
                               None)
        return f"{type(self).__name__}({attributes})"


@dataclass(init=False)
class ProtocolData:
    """ A representation of a data line which is sent by the OpenSMTPd filter API. """
    
    protocol_prefix: ProtocolPrefix
    payload: str | None = None
    
    # pylint: disable-next=too-many-arguments, too-many-positional-arguments
    def __init__(self, stream: str | Stream, protocol_version: str, timestamp: str | datetime,
            subsystem: str | Subsystem, event: str | Event, session_id: str) -> None:
        """
        Initialise the data representation from raw string values sent by the OpenSMTPd filter API.
        
        :param stream: The stream for which this data has been sent (e.g., "filter" or "report").
        :type stream: str | Stream
        :param protocol_version: The version of the protocol used by the OpenSMTPd filter API.
        :type protocol_version: str
        :param timestamp: The timestamp at which this data has been sent (Unix timestamp as string).
        :type timestamp: str | datetime
        :param subsystem: The subsystem for which this data has been sent (e.g., "smtp-in").
        :type subsystem: str | Subsystem
        :param event: The event for which this data has been sent (e.g., "mail-from").
        :type event: str | Event
        :param session_id: The unique session identifier.
        :type session_id: str
        :raises FilterEngineException: If the timestamp string cannot be converted to a datetime object.
        """
        
        _stream = Stream(stream)
        if isinstance(timestamp, datetime):
            _timestamp = timestamp
        else:
            try:
                _timestamp = datetime.fromtimestamp(float(str(timestamp)))
            except (ValueError, OverflowError, OSError) as conversion_exception:
                raise FilterEngineException(f"Invalid timestamp: {timestamp}") from conversion_exception
        _subsystem: Subsystem = subsystem if isinstance(subsystem, Subsystem) else Subsystem(str(subsystem))
        _event: Event = event if isinstance(event, Event) else Event(str(event))
        self.protocol_prefix = ProtocolPrefix(_stream, protocol_version, _timestamp, _subsystem, _event, session_id)
