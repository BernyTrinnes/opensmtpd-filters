from enum import Enum, unique


@unique
class Stream(Enum):
    """ Streams supported by the OpenSMTPd filter API. """
    
    UNKNOWN = "unknown"
    """ An unknown/invalid stream. """
    
    CONFIG = "config"
    """ The configuration stream - it is only used during the protocol handshake.
    `External documentation. <https://man.openbsd.org/smtpd-filters#CONFIGURATION>`__ """
    
    REPORT = ("report", True)
    """ The stream for report events.
    `External documentation. <https://man.openbsd.org/smtpd-filters#PROTOCOL>`__ """
    
    FILTER = ("filter", True)
    """ The stream for filter requests.
    `External documentation. <https://man.openbsd.org/smtpd-filters#PROTOCOL>`__ """
    
    def __new__(cls, value: str, can_register: bool = False) -> 'Stream':
        """
        Create a new stream enumeration member.
        
        :param value: The value of the stream, as it is used in the API.
        :type value: str
        :param can_register: ``True`` if this stream can register to handle API events, ``False`` otherwise.
        :type can_register: bool
        :return: The newly created stream enum member.
        :rtype: Stream
        """
        
        stream = object.__new__(cls)
        stream._value_ = value
        stream.can_register = can_register
        return stream
    
    def __bool__(self) -> bool:
        """
        Implement truth value testing for this enumeration.
        
        :return: ``False`` if the enumeration member is ``Stream.UNKNOWN``, ``True`` for all other enumeration members.
        :rtype: bool
        """
        
        return self is not Stream.UNKNOWN
    
    def __str__(self) -> str:
        """
        Retrieve the string representation of this stream.
        
        :return: The string which represents this stream.
        :rtype: str
        """
        
        return str(self.value)
    
    def __repr__(self) -> str:
        """
        Retrieve the representation of this stream.
        
        :return: The representation of this stream.
        :rtype: str
        """
        
        return f"{self.__class__.__name__}.{self.name}"
    
    @classmethod
    def _missing_(cls, value: object) -> 'Stream':
        """
        A method for looking up values in ``Stream``. The value will be searched case-insensitive.
        
        :param value: The case-insensitive value to search for.
        :type value: object
        :return: The matched stream, or ``Stream.UNKNOWN`` if the value is not a string or does not match a defined
        stream.
        :rtype: Stream
        """
        
        if not isinstance(value, str):
            return Stream.UNKNOWN
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        return Stream.UNKNOWN
