from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionContext:
    """
    Represents the detailed session information containing the mandatory session_id and optional the data for rdns,
    fcrdns, src, and dest. This will be passed as the first parameter to all the filter processors.
    
    These are the same parameters which are sent during the link-connect event in the report stream.
    See https://man.openbsd.org/smtpd-filters#link-connect.
    """
    
    session_id: str
    """ A unique session ID. """
    
    rdns: str | None = None
    """ The reverse DNS hostname for the remote end, or ``None`` if not available. """
    
    fcrdns: str | None = None
    """ Contains ``pass`` or ``fail`` signaling if the remote end validates FCrDNS (Forward-confirmed reverse DNS),
    or ``None`` if not available. """
    
    src: str | None = None
    """ Contains either the IP address and port of the source address (format "address:port"), or the path to a UNIX
    socket (format "unix:/path"), or ``None`` if not available. """
    
    dest: str | None = None
    """ Contains either the IP address and port of the destination address (format "address:port"), or the path to a
    UNIX socket (format "unix:/path"), or ``None`` if not available.  """
    
    context_data: dict[str, Any] = field(default_factory=dict, init=False)
    """ Variable data which can be modified by the processor at will. """
    
    def __str__(self) -> str:
        attributes = ", ".join(f"{attribute}='{value}'" for attribute, value in self.__dict__.items() if value is not
                               None and attribute != "context_data")
        return f"{type(self).__name__}({attributes})"
