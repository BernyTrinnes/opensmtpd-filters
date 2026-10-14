from enum import Enum, unique

from .stream import Stream


@unique
class Event(Enum):
    """
    Events (for the report stream) / filtering phases (for the filter stream) supported by the OpenSMTPd filter API.
    """
    
    UNKNOWN = "unknown"
    """ An unknown/invalid event. """
    
    LINK_CONNECT = ("link-connect", Stream.REPORT, 4)
    """ This event is generated upon connection.
    `External documentation. <https://man.openbsd.org/smtpd-filters#link-connect>`__ """
    
    LINK_GREETING = ("link-greeting", Stream.REPORT, 1)
    """ This event is generated upon display of the server banner.
    `External documentation. <https://man.openbsd.org/smtpd-filters#link-greeting>`__ """
    
    LINK_IDENTIFY = ("link-identify", Stream.REPORT, 2)
    """ This event is generated upon “HELO” or “EHLO” command from the client.
    `External documentation. <https://man.openbsd.org/smtpd-filters#link-identify>`__ """
    
    LINK_TLS = ("link-tls", Stream.REPORT, 1)
    """ This event is generated upon successful negotiation of TLS.
    `External documentation. <https://man.openbsd.org/smtpd-filters#link-tls>`__ """
    
    LINK_DISCONNECT = ("link-disconnect", Stream.REPORT)
    """ This event is generated upon disconnection of the client.
    `External documentation. <https://man.openbsd.org/smtpd-filters#link-disconnect>`__ """
    
    LINK_AUTH = ("link-auth", Stream.REPORT, 2)
    """ This event is generated upon an authentication attempt by the client.
    `External documentation. <https://man.openbsd.org/smtpd-filters#link-auth>`__ """
    
    TX_RESET = ("tx-reset", Stream.REPORT, 1, True)
    """ This event is generated when a transaction is reset.
    `External documentation. <https://man.openbsd.org/smtpd-filters#tx-reset>`__ """
    
    TX_BEGIN = ("tx-begin", Stream.REPORT, 1)
    """ This event is generated when a transaction is initiated.
    `External documentation. <https://man.openbsd.org/smtpd-filters#tx-begin>`__ """
    
    TX_MAIL = ("tx-mail", Stream.REPORT, 3)
    """ This event is generated when client emits “MAIL FROM”.
    `External documentation. <https://man.openbsd.org/smtpd-filters#tx-mail>`__ """
    
    TX_RCPT = ("tx-rcpt", Stream.REPORT, 3)
    """ This event is generated when client emits “RCPT TO”.
    `External documentation. <https://man.openbsd.org/smtpd-filters#tx-rcpt>`__ """
    
    TX_ENVELOPE = ("tx-envelope", Stream.REPORT, 2)
    """ This event is generated when an envelope is accepted.
    `External documentation. <https://man.openbsd.org/smtpd-filters#tx-envelope>`__ """
    
    TX_DATA = ("tx-data", Stream.REPORT, 2)
    """ This event is generated when client has emitted “DATA”.
    `External documentation. <https://man.openbsd.org/smtpd-filters#tx-data>`__ """
    
    TX_COMMIT = ("tx-commit", Stream.REPORT, 2)
    """ This event is generated when a transaction has been accepted by the server.
    `External documentation. <https://man.openbsd.org/smtpd-filters#tx-commit>`__ """
    
    TX_ROLLBACK = ("tx-rollback", Stream.REPORT, 1)
    """ This event is generated when a transaction has been rejected by the server.
    `External documentation. <https://man.openbsd.org/smtpd-filters#tx-rollback>`__ """
    
    PROTOCOL_CLIENT = ("protocol-client", Stream.REPORT, 1)
    """ This event is generated for every command submitted by the client.
    `External documentation. <https://man.openbsd.org/smtpd-filters#protocol-client>`__ """
    
    PROTOCOL_SERVER = ("protocol-server", Stream.REPORT, 1)
    """ This event is generated for every response emitted by the server.
    `External documentation. <https://man.openbsd.org/smtpd-filters#protocol-server>`__ """
    
    FILTER_REPORT = ("filter-report", Stream.REPORT, 3)
    """ This event is generated when a filter emits a report.
    `External documentation. <https://man.openbsd.org/smtpd-filters#filter-report>`__ """
    
    FILTER_RESPONSE = ("filter-response", Stream.REPORT, 3, True)
    """ This event is generated when a filter responds to a filtering request.
    `External documentation. <https://man.openbsd.org/smtpd-filters#filter-response>`__ """
    
    TIMEOUT = ("timeout", Stream.REPORT)
    """ This event is generated when a timeout happens for a session.
    `External documentation. <https://man.openbsd.org/smtpd-filters#>`__ """
    
    CONNECT = ("connect", Stream.FILTER, 2)
    """ This request is emitted after connection, before the banner is displayed.
    `External documentation. <https://man.openbsd.org/smtpd-filters#connect>`__ """
    
    HELO = ("helo", Stream.FILTER, 1)
    """ This request is emitted after the client has emitted ``HELO``.
    `External documentation. <https://man.openbsd.org/smtpd-filters#hello>`__ """
    
    EHLO = ("ehlo", Stream.FILTER, 1)
    """ This request is emitted after the client has emitted ``EHLO``.
    `External documentation. <https://man.openbsd.org/smtpd-filters#ehlo>`__ """
    
    STARTTLS = ("starttls", Stream.FILTER, 1)
    """ This request is emitted after the client has requested ``STARTTLS``.
    `External documentation. <https://man.openbsd.org/smtpd-filters#starttls>`__ """
    
    AUTH = ("auth", Stream.FILTER, 1)
    """ This request is emitted after the client has requested ``AUTH``.
    `External documentation. <https://man.openbsd.org/smtpd-filters#auth>`__ """
    
    MAIL_FROM = ("mail-from", Stream.FILTER, 1)
    """ This request is emitted after the client has requested ``MAIL FROM``.
    `External documentation. <https://man.openbsd.org/smtpd-filters#mail-from>`__ """
    
    RCPT_TO = ("rcpt-to", Stream.FILTER, 1)
    """ This request is emitted after the client has requested ``RCPT TO``.
    `External documentation. <https://man.openbsd.org/smtpd-filters#rcpt-to>`__ """
    
    DATA = ("data", Stream.FILTER)
    """ This request is emitted after the client has requested ``DATA``.
    `External documentation. <https://man.openbsd.org/smtpd-filters#data>`__ """
    
    DATA_LINE = ("data-line", Stream.FILTER, 1)
    """ This request is emitted for each line of input in the ``DATA`` phase.
    `External documentation. <https://man.openbsd.org/smtpd-filters#data-line>`__ """
    
    COMMIT = ("commit", Stream.FILTER)
    """ This request is emitted after the final single dot is received.
    `External documentation. <https://man.openbsd.org/smtpd-filters#commit>`__ """
    
    READY = "ready"
    """ This event is either emitted at the end of protocol handshake ``config|ready``. Or it signals the end of the
    register phase ``register|ready``."""
    
    def __new__(cls, value: str, stream: Stream | None = None, parameter_count: int = 0,
                has_optional_last_param: bool = False) -> 'Event':
        """
        Create a new event enumeration member.
        
        :param value: The value of the event, as it is used in the API.
        :type value: str
        :param stream: The stream for which this event will be used, or ``None`` to signal a special value.
        :type stream: Stream | None
        :param parameter_count: The numer of parameters this event has.
        :type parameter_count: int
        :param has_optional_last_param: ``True`` if the last parameter is optional, ``False`` otherwise.
        :type has_optional_last_param: bool
        :return: The newly created event enum member.
        :rtype: Event
        """
        
        event = object.__new__(cls)
        event._value_ = value
        event.stream = stream
        event.parameter_count = parameter_count
        event.has_optional_last_param = has_optional_last_param
        return event
    
    def __bool__(self) -> bool:
        """
        Implement truth value testing for this enumeration.
        
        :return: ``False`` if the enumeration member is ``Event.UNKNOWN``, ``True`` for all other enumeration members.
        :rtype: bool
        """
        
        return self is not Event.UNKNOWN
    
    def __str__(self) -> str:
        """
        Retrieve the string representation of this event.
        
        :return: The string which represents this event.
        :rtype: str
        """
        
        return str(self.value)
    
    def __repr__(self) -> str:
        """
        Retrieve the representation of this event.
        
        :return: The representation of this event.
        :rtype: str
        """
        
        return f"{self.__class__.__name__}.{self.name}"
    
    @classmethod
    def _missing_(cls, value: object) -> 'Event':
        """
        A method for looking up values in ``Event``. The value will be searched case-insensitive.
        
        :param value: The case-insensitive value to search for.
        :type value: object
        :return: The matched event, or ``Event.UNKNOWN`` if the value is not a string or does not match a defined event.
        :rtype: Event
        """
        
        if not isinstance(value, str):
            return Event.UNKNOWN
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        return Event.UNKNOWN
    
    @classmethod
    def all_events(cls, stream: Stream) -> list['Event']:
        """
        Retrieve the list containing all events for the given stream.
        
        :param stream: The stream for which to retrieve all events.
        :return: A list containing all events for the given stream, or an empty list if the given stream can not be
        registered for receiving events.
        :rtype: list[Event]
        """
        
        if not stream or not stream.can_register:
            return []
        
        events: list['Event'] = []
        for member in cls:
            if stream == member.stream:
                events.append(member)
        return events
