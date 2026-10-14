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
